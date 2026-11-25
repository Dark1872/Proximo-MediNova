// Pruebas HTTP reales de la ronda P0.
// Ejecutan el código fuente (vía tsx), no dist/: createApp() del Backend con sus middleware,
// routers y controladores reales, y el Gateway real (packages/gateway/index.js) como proceso hijo.
// La base de datos es una simulación en memoria; no se usa Neon ni Gemini.
import test from 'node:test';
import assert from 'node:assert/strict';
import jwt from 'jsonwebtoken';
import {
  newSecret, freePort, startGateway, startBackendServer, legacyPublicSecret,
  createFakeDb, seedUser, http,
} from './support.mjs';

const JWT_SECRET = newSecret();
const INTERNAL_API_SECRET = newSecret();
process.env.JWT_SECRET = JWT_SECRET;
process.env.INTERNAL_API_SECRET = INTERNAL_API_SECRET;
process.env.ENABLE_AI_ASSISTANT = 'false';
process.env.AI_USE_GEMINI = 'false';
delete process.env.GEMINI_API_KEY;
process.env.AI_DEBUG_LOGS = 'false';

const INTERNAL = { 'x-internal-api-secret': INTERNAL_API_SECRET };
const LEGACY = legacyPublicSecret();

const { default: Database } = await import('../shared/db.js');
const { createApp } = await import('../app.js');
const { hashPassword } = await import('../shared/password.js');

const { pool, state } = createFakeDb();
Database.getInstance().pool = pool; // inyección del pool simulado en el singleton real

const PASS = { admin: 'Admin#Test2026', cliente: 'Cliente#Test2026', otro: 'Otro#Test2026' };
seedUser(state, { id: 1, name: 'Admin', email: 'admin@test.local', passwordHash: await hashPassword(PASS.admin), role: 'admin' });
seedUser(state, { id: 2, name: 'Cliente', email: 'cliente@test.local', passwordHash: await hashPassword(PASS.cliente), role: 'cliente', phone: '3000000000' });
seedUser(state, { id: 3, name: 'Otro', email: 'otro@test.local', passwordHash: await hashPassword(PASS.otro), role: 'cliente', phone: '3111111111' });
seedUser(state, { id: 4, name: 'Equipo', email: 'equipo@test.local', passwordHash: await hashPassword('Equipo#Test2026'), role: 'farmaceutico', isTeamMember: true });

const signed = (claims, secret = JWT_SECRET, opts = {}) =>
  jwt.sign(claims, secret, { algorithm: 'HS256', expiresIn: '1h', ...opts });

let B; let G; let backendServer; let gateway;

test.before(async () => {
  backendServer = createApp().listen(0, '127.0.0.1');
  await new Promise((r) => backendServer.once('listening', r));
  B = `http://127.0.0.1:${backendServer.address().port}`;
  const gPort = await freePort();
  gateway = await startGateway({ port: gPort, env: { JWT_SECRET, INTERNAL_API_SECRET, BACKEND_URL: B } });
  assert.equal(gateway.started, true, `El Gateway no arrancó con secretos válidos: ${gateway.stderr}`);
  G = `http://127.0.0.1:${gPort}`;
});

test.after(() => {
  gateway?.child?.kill();
  backendServer?.close();
  assert.deepEqual(state.unsupported, [], 'Se ejecutaron consultas que la BD simulada no reconoce');
});

const login = async (email, password) => {
  const r = await http(G, 'POST', '/api/auth/login', { body: { email, password } });
  assert.equal(r.status, 200, `login ${email}: ${JSON.stringify(r.body)}`);
  return r.body.token;
};

