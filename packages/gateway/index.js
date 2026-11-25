require('dotenv').config();
const express = require('express');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const { JWT_ALGORITHMS, INTERNAL_AUTH_HEADER, SecretConfigError, loadSecurityConfig } = require('./securityConfig');
const {
    resolveBackendUrl, resolveBackendPublicUrl, describeBackendOrigin, selectBackendOrigin, watchPrivateNetwork, BackendUrlError,
} = require('./backendUrl');
const {
    createBackendClient, loadResilienceConfig, sendBackendError, classifyBackendError, seg, BackendConfigError,
} = require('./backendClient');

// Validación de configuración antes de abrir el puerto. Sin secretos válidos el Gateway no arranca.
let securityConfig;
let BACKEND_URL;
let BACKEND_PUBLIC_URL;
let resilience;
try {
    securityConfig = loadSecurityConfig();
    BACKEND_URL = resolveBackendUrl();
    BACKEND_PUBLIC_URL = resolveBackendPublicUrl();
    resilience = loadResilienceConfig();
} catch (err) {
    const reason = err instanceof SecretConfigError || err instanceof BackendUrlError || err instanceof BackendConfigError
        ? err.message
        : 'Error desconocido validando la configuración';
    console.error(`[Gateway] Arranque cancelado: ${reason}`);
    process.exit(1);
}
const JWT_SECRET = securityConfig.jwtSecret;

const app = express();
const PORT = process.env.PORT || 8080;

// IP real del cliente detrás del proxy de Render. Con "trust proxy" = N, Express toma la
// N-ésima entrada desde la DERECHA de X-Forwarded-For (las que añaden los proxies de
// confianza); lo que el cliente escriba a la izquierda se ignora. Por defecto 1 (Render).
const TRUST_PROXY_HOPS = Number(process.env.GATEWAY_TRUST_PROXY_HOPS ?? 1);
if (!Number.isInteger(TRUST_PROXY_HOPS) || TRUST_PROXY_HOPS < 0 || TRUST_PROXY_HOPS > 5) {
    console.error('[Gateway] Arranque cancelado: GATEWAY_TRUST_PROXY_HOPS debe ser un entero entre 0 y 5.');
    process.exit(1);
}
app.set('trust proxy', TRUST_PROXY_HOPS);

// Cabecera con la IP del cliente que el Gateway envía al Backend. La fija SIEMPRE el Gateway
// (las cabeceras del cliente nunca se reenvían) y el Backend solo la acepta en peticiones
// autenticadas con INTERNAL_API_SECRET.
const CLIENT_IP_HEADER = 'x-farmalink-client-ip';
const AI_PROXY_TIMEOUT_MS = parseInt(process.env.AI_PROXY_TIMEOUT_MS || '15000', 10);
// Autocompletado: si el Backend no responde pronto, la sugerencia ya no le sirve al usuario.
const SUGERENCIAS_DEADLINE_MS = Math.min(10000, resilience.totalTimeoutMs);

// Cliente HTTP hacia el Backend: toda petición se autentica con INTERNAL_API_SECRET, los GET se
// reintentan ante fallos transitorios y cada fallo queda registrado (ver backendClient.js).
const backend = createBackendClient({
    origin: BACKEND_URL,
    defaultHeaders: { [INTERNAL_AUTH_HEADER]: securityConfig.internalApiSecret },
    config: resilience,
});
let backendNetwork = describeBackendOrigin(BACKEND_URL).network;

console.log('[Gateway] Secretos de seguridad validados.');

/** Reenvía Authorization solo si el cliente lo envió. */
function withAuth(req, extra = {}) {
    return req.headers.authorization ? { Authorization: req.headers.authorization, ...extra } : { ...extra };
}

app.use(cors());
app.use(express.json());

