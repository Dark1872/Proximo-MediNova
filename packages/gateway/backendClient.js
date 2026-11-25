/**
 * Comunicación resiliente Gateway → Backend.
 *
 * - Reintenta SOLO peticiones GET ante errores de conexión, tiempo agotado y 502/503/504,
 *   con espera creciente (por defecto 1 s, 3 s y 6 s) más una variación aleatoria, siempre
 *   dentro de un plazo total por petición (por defecto 45 s). POST, PUT, PATCH y DELETE
 *   nunca se reintentan (no son idempotentes).
 * - Registra cada fallo hacia el Backend (método, ruta normalizada, intento, resultado y
 *   duración). Nunca registra cabeceras, tokens, cuerpos ni query string.
 * - sendBackendError() traduce cualquier fallo a una respuesta útil para el cliente:
 *     · el Backend respondió con JSON      → mismo código y mismo cuerpo;
 *     · el Backend no respondió (conexión, tiempo agotado, desafío de Cloudflare,
 *       502/503/504 o 429 sin JSON)         → 503 backend_unavailable + Retry-After;
 *     · respuesta no JSON con otro código   → mismo código con un JSON genérico (nunca HTML).
 */
const axiosLib = require('axios');

class BackendConfigError extends Error {}

const RETRY_AFTER_SECONDS = 10;
const UNAVAILABLE_BODY = Object.freeze({
    success: false,
    error: 'backend_unavailable',
    message: 'El servicio se está iniciando, inténtalo en unos segundos',
});

const RETRYABLE_METHODS = new Set(['GET']);
const RETRYABLE_STATUS = new Set([502, 503, 504]);
// Errores de axios que no son fallos de red (configuración, cancelación): no se reintentan.
const NON_TRANSIENT_CODES = new Set(['ERR_CANCELED', 'ERR_INVALID_URL', 'ERR_BAD_OPTION', 'ERR_BAD_OPTION_VALUE', 'ERR_NOT_SUPPORT']);
const TIMEOUT_CODES = new Set(['ECONNABORTED', 'ETIMEDOUT']);
const JITTER_RATIO = 0.3;      // hasta +30 % sobre cada espera
const MIN_ATTEMPT_MS = 250;    // no se inicia un intento si quedan menos de 250 ms de plazo
const MAX_RETRIES = 3;

const DEFAULTS = Object.freeze({
    totalTimeoutMs: 45000,
    attemptTimeoutMs: 20000,
    retryDelaysMs: [1000, 3000, 6000],
    deepHealthTimeoutMs: 15000,
});

function readInt(env, key, def, min, max) {
    const raw = env[key];
    if (raw === undefined || String(raw).trim() === '') return def;
    const n = Number(String(raw).trim());
    if (!Number.isInteger(n) || n < min || n > max) {
        throw new BackendConfigError(`${key} debe ser un entero entre ${min} y ${max}.`);
    }
    return n;
}

/** Lee la configuración de resiliencia (variables opcionales; valores por defecto seguros). */
function loadResilienceConfig(env = process.env) {
    const totalTimeoutMs = readInt(env, 'GATEWAY_BACKEND_TIMEOUT_MS', DEFAULTS.totalTimeoutMs, 100, 120000);
    const attemptTimeoutMs = readInt(env, 'GATEWAY_BACKEND_ATTEMPT_TIMEOUT_MS', DEFAULTS.attemptTimeoutMs, 100, 120000);
    const deepHealthTimeoutMs = readInt(env, 'GATEWAY_DEEP_HEALTH_TIMEOUT_MS', DEFAULTS.deepHealthTimeoutMs, 100, 60000);

    let retryDelaysMs = [...DEFAULTS.retryDelaysMs];
    const rawDelays = env.GATEWAY_RETRY_DELAYS_MS;
    if (rawDelays !== undefined && String(rawDelays).trim() !== '') {
        const parts = String(rawDelays).split(',').map((s) => s.trim());
        if (parts.length > MAX_RETRIES || parts.some((p) => !/^\d+$/.test(p) || Number(p) > 60000)) {
            throw new BackendConfigError(
                `GATEWAY_RETRY_DELAYS_MS debe ser una lista de hasta ${MAX_RETRIES} esperas en ms (p. ej. 1000,3000,6000).`
            );
        }
        retryDelaysMs = parts.map(Number);
    }
    return { totalTimeoutMs, attemptTimeoutMs, retryDelaysMs, deepHealthTimeoutMs };
}

function isJsonBody(response) {
    return response.data !== null && typeof response.data === 'object' && !Buffer.isBuffer(response.data);
}

/** Desafío anti-bots de Cloudflare ("Just a moment..."): nunca es una respuesta del Backend. */
function isCloudflareChallenge(response) {
    const headers = response.headers || {};
    if (String(headers['cf-mitigated'] || '').toLowerCase() === 'challenge') return true;
    if (typeof response.data !== 'string') return false;
    return /just a moment|cf-chl|challenge-platform|cf_chl_opt|attention required/i.test(response.data.slice(0, 20000));
}

