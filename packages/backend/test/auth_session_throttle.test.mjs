// I1 (límite de login por cliente real) e I2 (sesión ligada al id, no al email).
// Código real: LoginThrottle, createApp() del Backend (fuente vía tsx) y el Gateway como proceso.
// En las pruebas HTTP este archivo hace de proxy de Render: añade la IP "real" al FINAL de
// X-Forwarded-For; lo que un cliente escriba antes queda a la izquierda y debe ignorarse.
import test from 'node:test';
import assert from 'node:assert/strict';
import jwt from 'jsonwebtoken';
import { newSecret, freePort, startGateway, createFakeDb, seedUser, http } from './support.mjs';

const JWT_SECRET = newSecret();
const INTERNAL_API_SECRET = newSecret();
process.env.JWT_SECRET = JWT_SECRET;
process.env.INTERNAL_API_SECRET = INTERNAL_API_SECRET;
process.env.ENABLE_AI_ASSISTANT = 'false';
process.env.AI_USE_GEMINI = 'false';
process.env.AI_DEBUG_LOGS = 'false';
delete process.env.GEMINI_API_KEY;

const { LoginThrottle, resolveClientIp } = await import('../auth/loginThrottle.js');
const { default: Database } = await import('../shared/db.js');
const { createApp } = await import('../app.js');
const { hashPassword } = await import('../shared/password.js');

const { pool, state } = createFakeDb();
Database.getInstance().pool = pool;

const PASS = 'Clave#Test2026';
const hash = await hashPassword(PASS);
seedUser(state, { id: 1, name: 'Admin', email: 'admin@test.local', passwordHash: hash, role: 'admin' });
seedUser(state, { id: 2, name: 'Victima', email: 'victima@test.local', passwordHash: hash, role: 'cliente' });
seedUser(state, { id: 3, name: 'Otra', email: 'otra@test.local', passwordHash: hash, role: 'cliente' });
seedUser(state, { id: 4, name: 'Cambia', email: 'cambia@test.local', passwordHash: hash, role: 'cliente' });
seedUser(state, { id: 5, name: 'Borrado', email: 'borrado@test.local', passwordHash: hash, role: 'cliente' });

const IP_VICTIMA = '203.0.113.10';
const IP_ATACANTE = '198.51.100.7';
const IP_SPRAY = '192.0.2.50';
const via = (realIp, clientXff) => ({ 'X-Forwarded-For': clientXff ? `${clientXff}, ${realIp}` : realIp });

let backendServer; let gateway; let G; let B;

test.before(async () => {
  backendServer = createApp().listen(0, '127.0.0.1');
  await new Promise((r) => backendServer.once('listening', r));
  B = `http://127.0.0.1:${backendServer.address().port}`;
  const gPort = await freePort();
  gateway = await startGateway({ port: gPort, env: { JWT_SECRET, INTERNAL_API_SECRET, BACKEND_URL: B } });
  assert.equal(gateway.started, true, gateway.stderr);
  G = `http://127.0.0.1:${gPort}`;
});

test.after(() => {
  gateway?.child?.kill();
  backendServer?.close();
  assert.deepEqual(state.unsupported, [], 'Consultas no reconocidas por la BD simulada');
});

const login = (email, password, headers) => http(G, 'POST', '/api/auth/login', { body: { email, password }, headers });

// ═════════════════════════════════════════════════════════════════════════════
test('I1 — LoginThrottle (unidad, reloj simulado)', async (t) => {
  let now = 1_000_000;
  const clock = () => now;

  await t.test('5 fallos email+IP bloquean solo ese par', () => {
    const th = new LoginThrottle(clock);
    for (let i = 0; i < 5; i++) th.recordFailure('a@x.co', '1.1.1.1');
    assert.equal(th.check('a@x.co', '1.1.1.1').blocked, true);
    assert.equal(th.check('a@x.co', '2.2.2.2').blocked, false, 'otra IP no queda bloqueada');
    assert.equal(th.check('b@x.co', '1.1.1.1').blocked, false, 'otro email desde la misma IP no queda bloqueado');
  });
  await t.test('Los fallos caducan al vencer la ventana (antes se acumulaban para siempre)', () => {
    const th = new LoginThrottle(clock);
    for (let i = 0; i < 4; i++) th.recordFailure('c@x.co', '1.1.1.1');
    now += 16 * 60 * 1000;
    th.recordFailure('c@x.co', '1.1.1.1');
    assert.equal(th.check('c@x.co', '1.1.1.1').blocked, false);
  });
  await t.test('El bloqueo vence a los 15 minutos', () => {
    const th = new LoginThrottle(clock);
    for (let i = 0; i < 5; i++) th.recordFailure('d@x.co', '1.1.1.1');
    assert.equal(th.check('d@x.co', '1.1.1.1').blocked, true);
    now += 15 * 60 * 1000;
    assert.equal(th.check('d@x.co', '1.1.1.1').blocked, false);
  });
  await t.test('20 fallos desde una IP contra emails distintos bloquean esa IP (spraying)', () => {
    const th = new LoginThrottle(clock);
    for (let i = 0; i < 20; i++) th.recordFailure(`u${i}@x.co`, '9.9.9.9');
    const r = th.check('nuevo@x.co', '9.9.9.9');
    assert.equal(r.blocked, true);
    assert.equal(r.rule, 'ip');
    assert.equal(th.check('nuevo@x.co', '8.8.8.8').blocked, false);
  });
  await t.test('50 fallos distribuidos contra un email lo bloquean globalmente', () => {
    const th = new LoginThrottle(clock);
    for (let i = 0; i < 50; i++) th.recordFailure('e@x.co', `10.0.0.${i}`);
    const r = th.check('e@x.co', '172.16.0.1');
    assert.equal(r.blocked, true);
    assert.equal(r.rule, 'email');
  });
  await t.test('Un login correcto limpia solo el contador email+IP', () => {
    const th = new LoginThrottle(clock);
    for (let i = 0; i < 4; i++) th.recordFailure('f@x.co', '1.1.1.1');
    th.recordSuccess('f@x.co', '1.1.1.1');
    th.recordFailure('f@x.co', '1.1.1.1');
    assert.equal(th.check('f@x.co', '1.1.1.1').blocked, false);
  });
  await t.test('resolveClientIp acepta IPs y descarta valores manipulados', () => {
    assert.equal(resolveClientIp('203.0.113.10', 'fb'), '203.0.113.10');
    assert.equal(resolveClientIp('::ffff:127.0.0.1', 'fb'), '::ffff:127.0.0.1');
    for (const bad of ['1.1.1.1; DROP', '<script>', 'a'.repeat(46), '', 5, undefined]) {
      assert.equal(resolveClientIp(bad, 'fb'), 'fb', String(bad));
    }
  });
});