app.get('/health', (_req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Diagnóstico: estado y latencia del Backend (sin URLs internas ni secretos). 200 si responde, 503 si no.
app.get('/health/deep', async (_req, res) => {
    const result = await backend.checkHealth();
    const backendInfo = { status: result.status, latencyMs: result.latencyMs, network: backendNetwork };
    if (!result.ok) {
        backendInfo.reason = result.reason;
        if (result.httpStatus) backendInfo.httpStatus = result.httpStatus;
    }
    res.set('Cache-Control', 'no-store');
    res.status(result.ok ? 200 : 503).json({
        status: result.ok ? 'ok' : 'degraded',
        gateway: 'ok',
        backend: backendInfo,
        timestamp: new Date().toISOString(),
    });
});

/* ================= AI ASSISTANT ================= */

app.get('/api/ai/health', async (req, res) => {
    const startedAt = Date.now();
    try {
        const response = await backend.get('/api/ai/health', { timeoutMs: AI_PROXY_TIMEOUT_MS });
        console.log('[Gateway][AI] GET /api/ai/health <- backend', {
            status: response.status,
            ms: Date.now() - startedAt,
            enabled: response.data?.enabled,
            model: response.data?.model,
        });
        res.json(response.data);
    } catch (err) {
        sendBackendError(res, err);
    }
});

app.post('/api/ai/assistant', async (req, res) => {
    const startedAt = Date.now();
    const message = typeof req.body?.message === 'string' ? req.body.message.trim() : '';
    console.log('[Gateway][AI] POST /api/ai/assistant -> backend', {
        messageLength: message.length,
        hasAuth: Boolean(req.headers.authorization),
    });
    try {
        const response = await backend.post('/api/ai/assistant', req.body, {
            headers: withAuth(req, { 'Content-Type': 'application/json' }),
            timeoutMs: AI_PROXY_TIMEOUT_MS,
        });
        console.log('[Gateway][AI] POST /api/ai/assistant <- backend', {
            status: response.status,
            ms: Date.now() - startedAt,
            traceId: response.data?.traceId,
            success: response.data?.success,
            policy: response.data?.policy,
            action: response.data?.action,
        });
        res.json(response.data);
    } catch (err) {
        // Además del cuerpo estándar, se mantienen los campos que el cliente del asistente espera.
        sendBackendError(res, err, {
            unavailableExtra: { policy: 'blocked', action: 'none', params: {}, traceId: 'gateway-backend-unavailable' },
        });
    }
});

/* ================= AUTH (delegado al backend: bcrypt + JWT) ================= */

app.post('/api/auth/login', async (req, res) => {
    try {
        const response = await backend.post('/api/auth/login', req.body, {
            headers: { [CLIENT_IP_HEADER]: req.ip || '' },
        });
        const d = response.data;
        if (d.token && d.user) {
            return res.json({ token: d.token, user: d.user });
        }
        res.json(d);
    } catch (err) {
        sendBackendError(res, err);
    }
});

/** Registro público: el Backend crea siempre rol 'cliente'; no se reenvía ningún campo de rol. */
app.post('/api/auth/register', async (req, res) => {
    try {
        const { name, email, password } = req.body || {};
        if (!name || !email || !password) {
            return res.status(400).json({ success: false, message: 'Nombre, email y contraseña son obligatorios' });
        }
        const response = await backend.post('/api/auth/register', {
            name: String(name).trim(),
            email: String(email).trim().toLowerCase(),
            password: String(password),
        });
        res.status(response.status === 201 ? 201 : 200).json(response.data);
    } catch (err) {
        sendBackendError(res, err);
    }
});

/* ================= MIDDLEWARE JWT ================= */

function validateJWT(req, res, next) {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ success: false, message: 'Token requerido' });
    }
    const token = authHeader.slice(7).trim();
    if (!token) {
        return res.status(401).json({ success: false, message: 'Token requerido' });
    }
    try {
        const decoded = jwt.verify(token, JWT_SECRET, { algorithms: JWT_ALGORITHMS });
        req.user = decoded;
        next();
    } catch (err) {
        return res.status(401).json({ success: false, message: 'Token inválido o expirado' });
    }
}

function requireAdmin(req, res, next) {
    if (!req.user || req.user.role !== 'admin') {
        return res.status(403).json({ success: false, message: 'Acceso denegado. Se requiere rol de administrador.' });
    }
    next();
}

/* ================= PROXIES ================= */

