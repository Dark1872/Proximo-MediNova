// Resiliencia Gateway → Backend (fallos 500 / 429 intermitentes):
//  - manejador común de errores: el código y el cuerpo del Backend se reenvían; si el Backend no
//    responde (caído, tiempo agotado, desafío de Cloudflare) → 503 backend_unavailable + Retry-After;
//  - reintentos SOLO en GET (conexión, tiempo agotado, 502/503/504) con espera creciente y plazo total;
//  - /health/deep; selección red privada / alternativa pública; logs sin tokens ni datos personales.
// Código real: packages/gateway/index.js como proceso hijo contra un Backend simulado (sin BD ni red externa).
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import nodeHttp from 'node:http';
import net from 'node:net';
import path from 'node:path';
import express from 'express';
import { newSecret, freePort, startGateway, GATEWAY_DIR } from './support.mjs';

const require = createRequire(import.meta.url);
const {
  createBackendClient, loadResilienceConfig, BackendConfigError, DEFAULTS, UNAVAILABLE_BODY,
} = require(path.join(GATEWAY_DIR, 'backendClient.js'));
const {
  selectBackendOrigin, describeBackendOrigin, watchPrivateNetwork, probeTcp, resolveBackendPublicUrl, BackendUrlError,
} = require(path.join(GATEWAY_DIR, 'backendUrl.js'));

const JWT_SECRET = newSecret();
const INTERNAL_API_SECRET = newSecret();
// Esperas cortas para que las pruebas sean rápidas; la lógica es la misma que con 1 s / 3 s / 6 s.
const FAST = {
  GATEWAY_RETRY_DELAYS_MS: '50,100,150',
  GATEWAY_BACKEND_ATTEMPT_TIMEOUT_MS: '400',
  GATEWAY_BACKEND_TIMEOUT_MS: '3000',
  GATEWAY_DEEP_HEALTH_TIMEOUT_MS: '500',
};
const STANDARD_503 = { success: false, error: 'backend_unavailable', message: 'El servicio se está iniciando, inténtalo en unos segundos' };
const FARMACIAS = { success: true, data: [{ id: 1, name: 'Farmacia Uno' }] };
const MEDICAMENTOS = { success: true, data: [{ id: '1', name: 'Acetaminofén' }] };

// ── Backend simulado ─────────────────────────────────────────────────────────
const hits = new Map();
const seen = [];              // rutas recibidas (originalUrl) y si traían el secreto interno
const queues = {};            // comportamiento programado por clave: 'ok' | '503html' | 'reset' | 'hang'
const plan = (key, ...steps) => { queues[key] = steps; hits.set(key, 0); };
function behave(key, req, res, okBody) {
  hits.set(key, (hits.get(key) || 0) + 1);
  const step = (queues[key] && queues[key].shift()) || 'ok';
  if (step === 'hang') return;                                           // nunca responde
  if (step === 'reset') return req.socket.destroy();                     // conexión cortada
  if (step === '503html') return res.status(503).type('html').send('<html><body>Service Unavailable</body></html>');
  res.json(okBody);
}

const fake = express();
fake.use(express.json());
fake.use((req, _res, next) => {
  seen.push({ url: req.originalUrl, internal: req.headers['x-internal-api-secret'] === INTERNAL_API_SECRET });
  next();
});
fake.get('/api/health', (_req, res) => res.json({ status: 'ok' }));
fake.get('/api/farmacias', (req, res) => behave('farmacias', req, res, FARMACIAS));
fake.get('/api/medicamentos', (req, res) => behave('medicamentos', req, res, MEDICAMENTOS));
fake.get('/api/medicamentos/:id', (req, res) => res.json({ success: true, data: { id: req.params.id } }));
fake.get('/api/busqueda', (req, res) => behave('busqueda', req, res, { success: true, data: [] }));
fake.get('/api/usuarios/public/equipo', (req, res) => behave('equipo', req, res, { success: true, data: [] }));
fake.get('/api/categorias', (_req, res) => res.status(404).json({ success: false, message: 'Categoría no encontrada' }));
fake.get('/api/precios/historial/:id', (req, res) => {
  hits.set('historial', (hits.get('historial') || 0) + 1);
  res.status(429).set('cf-mitigated', 'challenge').type('html')
    .send('<!DOCTYPE html><html><head><title>Just a moment...</title></head><body>cf-chl</body></html>');
});
fake.post('/api/auth/login', (req, res) => {
  hits.set('login', (hits.get('login') || 0) + 1);
  res.status(503).type('html').send('<html>503</html>');
});
fake.post('/api/auth/register', (req, res) => behave('register', req, res, { success: true }));
// /api/busqueda/filtros no existe: Express responde su 404 HTML por defecto ("Cannot GET ...").