// ═════════════════════════════════════════════════════════════════════════════
test('I1 — Login a través del Gateway (HTTP)', async (t) => {
  await t.test('Dos usuarios distintos inician sesión desde el mismo Gateway', async () => {
    assert.equal((await login('victima@test.local', PASS, via(IP_VICTIMA))).status, 200);
    assert.equal((await login('otra@test.local', PASS, via(IP_VICTIMA))).status, 200);
  });

  await t.test('5 fallos del atacante bloquean al ATACANTE, no a la víctima', async () => {
    for (let i = 0; i < 5; i++) assert.equal((await login('victima@test.local', 'mala', via(IP_ATACANTE))).status, 401);
    assert.equal((await login('victima@test.local', PASS, via(IP_ATACANTE))).status, 429, 'el atacante queda bloqueado');
    assert.equal((await login('victima@test.local', PASS, via(IP_VICTIMA))).status, 200, 'la víctima entra desde su IP');
    assert.equal((await login('otra@test.local', PASS, via(IP_ATACANTE))).status, 200, 'otra cuenta desde la IP del atacante no se bloquea');
  });

  await t.test('El cliente no puede falsificar su IP con X-Forwarded-For', async () => {
    // El atacante antepone la IP de la víctima; el proxy de Render añade la real al final.
    const r = await login('victima@test.local', PASS, via(IP_ATACANTE, IP_VICTIMA));
    assert.equal(r.status, 429, 'se usa la IP añadida por el proxy, no la escrita por el cliente');
  });

  await t.test('El cliente no puede falsificar la cabecera interna de IP del Gateway', async () => {
    const r = await login('victima@test.local', PASS, { ...via(IP_ATACANTE), 'x-farmalink-client-ip': IP_VICTIMA });
    assert.equal(r.status, 429, 'el Gateway sobrescribe x-farmalink-client-ip');
  });

  await t.test('Spraying: 20 fallos desde una IP la bloquean incluso con contraseña correcta; otras IPs siguen entrando', async () => {
    for (let i = 0; i < 20; i++) assert.equal((await login(`noexiste${i}@test.local`, 'mala', via(IP_SPRAY))).status, 401);
    assert.equal((await login('victima@test.local', PASS, via(IP_SPRAY))).status, 429);
    assert.equal((await login('victima@test.local', PASS, via(IP_VICTIMA))).status, 200);
  });

  await t.test('Acceso directo al Backend sin autenticación interna → 403 (aunque falsifique la IP)', async () => {
    const r = await http(B, 'POST', '/api/auth/login', { body: { email: 'victima@test.local', password: PASS }, headers: { 'x-farmalink-client-ip': '10.9.9.9' } });
    assert.equal(r.status, 403);
    const r2 = await http(B, 'POST', '/api/auth/login', { body: { email: 'victima@test.local', password: PASS }, headers: { 'x-internal-api-secret': newSecret(), 'x-farmalink-client-ip': '10.9.9.9' } });
    assert.equal(r2.status, 403);
  });
});