// ═════════════════════════════════════════════════════════════════════════════
test('P0.1 — Arranque: sin secreto válido Gateway y Backend no inician', async (t) => {
  const good = { JWT_SECRET: newSecret(), INTERNAL_API_SECRET: newSecret() };
  const cases = [
    ['sin JWT_SECRET', { ...good, JWT_SECRET: undefined }],
    ['JWT_SECRET vacío', { ...good, JWT_SECRET: '   ' }],
    ['JWT_SECRET de 31 bytes', { ...good, JWT_SECRET: 'a'.repeat(31) }],
    ['sin INTERNAL_API_SECRET', { ...good, INTERNAL_API_SECRET: undefined }],
    ['INTERNAL_API_SECRET de 16 bytes', { ...good, INTERNAL_API_SECRET: 'b'.repeat(16) }],
    ['JWT_SECRET igual a INTERNAL_API_SECRET', { JWT_SECRET: good.JWT_SECRET, INTERNAL_API_SECRET: good.JWT_SECRET }],
  ];
  if (LEGACY) cases.push(['JWT_SECRET igual al secreto público anterior', { ...good, JWT_SECRET: LEGACY }]);

  for (const [label, env] of cases) {
    await t.test(`Gateway ${label} → no inicia (exit 1)`, async () => {
      const r = await startGateway({ port: await freePort(), env: { ...env, BACKEND_URL: 'http://127.0.0.1:1' } });
      r.child.kill();
      assert.equal(r.started, false);
      assert.equal(r.code, 1);
      assert.match(r.stderr, /Arranque cancelado/);
      if (env.JWT_SECRET) assert.ok(!r.stderr.includes(env.JWT_SECRET) && !r.stdout.includes(env.JWT_SECRET), 'El secreto aparece en los logs');
    });
    await t.test(`Backend ${label} → no inicia (exit 1)`, async () => {
      const r = await startBackendServer({ port: await freePort(), env });
      r.child.kill();
      assert.equal(r.started, false);
      assert.equal(r.code, 1);
      assert.match(r.stderr, /Arranque cancelado/);
      if (env.JWT_SECRET) assert.ok(!r.stderr.includes(env.JWT_SECRET) && !r.stdout.includes(env.JWT_SECRET), 'El secreto aparece en los logs');
    });
  }

  await t.test('Backend con secretos válidos → inicia (control positivo)', async () => {
    const r = await startBackendServer({ port: await freePort(), env: good });
    r.child.kill();
    assert.equal(r.started, true, r.stderr);
  });

  if (!LEGACY) {
    await t.test('Caso "JWT_SECRET igual al secreto público anterior"', { skip: 'Historial Git no disponible: caso NO ejecutado' }, () => {});
  }
});

// ═════════════════════════════════════════════════════════════════════════════
test('P0.1 — Validación de tokens (Gateway y Backend)', async (t) => {
  const forgedLegacyAdmin = LEGACY ? signed({ id: 1, email: 'admin@test.local', role: 'admin' }, LEGACY) : null;
  const expired = signed({ id: 2, email: 'cliente@test.local', role: 'cliente' }, JWT_SECRET, { expiresIn: '-10s' });
  const algNone = `${Buffer.from('{"alg":"none","typ":"JWT"}').toString('base64url')}.${Buffer.from('{"email":"admin@test.local","role":"admin"}').toString('base64url')}.`;
  const hs512 = jwt.sign({ id: 1, email: 'admin@test.local', role: 'admin' }, JWT_SECRET, { algorithm: 'HS512' });

  const bad = [
    ['token inválido (basura)', 'esto.no.es-un-jwt'],
    ['Base64(email) legado', Buffer.from('admin@test.local').toString('base64')],
    ['token expirado', expired],
    ['alg=none', algNone],
    ['algoritmo no permitido (HS512)', hs512],
    ['firmado con otro secreto', signed({ id: 1, email: 'admin@test.local', role: 'admin' }, newSecret())],
  ];
  if (forgedLegacyAdmin) bad.push(['admin firmado con el secreto público ANTERIOR', forgedLegacyAdmin]);

  for (const [label, token] of bad) {
    await t.test(`Gateway: ${label} → 401`, async () => {
      const r = await http(G, 'GET', '/api/usuarios/me', { token });
      assert.equal(r.status, 401);
      assert.equal(r.body.success, false);
    });
    await t.test(`Backend directo (con cabecera interna): ${label} → 401`, async () => {
      const r = await http(B, 'GET', '/api/usuarios', { token, headers: INTERNAL });
      assert.equal(r.status, 401);
      assert.equal(r.body.success, false);
    });
  }
  if (!LEGACY) await t.test('Token con secreto anterior', { skip: 'Historial Git no disponible: caso NO ejecutado' }, () => {});

  await t.test('Token emitido por el login del Backend es aceptado por el Gateway (secreto compartido)', async () => {
    const token = await login('cliente@test.local', PASS.cliente);
    const r = await http(G, 'GET', '/api/usuarios/me', { token });
    assert.equal(r.status, 200);
    assert.equal(r.body.data.email, 'cliente@test.local');
  });
});

