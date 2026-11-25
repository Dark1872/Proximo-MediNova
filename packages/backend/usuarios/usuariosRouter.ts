import express from 'express';
import Database from '../shared/db.js';
import { requireAuth, requireAdmin, UserRole } from '../shared/authMiddleware.js';
import { hashPassword } from '../shared/password.js';
import { createUsuario, VALID_ROLES } from './createUsuario.js';

const router = express.Router();

// Auto-migration: ensure required columns exist
async function ensureColumns(pool: any) {
  const migrations = [
    `ALTER TABLE public.usuarios ADD COLUMN IF NOT EXISTS is_team_member BOOLEAN NOT NULL DEFAULT false`,
    `ALTER TABLE public.usuarios ADD COLUMN IF NOT EXISTS phone VARCHAR(30)`,
    `ALTER TABLE public.usuarios ADD COLUMN IF NOT EXISTS bio TEXT`,
    `ALTER TABLE public.usuarios ADD COLUMN IF NOT EXISTS profile_picture TEXT`,
  ];
  for (const sql of migrations) {
    try { await pool.query(sql); } catch { /* ignorar si ya existe */ }
  }
}

let migrationDone = false;
async function withMigration(pool: any) {
  if (!migrationDone) { await ensureColumns(pool); migrationDone = true; }
}

type UsuariosSchema = {
  telefono: boolean;
  avatar_url: boolean;
  preferencias: boolean;
};

let cachedUsuariosSchema: UsuariosSchema | null = null;

async function getUsuariosSchema(pool: any): Promise<UsuariosSchema> {
  if (cachedUsuariosSchema) return cachedUsuariosSchema;

  const columns = ['telefono', 'avatar_url', 'preferencias'];
  const result = await pool.query(
    `SELECT column_name
     FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name = 'usuarios'
       AND column_name = ANY($1::text[])`,
    [columns]
  );
  const set = new Set<string>(result.rows.map((r: any) => r.column_name));
  cachedUsuariosSchema = {
    telefono: set.has('telefono'),
    avatar_url: set.has('avatar_url'),
    preferencias: set.has('preferencias'),
  };
  return cachedUsuariosSchema;
}

// GET /api/usuarios/public/equipo — Lista pública de miembros del equipo (sin auth)
router.get('/public/equipo', async (_req, res) => {
  try {
    const pool = Database.getInstance().getPool();
    await withMigration(pool);
    const result = await pool.query(
      `SELECT id, name, role, phone, profile_picture, bio, created_at
       FROM public.usuarios
       WHERE is_team_member = true
       ORDER BY created_at ASC`
    );
    res.json({ success: true, data: result.rows });
  } catch (err: any) {
    console.error('[Usuarios] Error en GET /public/equipo:', err.message);
    res.status(500).json({ success: false, message: 'Error al obtener equipo', error: err.message });
  }
});

// GET /api/usuarios/public/:id — Perfil público individual (sin auth)
// Solo expone perfiles marcados como miembros del equipo; el resto de usuarios responde 404.
router.get('/public/:id', async (req, res) => {
  try {
    const pool = Database.getInstance().getPool();
    await withMigration(pool);
    const result = await pool.query(
      `SELECT id, name, role, phone, profile_picture, bio, created_at
       FROM public.usuarios WHERE id = $1 AND is_team_member = true`,
      [req.params.id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ success: false, message: 'Usuario no encontrado' });
    }
    res.json({ success: true, data: result.rows[0] });
  } catch (err: any) {
    res.status(500).json({ success: false, message: 'Error al obtener perfil', error: err.message });
  }
});