// ═════════════════════════════════════════════════════════════════════════════
test('I2 — Identidad de sesión por id', async (t) => {
  await t.test('El JWT incluye el id del usuario', async () => {
    const r = await login('cambia@test.local', PASS, via('203.0.113.40'));
    const claims = jwt.verify(r.body.token, JWT_SECRET, { algorithms: ['HS256'] });
    assert.equal(String(claims.id), '4');
  });

  await t.test('Cambio de email con token vigente: la sesión sigue siendo válida', async () => {
    const r0 = await login('cambia@test.local', PASS, via('203.0.113.40'));
    const token = r0.body.token;
    const put = await http(G, 'PUT', '/api/usuarios/4', { token, body: { email: 'cambiado@test.local' } });
    assert.equal(put.status, 200, JSON.stringify(put.body));
    const me = await http(G, 'GET', '/api/usuarios/me', { token });
    assert.equal(me.status, 200);
    assert.equal(me.body.data.id, '4');
    assert.equal(me.body.data.email, 'cambiado@test.local');
    assert.equal((await login('cambiado@test.local', PASS, via('203.0.113.40'))).status, 200);
    assert.equal((await login('cambia@test.local', PASS, via('203.0.113.40'))).status, 401);

    // Alguien registra el email antiguo: el token viejo sigue identificando a la cuenta 4, no a la nueva.
    const reg = await http(G, 'POST', '/api/auth/register', { body: { name: 'Nuevo Dueño', email: 'cambia@test.local', password: PASS } });
    assert.equal(reg.status, 201);
    const me2 = await http(G, 'GET', '/api/usuarios/me', { token });
    assert.equal(me2.body.data.id, '4');
  });

  await t.test('Usuario eliminado: su token deja de valer (401)', async () => {
    const tUser = (await login('borrado@test.local', PASS, via('203.0.113.50'))).body.token;
    const tAdmin = (await login('admin@test.local', PASS, via('203.0.113.50'))).body.token;
    assert.equal((await http(G, 'DELETE', '/api/usuarios/5', { token: tAdmin })).status, 200);
    const me = await http(G, 'GET', '/api/usuarios/me', { token: tUser });
    assert.equal(me.status, 401);
  });

  await t.test('Token sin claim id (aunque esté bien firmado) → 401', async () => {
    const sinId = jwt.sign({ email: 'victima@test.local', role: 'cliente' }, JWT_SECRET, { algorithm: 'HS256', expiresIn: '1h' });
    assert.equal((await http(G, 'GET', '/api/usuarios/me', { token: sinId })).status, 401);
  });

  await t.test('Token con id inexistente → 401', async () => {
    const fantasma = jwt.sign({ id: 999, email: 'x@test.local', role: 'admin' }, JWT_SECRET, { algorithm: 'HS256', expiresIn: '1h' });
    assert.equal((await http(G, 'GET', '/api/usuarios/me', { token: fantasma })).status, 401);
  });

  await t.test('El rol sigue saliendo de la BD (claim role=admin de un cliente no da permisos)', async () => {
    const falsoAdmin = jwt.sign({ id: 2, email: 'victima@test.local', role: 'admin' }, JWT_SECRET, { algorithm: 'HS256', expiresIn: '1h' });
    const r = await http(B, 'GET', '/api/usuarios', { token: falsoAdmin, headers: { 'x-internal-api-secret': INTERNAL_API_SECRET } });
    assert.equal(r.status, 403);
  });
});

// ═════════════════════════════════════════════════════════════════════════════
test('Regresión de contratos: login, registro y /me', async (t) => {
  await t.test('login → 200 {token, user{id,name,email,role}}', async () => {
    const r = await login('otra@test.local', PASS, via('203.0.113.60'));
    assert.equal(r.status, 200);
    assert.deepEqual(Object.keys(r.body).sort(), ['token', 'user']);
    assert.deepEqual(r.body.user, { id: '3', name: 'Otra', email: 'otra@test.local', role: 'cliente' });
  });
  await t.test('registro → 201 {success, data{id,name,email,role,created_at}}', async () => {
    const r = await http(G, 'POST', '/api/auth/register', { body: { name: 'Reg', email: 'reg@test.local', password: PASS } });
    assert.equal(r.status, 201);
    assert.deepEqual(Object.keys(r.body.data).sort(), ['created_at', 'email', 'id', 'name', 'role']);
    assert.equal(r.body.data.role, 'cliente');
  });
  await t.test('/me → 200 {success, data{...}}', async () => {
    const token = (await login('otra@test.local', PASS, via('203.0.113.60'))).body.token;
    const r = await http(G, 'GET', '/api/usuarios/me', { token });
    assert.equal(r.status, 200);
    assert.deepEqual(Object.keys(r.body.data).sort(), ['bio', 'created_at', 'email', 'id', 'name', 'phone', 'profile_picture', 'role']);
  });
  await t.test('Credenciales inválidas siguen respondiendo 401 y el bloqueo 429 conserva su mensaje', async () => {
    assert.equal((await login('otra@test.local', 'mala', via('203.0.113.61'))).status, 401);
    for (let i = 0; i < 4; i++) await login('otra@test.local', 'mala', via('203.0.113.61'));
    const r = await login('otra@test.local', PASS, via('203.0.113.61'));
    assert.equal(r.status, 429);
    assert.match(r.body.message, /Demasiados intentos fallidos/);
  });
});
