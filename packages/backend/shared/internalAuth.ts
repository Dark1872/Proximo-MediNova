import { timingSafeEqual, createHash } from 'node:crypto';
import type { Request, Response, NextFunction } from 'express';
import { INTERNAL_AUTH_HEADER, getInternalApiSecret } from './securityConfig.js';

/** Rutas que pueden responder sin pasar por el Gateway (health check de la plataforma). */
const PUBLIC_PATHS = new Set<string>(['/api/health']);

function sameSecret(provided: string, expected: string): boolean {
  // Se comparan los hash para obtener longitudes iguales y una comparación en tiempo constante.
  const a = createHash('sha256').update(provided, 'utf8').digest();
  const b = createHash('sha256').update(expected, 'utf8').digest();
  return timingSafeEqual(a, b);
}

/**
 * Exige que toda petición a /api/* provenga del Gateway, que se autentica con
 * INTERNAL_API_SECRET en la cabecera x-internal-api-secret.
 * Es una capa adicional: no sustituye la autenticación JWT ni la autorización por rol.
 */
export function requireInternalGateway(req: Request, res: Response, next: NextFunction): void {
  if (PUBLIC_PATHS.has(req.path)) {
    next();
    return;
  }
  const provided = req.headers[INTERNAL_AUTH_HEADER];
  if (typeof provided !== 'string' || provided.length === 0 || !sameSecret(provided, getInternalApiSecret())) {
    res.status(403).json({ success: false, message: 'Acceso directo al servicio no permitido' });
    return;
  }
  next();
}
