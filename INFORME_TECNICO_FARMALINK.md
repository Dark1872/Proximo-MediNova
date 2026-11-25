# Farmalink-SAS — Paquete técnico (API, servicios, datos y seguridad)

Extraído del código fuente actual del repositorio (estado de trabajo posterior a las tres rondas de correcciones de la Fase 3). No contiene secretos. Rutas de archivo relativas a la raíz del repositorio.

**Pila:** Gateway Express 5 (CommonJS, `packages/gateway/index.js`) → Backend Express 5 + TypeScript (`packages/backend`) → PostgreSQL (Neon). Frontend React/Vite en `src/`. IA: Google Gemini (opcional) más reglas locales.

---

## 1. Rutas del API Gateway

Archivo: `packages/gateway/index.js`. Es el **único punto de entrada para clientes**. Cada llamada al Backend lleva la cabecera interna `x-internal-api-secret`.

- **`validateJWT`:** comprueba la firma HS256 y la expiración con `JWT_SECRET`; si falla, responde 401.
- **`requireAdmin`:** comprueba el claim `role === 'admin'` del token; si no, 403. Es un filtro previo: el Backend vuelve a comprobar el rol contra la BD.

| Método | Ruta pública | Middleware Gateway | Ruta Backend |
|---|---|---|---|
| GET | `/health` | — | (local) |
| GET | `/api/ai/health` | — | `/api/ai/health` |
| POST | `/api/ai/assistant` | — | `/api/ai/assistant` |
| POST | `/api/auth/login` | — | `/api/auth/login` (el Gateway quita `success` de la respuesta) |
| POST | `/api/auth/register` | — | `/api/auth/register` (siempre rol `cliente`) |
| GET | `/api/medicamentos` | — | `/api/medicamentos` |
| GET | `/api/medicamentos/:id` | — | `/api/medicamentos/:id` |
| POST / PUT / DELETE | `/api/medicamentos[/:id]` | validateJWT, requireAdmin | idem |
| GET | `/api/farmacias/cercanas?lat&lng` | — | idem |
| GET | `/api/farmacias` | — | idem |
| GET | `/api/precios` | validateJWT | idem |
| POST | `/api/precios` | validateJWT, requireAdmin | idem |
| GET | `/api/precios/comparar/:medicamentoId?orden=` | validateJWT | idem |
| PUT | `/api/precios/:id` | validateJWT, requireAdmin | idem |
| GET | `/api/precios/historial/:medicamentoId` | — | idem |
| GET | `/api/categorias` | — | idem |
| GET | `/api/dashboard` | validateJWT | idem |
| GET | `/api/home` | — | idem |
| GET | `/api/sugerencias?q=` | — | idem (si falla, recurre a `/api/medicamentos`) |
| GET | `/api/busqueda` y `/api/busqueda/filtros` | — | idem |
| GET | `/api/usuarios/public/equipo` y `/api/usuarios/public/:id` | — | idem |
| GET | `/api/usuarios/me` | validateJWT | idem |
| GET | `/api/usuarios` y `/api/usuarios/:id` | validateJWT, requireAdmin | idem |
| POST | `/api/usuarios` | validateJWT, requireAdmin | idem (creación administrativa) |
| PATCH | `/api/usuarios/:id/team-member` | validateJWT, requireAdmin | idem |
| PUT | `/api/usuarios/:id` | validateJWT (propio usuario o admin; quita `role` e `is_team_member` si no es admin) | idem |
| DELETE | `/api/usuarios/:id` | validateJWT, requireAdmin | idem |

Total: 32 rutas. `PATCH /api/precios/:id` solo existe en el Backend.

---

## 2. Rutas y controladores del Backend

La aplicación se construye en `packages/backend/app.ts` (`createApp()`); `server.ts` valida los secretos, conecta a la BD y abre el puerto.

- **`requireInternalGateway`** (global): exige `x-internal-api-secret` en todo `/api/*` salvo `/api/health`; si falta o no coincide, 403.
- **`requireAuth`:** valida el JWT y carga `usuarioActual` desde la BD **buscando por email**.
- **`requireRole(...)` / `requireAdmin`:** rol leído de la BD (`shared/authMiddleware.ts`).

