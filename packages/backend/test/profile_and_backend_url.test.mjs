// Pruebas de la corrección de integración con MediNova:
//  1) Comunicación Gateway → Backend usando la dirección interna de Render (host:puerto sin esquema)
//     y normalización de respuestas no JSON (p. ej. 429 HTML de Cloudflare).
//  2) PUT /api/usuarios/:id con los campos que envía MediNova (name, phone, bio, profile_picture):
//     persistencia real en la BD simulada, recuperación posterior y errores.
// Código real: createApp() del Backend (fuente vía tsx) y packages/gateway/index.js como proceso hijo.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import path from 'node:path';
import express from 'express';
import jwt from 'jsonwebtoken';
import {
  newSecret, freePort, startGateway, createFakeDb, seedUser, http, GATEWAY_DIR,
} from './support.mjs';

const JWT_SECRET = newSecret();
const INTERNAL_API_SECRET = newSecret();
process.env.JWT_SECRET = JWT_SECRET;
process.env.INTERNAL_API_SECRET = INTERNAL_API_SECRET;
process.env.ENABLE_AI_ASSISTANT = 'false';
process.env.AI_USE_GEMINI = 'false';
process.env.AI_DEBUG_LOGS = 'false';
delete process.env.GEMINI_API_KEY;

const { resolveBackendUrl, BackendUrlError } = createRequire(import.meta.url)(path.join(GATEWAY_DIR, 'backendUrl.js'));
const { default: Database } = await import('../shared/db.js');
const { createApp } = await import('../app.js');
const { hashPassword } = await import('../shared/password.js');

const { pool, state } = createFakeDb();
Database.getInstance().pool = pool;

const PASS = { admin: 'Admin#Test2026', ana: 'Ana#Test2026', beto: 'Beto#Test2026' };
seedUser(state, { id: 1, name: 'Admin', email: 'admin@test.local', passwordHash: await hashPassword(PASS.admin), role: 'admin' });
seedUser(state, { id: 2, name: 'Ana', email: 'ana@test.local', passwordHash: await hashPassword(PASS.ana), role: 'cliente' });
seedUser(state, { id: 3, name: 'Beto', email: 'beto@test.local', passwordHash: await hashPassword(PASS.beto), role: 'cliente', phone: '3111111111' });

let backendServer; let gateway; let G; let B;

test.before(async () => {
  backendServer = createApp().listen(0, '127.0.0.1');
  await new Promise((r) => backendServer.once('listening', r));
  const bPort = backendServer.address().port;
  B = `http://127.0.0.1:${bPort}`;
  const gPort = await freePort();
  // Igual que la dirección interna de Render: host:puerto, SIN http://
  gateway = await startGateway({ port: gPort, env: { JWT_SECRET, INTERNAL_API_SECRET, BACKEND_URL: `127.0.0.1:${bPort}` } });
  assert.equal(gateway.started, true, gateway.stderr);
  G = `http://127.0.0.1:${gPort}`;
});

test.after(() => {
  gateway?.child?.kill();
  backendServer?.close();
  assert.deepEqual(state.unsupported, [], 'Consultas no reconocidas por la BD simulada');
});

const login = async (email, password) => {
  const r = await http(G, 'POST', '/api/auth/login', { body: { email, password } });
  assert.equal(r.status, 200, JSON.stringify(r.body));
  return r.body.token;
};

// ═════════════════════════════════════════════════════════════════════════════
test('FASE 1 — resolveBackendUrl (dirección interna de Render y URL pública)', async (t) => {
  const ok = [
    ['https://farmalink-backend.onrender.com', 'https://farmalink-backend.onrender.com'],
    ['https://farmalink-backend.onrender.com/', 'https://farmalink-backend.onrender.com'],
    ['farmalink-backend-ab12:10000', 'http://farmalink-backend-ab12:10000'],
    ['http://farmalink-backend-ab12:10000', 'http://farmalink-backend-ab12:10000'],
    ['  farmalink-backend-ab12:10000  ', 'http://farmalink-backend-ab12:10000'],
    [undefined, 'http://localhost:3001'],
  ];
  for (const [input, expected] of ok) {
    await t.test(`${JSON.stringify(input)} → ${expected}`, () => {
      assert.equal(resolveBackendUrl({ BACKEND_URL: input }), expected);
    });
  }
  const bad = ['ftp://backend:21', 'http://backend:10000/api', 'http://user:pass@backend:10000', 'http://backend:10000?x=1', 'http://:99999'];
  for (const input of bad) {
    await t.test(`rechaza ${input}`, () => {
      assert.throws(() => resolveBackendUrl({ BACKEND_URL: input }), BackendUrlError);
    });
  }
});