// GET /api/usuarios/me - Retorna el usuario autenticado (usa el token)
router.get('/me', requireAuth, async (req, res) => {
  const usuarioActual = (req as any).usuarioActual;
  console.log('[Usuarios] GET /me — usuario:', usuarioActual.email);
  try {
    const pool = Database.getInstance().getPool();
    const result = await pool.query(
      `SELECT id, name, email, role, phone, profile_picture, bio, created_at
       FROM public.usuarios WHERE id = $1`,
      [usuarioActual.id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ success: false, message: 'Usuario no encontrado' });
    }
    console.log('[Usuarios] GET /me — datos retornados para id:', usuarioActual.id);
    res.json({ success: true, data: result.rows[0] });
  } catch (err: any) {
    console.error('[Usuarios] Error en GET /me:', err.message);
    res.status(500).json({ success: false, message: 'Error al obtener usuario', error: err.message });
  }
});

// GET /api/usuarios - Listar todos los usuarios (solo admin)
router.get('/', requireAuth, async (req, res) => {
  const usuarioActual = (req as any).usuarioActual;
  console.log('[Usuarios] GET / — usuario:', usuarioActual.email, 'role:', usuarioActual.role);
  if (usuarioActual.role !== 'admin') {
    return res.status(403).json({ success: false, message: 'Se requiere rol de administrador' });
  }
  try {
    const pool = Database.getInstance().getPool();
    await withMigration(pool);
    const result = await pool.query(
      `SELECT id, name, email, role, phone, profile_picture, bio, is_team_member, created_at
       FROM public.usuarios ORDER BY created_at DESC`
    );
    res.json({ success: true, data: result.rows });
  } catch (err: any) {
    res.status(500).json({ success: false, message: 'Error al obtener usuarios', error: err.message });
  }
});

// PATCH /api/usuarios/:id/team-member — Activar/desactivar como miembro del equipo (solo admin)
router.patch('/:id/team-member', requireAuth, async (req, res) => {
  const usuarioActual = (req as any).usuarioActual;
  if (usuarioActual.role !== 'admin') {
    return res.status(403).json({ success: false, message: 'Se requiere rol de administrador' });
  }
  const { is_team_member } = req.body;
  if (typeof is_team_member !== 'boolean') {
    return res.status(400).json({ success: false, message: 'is_team_member debe ser boolean' });
  }
  try {
    const pool = Database.getInstance().getPool();
    await withMigration(pool);
    const result = await pool.query(
      `UPDATE public.usuarios SET is_team_member = $1 WHERE id = $2
       RETURNING id, name, email, role, phone, profile_picture, bio, is_team_member, created_at`,
      [is_team_member, req.params.id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ success: false, message: 'Usuario no encontrado' });
    }
    res.json({ success: true, data: result.rows[0] });
  } catch (err: any) {
    res.status(500).json({ success: false, message: 'Error al actualizar estado', error: err.message });
  }
});

// GET /api/usuarios/:id - Obtener usuario por ID (el propio usuario o un administrador)
router.get('/:id', requireAuth, async (req, res) => {
  const usuarioActual = (req as any).usuarioActual;
  const idParam = Array.isArray(req.params.id) ? req.params.id[0] : req.params.id;
  if (!/^\d+$/.test(String(idParam))) {
    return res.status(400).json({ success: false, message: 'ID inválido' });
  }
  if (usuarioActual.role !== 'admin' && String(usuarioActual.id) !== String(idParam)) {
    return res.status(403).json({ success: false, message: 'No tienes permiso para consultar este usuario' });
  }
  try {
    const pool = Database.getInstance().getPool();
    const result = await pool.query(
      'SELECT id, name, email, role, phone, profile_picture, bio, created_at FROM public.usuarios WHERE id = $1',
      [req.params.id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ success: false, message: 'Usuario no encontrado' });
    }
    res.json({ success: true, data: result.rows[0] });
  } catch (err: any) {
    res.status(500).json({ success: false, message: 'Error al obtener usuario', error: err.message });
  }
});