function isTimeout(err) {
    return TIMEOUT_CODES.has(err.code);
}

/**
 * Clasifica un error de una llamada al Backend.
 *  kind: 'response'    — el Backend respondió con JSON (se reenvía tal cual)
 *        'unavailable' — el Backend no respondió (reason: timeout | connection | cloudflare_challenge | http_5xx | http_429)
 *        'unexpected'  — respuesta no JSON con un código que no indica indisponibilidad
 *        'bad_request' — la ruta construida no es segura (p. ej. segmento "..")
 *        'internal'    — error del propio Gateway
 */
function classifyBackendError(err) {
    if (err && err.code === 'GATEWAY_UNSAFE_PATH') return { kind: 'bad_request' };
    if (!err || !err.isAxiosError) return { kind: 'internal' };
    const res = err.response;
    if (!res) {
        if (NON_TRANSIENT_CODES.has(err.code)) return { kind: 'internal' };
        return { kind: 'unavailable', reason: isTimeout(err) ? 'timeout' : 'connection' };
    }
    if (isCloudflareChallenge(res)) return { kind: 'unavailable', reason: 'cloudflare_challenge', status: res.status };
    if (isJsonBody(res)) {
        return { kind: 'response', status: res.status, body: res.data, retryAfter: res.headers?.['retry-after'] };
    }
    if (RETRYABLE_STATUS.has(res.status) || res.status === 429) {
        return { kind: 'unavailable', reason: `http_${res.status}`, status: res.status };
    }
    return { kind: 'unexpected', status: res.status };
}

/** ¿Merece la pena reintentar (solo GET)? Conexión, tiempo agotado y 502/503/504. */
function isTransient(err) {
    if (!err || !err.isAxiosError) return false;
    if (!err.response) return !NON_TRANSIENT_CODES.has(err.code);
    return RETRYABLE_STATUS.has(err.response.status) && !isCloudflareChallenge(err.response);
}

function describeOutcome(err) {
    if (err && err.response) {
        return isCloudflareChallenge(err.response) ? `cloudflare_challenge(${err.response.status})` : `http_${err.response.status}`;
    }
    if (err && isTimeout(err)) return 'timeout';
    return `connection(${(err && err.code) || 'unknown'})`;
}

/** Ruta sin query string y sin identificadores ni datos libres (para logs). */
function pathForLog(url) {
    const pathname = String(url || '').split('?')[0];
    return pathname
        .split('/')
        .map((seg) => (/^\d+$/.test(seg) ? ':id' : (seg.length > 40 || seg.includes('@') || seg.includes('%')) ? ':param' : seg))
        .join('/');
}

/** Segmentos "." o ".." (también codificados) harían que la URL apuntara a otra ruta del Backend. */
function assertSafePath(url) {
    const pathname = String(url || '').split('?')[0];
    const unsafe = pathname.split('/').some((seg) => {
        let decoded = seg;
        try { decoded = decodeURIComponent(seg); } catch { return true; }
        return decoded === '.' || decoded === '..';
    });
    if (unsafe || !pathname.startsWith('/api/')) {
        const err = new Error('Ruta hacia el Backend no permitida');
        err.code = 'GATEWAY_UNSAFE_PATH';
        throw err;
    }
}

/** Codifica un parámetro de ruta recibido del cliente antes de insertarlo en la URL del Backend. */
function seg(value) {
    return encodeURIComponent(String(value));
}

const defaultSleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * @param {object} opts
 * @param {string} opts.origin             Origen del Backend (http(s)://host[:puerto])
 * @param {object} opts.defaultHeaders     Cabeceras para todas las llamadas (secreto interno)
 * @param {object} [opts.config]           Resultado de loadResilienceConfig()
 * @param {object} [opts.logger]           console por defecto
 */
function createBackendClient({ origin, defaultHeaders = {}, config = loadResilienceConfig({}), logger = console, random = Math.random, sleep = defaultSleep }) {
    const http = axiosLib.create({ headers: defaultHeaders });
    let currentOrigin = origin;

    async function request({ method = 'GET', url, data, headers, timeoutMs, deadlineMs }) {
        const verb = String(method).toUpperCase();
        assertSafePath(url);
        const retryable = RETRYABLE_METHODS.has(verb);
        const startedAt = Date.now();
        const deadline = startedAt + (deadlineMs ?? config.totalTimeoutMs);
        const maxAttempts = retryable ? config.retryDelaysMs.length + 1 : 1;
        // GET: cada intento tiene su propio límite (un intento colgado no consume todo el plazo).
        // Resto de métodos: un único intento con el plazo total (salvo timeoutMs explícito).
        const attemptCap = timeoutMs ?? (retryable ? config.attemptTimeoutMs : config.totalTimeoutMs);
        const logPath = pathForLog(url);

        for (let attempt = 1; ; attempt += 1) {
            const attemptStart = Date.now();
            const timeout = Math.max(1, Math.min(attemptCap, deadline - attemptStart));
            try {
                const response = await http.request({ method: verb, baseURL: currentOrigin, url, data, headers, timeout });
                if (attempt > 1) {
                    logger.info('[Gateway][backend] recuperado tras reintento', {
                        method: verb, path: logPath, attempt, status: response.status, totalMs: Date.now() - startedAt,
                    });
                }
                return response;
            } catch (err) {
                const ms = Date.now() - attemptStart;
                const outcome = describeOutcome(err);
                const ordinaryAnswer = err?.response && isJsonBody(err.response) && err.response.status < 500;
                let delay = null;
                if (retryable && attempt < maxAttempts && isTransient(err)) {
                    const base = config.retryDelaysMs[attempt - 1];
                    const candidate = base + Math.floor(random() * base * JITTER_RATIO);
                    if (Date.now() + candidate + MIN_ATTEMPT_MS < deadline) delay = candidate;
                }
                const entry = { method: verb, path: logPath, attempt, outcome, ms };
                if (ordinaryAnswer) {
                    // 4xx con JSON: respuesta normal del Backend (credenciales, validación...).
                    logger.info('[Gateway][backend] respuesta de error', entry);
                } else if (delay !== null) {
                    logger.warn('[Gateway][backend] fallo, se reintenta', { ...entry, retryInMs: delay });
                } else {
                    logger.error('[Gateway][backend] fallo', { ...entry, totalMs: Date.now() - startedAt, retried: attempt > 1 });
                }
                if (delay === null) throw err;
                await sleep(delay);
            }
        }
    }

    /** Diagnóstico: un único intento contra /api/health (sin reintentos). Nunca expone URLs. */
    async function checkHealth(timeoutMs = config.deepHealthTimeoutMs) {
        const startedAt = Date.now();
        try {
            const response = await http.request({ method: 'GET', baseURL: currentOrigin, url: '/api/health', timeout: timeoutMs });
            const latencyMs = Date.now() - startedAt;
            const ok = response.data?.status === 'ok';
            return { ok, status: ok ? 'ok' : 'error', httpStatus: response.status, latencyMs };
        } catch (err) {
            const latencyMs = Date.now() - startedAt;
            const c = classifyBackendError(err);
            const reason = c.reason || (c.status ? `http_${c.status}` : 'error');
            logger.error('[Gateway][backend] comprobación de salud fallida', { outcome: describeOutcome(err), ms: latencyMs });
            return { ok: false, status: c.kind === 'unavailable' ? 'unavailable' : 'error', httpStatus: err.response?.status, reason, latencyMs };
        }
    }

    return {
        request,
        get: (url, opts = {}) => request({ ...opts, method: 'GET', url }),
        post: (url, data, opts = {}) => request({ ...opts, method: 'POST', url, data }),
        put: (url, data, opts = {}) => request({ ...opts, method: 'PUT', url, data }),
        patch: (url, data, opts = {}) => request({ ...opts, method: 'PATCH', url, data }),
        delete: (url, opts = {}) => request({ ...opts, method: 'DELETE', url }),
        checkHealth,
        getOrigin: () => currentOrigin,
        setOrigin: (next) => { currentOrigin = next; },
    };
}

/**
 * Manejador común de errores para las rutas proxy.
 * @param {object} [opts.unavailableExtra] campos adicionales para el 503 (p. ej. el contrato del asistente IA)
 */
function sendBackendError(res, err, { unavailableExtra, logger = console } = {}) {
    if (res.headersSent) return;
    const c = classifyBackendError(err);
    switch (c.kind) {
        case 'response':
            if (c.retryAfter) res.set('Retry-After', String(c.retryAfter));
            res.status(c.status).json(c.body);
            return;
        case 'unavailable':
            res.set('Retry-After', String(RETRY_AFTER_SECONDS));
            res.status(503).json({ ...UNAVAILABLE_BODY, ...(unavailableExtra || {}), ...UNAVAILABLE_BODY });
            return;
        case 'unexpected':
            res.status(c.status).json({
                success: false,
                error: 'backend_error',
                message: 'El servicio interno respondió de forma inesperada.',
                upstreamStatus: c.status,
            });
            return;
        case 'bad_request':
            res.status(400).json({ success: false, message: 'Parámetro inválido' });
            return;
        default:
            logger.error('[Gateway] Error interno', { name: err?.name, message: err?.message });
            res.status(500).json({ success: false, error: 'gateway_error', message: 'Error interno del Gateway' });
    }
}

module.exports = {
    BackendConfigError,
    RETRY_AFTER_SECONDS,
    UNAVAILABLE_BODY,
    DEFAULTS,
    loadResilienceConfig,
    classifyBackendError,
    isCloudflareChallenge,
    isTransient,
    pathForLog,
    assertSafePath,
    seg,
    createBackendClient,
    sendBackendError,
};