| Módulo (archivo) | Rutas | Autorización Backend | Notas de implementación |
|---|---|---|---|
| Auth (`auth/authRouter.ts`) | `POST /api/auth/login` | pública | bcrypt (acepta también texto plano heredado). Bloqueo de 15 min tras 5 fallos (en memoria, por email+IP). JWT HS256 de 24 h con `{id, email, role}` |
| | `POST /api/auth/register` | pública | `usuarios/createUsuario.ts`; siempre `cliente`; contraseña de 4 caracteres o más; 409 si el email ya existe |
| Medicamentos (`medicamentos/medicamentosRouter.ts` + `medicamentosController.ts`, validación en `MedicamentoDTO.ts`) | `GET /`, `GET /:id` | públicas | Filtros `category`, `active`, `lab`. Devuelve el precio **más reciente** de cualquier farmacia (`DISTINCT ON`) |
| | `POST /`, `PUT /:id`, `DELETE /:id` | requireAdmin | — |
| Precios (`precios/preciosRouter.ts`) | `GET /` | requireAuth | — |
| | `GET /comparar/:medicamentoId` | requireAuth | Patrón Strategy para ordenar (§3.3) |
| | `POST /`, `PUT /:id`, `PATCH /:id` | `requireRole('admin')` | POST hace upsert por (medicamento, farmacia). Cada cambio se registra en `historial_precios` (`PrecioHistorialService.ts`) |
| | `GET /historial/:medicamentoId` | pública | Series de puntos por farmacia |
| Farmacias (`farmacias/farmaciasRouter.ts`) | `GET /`, `GET /cercanas` | públicas | Haversine en SQL, 10 resultados como máximo |
| Categorías (`categorias/categoriasRouter.ts`) | `GET /` | pública | — |
| Búsqueda (`busqueda/busquedaRouter.ts`) | `GET /`, `GET /filtros` | públicas | §3.1 |
| Sugerencias (`sugerencias/sugerenciasRouter.ts`) | `GET /` | pública | §3.2 |
| Usuarios (`usuarios/usuariosRouter.ts`) | `GET /public/equipo`, `GET /public/:id` | públicas | Solo miembros del equipo (`is_team_member = true`) |
| | `GET /me` | requireAuth | — |
| | `GET /` y `PATCH /:id/team-member` | requireAuth + rol admin | — |
| | `GET /:id` | requireAuth (propio usuario o admin) | 400 si el ID no es numérico |
| | `POST /` | requireAdmin | Creación con rol validado |
| | `PUT /:id` | requireAuth (propio usuario o admin) | Solo un admin puede cambiar `role` |
| | `DELETE /:id` | requireAdmin | — |
| IA (`ai/aiRouter.ts` → `aiController.ts`) | `GET /health`, `POST /assistant` | públicas (tras el Gateway) | §4 |
| App (`app.ts`) | `GET /api/home` | pública | — |
| | `GET /api/dashboard` | requireAuth | — |
| | `GET /api/health` | pública, sin cabecera interna | Health check de Render |

---

## 3. Servicios de búsqueda, precios y farmacias

### 3.1 Búsqueda avanzada — `GET /api/busqueda` (`busqueda/busquedaRouter.ts`)

- **Parámetros:** `q`, `categoria`, `lab`, `orden` (`relevancia` | `precio_asc` | `precio_desc` | `nombre`), `disponible` (`true` | `false`), `precioMin`, `precioMax`, `page` y `limit` (máximo 50).
- **Algoritmo en dos pasadas** (solo medicamentos con `active = true`):
  1. `unaccent(name|lab) ILIKE unaccent('%q%')`, que ignora tildes y mayúsculas → `metodo: "ilike_exacto"`.
  2. Solo si la pasada 1 no devuelve nada: `word_similarity(q, name|lab) > 0.6` con pg_trgm → `metodo: "fuzzy_fallback"`.
  - Sin `q`: aplica solo los filtros → `metodo: "sin_query"`.