test('FASE 1 — Gateway con BACKEND_URL inválido no arranca', async () => {
  const r = await startGateway({ port: await freePort(), env: { JWT_SECRET, INTERNAL_API_SECRET, BACKEND_URL: 'http://backend:10000/api' } });
  r.child.kill();
  assert.equal(r.started, false);
  assert.equal(r.code, 1);
  assert.match(r.stderr, /BACKEND_URL/);
});

test('FASE 1 — Gateway se comunica con el Backend vía host:puerto sin esquema', async (t) => {
  await t.test('GET /api/categorias → 200 con el contrato existente', async () => {
    const r = await http(G, 'GET', '/api/categorias');
    assert.equal(r.status, 200);
    assert.deepEqual(r.body, { success: true, data: [{ id: '1', nombre: 'Analgésicos', orden: 1 }] });
  });
  await t.test('Regresión medicamentos: GET /api/medicamentos/1 → 200', async () => {
    const r = await http(G, 'GET', '/api/medicamentos/1');
    assert.equal(r.status, 200);
    assert.equal(r.body.success, true);
    assert.equal(r.body.data.id, '1');
  });
  await t.test('Regresión autenticación: login → {token, user}', async () => {
    const r = await http(G, 'POST', '/api/auth/login', { body: { email: 'ana@test.local', password: PASS.ana } });
    assert.equal(r.status, 200);
    assert.deepEqual(Object.keys(r.body).sort(), ['token', 'user']);
  });
});

test('FASE 1 — Desafío de Cloudflare (429 HTML "Just a moment...") → 503 backend_unavailable en JSON', async () => {
  const cf = express();
  cf.use((_req, res) => res.status(429).type('html').send('<!DOCTYPE html><html><head><title>Just a moment...</title></head></html>'));
  const cfServer = cf.listen(0, '127.0.0.1');
  await new Promise((r) => cfServer.once('listening', r));
  const port = await freePort();
  const g2 = await startGateway({ port, env: { JWT_SECRET, INTERNAL_API_SECRET, BACKEND_URL: `http://127.0.0.1:${cfServer.address().port}` } });
  try {
    assert.equal(g2.started, true, g2.stderr);
    const res = await fetch(`http://127.0.0.1:${port}/api/medicamentos/1`);
    const text = await res.text();
    assert.equal(res.status, 503);
    assert.equal(res.headers.get('retry-after'), '10');
    assert.ok(!text.includes('Just a moment') && !text.includes('Request failed'), 'Nunca se reenvía el HTML de Cloudflare ni el texto de axios');
    assert.deepEqual(JSON.parse(text), {
      success: false, error: 'backend_unavailable', message: 'El servicio se está iniciando, inténtalo en unos segundos',
    });
  } finally {
    g2.child.kill();
    cfServer.close();
  }
});