// ═════════════════════════════════════════════════════════════════════════════
test('P0.3 — Modificación de precios', async (t) => {
  const tCliente = await login('cliente@test.local', PASS.cliente);
  const tAdmin = await login('admin@test.local', PASS.admin);
  const before = state.precios.get('5').precio;

  await t.test('Sin autenticación: POST/PUT vía Gateway → 401', async () => {
    assert.equal((await http(G, 'POST', '/api/precios', { body: { medicamento_id: 1, farmacia_id: 1, precio: 1 } })).status, 401);
    assert.equal((await http(G, 'PUT', '/api/precios/5', { body: { precio: 1 } })).status, 401);
  });
  await t.test('Sin autenticación: POST/PUT/PATCH en Backend (con cabecera interna) → 401', async () => {
    assert.equal((await http(B, 'POST', '/api/precios', { body: { medicamento_id: 1, farmacia_id: 1, precio: 1 }, headers: INTERNAL })).status, 401);
    assert.equal((await http(B, 'PUT', '/api/precios/5', { body: { precio: 1 }, headers: INTERNAL })).status, 401);
    assert.equal((await http(B, 'PATCH', '/api/precios/5', { body: { precio: 1 }, headers: INTERNAL })).status, 401);
  });
  await t.test('Cliente autenticado: POST/PUT vía Gateway → 403', async () => {
    assert.equal((await http(G, 'POST', '/api/precios', { token: tCliente, body: { medicamento_id: 1, farmacia_id: 1, precio: 1 } })).status, 403);
    assert.equal((await http(G, 'PUT', '/api/precios/5', { token: tCliente, body: { precio: 1 } })).status, 403);
  });
  await t.test('Cliente autenticado: POST/PUT/PATCH en Backend (sin depender del Gateway) → 403', async () => {
    assert.equal((await http(B, 'POST', '/api/precios', { token: tCliente, body: { medicamento_id: 1, farmacia_id: 1, precio: 1 }, headers: INTERNAL })).status, 403);
    assert.equal((await http(B, 'PUT', '/api/precios/5', { token: tCliente, body: { precio: 1 }, headers: INTERNAL })).status, 403);
    assert.equal((await http(B, 'PATCH', '/api/precios/5', { token: tCliente, body: { precio: 1 }, headers: INTERNAL })).status, 403);
  });
  await t.test('Cliente con claim role=admin (firmado con el secreto vigente) sigue siendo cliente en la BD → 403', async () => {
    const claimAdmin = signed({ id: 2, email: 'cliente@test.local', role: 'admin' });
    // El Gateway confía en el claim como filtro previo, pero el Backend verifica el rol real en la BD.
    assert.equal((await http(G, 'PUT', '/api/precios/5', { token: claimAdmin, body: { precio: 1 } })).status, 403);
    assert.equal((await http(B, 'PATCH', '/api/precios/5', { token: claimAdmin, body: { precio: 1 }, headers: INTERNAL })).status, 403);
  });
  await t.test('Ningún intento rechazado alteró el precio', () => {
    assert.equal(state.precios.get('5').precio, before);
  });
  await t.test('Administrador: PUT vía Gateway → 200 y precio actualizado', async () => {
    const r = await http(G, 'PUT', '/api/precios/5', { token: tAdmin, body: { precio: 1500 } });
    assert.equal(r.status, 200, JSON.stringify(r.body));
    assert.equal(state.precios.get('5').precio, 1500);
  });
  await t.test('Administrador: POST vía Gateway → 200 (actualiza existente)', async () => {
    const r = await http(G, 'POST', '/api/precios', { token: tAdmin, body: { medicamento_id: 1, farmacia_id: 1, precio: 1700 } });
    assert.equal(r.status, 200, JSON.stringify(r.body));
    assert.equal(state.precios.get('5').precio, 1700);
  });
  await t.test('Administrador: PATCH en Backend → 200', async () => {
    const r = await http(B, 'PATCH', '/api/precios/5', { token: tAdmin, body: { precio: 1800 }, headers: INTERNAL });
    assert.equal(r.status, 200, JSON.stringify(r.body));
    assert.equal(state.precios.get('5').precio, 1800);
  });
  await t.test('Farmacéutico: rol existente pero NO autorizado para precios → 403', async () => {
    const tFarm = await login('equipo@test.local', 'Equipo#Test2026');
    assert.equal((await http(G, 'PUT', '/api/precios/5', { token: tFarm, body: { precio: 1 } })).status, 403);
    assert.equal((await http(B, 'PATCH', '/api/precios/5', { token: tFarm, body: { precio: 1 }, headers: INTERNAL })).status, 403);
  });
});