let fakeServer; let B; let gateway; let G; let backendPort;

test.before(async () => {
  fakeServer = fake.listen(0, '127.0.0.1');
  await new Promise((r) => fakeServer.once('listening', r));
  backendPort = fakeServer.address().port;
  B = `http://127.0.0.1:${backendPort}`;
  const gPort = await freePort();
  gateway = await startGateway({ port: gPort, env: { JWT_SECRET, INTERNAL_API_SECRET, BACKEND_URL: B, ...FAST } });
  assert.equal(gateway.started, true, gateway.stderr);
  G = `http://127.0.0.1:${gPort}`;
});

test.after(() => {
  gateway?.child?.kill();
  fakeServer?.closeAllConnections();
  fakeServer?.close();
});

async function call(base, method, url, body) {
  const res = await fetch(base + url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let json; try { json = JSON.parse(text); } catch { json = undefined; }
  return { status: res.status, retryAfter: res.headers.get('retry-after'), text, body: json };
}

function assertStandard503(r) {
  assert.equal(r.status, 503, r.text);
  assert.equal(r.retryAfter, '10');
  assert.deepEqual(r.body, STANDARD_503);
  assert.ok(!/<html|Just a moment|Request failed with status code/i.test(r.text), 'Nunca HTML ni texto de axios');
}

// ═════════════════════════════════════════════════════════════════════════════
test('Manejador común: el Backend respondió → se reenvía su código', async (t) => {
  await t.test('404 JSON del Backend → 404 con el mismo cuerpo', async () => {
    const r = await call(G, 'GET', '/api/categorias');
    assert.equal(r.status, 404);
    assert.deepEqual(r.body, { success: false, message: 'Categoría no encontrada' });
  });
  await t.test('404 HTML (ruta inexistente en el Backend) → 404 en JSON, sin HTML', async () => {
    const r = await call(G, 'GET', '/api/busqueda/filtros');
    assert.equal(r.status, 404);
    assert.equal(r.body.success, false);
    assert.equal(r.body.upstreamStatus, 404);
    assert.ok(!/<html|Cannot GET/i.test(r.text));
  });
  await t.test('El Gateway envía el secreto interno al Backend', () => {
    assert.ok(seen.length > 0 && seen.every((s) => s.internal));
  });
});

test('Reintentos de GET ante fallos transitorios', async (t) => {
  await t.test('503 HTML dos veces y luego 200 → 200 con el contrato intacto (3 llamadas)', async () => {
    plan('farmacias', '503html', '503html', 'ok');
    const r = await call(G, 'GET', '/api/farmacias');
    assert.equal(r.status, 200);
    assert.deepEqual(r.body, FARMACIAS);
    assert.equal(hits.get('farmacias'), 3);
  });
  await t.test('Conexión cortada (ECONNRESET) y luego 200 → 200', async () => {
    plan('medicamentos', 'reset', 'ok');
    const r = await call(G, 'GET', '/api/medicamentos');
    assert.equal(r.status, 200);
    assert.deepEqual(r.body, MEDICAMENTOS);
    assert.equal(hits.get('medicamentos'), 2);
  });
  await t.test('Tiempo agotado en el primer intento y luego 200 → 200', async () => {
    plan('busqueda', 'hang', 'ok');
    const r = await call(G, 'GET', '/api/busqueda?q=ace');
    assert.equal(r.status, 200);
    assert.equal(hits.get('busqueda'), 2);
  });
  await t.test('Backend colgado en todos los intentos → 503 + Retry-After dentro del plazo total', async () => {
    plan('equipo', 'hang', 'hang', 'hang', 'hang', 'hang');
    const started = Date.now();
    const r = await call(G, 'GET', '/api/usuarios/public/equipo');
    const elapsed = Date.now() - started;
    assertStandard503(r);
    assert.equal(hits.get('equipo'), 4, 'Intento inicial + 3 reintentos');
    assert.ok(elapsed < 3000 + 1500, `Respeta el plazo total (${elapsed} ms)`);
  });
  await t.test('Desafío de Cloudflare (429 HTML) → 503 estándar, sin reintentar', async () => {
    hits.set('historial', 0);
    const r = await call(G, 'GET', '/api/precios/historial/1');
    assertStandard503(r);
    assert.equal(hits.get('historial'), 1);
  });
});

test('Métodos no idempotentes: nunca se reintentan', async (t) => {
  await t.test('POST con 503 del Backend → 503 estándar y UNA sola llamada', async () => {
    hits.set('login', 0);
    const r = await call(G, 'POST', '/api/auth/login', { email: 'a@test.local', password: 'x' });
    assertStandard503(r);
    assert.equal(hits.get('login'), 1);
  });
  await t.test('POST con conexión cortada → 503 estándar y UNA sola llamada', async () => {
    plan('register', 'reset', 'ok', 'ok');
    const r = await call(G, 'POST', '/api/auth/register', { name: 'Ana', email: 'ana@test.local', password: 'Ana#Test2026' });
    assertStandard503(r);
    assert.equal(hits.get('register'), 1);
  });
});

test('Backend caído (puerto cerrado) → 503 con Retry-After, nunca 500', async (t) => {
  const deadPort = await freePort();
  const port = await freePort();
  const g2 = await startGateway({ port, env: { JWT_SECRET, INTERNAL_API_SECRET, BACKEND_URL: `http://127.0.0.1:${deadPort}`, ...FAST } });
  const G2 = `http://127.0.0.1:${port}`;
  try {
    assert.equal(g2.started, true, g2.stderr);
    for (const url of ['/api/farmacias', '/api/categorias', '/api/precios/historial/1', '/api/medicamentos']) {
      await t.test(`GET ${url} → 503`, async () => assertStandard503(await call(G2, 'GET', url)));
    }
    await t.test('POST /api/auth/login → 503 (antes respondía 401 "Error de autenticación")', async () => {
      assertStandard503(await call(G2, 'POST', '/api/auth/login', { email: 'a@test.local', password: 'x' }));
    });
    await t.test('POST /api/ai/assistant → 503 estándar conservando los campos del asistente', async () => {
      const r = await call(G2, 'POST', '/api/ai/assistant', { message: 'hola' });
      assert.equal(r.status, 503);
      assert.equal(r.retryAfter, '10');
      assert.equal(r.body.error, 'backend_unavailable');
      assert.equal(r.body.policy, 'blocked');
      assert.equal(r.body.action, 'none');
    });
    await t.test('/health/deep → 503 "degraded" sin exponer la URL interna', async () => {
      const r = await call(G2, 'GET', '/health/deep');
      assert.equal(r.status, 503);
      assert.equal(r.body.status, 'degraded');
      assert.equal(r.body.backend.status, 'unavailable');
      assert.equal(r.body.backend.reason, 'connection');
      assert.equal(typeof r.body.backend.latencyMs, 'number');
      assert.ok(!r.text.includes(String(deadPort)) && !r.text.includes('127.0.0.1'));
    });
    await t.test('/health (superficial) sigue respondiendo 200', async () => {
      assert.equal((await call(G2, 'GET', '/health')).status, 200);
    });
  } finally {
    g2.child.kill();
  }
});

test('/health/deep con el Backend activo → 200 con estado y latencia, sin URL', async () => {
  const r = await call(G, 'GET', '/health/deep');
  assert.equal(r.status, 200);
  assert.equal(r.body.status, 'ok');
  assert.equal(r.body.gateway, 'ok');
  assert.equal(r.body.backend.status, 'ok');
  assert.equal(r.body.backend.network, 'local');
  assert.equal(typeof r.body.backend.latencyMs, 'number');
  assert.ok(!r.text.includes(String(backendPort)) && !r.text.includes('127.0.0.1'));
});

test('50 peticiones seguidas a /api/medicamentos por el Gateway → 50 × 200, ninguna 429', async () => {
  plan('medicamentos');
  const statuses = [];
  for (let i = 0; i < 50; i += 1) statuses.push((await call(G, 'GET', '/api/medicamentos')).status);
  assert.deepEqual([...new Set(statuses)], [200]);
});

test('Parámetros de ruta: no permiten llegar a otra ruta del Backend', async (t) => {
  await t.test('"..%2Fusuarios" viaja codificado como un único segmento', async () => {
    const before = seen.length;
    const r = await call(G, 'GET', '/api/medicamentos/..%2Fusuarios');
    assert.equal(r.status, 200);
    assert.equal(r.body.data.id, '../usuarios');
    assert.deepEqual(seen.slice(before).map((s) => s.url), ['/api/medicamentos/..%2Fusuarios']);
  });
  await t.test('segmento "%2E%2E" → 400 sin llamar al Backend', async () => {
    const before = seen.length;
    const status = await new Promise((resolve, reject) => {
      const u = new URL(G);
      nodeHttp.get({ host: u.hostname, port: u.port, path: '/api/medicamentos/%2E%2E' }, (res) => { res.resume(); resolve(res.statusCode); })
        .on('error', reject);
    });
    assert.equal(status, 400);
    assert.equal(seen.length, before);
  });
});

// ── Unidad: cliente, configuración y selección de red ─────────────────────────
function captureLogger() {
  const lines = [];
  const push = (level) => (...args) => lines.push({ level, text: args.map((a) => (typeof a === 'string' ? a : JSON.stringify(a))).join(' ') });
  return { lines, logger: { info: push('info'), warn: push('warn'), error: push('error') } };
}

test('Cliente: espera creciente 1 s / 3 s / 6 s + variación, solo para GET', async (t) => {
  const always503 = express();
  let count = 0;
  always503.use((_req, res) => { count += 1; res.status(503).type('html').send('<html>503</html>'); });
  const srv = always503.listen(0, '127.0.0.1');
  await new Promise((r) => srv.once('listening', r));
  const { lines, logger } = captureLogger();
  const sleeps = [];
  const client = createBackendClient({
    origin: `http://127.0.0.1:${srv.address().port}`,
    config: loadResilienceConfig({}),          // valores por defecto de producción
    logger,
    random: () => 0.5,                         // variación determinista: +15 %
    sleep: async (ms) => { sleeps.push(ms); },  // sin esperar de verdad
  });
  try {
    await t.test('GET: 4 intentos (inicial + 3 reintentos) con esperas 1150 / 3450 / 6900 ms', async () => {
      count = 0;
      await assert.rejects(client.get('/api/farmacias?email=ana@test.local', { headers: { Authorization: 'Bearer token-secreto-123' } }));
      assert.equal(count, 4);
      assert.deepEqual(sleeps, [1150, 3450, 6900]);
    });
    await t.test('POST, PUT, PATCH y DELETE: un solo intento, sin esperas', async () => {
      for (const fn of [() => client.post('/api/x', {}), () => client.put('/api/x/1', {}), () => client.patch('/api/x/1', {}), () => client.delete('/api/x/1')]) {
        count = 0; sleeps.length = 0;
        await assert.rejects(fn());
        assert.equal(count, 1);
        assert.deepEqual(sleeps, []);
      }
    });
    await t.test('Los logs registran estado y duración, sin token, sin query ni email', () => {
      const all = lines.map((l) => l.text).join('\n');
      assert.match(all, /http_503/);
      assert.match(all, /"ms":\d+/);
      assert.match(all, /\/api\/farmacias/);
      assert.ok(!all.includes('token-secreto-123') && !all.includes('ana@test.local') && !all.includes('email='));
      assert.match(all, /\/api\/x\/:id/, 'Los identificadores se normalizan');
    });
    await t.test('Sin plazo suficiente no se reintenta (plazo total respetado)', async () => {
      const tight = createBackendClient({
        origin: `http://127.0.0.1:${srv.address().port}`,
        config: { ...loadResilienceConfig({}), totalTimeoutMs: 1000 },
        logger, random: () => 0, sleep: async (ms) => { sleeps.push(ms); },
      });
      count = 0; sleeps.length = 0;
      await assert.rejects(tight.get('/api/farmacias'));
      assert.equal(count, 1);
      assert.deepEqual(sleeps, []);
    });
  } finally {
    srv.close();
  }
});

test('Configuración de resiliencia', async (t) => {
  await t.test('valores por defecto: 45 s total, esperas 1 s / 3 s / 6 s', () => {
    const c = loadResilienceConfig({});
    assert.equal(c.totalTimeoutMs, 45000);
    assert.deepEqual(c.retryDelaysMs, [1000, 3000, 6000]);
    assert.deepEqual(DEFAULTS.retryDelaysMs, [1000, 3000, 6000]);
  });
  for (const [key, value] of [['GATEWAY_RETRY_DELAYS_MS', '1000,abc'], ['GATEWAY_RETRY_DELAYS_MS', '1,2,3,4'], ['GATEWAY_BACKEND_TIMEOUT_MS', '-5']]) {
    await t.test(`rechaza ${key}=${value}`, () => {
      assert.throws(() => loadResilienceConfig({ [key]: value }), BackendConfigError);
    });
  }
  await t.test('El Gateway no arranca con una configuración inválida', async () => {
    const r = await startGateway({ port: await freePort(), env: { JWT_SECRET, INTERNAL_API_SECRET, BACKEND_URL: B, GATEWAY_RETRY_DELAYS_MS: 'x' } });
    r.child.kill();
    assert.equal(r.started, false);
    assert.equal(r.code, 1);
    assert.match(r.stderr, /GATEWAY_RETRY_DELAYS_MS/);
  });
  await t.test('El cuerpo 503 estándar es exactamente el acordado', () => {
    assert.deepEqual({ ...UNAVAILABLE_BODY }, STANDARD_503);
  });
});

test('Selección de red: privada de Render, alternativa pública solo si la privada no responde', async (t) => {
  const PRIVATE = 'http://farmalink-backend:10000';
  const PUBLIC = 'https://farmalink-backend.onrender.com';

  await t.test('clasificación de orígenes', () => {
    assert.equal(describeBackendOrigin(PRIVATE).network, 'private');
    assert.equal(describeBackendOrigin('http://farmalink-backend-ab12:10000').network, 'private');
    assert.equal(describeBackendOrigin(PUBLIC).network, 'public');
    assert.equal(describeBackendOrigin('http://localhost:3001').network, 'local');
    assert.equal(describeBackendOrigin('http://127.0.0.1:3001').network, 'local');
  });
  await t.test('privada alcanzable → se usa la privada', async () => {
    const { lines, logger } = captureLogger();
    const r = await selectBackendOrigin({ primary: PRIVATE, fallback: PUBLIC, probe: async () => ({ ok: true }), logger });
    assert.deepEqual(r, { origin: PRIVATE, network: 'private', usingFallback: false });
    assert.match(lines[0].text, /RED PRIVADA/);
  });
  await t.test('privada no alcanzable + BACKEND_PUBLIC_URL → alternativa pública con aviso en el log', async () => {
    const { lines, logger } = captureLogger();
    const r = await selectBackendOrigin({ primary: PRIVATE, fallback: PUBLIC, probe: async () => ({ ok: false, reason: 'ENOTFOUND' }), logger });
    assert.deepEqual(r, { origin: PUBLIC, network: 'public', usingFallback: true });
    assert.equal(lines[0].level, 'warn');
    assert.match(lines[0].text, /ENOTFOUND/);
  });
  await t.test('privada no alcanzable sin alternativa → se mantiene la privada y se registra el error', async () => {
    const { lines, logger } = captureLogger();
    const r = await selectBackendOrigin({ primary: PRIVATE, fallback: null, probe: async () => ({ ok: false, reason: 'timeout' }), logger });
    assert.equal(r.origin, PRIVATE);
    assert.equal(lines[0].level, 'error');
  });
  await t.test('URL pública como BACKEND_URL → aviso de Cloudflare en el log', async () => {
    const { lines, logger } = captureLogger();
    const r = await selectBackendOrigin({ primary: PUBLIC, fallback: null, probe: async () => assert.fail('no debe sondear'), logger });
    assert.equal(r.network, 'public');
    assert.equal(lines[0].level, 'warn');
    assert.match(lines[0].text, /Cloudflare/);
  });
  await t.test('con la alternativa activa, vuelve a la red privada en cuanto responde', async () => {
    const { logger } = captureLogger();
    let probes = 0;
    const switched = await new Promise((resolve) => {
      watchPrivateNetwork({
        primary: PRIVATE, intervalMs: 10, logger,
        probe: async () => { probes += 1; return { ok: probes >= 2 }; },
        onAvailable: resolve,
      });
    });
    assert.equal(switched, PRIVATE);
  });
  await t.test('probeTcp real: puerto abierto → ok; puerto cerrado → no ok', async () => {
    const srv = net.createServer().listen(0, '127.0.0.1');
    await new Promise((r) => srv.once('listening', r));
    assert.equal((await probeTcp(`http://127.0.0.1:${srv.address().port}`, 1000)).ok, true);
    srv.close();
    assert.equal((await probeTcp(`http://127.0.0.1:${await freePort()}`, 1000)).ok, false);
  });
  await t.test('BACKEND_PUBLIC_URL se valida igual que BACKEND_URL', () => {
    assert.equal(resolveBackendPublicUrl({}), null);
    assert.equal(resolveBackendPublicUrl({ BACKEND_PUBLIC_URL: `${PUBLIC}/` }), PUBLIC);
    assert.throws(() => resolveBackendPublicUrl({ BACKEND_PUBLIC_URL: `${PUBLIC}/api` }), BackendUrlError);
  });
});
