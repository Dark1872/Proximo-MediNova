import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import Database from './db.js';
import { JWT_ALGORITHMS, getJwtSecret } from './securityConfig.js';

export type UserRole = 'cliente' | 'farmaceutico' | 'admin';

export interface AuthenticatedUser {
  id: number;
  name: string;
  email: string;
  role: UserRole;
}

export interface JwtPayloadData {
  id: number;
  email: string;
  role: string;
  iat?: number;
  exp?: number;
}

/**
 * Middleware para exigir y validar estrictamente un JWT firmado con HS256.
 * Se eliminó cualquier mecanismo de fallback que acepte tokens en Base64 o correos directos.
 */
export async function requireAuth(req: Request, res: Response, next: NextFunction): Promise<void> {
  const authHeader = req.headers['authorization'];

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    res.status(401).json({ success: false, message: 'Token de autenticación requerido' });
    return;
  }

  const token = authHeader.slice(7).trim();
  if (!token) {
    res.status(401).json({ success: false, message: 'Token de autenticación requerido' });
    return;
  }

  let secret: string;
  try {
    secret = getJwtSecret();
  } catch {
    console.error('[Auth] JWT_SECRET ausente o inválido: no se puede validar el token.');
    res.status(500).json({ success: false, message: 'Error interno al verificar autenticación' });
    return;
  }

  let decoded: JwtPayloadData;
  try {
    // Firma, algoritmo permitido y expiración se validan aquí; ningún claim se usa antes de esta verificación.
    decoded = jwt.verify(token, secret, { algorithms: JWT_ALGORITHMS }) as JwtPayloadData;
  } catch (err: any) {
    if (err?.name === 'TokenExpiredError') {
      res.status(401).json({ success: false, message: 'Token expirado' });
      return;
    }
    res.status(401).json({ success: false, message: 'Token inválido' });
    return;
  }

  // Identidad de sesión: el identificador estable del usuario (claim `id`), no el email.
  // Así un cambio de email no invalida la sesión ni puede hacer que un token antiguo
  // autentique a otra cuenta que registre después ese email.
  const userId = decoded ? String(decoded.id ?? '') : '';
  if (!/^\d+$/.test(userId)) {
    res.status(401).json({ success: false, message: 'Token inválido: estructura no reconocida' });
    return;
  }

  try {
    const pool = Database.getInstance().getPool();
    const result = await pool.query(
      'SELECT id, name, email, role FROM public.usuarios WHERE id = $1',
      [userId]
    );

    if (result.rows.length === 0) {
      res.status(401).json({ success: false, message: 'Usuario no encontrado o dado de baja' });
      return;
    }

    const usuario: AuthenticatedUser = result.rows[0];
    (req as any).user = decoded;
    (req as any).usuarioActual = usuario;
    next();
  } catch (error) {
    console.error('[Auth] Error verificando usuario en base de datos:', error);
    res.status(500).json({ success: false, message: 'Error interno al verificar autenticación' });
  }
}

/**
 * Middleware para exigir uno de los roles indicados. El rol se toma de la base de datos
 * (usuarioActual), nunca del claim `role` del JWT.
 */
export function requireRole(...roles: UserRole[]) {
  return async function roleGuard(req: Request, res: Response, next: NextFunction): Promise<void> {
    await requireAuth(req, res, async () => {
      const usuario = (req as any).usuarioActual as AuthenticatedUser | undefined;
      if (!usuario || !roles.includes(usuario.role)) {
        const message = roles.length === 1 && roles[0] === 'admin'
          ? 'Acceso denegado. Se requiere rol de administrador'
          : 'Acceso denegado. Rol no autorizado para esta operación';
        res.status(403).json({ success: false, message });
        return;
      }
      next();
    });
  };
}

/**
 * Middleware para exigir rol de administrador sobre un usuario previamente autenticado.
 */
export const requireAdmin = requireRole('admin');