// ═════════════════════════════════════════════════════════════════════════════
test('P0.4 — Registro público y creación de usuarios', async (t) => {
  const roleOf = (email) => [...state.usuarios.values()].find((u) => u.email === email)?.role;

  for (const role of ['admin', 'farmaceutico']) {
    await t.test(`Registro público vía Gateway con role=${role} → crea cliente`, async () => {
      const email = `reg-${role}@test.local`;
      const r = await http(G, 'POST', '/api/auth/register', { body: { name: 'Nuevo', email, password: 'Clave#2026', role } });
      assert.equal(r.status, 201, JSON.stringify(r.body));
      assert.equal(r.body.success, true);
      assert.equal(r.body.data.role, 'cliente');
      assert.equal(roleOf(email), 'cliente');
    });
    await t.test(`Registro público directo al Backend con role=${role} → crea cliente`, async () => {
      const email = `reg-direct-${role}@test.local`;
      const r = await http(B, 'POST', '/api/auth/register', { body: { name: 'Nuevo', email, password: 'Clave#2026', role }, headers: INTERNAL });
      assert.equal(r.status, 201, JSON.stringify(r.body));
      assert.equal(roleOf(email), 'cliente');
    });
  }
  await t.test('Registro con email existente → 409', async () => {
    const r = await http(G, 'POST', '/api/auth/register', { body: { name: 'Dup', email: 'cliente@test.local', password: 'Clave#2026' } });
    assert.equal(r.status, 409);
  });
  await t.test('POST /api/usuarios (ruta administrativa) sin token → 401 (Gateway y Backend)', async () => {
    const body = { name: 'X', email: 'x1@test.local', password: 'Clave#2026', role: 'admin' };
    assert.equal((await http(G, 'POST', '/api/usuarios', { body })).status, 401);
    assert.equal((await http(B, 'POST', '/api/usuarios', { body, headers: INTERNAL })).status, 401);
    assert.equal(roleOf('x1@test.local'), undefined);
  });
  await t.test('POST /api/usuarios con token de cliente → 403', async () => {
    const tCliente = await login('cliente@test.local', PASS.cliente);
    const body = { name: 'X', email: 'x2@test.local', password: 'Clave#2026', role: 'admin' };
    assert.equal((await http(G, 'POST', '/api/usuarios', { token: tCliente, body })).status, 403);
    assert.equal((await http(B, 'POST', '/api/usuarios', { token: tCliente, body, headers: INTERNAL })).status, 403);
    assert.equal(roleOf('x2@test.local'), undefined);
  });
  await t.test('POST /api/usuarios con claim role=admin de un cliente (secreto vigente) → 403: rol tomado de la BD', async () => {
    const claimAdmin = signed({ id: 2, email: 'cliente@test.local', role: 'admin' });
    const body = { name: 'X', email: 'x3@test.local', password: 'Clave#2026', role: 'admin' };
    assert.equal((await http(G, 'POST', '/api/usuarios', { token: claimAdmin, body })).status, 403);
    assert.equal(roleOf('x3@test.local'), undefined);
  });
  await t.test('POST /api/usuarios con token admin de un usuario INEXISTENTE en la BD → 401', async () => {
    const ghost = signed({ id: 777, email: 'fantasma@test.local', role: 'admin' });
    const r = await http(G, 'POST', '/api/usuarios', { token: ghost, body: { name: 'X', email: 'x4@test.local', password: 'Clave#2026', role: 'admin' } });
    assert.equal(r.status, 401);
    assert.equal(roleOf('x4@test.local'), undefined);
  });
  if (LEGACY) await t.test('POST /api/usuarios con token admin firmado con el secreto ANTERIOR → 401', async () => {
    const forged = signed({ id: 777, email: 'fantasma@test.local', role: 'admin' }, LEGACY);
    const r = await http(G, 'POST', '/api/usuarios', { token: forged, body: { name: 'X', email: 'x5@test.local', password: 'Clave#2026', role: 'admin' } });
    assert.equal(r.status, 401);
    assert.equal(roleOf('x5@test.local'), undefined);
  });
  await t.test('Administrador real crea un farmacéutico por la ruta administrativa → 201', async () => {
    const tAdmin = await login('admin@test.local', PASS.admin);
    const r = await http(G, 'POST', '/api/usuarios', { token: tAdmin, body: { name: 'Farma', email: 'farma@test.local', password: 'Clave#2026', role: 'farmaceutico' } });
    assert.equal(r.status, 201, JSON.stringify(r.body));
    assert.equal(roleOf('farma@test.local'), 'farmaceutico');
  });
  await t.test('Administrador con rol inválido → 400', async () => {
    const tAdmin = await login('admin@test.local', PASS.admin);
    const r = await http(G, 'POST', '/api/usuarios', { token: tAdmin, body: { name: 'Root', email: 'root@test.local', password: 'Clave#2026', role: 'superadmin' } });
    assert.equal(r.status, 400);
  });
  await t.test('Cliente no puede auto-escalar su rol con PUT /api/usuarios/:id (Backend directo)', async () => {
    const tCliente = await login('cliente@test.local', PASS.cliente);
    const r = await http(B, 'PUT', '/api/usuarios/2', { token: tCliente, body: { role: 'admin' }, headers: INTERNAL });
    // role se ignora para no-admins: sin otros campos no hay nada que actualizar.
    assert.equal(r.status, 400);
    assert.equal(roleOf('cliente@test.local'), 'cliente');
  });
});

