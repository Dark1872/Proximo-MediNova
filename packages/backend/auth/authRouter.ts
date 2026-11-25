import express from 'express';
import jwt from 'jsonwebtoken';
import Database from '../shared/db.js';
import { verifyPassword } from '../shared/password.js';
import { JWT_EXPIRES_IN, getJwtSecret } from '../shared/securityConfig.js';
import { createUsuario } from '../usuarios/createUsuario.js';
import { LoginThrottle, CLIENT_IP_HEADER, resolveClientIp } from './loginThrottle.js';

const router = express.Router();

// ── Control de Fuerza Bruta / Intentos Repetidos de Login ──────────────────────
const loginThrottle = new LoginThrottle();

// ── POST /api/auth/login ───────────────────────────────────────────────────────
router.post('/login', async (req, res) => {
  const { email, password } = req.body || {};
  // La IP del cliente la fija el Gateway (cabecera controlada por él, nunca reenviada desde el cliente).
  // Solo llegan aquí peticiones autenticadas con INTERNAL_API_SECRET (requireInternalGateway en app.ts).
  const clientIp = resolveClientIp(req.headers[CLIENT_IP_HEADER], req.ip || req.socket.remoteAddress);

  if (!email || typeof email !== 'string') {
    return res.status(400).json({ success: false, message: 'Email requerido' });
  }
  if (!password || typeof password !== 'string') {
    return res.status(400).json({ success: false, message: 'Contraseña requerida' });
  }

  const throttle = loginThrottle.check(email, clientIp);
  if (throttle.blocked) {
    return res.status(429).json({
      success: false,
      message: `Demasiados intentos fallidos. Intente nuevamente en ${Math.ceil(throttle.remainingSecs / 60)} minutos.`,
    });
  }

  try {
    const pool = Database.getInstance().getPool();
    const result = await pool.query(
      'SELECT id, name, email, role, password FROM usuarios WHERE email = $1',
      [email.trim().toLowerCase()]
    );

    if (result.rows.length === 0) {
      loginThrottle.recordFailure(email, clientIp);
      return res.status(401).json({ success: false, message: 'Credenciales inválidas' });
    }

    const row = result.rows[0];
    const ok = await verifyPassword(password, row.password);
    if (!ok) {
      loginThrottle.recordFailure(email, clientIp);
      return res.status(401).json({ success: false, message: 'Credenciales inválidas' });
    }

    // Login exitoso: limpiar el contador email+IP de este cliente
    loginThrottle.recordSuccess(email, clientIp);

    try {
      await pool.query(
        'UPDATE usuarios SET ultimo_login = NOW() WHERE id = $1',
        [row.id]
      );
    } catch {
      // columna ultimo_login opcional si no está migrada
    }

    const token = jwt.sign(
      { id: row.id, email: row.email, role: row.role },
      getJwtSecret(),
      { expiresIn: JWT_EXPIRES_IN, algorithm: 'HS256' }
    );

    res.json({
      success: true,
      token,
      user: {
        id: row.id,
        name: row.name,
        email: row.email,
        role: row.role,
      },
    });
  } catch (error) {
    console.error('[Auth] Error en login:', error);
    res.status(500).json({ success: false, message: 'Error interno del servidor' });
  }
});

// ── POST /api/auth/register ────────────────────────────────────────────────────
// Registro público: siempre crea rol 'cliente'. Cualquier campo `role` del cuerpo se ignora.
router.post('/register', async (req, res) => {
  const { name, email, password } = req.body || {};
  const result = await createUsuario({ name, email, password }, 'cliente');
  res.status(result.status).json(result.body);
});

export default router;
