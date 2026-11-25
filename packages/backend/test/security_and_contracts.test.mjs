// Pruebas unitarias sobre el código FUENTE (vía tsx), no sobre dist/.
// Usan un secreto temporal aleatorio; nunca el secreto público anterior como configuración.
//
// Nota: las antiguas "SUITE 2" (escalada de privilegios) y "SUITE 4" (fuerza bruta) se eliminaron porque
// reimplementaban la lógica dentro del propio test y no ejecutaban código de producción.
// Su cobertura real está en p0_http_security.test.mjs (peticiones HTTP contra Gateway y Backend reales).
import test from 'node:test';
import assert from 'node:assert/strict';
import jwt from 'jsonwebtoken';
import { newSecret, legacyPublicSecret } from './support.mjs';

const JWT_SECRET = newSecret();
process.env.JWT_SECRET = JWT_SECRET;
process.env.INTERNAL_API_SECRET = newSecret();

const { requireAuth } = await import('../shared/authMiddleware.js');
const { evaluatePolicy } = await import('../ai/policyGuard.js');
const { loadSecurityConfig, SecretConfigError, MIN_SECRET_BYTES } = await import('../shared/securityConfig.js');

function createMockHttp(options = {}) {
  const req = { headers: options.headers || {}, body: {}, params: {}, query: {}, ip: '127.0.0.1' };
  const res = {
    statusCode: 200,
    body: null,
    status(code) { this.statusCode = code; return this; },
    json(data) { this.body = data; return this; },
  };
  let nextCalled = false;
  return { req, res, next: () => { nextCalled = true; }, isNextCalled: () => nextCalled };
}

test('SUITE 0: loadSecurityConfig (sin valores por defecto)', async (t) => {
  const ok = { JWT_SECRET: newSecret(), INTERNAL_API_SECRET: newSecret() };
  await t.test('acepta dos secretos válidos y distintos', () => {
    assert.deepEqual(loadSecurityConfig(ok), { jwtSecret: ok.JWT_SECRET, internalApiSecret: ok.INTERNAL_API_SECRET });
  });
  const invalid = [
    ['JWT_SECRET ausente', { ...ok, JWT_SECRET: undefined }],
    ['JWT_SECRET vacío', { ...ok, JWT_SECRET: '' }],
    [`JWT_SECRET de ${MIN_SECRET_BYTES - 1} bytes`, { ...ok, JWT_SECRET: 'x'.repeat(MIN_SECRET_BYTES - 1) }],
    ['INTERNAL_API_SECRET ausente', { ...ok, INTERNAL_API_SECRET: undefined }],
    ['secretos iguales', { JWT_SECRET: ok.JWT_SECRET, INTERNAL_API_SECRET: ok.JWT_SECRET }],
  ];
  const legacy = legacyPublicSecret();
  if (legacy) invalid.push(['JWT_SECRET igual al secreto público anterior', { ...ok, JWT_SECRET: legacy }]);
  for (const [label, env] of invalid) {
    await t.test(`rechaza: ${label}`, () => {
      assert.throws(() => loadSecurityConfig(env), (err) => {
        assert.ok(err instanceof SecretConfigError);
        // El mensaje nunca debe contener el valor del secreto (solo se comprueba si el valor no es vacío).
        if (env.JWT_SECRET) assert.ok(!String(err.message).includes(env.JWT_SECRET));
        return true;
      });
    });
  }
  await t.test('se cuentan bytes, no caracteres (32 bytes exactos se aceptan)', () => {
    assert.doesNotThrow(() => loadSecurityConfig({ JWT_SECRET: 'ñ'.repeat(16), INTERNAL_API_SECRET: newSecret() }));
  });
});

test('SUITE 1: requireAuth (middleware real del Backend)', async (t) => {
  await t.test('1.1: sin encabezado Authorization → 401', async () => {
    const { req, res, next, isNextCalled } = createMockHttp();
    await requireAuth(req, res, next);
    assert.equal(res.statusCode, 401);
    assert.equal(isNextCalled(), false);
    assert.match(res.body.message, /Token de autenticación requerido/i);
  });

  await t.test('1.2: Base64(email) legado → 401', async () => {
    const { req, res, next, isNextCalled } = createMockHttp({
      headers: { authorization: `Bearer ${Buffer.from('admin-legacy@test.local').toString('base64')}` },
    });
    await requireAuth(req, res, next);
    assert.equal(res.statusCode, 401);
    assert.equal(isNextCalled(), false);
  });

  await t.test('1.3: token expirado → 401 "Token expirado"', async () => {
    const expired = jwt.sign({ id: 1, email: 'user@farmalink.com', role: 'cliente' }, JWT_SECRET, { expiresIn: '-10s', algorithm: 'HS256' });
    const { req, res, next, isNextCalled } = createMockHttp({ headers: { authorization: `Bearer ${expired}` } });
    await requireAuth(req, res, next);
    assert.equal(res.statusCode, 401);
    assert.equal(isNextCalled(), false);
    assert.equal(res.body.message, 'Token expirado');
  });

  await t.test('1.4: firma con otro secreto → 401 "Token inválido"', async () => {
    const forged = jwt.sign({ id: 1, email: 'hacker@farmalink.com', role: 'admin' }, newSecret(), { expiresIn: '1h', algorithm: 'HS256' });
    const { req, res, next, isNextCalled } = createMockHttp({ headers: { authorization: `Bearer ${forged}` } });
    await requireAuth(req, res, next);
    assert.equal(res.statusCode, 401);
    assert.equal(isNextCalled(), false);
    assert.equal(res.body.message, 'Token inválido');
  });

  await t.test('1.5: token vacío → 401', async () => {
    const { req, res, next, isNextCalled } = createMockHttp({ headers: { authorization: 'Bearer   ' } });
    await requireAuth(req, res, next);
    assert.equal(res.statusCode, 401);
    assert.equal(isNextCalled(), false);
  });

  await t.test('1.6: sin JWT_SECRET en el entorno → 500 y nunca next() (no hay respaldo)', async () => {
    const saved = process.env.JWT_SECRET;
    delete process.env.JWT_SECRET;
    try {
      const token = jwt.sign({ id: 1, email: 'a@b.co', role: 'admin' }, saved, { algorithm: 'HS256' });
      const { req, res, next, isNextCalled } = createMockHttp({ headers: { authorization: `Bearer ${token}` } });
      await requireAuth(req, res, next);
      assert.equal(res.statusCode, 500);
      assert.equal(isNextCalled(), false);
    } finally {
      process.env.JWT_SECRET = saved;
    }
  });
});

test('SUITE 3: PolicyGuard (código real)', () => {
  const blocked = [
    '¿cuál es la dosis de amoxicilina para mi hijo?',
    '¿cuánto tomar de acetaminofén para el dolor?',
    'tengo fiebre y tos fuerte, ¿qué diagnóstico tengo?',
    '¿qué me puedo automedicar para una infección?',
    'recétame algo para el dolor de estómago',
  ];
  for (const q of blocked) {
    const r = evaluatePolicy(q);
    assert.equal(r.blocked, true, `"${q}" debió bloquearse`);
    assert.ok(r.reason.length > 10);
  }
  const allowed = ['dónde venden acetaminofén más barato', 'farmacias cercanas en Bogotá', 'precio de ibuprofeno 400mg', 'ver categorías de medicamentos'];
  for (const q of allowed) assert.equal(evaluatePolicy(q).blocked, false, `"${q}" no debió bloquearse`);
});
