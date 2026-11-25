/**
 * Resolución de la URL del Backend y selección de red (privada / pública).
 *
 * BACKEND_URL acepta:
 *  - host:puerto sin esquema: farmalink-backend:10000   (dirección interna de Render, "hostport")
 *  - URL completa:            http://farmalink-backend:10000
 *                             https://farmalink-backend.onrender.com   (URL pública)
 *
 * La dirección interna de Render (panel del Backend > Connect > Internal, o
 * `fromService.property: hostport` en render.yaml) no incluye esquema; se antepone http://
 * porque el tráfico de la red privada no pasa por TLS ni por el proxy público (Cloudflare).
 *
 * BACKEND_PUBLIC_URL (opcional) es la alternativa pública. Solo se usa si BACKEND_URL es una
 * dirección privada y no es alcanzable al arrancar; se registra en el log y se vuelve a comprobar
 * periódicamente la red privada para regresar a ella en cuanto esté disponible.
 */
const net = require('net');

class BackendUrlError extends Error {}

const DEFAULT_BACKEND_URL = 'http://localhost:3001';
const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1', '[::1]', '::1']);

function parseBackendOrigin(rawValue, varName) {
    const raw = String(rawValue || '').trim();
    const withScheme = /^[a-z][a-z0-9+.-]*:\/\//i.test(raw) ? raw : `http://${raw}`;

    let parsed;
    try {
        parsed = new URL(withScheme);
    } catch {
        throw new BackendUrlError(`${varName} no es una URL ni un host:puerto válido.`);
    }
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        throw new BackendUrlError(`${varName} debe usar http:// o https://.`);
    }
    if (parsed.username || parsed.password) {
        throw new BackendUrlError(`${varName} no debe incluir credenciales.`);
    }
    if ((parsed.pathname && parsed.pathname !== '/') || parsed.search || parsed.hash) {
        throw new BackendUrlError(`${varName} debe ser solo el origen (sin ruta, query ni fragmento).`);
    }
    return parsed.origin;
}

function resolveBackendUrl(env = process.env) {
    const raw = String(env.BACKEND_URL || '').trim() || DEFAULT_BACKEND_URL;
    return parseBackendOrigin(raw, 'BACKEND_URL');
}

/** Alternativa pública opcional (BACKEND_PUBLIC_URL). Devuelve null si no está configurada. */
function resolveBackendPublicUrl(env = process.env) {
    const raw = String(env.BACKEND_PUBLIC_URL || '').trim();
    return raw ? parseBackendOrigin(raw, 'BACKEND_PUBLIC_URL') : null;
}

/**
 * Tipo de red de un origen:
 *  - local:   localhost / 127.0.0.1 (desarrollo)
 *  - private: nombre de host sin dominio (p. ej. farmalink-backend:10000), propio de la red privada de Render
 *  - public:  cualquier otro (p. ej. *.onrender.com, que pasa por Cloudflare)
 */
function describeBackendOrigin(origin) {
    const { hostname, host } = new URL(origin);
    if (LOCAL_HOSTS.has(hostname) || hostname.startsWith('127.')) return { network: 'local', host };
    if (!hostname.includes('.') && !hostname.includes(':') && !hostname.startsWith('[')) return { network: 'private', host };
    return { network: 'public', host };
}

/** Comprueba que el origen acepta conexiones TCP (no envía datos ni secretos). */
function probeTcp(origin, timeoutMs = 3000) {
    const url = new URL(origin);
    const port = Number(url.port || (url.protocol === 'https:' ? 443 : 80));
    const host = url.hostname.replace(/^\[|\]$/g, '');
    return new Promise((resolve) => {
        const socket = net.connect({ host, port });
        const finish = (ok, reason) => { socket.destroy(); resolve({ ok, reason }); };
        socket.setTimeout(timeoutMs, () => finish(false, 'timeout'));
        socket.once('connect', () => finish(true));
        socket.once('error', (err) => finish(false, err.code || 'error'));
    });
}

/**
 * Elige el origen del Backend al arrancar y lo registra en el log (sin secretos).
 * Devuelve { origin, network, usingFallback }.
 */
async function selectBackendOrigin({ primary, fallback, probe = probeTcp, logger = console }) {
    const p = describeBackendOrigin(primary);
    if (p.network === 'public') {
        logger.warn(`[Gateway] Backend por URL PÚBLICA (${p.host}). Ese tráfico pasa por Cloudflare y puede recibir 429 "Just a moment...". Configure BACKEND_URL con la dirección privada de Render.`);
        return { origin: primary, network: 'public', usingFallback: false };
    }
    if (p.network === 'local') {
        logger.info(`[Gateway] Backend local (${p.host}).`);
        return { origin: primary, network: 'local', usingFallback: false };
    }

    const result = await probe(primary);
    if (result.ok) {
        logger.info(`[Gateway] Backend por RED PRIVADA de Render (${p.host}).`);
        return { origin: primary, network: 'private', usingFallback: false };
    }
    if (fallback) {
        const f = describeBackendOrigin(fallback);
        logger.warn(`[Gateway] Red privada NO disponible (${p.host}: ${result.reason}). Se usa la alternativa ${f.network === 'public' ? 'PÚBLICA' : 'configurada'} (${f.host}) hasta que la red privada responda.`);
        return { origin: fallback, network: f.network, usingFallback: true };
    }
    logger.error(`[Gateway] Red privada NO disponible (${p.host}: ${result.reason}) y no hay BACKEND_PUBLIC_URL. Las peticiones responderán 503 hasta que el Backend sea alcanzable.`);
    return { origin: primary, network: 'private', usingFallback: false };
}

/**
 * Mientras se usa la alternativa pública, comprueba periódicamente la red privada y vuelve a ella
 * en cuanto responde. Devuelve una función para detener la comprobación.
 */
function watchPrivateNetwork({ primary, onAvailable, intervalMs = 60000, probe = probeTcp, logger = console }) {
    const timer = setInterval(async () => {
        const result = await probe(primary);
        if (result.ok) {
            clearInterval(timer);
            logger.info(`[Gateway] Red privada disponible de nuevo (${describeBackendOrigin(primary).host}); se deja de usar la URL pública.`);
            onAvailable(primary);
        }
    }, intervalMs);
    timer.unref();
    return () => clearInterval(timer);
}

module.exports = {
    resolveBackendUrl,
    resolveBackendPublicUrl,
    describeBackendOrigin,
    probeTcp,
    selectBackendOrigin,
    watchPrivateNetwork,
    BackendUrlError,
    DEFAULT_BACKEND_URL,
};