- `precio_minimo` es `MIN(precios.precio)` y `farmacias_count` es `COUNT(DISTINCT farmacia_id)`.
- Ejecuta `CREATE EXTENSION IF NOT EXISTS pg_trgm/unaccent` en cada petición.
- **Respuesta:** `{success, query, metodo, filtros, paginacion{page, limit, total, totalPaginas}, data[{id, name, lab, description, categoria_id, categoria_nombre, precio_minimo, farmacias_count, score}]}`.
- `GET /api/busqueda/filtros` devuelve las categorías con su número de medicamentos, los laboratorios y el rango de precios `{min, max, promedio}`.

### 3.2 Sugerencias — `GET /api/sugerencias?q=&estrategia=&limit=` (`sugerencias/`)

`SugerenciaFactory` (patrón Factory Method + Strategy) elige la estrategia automáticamente si no se pasa `estrategia`:

| Condición del query | Estrategia (`estrategiaUsada`) | Técnica |
|---|---|---|
| Contiene una raíz de categoría (`analg`, `antibio`, `cardio`…) | `PorCategoriaStrategy` (`por_categoria`) | Medicamentos activos de la categoría encontrada |
| 4 caracteres o más | `FuzzySearchStrategy` (`fuzzy_trgm`) | SQL con `word_similarity(q, name\|lab) > 0.35` |
| 3 caracteres | `CoincidenciaParcialStrategy` (`coincidencia_parcial`) | El nombre empieza por q (en memoria) |
| Otros casos | `SimilitudBasicaStrategy` (`similitud_basica`) | `includes` en nombre, laboratorio o descripción (en memoria) |

- Si la estrategia elegida no devuelve resultados, se usa `similitud_basica`. Luego se eliminan duplicados por `_id` y se cortan a `limit` (8 por defecto, máximo 20).
- `q` necesita 2 caracteres o más: el Backend responde 400 y el Gateway lo convierte en 200 con lista vacía.
- El router carga **todo el catálogo activo** en memoria en cada petición.
- **Respuesta:** `{success, query, estrategiaUsada, total, sugerencias[{_id (string), id, name, lab, category, categoria_nombre, categoria_id, description, estrategiaUsada}]}`.

### 3.3 Precios

- **Comparar** (`/comparar/:id`): `PrecioStrategyFactory` elige `asc` (por defecto, `precio_ascendente`), `desc` (`precio_descendente`) o `reciente` (`precio_reciente`).
  - Respuesta: `{success, estrategiaUsada, medicamento{id, name, lab, description}, mejorPrecio{precio, farmaciaNombre, fecha}, listaOrdenada[{precioId, farmaciaId:{_id, name, address}, farmaciaNombre, precio, fecha, estrategiaUsada}]}`.
  - Devuelve 404 si el medicamento no existe **y también** si no tiene precios.
- **Historial** (`/historial/:id`): combina `historial_precios` con el precio actual de cada farmacia, ordena cronológicamente y elimina duplicados.
  - Respuesta: `{success, medicamento{id, name, lab}, totalCambios, series[{farmaciaId, farmaciaNombre, farmaciaDireccion, puntos[{fecha, precio}]}]}`.
- **Escritura:** solo admin. Cada cambio queda auditado en `historial_precios.quien_cambio` con el email del usuario que lo hizo.

### 3.4 Farmacias

- **`GET /api/farmacias`:** devuelve un **array directo** (sin `success/data`) con el `SELECT *`: `{id, name, address, phone, latitude, longitude, created_at}`.
- **`GET /api/farmacias/cercanas?lat&lng`:** calcula la distancia con Haversine en SQL (`6371 * acos(...)`, en km) y devuelve las 10 más cercanas, sin radio máximo: `{success, data[{id, name, address, phone, latitude, longitude, distance}]}`.
  - Si faltan `lat`/`lng` o no son válidos, el Backend responde 400, pero el Gateway lo convierte en 500.

---

## 4. Servicio del asistente de IA (`packages/backend/ai/`)

| Archivo | Responsabilidad |
|---|---|
| `aiController.ts` | Valida que `message` tenga 2 caracteres o más (si no, 400). Si `ENABLE_AI_ASSISTANT !== 'true'` responde 200 `{success:false, policy:'blocked'}`. Captura errores (500) |
| `aiService.ts` → `resolveAssistantMessage()` | Orquesta todo el flujo (abajo) |
| `policyGuard.ts` | Reglas regex que bloquean consultas de diagnóstico, dosis, automedicación, tratamiento y síntomas |
| `tools.ts` | Consultas SQL que usa el asistente: `searchMedicines`, `getMedicineById`, `comparePrices`, `getPriceHistory`, `getNearbyPharmacies` |
| `types.ts` | Contratos `AssistantRequest`, `AssistantResponse` y la lista de acciones de navegación `AiAction` |
| `geminiClient.ts` | `generateNarrationWithGemini()`: **no se usa en ningún sitio** (código muerto) |