// ═════════════════════════════════════════════════════════════════════════════
test('P0.5 — Datos privados y acceso directo al Backend', async (t) => {
  const tCliente = await login('cliente@test.local', PASS.cliente);
  const tAdmin = await login('admin@test.local', PASS.admin);

  await t.test('Sin autenticación: datos privados → 401 (Gateway)', async () => {
    assert.equal((await http(G, 'GET', '/api/usuarios/me')).status, 401);
    assert.equal((await http(G, 'GET', '/api/usuarios/3')).status, 401);
    assert.equal((await http(G, 'GET', '/api/precios')).status, 401);
  });
  await t.test('Sin autenticación: datos privados → 401 (Backend con cabecera interna)', async () => {
    assert.equal((await http(B, 'GET', '/api/usuarios/me', { headers: INTERNAL })).status, 401);
    assert.equal((await http(B, 'GET', '/api/usuarios/3', { headers: INTERNAL })).status, 401);
    assert.equal((await http(B, 'GET', '/api/precios', { headers: INTERNAL })).status, 401);
  });
  await t.test('Cliente consulta a OTRO usuario → 403 (Gateway y Backend)', async () => {
    assert.equal((await http(G, 'GET', '/api/usuarios/3', { token: tCliente })).status, 403);
    const r = await http(B, 'GET', '/api/usuarios/3', { token: tCliente, headers: INTERNAL });
    assert.equal(r.status, 403);
    assert.ok(!JSON.stringify(r.body).includes('otro@test.local'));
  });
  await t.test('Cliente consulta su propio id en Backend → 200', async () => {
    const r = await http(B, 'GET', '/api/usuarios/2', { token: tCliente, headers: INTERNAL });
    assert.equal(r.status, 200);
    assert.equal(r.body.data.email, 'cliente@test.local');
  });
  await t.test('Administrador consulta a otro usuario → 200', async () => {
    const r = await http(G, 'GET', '/api/usuarios/3', { token: tAdmin });
    assert.equal(r.status, 200);
    assert.equal(r.body.data.id, '3');
  });
  await t.test('Perfil público de un usuario que NO es del equipo → 404 (sin teléfono ni rol)', async () => {
    const r = await http(G, 'GET', '/api/usuarios/public/3');
    assert.equal(r.status, 404);
    assert.ok(!JSON.stringify(r.body).includes('3111111111'));
  });
  await t.test('Perfil público de un miembro del equipo → 200', async () => {
    const r = await http(G, 'GET', '/api/usuarios/public/4');
    assert.equal(r.status, 200);
    assert.equal(r.body.data.name, 'Equipo');
  });

  const direct = ['/api/usuarios/3', '/api/precios', '/api/categorias', '/api/usuarios/public/4', '/api/auth/login'];
  for (const url of direct) {
    await t.test(`Acceso directo al Backend SIN cabecera interna: ${url} → 403`, async () => {
      const method = url === '/api/auth/login' ? 'POST' : 'GET';
      const r = await http(B, method, url, { token: tAdmin, body: method === 'POST' ? { email: 'admin@test.local', password: PASS.admin } : undefined });
      assert.equal(r.status, 403);
    });
    await t.test(`Acceso directo al Backend con cabecera interna INCORRECTA: ${url} → 403`, async () => {
      const method = url === '/api/auth/login' ? 'POST' : 'GET';
      const r = await http(B, method, url, { token: tAdmin, headers: { 'x-internal-api-secret': newSecret() }, body: method === 'POST' ? { email: 'admin@test.local', password: PASS.admin } : undefined });
      assert.equal(r.status, 403);
    });
  }
  await t.test('Health check del Backend sigue disponible sin cabecera (Render) → 200', async () => {
    assert.equal((await http(B, 'GET', '/api/health')).status, 200);
  });
  await t.test('Las peticiones legítimas del Gateway siguen funcionando', async () => {
    const r = await http(G, 'GET', '/api/categorias');
    assert.equal(r.status, 200);
    assert.deepEqual(r.body, { success: true, data: [{ id: '1', nombre: 'Analgésicos', orden: 1 }] });
  });
});