// POST /api/usuarios - Creación ADMINISTRATIVA de usuarios (cualquier rol).
// requireAdmin obtiene el rol real del solicitante desde la base de datos.
// El registro público está en POST /api/auth/register y siempre crea 'cliente'.
router.post('/', requireAdmin, async (req, res) => {
  const { name, email, password, role } = req.body || {};
  if (role !== undefined && !VALID_ROLES.includes(role)) {
    return res.status(400).json({ success: false, errors: ['Rol inválido'] });
  }
  const roleAsignado: UserRole = role ?? 'cliente';
  const result = await createUsuario({ name, email, password }, roleAsignado);
  res.status(result.status).json(result.body);
});

// PUT /api/usuarios/:id - Actualizar usuario
router.put('/:id', requireAuth, async (req, res) => {
  const usuarioActual = (req as any).usuarioActual;
  const idParam = Array.isArray(req.params.id) ? req.params.id[0] : req.params.id;
  if (!/^\d+$/.test(String(idParam))) {
    return res.status(400).json({ success: false, message: 'ID inválido' });
  }
  const idObjetivo = parseInt(idParam, 10);

  if (usuarioActual.role !== 'admin' && Number(usuarioActual.id) !== idObjetivo) {
    return res.status(403).json({ success: false, message: 'No tienes permiso para editar este usuario' });
  }

  const {
    name, email, role, password, telefono, avatar_url, preferencias,
  } = req.body || {};
  const { phone, bio, profile_picture } = req.body || {};

  // Solo administradores pueden alterar el rol; para usuarios estándar se ignora
  const roleAActualizar = usuarioActual.role === 'admin' ? role : undefined;

  const errors: string[] = [];
  if (name !== undefined && (typeof name !== 'string' || name.trim().length < 2)) errors.push('Nombre: mínimo 2 caracteres');
  if (email !== undefined && (typeof email !== 'string' || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))) errors.push('Email inválido');
  // Campos de perfil: texto o null (null borra el valor). Otros tipos se rechazan con 400 en lugar de provocar un 500.
  for (const [campo, valor] of [['phone', phone], ['bio', bio], ['profile_picture', profile_picture]] as const) {
    if (valor !== undefined && valor !== null && typeof valor !== 'string') errors.push(`${campo}: debe ser texto o null`);
  }
  if (typeof phone === 'string' && phone.trim().length > 20) errors.push('phone: máximo 20 caracteres');
  if (roleAActualizar !== undefined && !['cliente', 'farmaceutico', 'admin'].includes(roleAActualizar)) errors.push('Rol inválido');
  if (telefono !== undefined && telefono !== null && String(telefono).length > 20) {
    errors.push('Teléfono: máximo 20 caracteres');
  }
  if (avatar_url !== undefined && avatar_url !== null && String(avatar_url).trim().length > 500) {
    errors.push('URL de foto: máximo 500 caracteres');
  }
  let preferenciasJson: string | null = null;
  if (preferencias !== undefined) {
    let pref: unknown = preferencias;
    if (typeof preferencias === 'string') {
      try {
        pref = JSON.parse(preferencias);
      } catch {
        errors.push('Preferencias: JSON inválido');
      }
    }
    if (pref !== undefined && pref !== null && typeof pref !== 'object') {
      errors.push('Preferencias: debe ser un objeto');
    } else if (pref !== undefined && errors.length === 0) {
      preferenciasJson = JSON.stringify(pref === null ? {} : pref);
    }
  }
  if (errors.length > 0) return res.status(400).json({ success: false, errors });

  try {
    const pool = Database.getInstance().getPool();
    // Garantiza que existan las columnas de perfil (phone, bio, profile_picture) antes de escribirlas.
    await withMigration(pool);
    if (email) {
      const exists = await pool.query('SELECT id FROM public.usuarios WHERE email = $1 AND id != $2', [email.trim().toLowerCase(), idObjetivo]);
      if (exists.rows.length > 0) {
        return res.status(409).json({ success: false, errors: ['El email ya está registrado'] });
      }
    }

    const setClauses: string[] = [];
    const values: unknown[] = [];
    let idx = 1;
    if (name !== undefined) { setClauses.push(`name = $${idx++}`); values.push(name.trim()); }
    if (email !== undefined) { setClauses.push(`email = $${idx++}`); values.push(email.trim().toLowerCase()); }
    if (roleAActualizar !== undefined) { setClauses.push(`role = $${idx++}`); values.push(roleAActualizar); }
    if (password !== undefined && String(password).length >= 4) {
      setClauses.push(`password = $${idx++}`);
      values.push(await hashPassword(String(password)));
    }

    // Handle profile fields (phone, bio, profile_picture)
    if (phone !== undefined) { setClauses.push(`phone = $${idx++}`); values.push(phone?.trim() || null); }
    if (bio !== undefined) { setClauses.push(`bio = $${idx++}`); values.push(bio?.trim() || null); }
    if (profile_picture !== undefined) { setClauses.push(`profile_picture = $${idx++}`); values.push(profile_picture?.trim() || null); }
    const pideCamposPerfil = phone !== undefined || bio !== undefined || profile_picture !== undefined;

    if (setClauses.length === 0) return res.status(400).json({ success: false, message: 'Nada que actualizar' });

    values.push(idObjetivo);
    const returningCols: string[] = ['id', 'name', 'email', 'role', 'phone', 'profile_picture', 'bio', 'created_at'];
    let result;
    try {
      result = await pool.query(
        `UPDATE public.usuarios SET ${setClauses.join(', ')} WHERE id = $${idx}
         RETURNING ${returningCols.join(', ')}`,
        values
      );
    } catch (err: any) {
      const msg = String(err?.message || err);
      if (msg.includes('column') && msg.includes('does not exist')) {
        // Si se pidieron campos de perfil y sus columnas no existen, no se informa un éxito falso.
        if (pideCamposPerfil) {
          console.error('[Usuarios] PUT: columnas de perfil ausentes en la BD:', msg);
          return res.status(500).json({ success: false, message: 'No se pudieron guardar los campos de perfil' });
        }
        // Fallback: sólo columnas base.
        const fallbackClauses: string[] = [];
        const fallbackValues: unknown[] = [];
        let fIdx = 1;

        if (name !== undefined) { fallbackClauses.push(`name = $${fIdx++}`); fallbackValues.push(name.trim()); }
        if (email !== undefined) { fallbackClauses.push(`email = $${fIdx++}`); fallbackValues.push(email.trim().toLowerCase()); }
        if (roleAActualizar !== undefined) { fallbackClauses.push(`role = $${fIdx++}`); fallbackValues.push(roleAActualizar); }
        if (password !== undefined && String(password).length >= 4) {
          fallbackClauses.push(`password = $${fIdx++}`);
          fallbackValues.push(await hashPassword(String(password)));
        }

        if (fallbackClauses.length === 0) return res.status(400).json({ success: false, message: 'Nada que actualizar' });

        fallbackValues.push(idObjetivo);
        const fallbackReturning = ['id', 'name', 'email', 'role', 'created_at'];
        result = await pool.query(
          `UPDATE public.usuarios SET ${fallbackClauses.join(', ')} WHERE id = $${fIdx}
           RETURNING ${fallbackReturning.join(', ')}`,
          fallbackValues
        );
      } else {
        throw err;
      }
    }
    if (result.rows.length === 0) return res.status(404).json({ success: false, message: 'Usuario no encontrado' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err: any) {
    res.status(500).json({ success: false, message: 'Error al actualizar usuario', error: err.message });
  }
});

// DELETE /api/usuarios/:id - Eliminar usuario (solo admin)
router.delete('/:id', requireAdmin, async (req, res) => {
  try {
    const pool = Database.getInstance().getPool();
    const result = await pool.query('DELETE FROM public.usuarios WHERE id = $1 RETURNING id', [req.params.id]);
    if (result.rows.length === 0) return res.status(404).json({ success: false, message: 'Usuario no encontrado' });
    res.json({ success: true, message: 'Usuario eliminado' });
  } catch (err: any) {
    res.status(500).json({ success: false, message: 'Error al eliminar usuario', error: err.message });
  }
});

export default router;