**Flujo:**
1. **Política:** reglas de `policyGuard` y, además, `evaluatePolicyWithModel()` en Gemini (JSON, temperatura 0) si `AI_USE_GEMINI !== 'false'` y hay `GEMINI_API_KEY`. Si alguna de las dos bloquea, responde `{success:true, policy:'blocked', data{reason, policySource}}`. Si Gemini falla, solo se aplican las reglas.
2. **Intención:** `extractSemanticsWithModel()` en Gemini; si falla, se usa `detectIntent()` por regex. Intenciones posibles: `greeting`, `search`, `product`, `compare`, `history`, `map`, `unknown`.
3. **Navegación:** si el mensaje menciona secciones de la web (carrito, FAQ, etc.), devuelve opciones `go_*`.
4. **Datos:** con `searchMedicines` (unaccent + ILIKE, máximo 6) elige un medicamento principal y, según la intención, llama a `comparePrices`, `getPriceHistory` o `getNearbyPharmacies` (esta última si llegan `context.lat/lng`).
5. **Respuesta:** `{success, policy, message, action, params, requiresConfirmation?, options?[{id, label, action, params}], data?, traceId}`.

**Petición:** `{message, sessionId?, context?{currentView, isAuthenticated, userRole, lat, lng}}`. El contexto lo envía el cliente y no se verifica.

**Advertencias:**
- El endpoint es público y no tiene límite de peticiones ni longitud máxima de mensaje.
- PolicyGuard se puede evadir con paráfrasis («posología», «qué puedo tomar si me duele…»).
- `action` son rutas de la web, y las herramientas devuelven IDs **numéricos** (los endpoints REST los devuelven como string).
- Variables de entorno: `ENABLE_AI_ASSISTANT`, `AI_USE_GEMINI`, `GEMINI_API_KEY`, `AI_MODEL` (por defecto `gemini-2.5-flash`), `AI_TIMEOUT_MS` y `AI_DEBUG_LOGS`.

---

## 5. Esquema de la base de datos (PostgreSQL)

Fuente principal: `packages/backend/database/neon_init.sql` (`farmalink.sql` es equivalente e incluye datos). Las migraciones están en `database/migration_*.sql`, y `usuariosRouter.ts` añade columnas al ejecutarse.

```
categorias (id BIGINT PK, nombre VARCHAR(100) UNIQUE NOT NULL, orden INT NOT NULL)

farmacias (id BIGINT PK, name VARCHAR(255) NN, address VARCHAR(500) NN, phone VARCHAR(20) NN,
           latitude DECIMAL(10,7) NN, longitude DECIMAL(10,7) NN, created_at TIMESTAMP)

medicamentos (id BIGINT PK, name VARCHAR(255) NN, lab VARCHAR(255) NN, active BOOLEAN DEFAULT true,
              description TEXT, categoria_id BIGINT → categorias(id), created_at TIMESTAMP)

precios (id BIGINT PK, precio INTEGER NN, medicamento_id BIGINT NN → medicamentos(id),
         farmacia_id BIGINT NN → farmacias(id), fecha TIMESTAMP)

historial_precios (id BIGINT PK, precio_id BIGINT NN → precios(id) ON DELETE CASCADE,
                   medicamento_id → medicamentos(id), farmacia_id → farmacias(id),
                   precio_anterior INT NN, precio_nuevo INT NN, quien_cambio VARCHAR(255),
                   fecha_cambio TIMESTAMP)

usuarios (id BIGINT PK, name VARCHAR(255) NN, email VARCHAR(255) UNIQUE NN, password VARCHAR(255) NN,
          role VARCHAR(20) CHECK IN ('cliente','farmaceutico','admin'), created_at TIMESTAMP,
          + migraciones: phone, address, bio, birth_date, profile_picture, preferences JSONB,
            last_login, updated_at (v1_4_0); telefono, avatar_url, preferencias JSONB,
            ultimo_login (punto4); is_team_member BOOLEAN (añadida por el router en ejecución))
```