// ═════════════════════════════════════════════════════════════════════════════
test('FASE 2 — PUT /api/usuarios/:id (perfil) vía Gateway', async (t) => {
  const tAna = await login('ana@test.local', PASS.ana);
  const tAdmin = await login('admin@test.local', PASS.admin);
  const body = { name: 'Ana Actualizada', phone: '3001234567', bio: 'Bio de prueba', profile_picture: 'https://ejemplo.test/ana.png' };

  await t.test('El propio usuario actualiza name/phone/bio/profile_picture → 200 y contrato intacto', async () => {
    const r = await http(G, 'PUT', '/api/usuarios/2', { token: tAna, body });
    assert.equal(r.status, 200, JSON.stringify(r.body));
    assert.equal(r.body.success, true);
    assert.deepEqual(Object.keys(r.body.data).sort(), ['bio', 'created_at', 'email', 'id', 'name', 'phone', 'profile_picture', 'role']);
    assert.equal(r.body.data.id, '2');
    assert.equal(r.body.data.name, 'Ana Actualizada');
    assert.equal(r.body.data.phone, '3001234567');
    assert.equal(r.body.data.bio, 'Bio de prueba');
    assert.equal(r.body.data.profile_picture, 'https://ejemplo.test/ana.png');
  });
  await t.test('Los datos quedaron persistidos en la BD', () => {
    const u = state.usuarios.get('2');
    assert.equal(u.name, 'Ana Actualizada');
    assert.equal(u.phone, '3001234567');
    assert.equal(u.bio, 'Bio de prueba');
    assert.equal(u.profile_picture, 'https://ejemplo.test/ana.png');
  });
  await t.test('GET /api/usuarios/me recupera los datos actualizados', async () => {
    const r = await http(G, 'GET', '/api/usuarios/me', { token: tAna });
    assert.equal(r.status, 200);
    assert.equal(r.body.data.name, 'Ana Actualizada');
    assert.equal(r.body.data.phone, '3001234567');
    assert.equal(r.body.data.bio, 'Bio de prueba');
    assert.equal(r.body.data.profile_picture, 'https://ejemplo.test/ana.png');
  });
  await t.test('phone: null borra el valor', async () => {
    const r = await http(G, 'PUT', '/api/usuarios/2', { token: tAna, body: { phone: null } });
    assert.equal(r.status, 200);
    assert.equal(r.body.data.phone, null);
    assert.equal(state.usuarios.get('2').phone, null);
  });
  await t.test('role en el cuerpo se ignora para un cliente', async () => {
    const r = await http(G, 'PUT', '/api/usuarios/2', { token: tAna, body: { name: 'Ana', role: 'admin' } });
    assert.equal(r.status, 200);
    assert.equal(state.usuarios.get('2').role, 'cliente');
  });
  await t.test('Editar a OTRO usuario → 403 y sin cambios', async () => {
    const r = await http(G, 'PUT', '/api/usuarios/3', { token: tAna, body: { name: 'Hack' } });
    assert.equal(r.status, 403);
    assert.equal(state.usuarios.get('3').name, 'Beto');
  });
  await t.test('Sin token → 401', async () => {
    assert.equal((await http(G, 'PUT', '/api/usuarios/2', { body: { name: 'X X' } })).status, 401);
  });
  await t.test('Token inválido → 401', async () => {
    const forged = jwt.sign({ id: 2, email: 'ana@test.local', role: 'cliente' }, newSecret(), { algorithm: 'HS256' });
    assert.equal((await http(G, 'PUT', '/api/usuarios/2', { token: forged, body: { name: 'X X' } })).status, 401);
  });
  await t.test('Tipos inválidos → 400 (no 500)', async () => {
    for (const bad of [{ phone: 3001234567 }, { bio: { a: 1 } }, { profile_picture: 5 }, { name: 12 }]) {
      const r = await http(G, 'PUT', '/api/usuarios/2', { token: tAna, body: bad });
      assert.equal(r.status, 400, `${JSON.stringify(bad)} → ${r.status} ${JSON.stringify(r.body)}`);
      assert.equal(r.body.success, false);
    }
  });
  await t.test('phone de más de 20 caracteres → 400', async () => {
    const r = await http(G, 'PUT', '/api/usuarios/2', { token: tAna, body: { phone: '1'.repeat(21) } });
    assert.equal(r.status, 400);
  });
  await t.test('Cuerpo vacío → 400 "Nada que actualizar"', async () => {
    const r = await http(G, 'PUT', '/api/usuarios/2', { token: tAna, body: {} });
    assert.equal(r.status, 400);
  });
  await t.test('Admin edita a otro usuario → 200', async () => {
    const r = await http(G, 'PUT', '/api/usuarios/3', { token: tAdmin, body: { bio: 'Editado por admin' } });
    assert.equal(r.status, 200);
    assert.equal(state.usuarios.get('3').bio, 'Editado por admin');
  });
  await t.test('Admin con id no numérico → 400', async () => {
    const r = await http(G, 'PUT', '/api/usuarios/abc', { token: tAdmin, body: { bio: 'x' } });
    assert.equal(r.status, 400);
  });
  await t.test('id "2abc" (parseInt lo leería como 2) → 400 y sin cambios', async () => {
    const r = await http(G, 'PUT', '/api/usuarios/2abc', { token: tAna, body: { bio: 'no debe guardarse' } });
    assert.equal(r.status, 400);
    assert.notEqual(state.usuarios.get('2').bio, 'no debe guardarse');
  });
  await t.test('Si faltan las columnas de perfil NO se informa éxito falso → 500 explícito y sin cambios', async () => {
    state.missingProfileColumns = true;
    try {
      const r = await http(G, 'PUT', '/api/usuarios/2', { token: tAna, body: { bio: 'no debe guardarse' } });
      assert.equal(r.status, 500);
      assert.equal(r.body.success, false);
      assert.notEqual(state.usuarios.get('2').bio, 'no debe guardarse');
    } finally {
      state.missingProfileColumns = false;
    }
  });
  await t.test('El Backend sigue exigiendo la cabecera interna (acceso directo → 403)', async () => {
    const r = await http(B, 'PUT', '/api/usuarios/2', { token: tAna, body: { name: 'Directo' } });
    assert.equal(r.status, 403);
  });
});
