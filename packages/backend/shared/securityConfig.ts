import { createHash } from 'node:crypto';
import type { Algorithm } from 'jsonwebtoken';

/**
 * Configuración de secretos del Backend.
 *
 * - No existe ningún valor de respaldo: si falta un secreto, la aplicación no debe arrancar.
 * - Nunca se registra el valor de un secreto en logs ni en mensajes de error.
 */

export const JWT_ALGORITHMS: Algorithm[] = ['HS256'];
export const JWT_EXPIRES_IN = '24h';
export const MIN_SECRET_BYTES = 32;

/** Cabecera con la que el Gateway se autentica ante el Backend. */
export const INTERNAL_AUTH_HEADER = 'x-internal-api-secret';

/**
 * Huellas SHA-256 de valores que ya fueron publicados en el repositorio
 * (antiguo secreto de respaldo y el literal de render.yaml). Se rechazan aunque
 * cumplan la longitud mínima. Solo se guarda el hash, nunca el valor.
 */
const COMPROMISED_SECRET_SHA256 = new Set<string>([
  '8c59680ad221909f9a77909ecb11c64321667d3ce51b0f524516ecbd66b398ba',
  '92b5d5c63b9a0a84dec71603db4f4326aed706a8d376af6c301b4345e8577418',
]);

export class SecretConfigError extends Error {}

function validateSecret(name: string, value: string | undefined): string {
  if (value === undefined || value.trim() === '') {
    throw new SecretConfigError(`${name} no está definido. Configure la variable de entorno antes de iniciar.`);
  }
  if (Buffer.byteLength(value, 'utf8') < MIN_SECRET_BYTES) {
    throw new SecretConfigError(`${name} es demasiado corto: se requieren al menos ${MIN_SECRET_BYTES} bytes.`);
  }
  if (COMPROMISED_SECRET_SHA256.has(createHash('sha256').update(value, 'utf8').digest('hex'))) {
    throw new SecretConfigError(`${name} coincide con un valor publicado en el repositorio y no puede utilizarse.`);
  }
  return value;
}

export interface SecurityConfig {
  jwtSecret: string;
  internalApiSecret: string;
}

/** Valida todos los secretos requeridos. Lanza SecretConfigError si alguno es inválido. */
export function loadSecurityConfig(env: NodeJS.ProcessEnv = process.env): SecurityConfig {
  const jwtSecret = validateSecret('JWT_SECRET', env.JWT_SECRET);
  const internalApiSecret = validateSecret('INTERNAL_API_SECRET', env.INTERNAL_API_SECRET);
  if (jwtSecret === internalApiSecret) {
    throw new SecretConfigError('JWT_SECRET e INTERNAL_API_SECRET deben ser valores distintos.');
  }
  return { jwtSecret, internalApiSecret };
}

/** Secreto JWT vigente. Se valida en cada lectura; nunca devuelve un valor por defecto. */
export function getJwtSecret(): string {
  return validateSecret('JWT_SECRET', process.env.JWT_SECRET);
}

/** Secreto de autenticación interna Gateway → Backend. */
export function getInternalApiSecret(): string {
  return validateSecret('INTERNAL_API_SECRET', process.env.INTERNAL_API_SECRET);
}
