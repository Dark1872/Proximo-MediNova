// Utilidades compartidas por las pruebas de seguridad.
// - Secretos temporales aleatorios por ejecución (nunca el secreto público anterior como configuración).
// - Base de datos simulada en memoria: no se conecta a Neon ni modifica datos reales.
// - Arranque de procesos reales (Gateway / Backend) en un directorio temporal sin archivos .env.
import { spawn, execFileSync } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import fs from 'node:fs';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const BACKEND_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const GATEWAY_DIR = path.resolve(BACKEND_DIR, '..', 'gateway');
export const REPO_DIR = path.resolve(BACKEND_DIR, '..', '..');

export const newSecret = () => randomBytes(48).toString('base64');

/** Entorno mínimo para procesos hijos: sin credenciales heredadas (PG*, DATABASE_URL, GEMINI, JWT...). */
export function cleanEnv(extra = {}) {
  const env = {};
  for (const [k, v] of Object.entries(process.env)) {
    if (/^(PG|DATABASE_URL|GEMINI|JWT_SECRET|INTERNAL_API_SECRET|ENABLE_AI|AI_|BACKEND_URL|PORT$)/i.test(k)) continue;
    env[k] = v;
  }
  for (const [k, v] of Object.entries(extra)) {
    if (v === undefined) delete env[k];
    else env[k] = v;
  }
  return env;
}

/** Directorio de trabajo vacío: dotenv no encontrará ningún .env real. */
export function emptyCwd() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'farmalink-test-'));
}

export async function freePort() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.unref();
    srv.on('error', reject);
    srv.listen(0, '127.0.0.1', () => {
      const { port } = srv.address();
      srv.close(() => resolve(port));
    });
  });
}

/**
 * Lanza un proceso y espera a que imprima `readyText` (arrancó) o termine (no arrancó).
 * Devuelve { started, code, stdout, stderr, child }.
 */
export function startProcess(args, { env, cwd, readyText, timeoutMs = 20000 }) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, args, { env, cwd, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    let done = false;
    const finish = (result) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      resolve({ ...result, stdout, stderr, child });
    };
    child.stdout.on('data', (d) => {
      stdout += d;
      if (readyText && stdout.includes(readyText)) finish({ started: true, code: null });
    });
    child.stderr.on('data', (d) => { stderr += d; });
    child.on('exit', (code) => finish({ started: false, code }));
    const timer = setTimeout(() => finish({ started: false, code: 'timeout' }), timeoutMs);
  });
}

export function startGateway({ env, port }) {
  return startProcess([path.join(GATEWAY_DIR, 'index.js')], {
    env: cleanEnv({ PORT: String(port), ...env }),
    cwd: emptyCwd(),
    readyText: 'Gateway corriendo',
  });
}

export function startBackendServer({ env, port }) {
  const tsxLoader = import.meta.resolve('tsx');
  return startProcess(['--import', tsxLoader, path.join(BACKEND_DIR, 'server.ts')], {
    // PGHOST/PGPORT apuntan a un puerto cerrado local: si llegara a intentar conectar, falla sin salir de la máquina.
    env: cleanEnv({ PORT: String(port), PGHOST: '127.0.0.1', PGPORT: '1', ...env }),
    cwd: emptyCwd(),
    readyText: 'Servidor corriendo',
  });
}

/**
 * Secreto de respaldo público que existió en el código (commit ee00a39).
 * Se obtiene del historial Git solo para FIRMAR TOKENS DE ATAQUE en las pruebas; nunca se imprime
 * ni se usa como configuración. Si el historial no está disponible devuelve null.
 */
export function legacyPublicSecret() {
  try {
    const src = execFileSync('git', ['show', 'ee00a39:packages/backend/shared/authMiddleware.ts'], {
      cwd: REPO_DIR, stdio: ['ignore', 'pipe', 'ignore'],
    }).toString();
    const m = src.match(/process\.env\.JWT_SECRET \|\| '([^']+)'/);
    return m ? m[1] : null;
  } catch {
    return null;
  }
}

