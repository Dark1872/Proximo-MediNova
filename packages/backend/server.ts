import 'dotenv/config';
import Database from './shared/db.js';
import { loadSecurityConfig, SecretConfigError } from './shared/securityConfig.js';
import { createApp } from './app.js';

// Validación de secretos ANTES de conectar a la base de datos o abrir el puerto.
// Sin JWT_SECRET / INTERNAL_API_SECRET válidos el servidor no arranca.
try {
  loadSecurityConfig();
} catch (err) {
  const reason = err instanceof SecretConfigError ? err.message : 'Error desconocido validando secretos';
  console.error(`[Backend] Arranque cancelado: ${reason}`);
  process.exit(1);
}

const PORT = process.env.PORT || 3001;
const app = createApp();

const db = Database.getInstance();

db.connect()
  .then(() => {
    console.log('✅ PostgreSQL conectado exitosamente');
  })
  .catch(err => {
    console.error('❌ Error conectando a PostgreSQL:', err.message);
  });

app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
});