**Índices:** `farmacias(latitude, longitude)`; `precios(medicamento_id)`, `(farmacia_id)` y `(fecha DESC)`; `medicamentos(categoria_id)`, `(name)` y `(lab)`; `usuarios(email)` y `(role)`; `historial_precios(medicamento_id)`, `(farmacia_id)`, `(fecha_cambio DESC)` y `(precio_id)`.

**Extensiones:** `pg_trgm` y `unaccent`, que el código crea en tiempo de ejecución.

**Observaciones:**
- No hay un `UNIQUE (medicamento_id, farmacia_id)` en `precios`; el upsert lo hace el código.
- Hay columnas duplicadas en `usuarios` (`phone`/`telefono`, `profile_picture`/`avatar_url`, `preferences`/`preferencias`, `last_login`/`ultimo_login`).
- node-pg devuelve `BIGINT` y `DECIMAL` como **string**, así que los IDs y las coordenadas llegan en JSON como texto.
- No existen tablas de carrito, pedidos, favoritos, tokens de dispositivo ni recuperación de contraseña.

---

## 6. Documentación de endpoints existente

| Documento | Estado |
|---|---|
| `DOCUMENTACION.md` | **Obsoleto**: describe un esquema MongoDB que ya no usa el código |
| `ARQUITECTURA.md` | **Parcialmente obsoleto**: cita Mongoose y `/gateway` y `/backend`; los patrones Strategy, Factory y Singleton siguen siendo válidos |
| `Fase1_Reconocimiento_Backend_Farmalink_MediNova.docx` | Lista de endpoints y brechas para MediNova (carrito/pedidos, push, recuperación de contraseña); útil como referencia |
| `Plan_Implementacion_Farmalink_Mobile_Flutter.docx` | Plan de integración Flutter; no es una especificación de API |
| OpenAPI / Swagger | **No existe** |

Este documento (§1–§5) es la referencia de rutas más actualizada; está contrastada con el código.

---

## 7. Informe final de las correcciones de seguridad (Fase 3)

### 7.1 Situación de partida (auditoría independiente)

- El secreto JWT de respaldo era público y estaba en el código, así que se podían falsificar tokens y crear administradores.
- Un cliente podía modificar precios.
- El Backend expuesto respondía sin token en `GET /api/usuarios/:id` (datos personales) y en `GET /api/precios`.
- Había credenciales reales de Neon y Gemini en `.env` versionados.
- Las pruebas copiaban la lógica dentro del test.
- El frontend contenía credenciales de administrador.

### 7.2 Correcciones implementadas y verificadas

| # | Corrección | Archivos principales | Evidencia |
|---|---|---|---|
| P0.1 | Sin secreto de respaldo. Gateway y Backend **no arrancan** sin `JWT_SECRET` e `INTERNAL_API_SECRET` válidos (32 bytes o más, distintos entre sí y distintos de los valores ya publicados, de los que solo se guarda el hash). Solo HS256 y expiración obligatoria | `backend/shared/securityConfig.ts`, `backend/server.ts`, `gateway/securityConfig.js`, `gateway/index.js`, `render.yaml` (`sync: false`) | 14 arranques inválidos terminan con código 1 sin mostrar el secreto; 7 tipos de token inválido reciben 401 |
| P0.3 | Crear o modificar precios exige el rol `admin` leído de la BD, en Backend y Gateway | `backend/precios/preciosRouter.ts`, `backend/shared/authMiddleware.ts` (`requireRole`) | Sin token 401; cliente, cliente con `role=admin` en el token y farmacéutico 403; admin 200; el precio no cambia tras ningún intento rechazado |
| P0.4 | Registro público separado (`/api/auth/register`, siempre `cliente`). `POST /api/usuarios` solo para admin, con el rol leído de la BD | `backend/auth/authRouter.ts`, `backend/usuarios/createUsuario.ts`, `backend/usuarios/usuariosRouter.ts` | Pedir `role` admin o farmacéutico crea un cliente; un token manipulado no crea usuarios |
| P0.5 | El Backend solo responde al Gateway (secreto interno comparado en tiempo constante). `GET /usuarios/:id` solo para el propio usuario o un admin; `GET /precios` con autenticación; perfil público solo para el equipo | `backend/app.ts`, `backend/shared/internalAuth.ts` | Acceso directo sin cabecera o con cabecera incorrecta → 403; health 200; el tráfico legítimo del Gateway funciona |
| P0.6 | Pruebas HTTP reales sobre el código fuente (vía tsx): Backend real con BD simulada en memoria y Gateway real como proceso | `backend/test/p0_http_security.test.mjs`, `security_and_contracts.test.mjs`, `support.mjs`; `npm test` | **100/100**, 0 omitidas. Una prueba de mutación (reintroduciendo dos fallos) produjo 16 fallos |
| FE | Eliminadas las credenciales incrustadas y el inicio de sesión automático (`useDashboard.ts`, `AdminMedicamentos.tsx`, botones demo de `Login.tsx`). `isAdmin` usa el rol verificado por `/api/usuarios/me` | `src/hooks/useSession.ts`, `src/hooks/useDashboard.ts`, `src/components/...` | Bundle nuevo: 0 de 15 valores sensibles; el `src/dist` anterior contenía 6 |