// Medicamentos - CRUD
app.get('/api/medicamentos', async (req, res) => {
    try {
        const query = new URLSearchParams(req.query).toString();
        const response = await backend.get(`/api/medicamentos?${query}`);
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// Detalle de medicamento: público (catálogo navegable)
app.get('/api/medicamentos/:id', async (req, res) => {
    try {
        const response = await backend.get(`/api/medicamentos/${seg(req.params.id)}`, { headers: withAuth(req) });
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

app.post('/api/medicamentos', validateJWT, requireAdmin, async (req, res) => {
    try {
        const response = await backend.post('/api/medicamentos', req.body, { headers: withAuth(req) });
        res.status(201).json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

app.put('/api/medicamentos/:id', validateJWT, requireAdmin, async (req, res) => {
    try {
        const response = await backend.put(`/api/medicamentos/${seg(req.params.id)}`, req.body, { headers: withAuth(req) });
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

app.delete('/api/medicamentos/:id', validateJWT, requireAdmin, async (req, res) => {
    try {
        const response = await backend.delete(`/api/medicamentos/${seg(req.params.id)}`, { headers: withAuth(req) });
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// Farmacias
app.get('/api/farmacias/cercanas', async (req, res) => {
    try {
        const { lat, lng } = req.query;
        // Mismos valores que antes (String(undefined) → "undefined", que el Backend rechaza con 400), ahora codificados.
        const query = new URLSearchParams({ lat: String(lat), lng: String(lng) }).toString();
        const response = await backend.get(`/api/farmacias/cercanas?${query}`);
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

app.get('/api/farmacias', async (req, res) => {
    try {
        const response = await backend.get('/api/farmacias');
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// Precios
app.get('/api/precios', validateJWT, async (req, res) => {
    try {
        const response = await backend.get('/api/precios', { headers: withAuth(req) });
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// Crear/actualizar precios: solo administradores (el Backend vuelve a verificar el rol en la BD).
app.post('/api/precios', validateJWT, requireAdmin, async (req, res) => {
    try {
        const response = await backend.post('/api/precios', req.body, {
            headers: withAuth(req, { 'x-user-email': req.user?.email || 'sistema' }),
        });
        res.status(response?.status || 201).json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// Comparar precios: GET /api/precios/comparar/:medicamentoId?orden=asc|desc|reciente
app.get('/api/precios/comparar/:medicamentoId', validateJWT, async (req, res) => {
    try {
        const orden = req.query.orden || 'asc';
        const query = new URLSearchParams({ orden: String(orden) }).toString();
        const response = await backend.get(`/api/precios/comparar/${seg(req.params.medicamentoId)}?${query}`, {
            headers: withAuth(req),
        });
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// Actualizar precio: solo administradores (el Backend vuelve a verificar el rol en la BD).
app.put('/api/precios/:id', validateJWT, requireAdmin, async (req, res) => {
    try {
        const response = await backend.put(`/api/precios/${seg(req.params.id)}`, req.body, { headers: withAuth(req) });
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// Categorías
app.get('/api/categorias', async (req, res) => {
    try {
        const response = await backend.get('/api/categorias');
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// Dashboard - Agrega datos consolidados
app.get('/api/dashboard', validateJWT, async (req, res) => {
    try {
        const response = await backend.get('/api/dashboard', { headers: withAuth(req) });
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// Home público - datos mínimos sin autenticación. Si el Backend no responde se mantiene la
// respuesta degradada de siempre (200 con datos vacíos); el fallo queda registrado en el log.
app.get('/api/home', async (req, res) => {
    try {
        const response = await backend.get('/api/home');
        res.json(response.data);
    } catch {
        res.json({ success: true, farmCount: 0, categorias: [] });
    }
});

// Sugerencias (búsqueda de medicamentos). Ante cualquier fallo se mantiene la respuesta de
// siempre (200 con lista vacía) para no romper el autocompletado.
app.get('/api/sugerencias', async (req, res) => {
    const empty = { success: true, sugerencias: [], estrategiaUsada: '' };
    try {
        const { q } = req.query;
        if (!q || String(q).trim().length < 2) {
            return res.json(empty);
        }
        const query = new URLSearchParams({ q: String(q) }).toString();
        // Try the dedicated sugerencias endpoint first (returns already formatted data)
        try {
            const sugResponse = await backend.get(`/api/sugerencias?${query}`, { deadlineMs: SUGERENCIAS_DEADLINE_MS });
            if (sugResponse.data && sugResponse.data.success) {
                return res.json(sugResponse.data);
            }
        } catch (e) {
            // Si el Backend no está disponible, el respaldo tampoco respondería: no se insiste.
            if (classifyBackendError(e).kind === 'unavailable') return res.json(empty);
        }
        const response = await backend.get(`/api/medicamentos?${query}`, { deadlineMs: SUGERENCIAS_DEADLINE_MS });
        const medicamentos = response.data?.data || response.data || [];
        const sugerencias = medicamentos.slice(0, 10).map((m) => ({
            _id: m._id || m.id,
            name: m.name || m.nombre || '',
            lab: m.lab || m.laboratorio || '',
            category: m.category || m.categoria || m.categoria_nombre || '',
            description: m.description || m.descripcion || '',
            estrategiaUsada: 'coincidencia_parcial'
        }));
        res.json({ success: true, sugerencias, estrategiaUsada: 'coincidencia_parcial' });
    } catch {
        res.json(empty);
    }
});

/* ================= USUARIOS ================= */

app.get('/api/usuarios/public/equipo', async (req, res) => {
    try {
        const response = await backend.get('/api/usuarios/public/equipo');
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

app.get('/api/usuarios/public/:id', async (req, res) => {
    try {
        const response = await backend.get(`/api/usuarios/public/${seg(req.params.id)}`);
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// GET /api/usuarios/me — cualquier usuario autenticado puede ver su propio perfil
// IMPORTANTE: debe ir ANTES de /:id para que Express no lo capture como id="me"
app.get('/api/usuarios/me', validateJWT, async (req, res) => {
    try {
        const response = await backend.get('/api/usuarios/me', { headers: withAuth(req) });
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

app.get('/api/usuarios', validateJWT, requireAdmin, async (req, res) => {
    try {
        const response = await backend.get('/api/usuarios', { headers: withAuth(req) });
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

app.get('/api/usuarios/:id', validateJWT, requireAdmin, async (req, res) => {
    try {
        const response = await backend.get(`/api/usuarios/${seg(req.params.id)}`, { headers: withAuth(req) });
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

app.post('/api/usuarios', validateJWT, requireAdmin, async (req, res) => {
    try {
        const response = await backend.post('/api/usuarios', req.body, { headers: withAuth(req) });
        res.status(201).json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// PATCH /api/usuarios/:id/team-member — solo admin puede activar/desactivar miembro del equipo
app.patch('/api/usuarios/:id/team-member', validateJWT, requireAdmin, async (req, res) => {
    try {
        const response = await backend.patch(`/api/usuarios/${seg(req.params.id)}/team-member`, req.body, {
            headers: withAuth(req),
        });
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// PUT /api/usuarios/:id — el propio usuario puede editarse; admin puede editar a cualquiera.
// La identidad sale del JWT verificado (claim `id`), sin consultar la lista de usuarios; el
// Backend vuelve a comprobar identidad y rol contra la base de datos.
app.put('/api/usuarios/:id', validateJWT, async (req, res) => {
    if (!/^\d+$/.test(String(req.params.id))) {
        return res.status(400).json({ success: false, message: 'ID inválido' });
    }
    const idObjetivo = Number(req.params.id);
    const solicitanteId = Number(req.user.id);
    const esAdmin = req.user.role === 'admin';

    if (!esAdmin && solicitanteId !== idObjetivo) {
        return res.status(403).json({ success: false, message: 'No tienes permiso para editar este usuario' });
    }

    // Proteger contra escalada de privilegios: campos privilegiados solo los edita un admin
    const updatePayload = { ...req.body };
    if (!esAdmin) {
        delete updatePayload.role;
        delete updatePayload.is_team_member;
    }

    try {
        const response = await backend.put(`/api/usuarios/${idObjetivo}`, updatePayload, { headers: withAuth(req) });
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

app.delete('/api/usuarios/:id', validateJWT, requireAdmin, async (req, res) => {
    try {
        const response = await backend.delete(`/api/usuarios/${seg(req.params.id)}`, { headers: withAuth(req) });
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// Búsqueda avanzada con fuzzy search y filtros
app.get('/api/busqueda', async (req, res) => {
    try {
        const query = new URLSearchParams(req.query).toString();
        const response = await backend.get(`/api/busqueda?${query}`);
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

app.get('/api/busqueda/filtros', async (req, res) => {
    try {
        const response = await backend.get('/api/busqueda/filtros');
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

// Historial de precios: GET /api/precios/historial/:medicamentoId (público)
app.get('/api/precios/historial/:medicamentoId', async (req, res) => {
    try {
        const response = await backend.get(`/api/precios/historial/${seg(req.params.medicamentoId)}`);
        res.json(response.data);
    } catch (err) { sendBackendError(res, err); }
});

/* ================= SERVER ================= */

/**
 * Tras abrir el puerto: elige red privada o alternativa pública (y lo registra) y lanza una
 * petición de salud que despierta al Backend en paralelo al arranque del Gateway.
 */
async function initBackendConnection() {
    const selected = await selectBackendOrigin({ primary: BACKEND_URL, fallback: BACKEND_PUBLIC_URL });
    backend.setOrigin(selected.origin);
    backendNetwork = selected.network;
    if (selected.usingFallback) {
        watchPrivateNetwork({
            primary: BACKEND_URL,
            onAvailable: (origin) => { backend.setOrigin(origin); backendNetwork = 'private'; },
        });
    }
    const health = await backend.checkHealth(resilience.totalTimeoutMs);
    console.log('[Gateway] Comprobación inicial del Backend', { status: health.status, ms: health.latencyMs, network: backendNetwork });
}

app.listen(PORT, () => {
    console.log(`Gateway corriendo en http://localhost:${PORT}`);
    initBackendConnection().catch((err) => {
        console.error('[Gateway] Error en la comprobación inicial del Backend', { name: err?.name, message: err?.message });
    });
});