// ═════════════════════════════════════════════════════════════════════════════
test('Contratos de autenticación vía Gateway sin cambios de forma', async (t) => {
  await t.test('POST /api/auth/login → 200 {token, user{id,name,email,role}}', async () => {
    const r = await http(G, 'POST', '/api/auth/login', { body: { email: 'cliente@test.local', password: PASS.cliente } });
    assert.equal(r.status, 200);
    assert.deepEqual(Object.keys(r.body).sort(), ['token', 'user']);
    assert.deepEqual(r.body.user, { id: '2', name: 'Cliente', email: 'cliente@test.local', role: 'cliente' });
    const decoded = jwt.verify(r.body.token, JWT_SECRET, { algorithms: ['HS256'] });
    assert.ok(decoded.exp - decoded.iat === 24 * 3600);
  });
  await t.test('POST /api/auth/login credenciales inválidas → 401', async () => {
    const r = await http(G, 'POST', '/api/auth/login', { body: { email: 'otro@test.local', password: 'mala' } });
    assert.equal(r.status, 401);
  });
  await t.test('POST /api/auth/register → 201 {success, data{id,name,email,role,created_at}}', async () => {
    const r = await http(G, 'POST', '/api/auth/register', { body: { name: 'Forma', email: 'forma@test.local', password: 'Clave#2026' } });
    assert.equal(r.status, 201);
    assert.deepEqual(Object.keys(r.body.data).sort(), ['created_at', 'email', 'id', 'name', 'role']);
  });
  await t.test('POST /api/auth/register incompleto → 400 {success,message}', async () => {
    const r = await http(G, 'POST', '/api/auth/register', { body: { email: 'a@b.co' } });
    assert.equal(r.status, 400);
    assert.equal(r.body.success, false);
  });
  await t.test('GET /api/usuarios/me → 200 {success, data}', async () => {
    const token = await login('cliente@test.local', PASS.cliente);
    const r = await http(G, 'GET', '/api/usuarios/me', { token });
    assert.equal(r.status, 200);
    assert.deepEqual(Object.keys(r.body.data).sort(), ['bio', 'created_at', 'email', 'id', 'name', 'phone', 'profile_picture', 'role']);
  });
});
