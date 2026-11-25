import Database from '../shared/db.js';
import { hashPassword } from '../shared/password.js';
import type { UserRole } from '../shared/authMiddleware.js';

export const VALID_ROLES: UserRole[] = ['cliente', 'farmaceutico', 'admin'];

export interface CreateUsuarioResult {
  status: number;
  body: Record<string, unknown>;
}

/**
 * Valida y crea un usuario con el rol indicado por el servidor.
 * El rol NUNCA proviene directamente del cuerpo de la petición: quien llama decide
 * el rol (registro público => 'cliente'; ruta administrativa => rol validado).
 */
export async function createUsuario(
  input: { name?: unknown; email?: unknown; password?: unknown },
  role: UserRole
): Promise<CreateUsuarioResult> {
  const name = typeof input.name === 'string' ? input.name : '';
  const email = typeof input.email === 'string' ? input.email : '';
  const password = typeof input.password === 'string' ? input.password : '';

  const errors: string[] = [];
  if (name.trim().length < 2) errors.push('Nombre: mínimo 2 caracteres');
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) errors.push('Email inválido');
  if (password.length < 4) errors.push('Contraseña: mínimo 4 caracteres');
  if (!VALID_ROLES.includes(role)) errors.push('Rol inválido');
  if (errors.length > 0) return { status: 400, body: { success: false, errors } };

  try {
    const pool = Database.getInstance().getPool();
    const em = email.trim().toLowerCase();
    const exists = await pool.query('SELECT id FROM public.usuarios WHERE email = $1', [em]);
    if (exists.rows.length > 0) {
      return { status: 409, body: { success: false, errors: ['El email ya está registrado'] } };
    }
    const hashed = await hashPassword(password);
    const result = await pool.query(
      'INSERT INTO public.usuarios (name, email, password, role) VALUES ($1, $2, $3, $4) RETURNING id, name, email, role, created_at',
      [name.trim(), em, hashed, role]
    );
    return { status: 201, body: { success: true, data: result.rows[0] } };
  } catch (err: any) {
    console.error('[Usuarios] Error al crear usuario:', err?.message);
    return { status: 500, body: { success: false, message: 'Error al crear usuario' } };
  }
}