// ── Base de datos simulada ────────────────────────────────────────────────────
// Devuelve los tipos como node-pg: BIGINT -> string, INTEGER -> number.
export function createFakeDb() {
  const state = {
    usuarios: new Map(), // id -> fila
    precios: new Map(),
    historial: [],
    medicamentos: new Map([['1', { id: '1', name: 'Acetaminofén 500mg', lab: 'Genfar' }]]),
    farmacias: new Map([['1', { id: '1', name: 'Farmacia Uno', address: 'Calle 1' }]]),
    categorias: [{ id: '1', nombre: 'Analgésicos', orden: 1 }],
    nextUserId: 100,
    nextPrecioId: 500,
    unsupported: [],
  };
  state.precios.set('5', { id: '5', medicamento_id: '1', farmacia_id: '1', precio: 1000, fecha: new Date() });

  const byEmail = (email) => [...state.usuarios.values()].find((u) => u.email === String(email).toLowerCase());
  const pub = (u) => ({ id: u.id, name: u.name, email: u.email, role: u.role, phone: u.phone, profile_picture: u.profile_picture, bio: u.bio, created_at: u.created_at });

  const pool = {
    async query(sql, params = []) {
      const s = sql.replace(/\s+/g, ' ').trim();
      let m;
      if (/^ALTER TABLE/i.test(s) || /^UPDATE usuarios SET ultimo_login/i.test(s)) return { rows: [] };
      if (/^SELECT id, name, email, role FROM public\.usuarios WHERE email = \$1$/i.test(s)) {
        const u = byEmail(params[0]); return { rows: u ? [{ id: u.id, name: u.name, email: u.email, role: u.role }] : [] };
      }
      if (/^SELECT id, name, email, role FROM public\.usuarios WHERE id = \$1$/i.test(s)) {
        const u = state.usuarios.get(String(params[0]));
        return { rows: u ? [{ id: u.id, name: u.name, email: u.email, role: u.role }] : [] };
      }
      if (/^DELETE FROM public\.usuarios WHERE id = \$1 RETURNING id$/i.test(s)) {
        const id = String(params[0]);
        const existed = state.usuarios.delete(id);
        return { rows: existed ? [{ id }] : [] };
      }
      if (/^SELECT id, name, email, role, password FROM usuarios WHERE email = \$1$/i.test(s)) {
        const u = byEmail(params[0]); return { rows: u ? [u] : [] };
      }
      if (/^SELECT id FROM public\.usuarios WHERE email = \$1$/i.test(s)) {
        const u = byEmail(params[0]); return { rows: u ? [{ id: u.id }] : [] };
      }
      if (/^INSERT INTO public\.usuarios \(name, email, password, role\)/i.test(s)) {
        const id = String(state.nextUserId++);
        const row = { id, name: params[0], email: params[1], password: params[2], role: params[3], phone: null, profile_picture: null, bio: null, is_team_member: false, created_at: new Date() };
        state.usuarios.set(id, row);
        return { rows: [{ id, name: row.name, email: row.email, role: row.role, created_at: row.created_at }] };
      }
      if (/FROM public\.usuarios WHERE id = \$1 AND is_team_member = true$/i.test(s)) {
        const u = state.usuarios.get(String(params[0]));
        return { rows: u && u.is_team_member ? [{ id: u.id, name: u.name, role: u.role, phone: u.phone, profile_picture: u.profile_picture, bio: u.bio, created_at: u.created_at }] : [] };
      }
      if (/^SELECT id, name, email, role, phone, profile_picture, bio, created_at FROM public\.usuarios WHERE id = \$1$/i.test(s)) {
        const u = state.usuarios.get(String(params[0])); return { rows: u ? [pub(u)] : [] };
      }
      if (/FROM public\.usuarios ORDER BY created_at DESC$/i.test(s)) {
        return { rows: [...state.usuarios.values()].map((u) => ({ ...pub(u), is_team_member: u.is_team_member })) };
      }
      if (/^SELECT \* FROM precios WHERE id = \$1$/i.test(s)) {
        const p = state.precios.get(String(params[0])); return { rows: p ? [{ ...p }] : [] };
      }
      if (/^INSERT INTO historial_precios/i.test(s)) { state.historial.push(params); return { rows: [] }; }
      if ((m = s.match(/^UPDATE precios SET precio = \$1, fecha = NOW\(\) WHERE id = \$2 RETURNING \*$/i))) {
        const p = state.precios.get(String(params[1]));
        if (!p) return { rows: [] };
        p.precio = Math.round(Number(params[0])); p.fecha = new Date();
        return { rows: [{ ...p }] };
      }
      if (/^SELECT name, lab FROM medicamentos WHERE id = \$1$/i.test(s)) {
        const x = state.medicamentos.get(String(params[0])); return { rows: x ? [{ name: x.name, lab: x.lab }] : [] };
      }
      if (/^SELECT name, address FROM farmacias WHERE id = \$1$/i.test(s)) {
        const x = state.farmacias.get(String(params[0])); return { rows: x ? [{ name: x.name, address: x.address }] : [] };
      }
      if (/^SELECT id FROM medicamentos WHERE id = \$1$/i.test(s)) {
        return { rows: state.medicamentos.has(String(params[0])) ? [{ id: String(params[0]) }] : [] };
      }
      if (/^SELECT id FROM farmacias WHERE id = \$1$/i.test(s)) {
        return { rows: state.farmacias.has(String(params[0])) ? [{ id: String(params[0]) }] : [] };
      }
      if (/^SELECT id, precio FROM precios WHERE medicamento_id = \$1 AND farmacia_id = \$2$/i.test(s)) {
        const p = [...state.precios.values()].find((x) => x.medicamento_id === String(params[0]) && x.farmacia_id === String(params[1]));
        return { rows: p ? [{ id: p.id, precio: p.precio }] : [] };
      }
      if (/^INSERT INTO precios \(medicamento_id, farmacia_id, precio, fecha\)/i.test(s)) {
        const id = String(state.nextPrecioId++);
        const row = { id, medicamento_id: String(params[0]), farmacia_id: String(params[1]), precio: params[2], fecha: new Date() };
        state.precios.set(id, row);
        return { rows: [{ ...row }] };
      }
      if (/^SELECT p\.\*, m\.name as medicamento_nombre.* FROM precios p JOIN medicamentos m/i.test(s)) {
        return { rows: [...state.precios.values()].map((p) => ({ ...p, medicamento_nombre: 'Acetaminofén 500mg', farmacia_nombre: 'Farmacia Uno' })) };
      }
      if (/^SELECT id, nombre, orden FROM categorias/i.test(s)) return { rows: state.categorias };
      if (/^SELECT id FROM public\.usuarios WHERE email = \$1 AND id != \$2$/i.test(s)) {
        const u = byEmail(params[0]);
        return { rows: u && u.id !== String(params[1]) ? [{ id: u.id }] : [] };
      }
      if ((m = s.match(/^UPDATE public\.usuarios SET (.+) WHERE id = \$(\d+) RETURNING (.+)$/i))) {
        const assignments = m[1].split(', ').map((c) => c.split(' = '));
        if (state.missingProfileColumns && assignments.some(([col]) => ['phone', 'bio', 'profile_picture'].includes(col))) {
          throw new Error('column "phone" of relation "usuarios" does not exist');
        }
        const u = state.usuarios.get(String(params[Number(m[2]) - 1]));
        if (!u) return { rows: [] };
        for (const [col, ph] of assignments) u[col] = params[Number(ph.slice(1)) - 1];
        const cols = m[3].split(',').map((c) => c.trim());
        return { rows: [Object.fromEntries(cols.map((c) => [c, u[c]]))] };
      }
      if (/^SELECT DISTINCT ON \(m\.id\).*WHERE m\.id = \$1/i.test(s)) {
        const x = state.medicamentos.get(String(params[0]));
        return { rows: x ? [{ ...x, active: true, description: null, categoria_id: '1', categoria_nombre: 'Analgésicos', categoria_orden: 1, farmaciaId: '1', farmaciaNombre: 'Farmacia Uno', precio: 1000 }] : [] };
      }
      state.unsupported.push(s.slice(0, 120));
      throw new Error('fake-db: consulta no soportada por la simulación');
    },
  };
  return { pool, state };
}

/** Inserta un usuario directamente en la BD simulada (contraseña ya hasheada con bcrypt). */
export function seedUser(state, { id, name, email, passwordHash, role, isTeamMember = false, phone = null }) {
  state.usuarios.set(String(id), {
    id: String(id), name, email: email.toLowerCase(), password: passwordHash, role,
    phone, profile_picture: null, bio: null, is_team_member: isTeamMember, created_at: new Date(),
  });
}

export async function http(base, method, url, { token, body, headers = {} } = {}) {
  const h = { ...headers };
  if (body !== undefined) h['Content-Type'] = 'application/json';
  if (token) h.Authorization = `Bearer ${token}`;
  const res = await fetch(base + url, { method, headers: h, body: body !== undefined ? JSON.stringify(body) : undefined });
  const text = await res.text();
  let json;
  try { json = JSON.parse(text); } catch { json = text; }
  return { status: res.status, body: json };
}