**Validación técnica:**
- `tsc --noEmit` del Backend: correcto.
- Sintaxis del Gateway: correcta.
- Frontend: compila; sus 21 errores de TypeScript ya existían y no se añadió ninguno.
- No se tocaron `dist/` (versionado), los `.env`, el índice de Git ni MediNova.

**Cambios de contrato:** ninguno en los endpoints que consumiría MediNova. Lo que cambió:
- El acceso directo al Backend responde 403.
- Escribir precios como cliente o farmacéutico responde 403.
- `/api/usuarios/public/:id` responde 404 para quien no es del equipo.
- Los tokens emitidos antes de rotar el secreto dejan de valer.

### 7.3 Pendientes operativos (no verificados como hechos)

1. Rotar la contraseña de Neon y actualizar `DATABASE_URL` en Render y en los `.env` locales.
2. Crear una clave de Gemini nueva y **revocar** la antigua.
3. Generar `JWT_SECRET` e `INTERNAL_API_SECRET` (distintos):
   `node -e "console.log(require('crypto').randomBytes(48).toString('base64'))"`.
4. Configurar ambos secretos, con los mismos valores, en Gateway y Backend de Render, y desplegar los dos a la vez. Añadirlos también a `packages/backend/.env` y `packages/gateway/.env`.
5. Verificar en la BD real el rol de la cuenta que estaba incrustada en el frontend (según `neon_init.sql`, **admin**, con una contraseña de 4 caracteres). Cambiar su contraseña y la de la cuenta demo de cliente, que usa la misma.
6. Volver a compilar y desplegar el frontend, y regenerar o eliminar el `src/dist` local.
7. Dejar de versionar los `.env` sin borrarlos: `git rm --cached .env packages/backend/.env packages/gateway/.env src/.env`, y después un commit.
8. Valorar limpiar el historial de Git si el repositorio estuvo al alcance de terceros. Lo que realmente neutraliza la fuga es la rotación.

### 7.4 Riesgos conocidos fuera del alcance P0

- Bloqueo de login en memoria y por email+IP: detrás del Gateway permite bloquear cuentas ajenas y no funciona con varias instancias.
- Asistente IA público, sin límite de peticiones ni longitud máxima, y PolicyGuard evadible.
- Las respuestas 500 incluyen detalles de error de PostgreSQL.
- `ssl.rejectUnauthorized: false` en la conexión a la BD.
- CORS del Backend abierto, con `credentials: true`.
- Contraseña mínima de 4 caracteres; cambiar contraseña o email no pide la contraseña actual.
- La identidad del token se resuelve por email, no por ID.
- No hay refresh token ni revocación de tokens.
- La prueba de Vitest del frontend ya fallaba antes (configuración sin `globals` y falta de `ToastProvider`).

### 7.5 Estado

**APTO CON BLOQUEOS OPERATIVOS.** El código está corregido y probado; faltan las rotaciones y la configuración de §7.3. No está certificado para producción. Fase 4 de MediNova no iniciada.
