const crypto = require('crypto');

/**
 * Configuración de secretos del Gateway. Debe mantenerse alineada con
 * packages/backend/shared/securityConfig.ts (mismas reglas, mismos valores en el entorno).
 *
 * - No existe ningún valor de respaldo: sin secretos válidos el Gateway no arranca.
 * - Nunca se registra el valor de un secreto.
 */

const JWT_ALGORITHMS = ['HS256'];
const MIN_SECRET_BYTES = 32;
const INTERNAL_AUTH_HEADER = 'x-internal-api-secret';

// Huellas SHA-256 de valores ya publicados en el repositorio (no se guarda el valor).
const COMPROMISED_SECRET_SHA256 = new Set([
    '8c59680ad221909f9a77909ecb11c64321667d3ce51b0f524516ecbd66b398ba',
    '92b5d5c63b9a0a84dec71603db4f4326aed706a8d376af6c301b4345e8577418',
]);

class SecretConfigError extends Error {}

function validateSecret(name, value) {
    if (value === undefined || String(value).trim() === '') {
        throw new SecretConfigError(`${name} no está definido. Configure la variable de entorno antes de iniciar.`);
    }
    if (Buffer.byteLength(value, 'utf8') < MIN_SECRET_BYTES) {
        throw new SecretConfigError(`${name} es demasiado corto: se requieren al menos ${MIN_SECRET_BYTES} bytes.`);
    }
    if (COMPROMISED_SECRET_SHA256.has(crypto.createHash('sha256').update(value, 'utf8').digest('hex'))) {
        throw new SecretConfigError(`${name} coincide con un valor publicado en el repositorio y no puede utilizarse.`);
    }
    return value;
}

function loadSecurityConfig(env = process.env) {
    const jwtSecret = validateSecret('JWT_SECRET', env.JWT_SECRET);
    const internalApiSecret = validateSecret('INTERNAL_API_SECRET', env.INTERNAL_API_SECRET);
    if (jwtSecret === internalApiSecret) {
        throw new SecretConfigError('JWT_SECRET e INTERNAL_API_SECRET deben ser valores distintos.');
    }
    return { jwtSecret, internalApiSecret };
}

module.exports = {
    JWT_ALGORITHMS,
    MIN_SECRET_BYTES,
    INTERNAL_AUTH_HEADER,
    SecretConfigError,
    loadSecurityConfig,
};
