# -*- coding: utf-8 -*-
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from build_plan_helpers import (
    doc, OUTPUT_FILE, add_header, add_callout, add_code_block, 
    create_table, add_bullet, COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT, COLOR_MUTED
)

print("Starting document creation...")

# ==============================================================================
# PORTADA CORPORATIVA
# ==============================================================================
for _ in range(3):
    doc.add_paragraph()

p_title_tag = doc.add_paragraph()
p_title_tag.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_tag = p_title_tag.add_run("DOCUMENTO TÉCNICO DE INGENIERÍA DE SOFTWARE")
r_tag.bold = True
r_tag.font.size = Pt(11)
r_tag.font.color.rgb = COLOR_SECONDARY

p_main_title = doc.add_paragraph()
p_main_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_mt = p_main_title.add_run("PLAN DE IMPLEMENTACIÓN PROFESIONAL\nMIGRACIÓN DE FARMALINK SAS A FLUTTER")
r_mt.bold = True
r_mt.font.size = Pt(26)
r_mt.font.color.rgb = COLOR_PRIMARY

p_sub = doc.add_paragraph()
p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_sub = p_sub.add_run("Estrategia Integral de Modernización Móvil, Arquitectura Distribuida Multidispositivo,\nMetodología Ágil SCRUM y Distribución de Roles para Equipo de 5 Integrantes")
r_sub.font.size = Pt(13)
r_sub.font.color.rgb = COLOR_TEXT

for _ in range(2):
    doc.add_paragraph()

# Metadatos en tabla
meta_headers = ["Campo Metadato", "Detalle de Especificación"]
meta_data = [
    ["Proyecto", "Farmalink SAS - Versión Móvil Nativa (Android & iOS)"],
    ["Organización / Empresa", "Farmalink SAS (Colombia)"],
    ["Modelo Arquitectónico", "Arquitectura Desacoplada Multidispositivo (BD Remota + Backend Node/TS + Frontend Flutter)"],
    ["Tamaño del Equipo", "5 Integrantes (Product Owner, Scrum Master, 3 Mobile/Full-Stack Developers)"],
    ["Marco de Trabajo", "SCRUM Adaptado (Sprints de 2 semanas, cadencia fija, DoD formal)"],
    ["Fecha de Expedición", "Octubre 2026"],
    ["Versión del Plan", "Versión 2.0 (Aprobación Técnica y Operativa)"],
    ["Estado", "En Fase de Planificación y Setup Inicial (Sprint 0)"]
]
create_table(doc, meta_headers, meta_data, [2.2, 4.6])

doc.add_page_break()

# ==============================================================================
# TABLA DE CONTENIDO Y RESUMEN EJECUTIVO
# ==============================================================================
add_header(doc, "Resumen Ejecutivo y Declaración de Propósito", level=1)
doc.add_paragraph(
    "El presente documento técnico establece el Plan Maestro de Implementación para la migración y reingeniería de la plataforma web "
    "FARMALINK SAS hacia una aplicación móvil nativa multiplataforma desarrollada en Flutter. Farmalink SAS es un sistema inteligente "
    "de comparación y geolocalización de medicamentos en Bogotá, que actualmente integra búsqueda difusa (fuzzy search), "
    "análisis histórico de fluctuación de precios (Keepa-style), carrito de compras y un asistente de inteligencia artificial con Google Gemini."
)
doc.add_paragraph(
    "El requerimiento fundamental del negocio exige que el nuevo ecosistema opere bajo una arquitectura física desacoplada y distribuida: "
    "la base de datos se ejecuta de forma independiente en un servidor/dispositivo dedicado (garantizando persistencia e integridad transaccional), "
    "la capa intermedia de lógica de negocio y API Gateway se ejecuta en un host especializado, y la capa de presentación (Frontend) corre "
    "exclusivamente en los dispositivos móviles de los usuarios finales (smartphones Android/iOS). El proyecto es ejecutado por un equipo "
    "altamente calificado de 5 profesionales bajo el marco ágil SCRUM, con una asignación de responsabilidades estrictamente balanceada."
)

add_callout(doc, "Directriz de Despliegue Físico Multidispositivo", 
    "A diferencia de un entorno monolítico local donde BD, Backend y Frontend comparten el mismo localhost, en este plan se garantiza "
    "que la base de datos PostgreSQL opere en una instancia independiente (Neon Cloud o servidor PostgreSQL dedicado en red), el API Gateway "
    "y Backend en un servidor centralizado, y la aplicación Flutter en los dispositivos móviles de cada miembro del equipo y usuarios finales, "
    "utilizando direccionamiento IP, túneles seguros y variables de entorno controladas.", "info")

add_header(doc, "Estructura del Plan de Implementación", level=2)
toc_items = [
    "1. Diagnóstico Integral del Proyecto Actual (Estructura, Código, Patrones y Cuellos de Botella)",
    "2. Arquitectura de Origen vs. Arquitectura Destino (Separación Multidispositivo y Flujo de Datos)",
    "3. Inventario Completo de Tecnologías, Librerías y Dependencias (React vs. Flutter)",
    "4. Justificación Técnica del Marco de Trabajo: SCRUM vs. Alternativas Ágiles",
    "5. Distribución Equitativa de Responsabilidades y Asignación de Roles (5 Integrantes)",
    "6. Requisitos de Hardware, Software y Configuración por Dispositivo de cada Miembro",
    "7. Estrategia de Migración por Fases y Desglose de Sprints (Fases 0 a 5)",
    "8. Plan de Migración y Operación de la Base de Datos Multidispositivo",
    "9. Migración y Adaptación del Backend Core y API Gateway",
    "10. Desarrollo del Frontend Móvil en Flutter (Clean Architecture, BLoC/Riverpod y Gemini IA)",
    "11. Estrategia de Pruebas QA, Automatización y Validación de Calidad",
    "12. Infraestructura, Redes, Cloud y Estrategia DevOps Móvil (CI/CD)",
    "13. Matriz de Gestión de Riesgos, Contingencias y Mitigación",
    "14. Cronograma Detallado, Criterios de Aceptación (Gherkin) y Definition of Done (DoD)",
    "15. Recomendaciones Técnicas de Experto y Sugerencias de Alto Impacto",
    "16. Preguntas y Decisiones Estratégicas Pendientes para el Equipo"
]
for item in toc_items:
    add_bullet(doc, item.split(". ")[0], item.split(". ")[1])

doc.add_page_break()

# ==============================================================================
# SECCIÓN 1: DIAGNÓSTICO DEL PROYECTO ACTUAL
# ==============================================================================
add_header(doc, "1. Diagnóstico del Proyecto Actual", level=1)

add_header(doc, "1.1 Análisis Estructural y Repositorio", level=2)
doc.add_paragraph(
    "El proyecto Farmalink SAS se encuentra estructurado bajo un monorepo híbrido que acopla paquetes de backend, "
    "un micro-gateway aplicativo y una aplicación de cliente web Single Page Application (SPA). A través de la auditoría "
    "directa del código fuente, se identifican tres componentes troncales:"
)
add_bullet(doc, "Frontend Web (src/)", "SPA desarrollada en React 19.2, TypeScript 5.9 y empaquetada mediante Vite 7.3. "
           "Implementa un enrutamiento interno gestionado por estado (App.tsx con 16 vistas modulares) y React Router DOM 7.13. "
           "Utiliza Leaflet 1.9 y React-Leaflet 5.0 para mapas, Recharts 3.8 para dashboard y React-GA4 para analítica.")
add_bullet(doc, "API Gateway (packages/gateway/)", "Servidor Node.js con Express 5.2 (escrito en JavaScript CommonJS puro). "
           "Actúa como proxy inverso aplicativo hacia el backend en el puerto 3001, valida tokens JWT, centraliza el inicio de sesión "
           "y controla el enrutamiento hacia los recursos.")
add_bullet(doc, "Backend Core (packages/backend/)", "Servidor modular en Node.js, Express 5.2 y TypeScript compilado mediante tsx/tsc. "
           "Conecta a una base de datos relacional PostgreSQL alojada en Neon Cloud mediante un Pool Singleton de node-postgres (pg 8.13). "
           "Contiene la lógica de negocio, módulos de sugerencias avanzadas y el asistente de inteligencia artificial con Gemini 2.5 Flash.")

add_header(doc, "1.2 Patrones de Diseño Detectados en el Código Fuente", level=2)
doc.add_paragraph(
    "Uno de los mayores activos de Farmalink SAS es la correcta implementación de patrones de diseño GoF (Gang of Four), "
    "los cuales deben ser preservados y replicados conceptualmente en la arquitectura Flutter:"
)
pat_headers = ["Patrón de Diseño", "Ubicación en Código Actual", "Propósito y Beneficio Observado", "Estrategia en Flutter"]
pat_data = [
    ["Strategy", "packages/backend/sugerencias/strategies/\npackages/backend/precios/strategies/", 
     "Encapsula algoritmos intercambiables de búsqueda (CoincidenciaParcial, PorCategoria, SimilitudBasica, FuzzySearch) y de ordenamiento de precios (Ascendente, Descendente, Reciente).",
     "Replicar en capa de servicios Flutter para filtros locales y ordenamiento en cliente."],
    ["Factory Method", "packages/backend/sugerencias/SugerenciaFactory.ts\npackages/backend/precios/PrecioStrategyFactory.ts",
     "Instancia dinámicamente la estrategia adecuada según el query o los parámetros del usuario sin contaminar los enrutadores.",
     "Utilizar SearchStrategyFactory en Dart para instanciar algoritmos de filtrado local."],
    ["Singleton", "packages/backend/shared/db.ts",
     "Garantiza una única instancia del Pool de conexiones a PostgreSQL, evitando fugas de memoria y agotamiento del pooler.",
     "Implementar en Flutter para clientes HTTP (DioClient) y bases de datos locales (Hive/SecureStorage)."],
    ["Proxy Inverso", "packages/gateway/index.js",
     "Intermediario de seguridad que valida JWT antes de permitir acceso a las operaciones sensibles del backend.",
     "Se mantiene en la arquitectura destino como punto único de entrada para la app móvil."],
    ["Data Transfer Object (DTO)", "packages/backend/medicamentos/MedicamentoDTO.ts\npackages/backend/precios/PrecioDTO.ts",
     "Desacopla el esquema relacional de la base de datos de los datos serializados enviados a la interfaz.",
     "Se mapea directamente a clases Dart con serialización segura (@JsonSerializable o Freezed)."]
]
create_table(doc, pat_headers, pat_data, [1.2, 1.8, 2.2, 1.6])

add_header(doc, "1.3 Hallazgos Críticos, Deuda Técnica y Oportunidades de Mejora", level=2)
doc.add_paragraph(
    "La auditoría del código reveló las siguientes fallas arquitectónicas en el sistema actual que deben corregirse obligatoriamente "
    "durante la migración móvil:"
)
add_bullet(doc, "Bypass del API Gateway (Vulnerabilidad de Enrutamiento)", 
           "En el frontend web (SearchAutocomplete.tsx), las peticiones de autocompletado y sugerencias se dirigen directamente al "
           "puerto 3001 del Backend Core, eludiendo el API Gateway (puerto 8080/4000). En la versión móvil Flutter, todo el tráfico "
           "debe pasar obligatoriamente por el Gateway centralizado.")
add_bullet(doc, "Discrepancia de Lenguaje en Gateway vs. Backend", 
           "El Backend está construido en TypeScript riguroso, mientras que el Gateway está escrito en JavaScript estándar con Axios. "
           "Se recomienda unificar el Gateway a TypeScript para garantizar tipado estricto en los DTOs de paso.")
add_bullet(doc, "Consumo Ineficiente de Recursos en Búsquedas", 
           "En sugerenciasRouter.ts, se ejecutan consultas amplias a la base de datos descargando colecciones a memoria RAM para luego "
           "filtrarlas mediante arrays de JavaScript. En la versión móvil, se debe aprovechar la capacidad de índices full-text y "
           "consultas parametrizadas en PostgreSQL, reduciendo el payload transferido por la red móvil (3G/4G/5G).")
add_bullet(doc, "Inexistencia de Caché Offline", 
           "El frontend React actual depende 100% de conectividad constante. Un usuario en un sótano o farmacia sin señal móvil "
           "pierde la funcionalidad. La versión Flutter implementará caché local con Hive y SharedPreferences.")

doc.add_page_break()

# ==============================================================================
# SECCIÓN 2: ARQUITECTURA DE ORIGEN VS ARQUITECTURA DESTINO
# ==============================================================================
add_header(doc, "2. Arquitectura de Origen y Arquitectura Destino", level=1)

add_header(doc, "2.1 Comparación de Topología y Despliegue Físico", level=2)
doc.add_paragraph(
    "El requerimiento fundamental del proyecto establece que la versión móvil debe mantener una estricta separación de capas "
    "en dispositivos independientes. A continuación, se detalla la comparativa física y lógica entre la arquitectura actual y la destino:"
)

arch_comp_headers = ["Dimensión", "Arquitectura de Origen (Web)", "Arquitectura Destino (Flutter Mobile)"]
arch_comp_data = [
    ["Dispositivo Frontend", "Navegador Web en PC de escritorio / laptop (Vercel CDN).", "Dispositivos móviles Android y iPhone de los usuarios finales y equipo."],
    ["Dispositivo Backend", "Servidor Web en Render.com ejecutando Node.js/Express.", "Servidor dedicado en red local o instancia cloud (Render/AWS/GCP/Host local)."],
    ["Dispositivo Base de Datos", "Instancia Neon Cloud PostgreSQL (AWS us-east-1).", "Servidor independiente de base de datos PostgreSQL (Neon Cloud o máquina dedicada en LAN)."],
    ["Protocolo de Comunicación", "HTTP/HTTPS con llamadas REST y fetch nativo.", "HTTPS REST seguro mediante cliente Dio con interceptores de reconexión y tokens."],
    ["Gestión de Sesión", "Tokens JWT almacenados en localStorage (vulnerable a XSS).", "Tokens JWT almacenados en Hardware Keystore / Keyring seguro vía flutter_secure_storage."],
    ["Capacidad Offline", "Nula. La aplicación falla si no hay conexión a Internet.", "Alta. Caché local con Hive NoSQL para consulta offline de farmacias y medicamentos."],
    ["Geolocalización", "API de navegador (Leaflet / OpenStreetMap).", "GPS nativo de alta precisión mediante geolocator (permisos nativos en runtime)."],
    ["Notificaciones", "No disponibles.", "Notificaciones push en tiempo real mediante Firebase Cloud Messaging (FCM)."]
]
create_table(doc, arch_comp_headers, arch_comp_data, [1.5, 2.6, 2.7])

add_header(doc, "2.2 Diagrama Arquitectónico Conceptual: Ecosistema Multidispositivo", level=2)
doc.add_paragraph(
    "El siguiente diagrama ilustra la separación física de los tres entornos obligatorios (Dispositivo de Datos, Dispositivo de Servicios y Dispositivos Clientes Móviles):"
)

diag_text = (
    "+-----------------------------------------------------------------------------------------+\n"
    "|                           DISPOSITIVO 1: SERVIDOR DE DATOS                              |\n"
    "|                      (Neon Cloud PostgreSQL / Servidor Dedicado)                        |\n"
    "|                                                                                         |\n"
    "|  +-----------------------------------------------------------------------------------+  |\n"
    "|  |   PostgreSQL 15+ Engine (Pooler SSL Port 5432)                                    |  |\n"
    "|  |   - Tablas: usuarios, categorias, farmacias, medicamentos, precios, historial     |  |\n"
    "|  |   - Nueva Tabla: device_tokens (FCM Push)                                         |  |\n"
    "|  |   - Vistas: vista_precios_actuales, vista_mejores_precios                         |  |\n"
    "|  |   - Indices: GIN Full-Text Search, Lat/Lng Proximidad, FKs                        |  |\n"
    "|  +-----------------------------------------------------------------------------------+  |\n"
    "+--------------------------------------------^--------------------------------------------+\n"
    "                                             | Conexión TCP SSL / Pool de Conexiones\n"
    "+--------------------------------------------v--------------------------------------------+\n"
    "|                         DISPOSITIVO 2: SERVIDOR BACKEND & GATEWAY                       |\n"
    "|                   (Host Linux/Windows Dedicado en Red LAN o Cloud Server)               |\n"
    "|                                                                                         |\n"
    "|  +-----------------------------------+     +-----------------------------------------+  |\n"
    "|  |   API Gateway (Express :8080)     |     |   Backend Core (Express + TS :3001)     |  |\n"
    "|  |   - JWT Validator Middleware      |---->|   - Controladores de Negocio & DTOs     |  |\n"
    "|  |   - Rate Limiter (Anti-DDoS)      |     |   - Motor Sugerencias (Strategy/Factory)|  |\n"
    "|  |   - Proxy inverso a microservicios|     |   - Modulo Asistente Gemini 2.5 Flash   |  |\n"
    "|  +-----------------------------------+     +-----------------------------------------+  |\n"
    "+--------------------------------------------^--------------------------------------------+\n"
    "                                             | API REST HTTPS (JSON Payload / JWT Bearer)\n"
    "+--------------------------------------------v--------------------------------------------+\n"
    "|                   DISPOSITIVOS 3, 4, 5...: SMARTPHONES DE USUARIOS Y EQUIPO             |\n"
    "|                              (App Nativa Compilada en Flutter)                          |\n"
    "|                                                                                         |\n"
    "|  +-----------------------------------------------------------------------------------+  |\n"
    "|  |   Capa de Presentacion: Flutter 3.24+ (Material 3 UI, Widgets, fl_chart, Map)     |  |\n"
    "|  |   Capa de Estado: Riverpod / BLoC State Notifiers                                 |  |\n"
    "|  |   Capa de Dominio: Casos de Uso (Buscar, Comparar, Comprar, Consultar IA)         |  |\n"
    "|  |   Capa de Datos: Repositorios + Dio HTTP Client + Interceptores                   |  |\n"
    "|  |   Almacenamiento Local: Hive (Caché Offline) + SecureStorage (JWT Keystore)       |  |\n"
    "|  |   Hardware Nativo: Geolocalización GPS + Notificaciones Push FCM                  |  |\n"
    "|  +-----------------------------------------------------------------------------------+  |\n"
    "+-----------------------------------------------------------------------------------------+"
)
add_code_block(doc, diag_text)

add_callout(doc, "Regla de Oro de Conectividad en Desarrollo Multidispositivo",
    "Cuando la base de datos y el backend se ejecutan en computadoras separadas y la app corre en un teléfono físico o emulador, "
    "NUNCA se debe usar 'localhost' ni '127.0.0.1' en la app Flutter. Se debe configurar la IP estática local del servidor "
    "(ej. http://192.168.1.50:8080) o utilizar túneles seguros con ngrok / Cloudflare Tunnels para permitir que los teléfonos "
    "accedan al Gateway sin bloqueos de firewall.", "warning")

doc.add_page_break()

# ==============================================================================
# SECCIÓN 3: INVENTARIO DE TECNOLOGÍAS Y DEPENDENCIAS
# ==============================================================================
add_header(doc, "3. Inventario de Tecnologías y Dependencias", level=1)

add_header(doc, "3.1 Matriz de Transición Tecnológica (Stack Web vs. Stack Móvil)", level=2)
doc.add_paragraph(
    "Para garantizar una migración sin fisuras, se ha diseñado una correspondencia biunívoca entre las herramientas "
    "del stack web actual y sus contrapartes en el ecosistema Flutter:"
)

tech_headers = ["Categoría", "Tecnología Web Actual", "Tecnología Móvil Destino", "Criterio Técnico de Elección"]
tech_data = [
    ["Framework Principal", "React 19.2.0 (SPA)", "Flutter 3.24+ (Dart 3.5+)", "Compilación nativa a código máquina AOT (ARM64), 60/120 fps constantes y un solo código base para Android e iOS."],
    ["Gestión de Estado", "useState + useEffect + Context API", "Flutter Riverpod 2.5+ / BLoC", "Inyección de dependencias reactiva, desacoplamiento estricto de UI y lógica, y testabilidad sin mocks complejos."],
    ["Enrutamiento", "React Router DOM 7.13.1", "GoRouter 14+", "Enrutamiento declarativo con soporte para Deep Linking nativo, paso de parámetros fuertemente tipados y guardias de autenticación."],
    ["Cliente HTTP", "fetch nativo + Axios 1.13.5", "Dio 5.4+", "Soporte nativo de interceptores (inyección de JWT, refresco automático de token, retry policies y control de timeouts móviles)."],
    ["Persistencia Local", "localStorage (Window API)", "Hive 2.2 + flutter_secure_storage", "Hive ofrece almacenamiento NoSQL ultrarrápido para catálogo offline; flutter_secure_storage cifra credenciales con Keystore/Keychain."],
    ["Mapas y Georreferencia", "Leaflet 1.9 + React-Leaflet", "flutter_map 6+ (OSM) / google_maps", "Renderizado fluido de capas OpenStreetMap sin costo de licencias o integración nativa con Google Maps SDK."],
    ["Visualización Gráfica", "Recharts 3.8.1 (SVG DOM)", "fl_chart 0.68+", "Gráficas interactivas nativas en Canvas para curvas de fluctuación de precios históricas tipo Keepa."],
    ["GPS y Localización", "Navigator Geolocation API", "geolocator 12+", "Acceso al hardware GPS nativo con manejo de permisos en segundo plano y cálculo de distancia geodésica."],
    ["Analítica de Uso", "react-ga4 3.0.1", "firebase_analytics 10+", "Seguimiento estándar de la industria móvil para eventos de usuario, pantallas vistas y embudos de conversión."],
    ["Notificaciones", "Inexistentes (Web Push limitado)", "firebase_messaging 14+ (FCM)", "Notificaciones push inmediatas ante caídas de precio de medicamentos guardados en favoritos o alertas del carrito."],
    ["Motor de Pruebas", "Vitest 4.0 + Testing Library", "flutter_test + integration_test", "Suite integral para pruebas unitarias de lógica, pruebas de widgets visuales y pruebas end-to-end automatizadas."]
]
create_table(doc, tech_headers, tech_data, [1.3, 1.8, 1.8, 1.9])

add_header(doc, "3.2 Especificación del pubspec.yaml del Proyecto Flutter", level=2)
doc.add_paragraph("A continuación se presenta el bloque de dependencias esenciales que debe incluir el archivo pubspec.yaml del frontend móvil:")

pubspec_code = (
    "name: farmalink_mobile\n"
    "description: Aplicación Móvil Oficial de Farmalink SAS en Flutter\n"
    "version: 1.0.0+1\n"
    "environment:\n"
    "  sdk: '>=3.5.0 <4.0.0'\n\n"
    "dependencies:\n"
    "  flutter:\n"
    "    sdk: flutter\n"
    "  flutter_riverpod: ^2.5.1      # State management reactivo\n"
    "  go_router: ^14.2.0            # Enrutamiento y Deep Linking\n"
    "  dio: ^5.4.3+1                 # Cliente HTTP con interceptores\n"
    "  flutter_secure_storage: ^9.2.2# Almacenamiento seguro de JWT\n"
    "  hive: ^2.2.3                  # Base de datos NoSQL local offline\n"
    "  hive_flutter: ^1.1.0\n"
    "  flutter_map: ^6.1.0           # Mapas OpenStreetMap interactivos\n"
    "  latlong2: ^0.9.1              # Manejo de coordenadas geodésicas\n"
    "  geolocator: ^12.0.2           # GPS nativo Android / iOS\n"
    "  fl_chart: ^0.68.0             # Gráficas históricas de precios\n"
    "  firebase_core: ^3.1.0         # Firebase Core SDK\n"
    "  firebase_messaging: ^15.0.1   # Notificaciones Push FCM\n"
    "  firebase_analytics: ^11.0.1   # Analítica de comportamiento\n"
    "  google_fonts: ^6.2.1          # Tipografía corporativa\n"
    "  intl: ^0.19.0                 # Formateo de moneda colombiana (COP) y fechas\n"
    "  cached_network_image: ^3.3.1  # Caché eficiente de fotos de medicamentos\n"
    "  flutter_dotenv: ^5.1.0        # Variables de entorno (.env)\n\n"
    "dev_dependencies:\n"
    "  flutter_test:\n"
    "    sdk: flutter\n"
    "  integration_test:\n"
    "    sdk: flutter\n"
    "  mocktail: ^1.0.4              # Mocking limpio para tests unitarios\n"
    "  flutter_lints: ^4.0.0         # Reglas oficiales de calidad Dart"
)
add_code_block(doc, pubspec_code)

doc.add_page_break()

# ==============================================================================
# SECCIÓN 4: JUSTIFICACIÓN DE METODOLOGÍA SCRUM
# ==============================================================================
add_header(doc, "4. Metodología de Trabajo: Justificación Técnica de SCRUM", level=1)

add_header(doc, "4.1 Evaluación Comparativa de Metodologías Ágiles", level=2)
doc.add_paragraph(
    "El equipo evaluó rigurosamente tres marcos de gestión de proyectos antes de seleccionar la metodología de ejecución. "
    "A continuación se presenta el análisis comparativo formal:"
)

scrum_comp_headers = ["Criterio de Evaluación", "SCRUM (Elegida)", "Kanban Puro", "Cascada (Waterfall)"]
scrum_comp_data = [
    ["Idoneidad para 5 Integrantes", "Óptima. El estándar de Scrum define equipos ideales entre 3 y 9 personas, facilitando comunicación total.", "Moderada. Puede provocar pérdida de enfoque global y dispersión de objetivos semanales.", "Inadecuada. Fomenta silos de trabajo y cuellos de botella secuenciales."],
    ["Gestión de Dependencias", "Excelente. Las dependencias entre Backend (API) y Frontend (Widgets) se planifican en cada Sprint.", "Débil. Al basarse en flujo continuo, una tarea móvil puede bloquearse indefinidamente esperando API.", "Pobre. Cualquier retraso en la fase previa bloquea todo el cronograma."],
    ["Entregables Funcionales", "Incrementos inspeccionables y ejecutables cada 2 semanas (APKs de prueba para QA).", "Entregas continuas pero sin una fecha de sincronización fija del release completo.", "Un solo entregable masivo al final del proyecto (altísimo riesgo de desalineación)."],
    ["Visibilidad y Control", "Máxima visibilidad diaria con Daily Standup de 15 minutos y métricas de velocidad de Sprint.", "Buena visibilidad visual de tarjetas, pero carece de compromisos de tiempo cerrados.", "Baja visibilidad operativa real hasta las fases tardías de pruebas."],
    ["Adaptabilidad a Cambios", "Alta. Permite reajustar prioridades del Product Backlog al inicio de cada nuevo Sprint.", "Muy alta, pero propensa a cambio excesivo de alcance sin control de release.", "Nula. Modificar especificaciones requiere procesos burocráticos de cambio de alcance."]
]
create_table(doc, scrum_comp_headers, scrum_comp_data, [1.5, 1.8, 1.8, 1.7])

add_callout(doc, "Conclusión Metodológica Oficial",
    "Se dictamina que SCRUM es la metodología más factible, eficiente y profesional para este proyecto. Proporciona la estructura "
    "necesaria para coordinar a 5 ingenieros con roles diferenciados, garantiza la entrega de versiones móviles operativas cada 14 días "
    "y asegura que los riesgos de integración multidispositivo sean detectados y resueltos en etapas tempranas.", "success")

add_header(doc, "4.2 Configuración del Ciclo SCRUM para Farmalink Mobile", level=2)
add_bullet(doc, "Duración de los Sprints", "Sprints de dos (2) semanas (10 días laborables). Cadencia fija de inicio en lunes y cierre en viernes.")
add_bullet(doc, "Sprint Planning (Lunes 08:00 AM - 1.5 horas)", "El PO presenta las historias de usuario priorizadas; el equipo técnico desglosa tareas, estima puntos de historia (Planning Poker) y sella el Sprint Backlog.")
add_bullet(doc, "Daily Standup (Lunes a Viernes 08:30 AM - 15 minutos)", "Reunión síncrona enfocada en tres preguntas: ¿Qué logré ayer? ¿Qué haré hoy? ¿Qué impedimentos técnicos bloquean mi avance?")
add_bullet(doc, "Sprint Review & Demo (Viernes semana 2 - 1 hora)", "Demostración en vivo de la APK ejecutándose en dispositivos reales frente a los criterios de aceptación.")
add_bullet(doc, "Sprint Retrospective (Viernes semana 2 - 45 minutos)", "Inspección y adaptación del proceso de trabajo: qué funcionó, qué falló y un plan de acción concreto para el siguiente Sprint.")

add_header(doc, "4.3 Criterios de Aceptación: DoR y DoD", level=2)
doc.add_paragraph(
    "Para erradicar la ambigüedad y garantizar calidad industrial, se establecen los siguientes acuerdos de equipo:"
)
add_bullet(doc, "Definition of Ready (DoR - Criterio de Entrada)", 
           "Una historia de usuario solo entra a un Sprint si: cuenta con descripción en formato 'Como... Quiero... Para...', "
           "criterios de aceptación verificables en formato Gherkin (Dado-Cuando-Entonces), diseño UI en mockup validado, "
           "endpoints del backend especificados con su contrato JSON y una estimación acordada por el equipo.")
add_bullet(doc, "Definition of Done (DoD - Criterio de Salida)", 
           "Una historia de usuario se considera terminada (Done) solo si: el código cumple con las reglas del linter de Dart sin advertencias, "
           "los tests unitarios y de widgets pasan exitosamente en el pipeline CI/CD, ha sido revisada y aprobada mediante Pull Request (PR) "
           "por al menos otro desarrollador, ha sido desplegada en APK de prueba y validada por el Product Owner en un dispositivo real.")

doc.add_page_break()

# ==============================================================================
# SECCIÓN 5: DISTRIBUCIÓN EQUITATIVA DE ROLES Y RESPONSABILIDADES
# ==============================================================================
add_header(doc, "5. Distribución Equitativa de Responsabilidades y Asignación de Roles", level=1)

doc.add_paragraph(
    "En un equipo ágil de 5 integrantes, la distribución de responsabilidades debe evitar la sobrecarga y el aislamiento. "
    "El Product Owner y el Scrum Master asumen compromisos técnicos complementarios acordes a su perfil, logrando un balance "
    "perfecto de 20% de carga operativa por integrante:"
)

roles_headers = ["Integrante", "Rol Principal SCRUM", "Rol Técnico / Especialidad", "Responsabilidades Clave", "Carga Estimada"]
roles_data = [
    ["Integrante 1", "Product Owner (PO)", "Functional QA & UX Validator", 
     "• Gestión del Product Backlog y definición de valor de negocio.\n"
     "• Redacción de criterios de aceptación funcionales.\n"
     "• Aprobación formal de historias de usuario en cada Sprint Demo.\n"
     "• Pruebas funcionales de usuario final y validación de flujos de negocio.\n"
     "• Interlocución con stakeholders y farmacias aliadas.", "20% (Balanceado)"],
    
    ["Integrante 2", "Scrum Master (SM)", "Backend & DevOps Engineer", 
     "• Facilitación de ceremonias ágiles y eliminación de impedimentos.\n"
     "• Mantenimiento y adaptación del API Gateway y Backend Core.\n"
     "• Configuración de conectividad remota a PostgreSQL y túneles seguros.\n"
     "• Automatización de pipelines CI/CD en GitHub Actions para build móvil.\n"
     "• Monitoreo de logs y métricas de salud del servidor (APIs).", "20% (Balanceado)"],
    
    ["Integrante 3", "Developer 1", "Mobile Lead Architect & Core Services", 
     "• Arquitectura base del proyecto Flutter (Clean Architecture).\n"
     "• Configuración del motor de inyección y estado (Riverpod).\n"
     "• Implementación de capa de red (Dio + Interceptors de autenticación JWT).\n"
     "• Módulo de persistencia segura (flutter_secure_storage) y sesión.\n"
     "• Conexión y streaming con el asistente de IA Google Gemini.", "20% (Balanceado)"],
    
    ["Integrante 4", "Developer 2", "Mobile UI/UX & Views Specialist", 
     "• Diseño de componentes visuales bajo Material Design 3.\n"
     "• Implementación de pantallas Home, Búsqueda, Filtros y Categorías.\n"
     "• Desarrollo de vistas de Detalle de Medicamento y Comparador de Precios.\n"
     "• Integración de gráficos interactivos de fluctuación con fl_chart.\n"
     "• Módulo de Carrito de compras y flujo de Checkout móvil.", "20% (Balanceado)"],
    
    ["Integrante 5", "Developer 3", "Mobile Features & QA Test Automator", 
     "• Módulo de mapas nativos con geolocalización GPS (flutter_map).\n"
     "• Implementación de base de datos local y caché offline con Hive.\n"
     "• Configuración de notificaciones push (Firebase Cloud Messaging).\n"
     "• Desarrollo de suite automatizada de pruebas unitarias y de widgets.\n"
     "• Gestión y testing de compatibilidad en múltiples resoluciones Android/iOS.", "20% (Balanceado)"]
]
create_table(doc, roles_headers, roles_data, [1.0, 1.2, 1.4, 2.4, 0.8])

add_header(doc, "5.1 Matriz RACI de Responsabilidades por Módulo", level=2)
doc.add_paragraph("A continuación se define la matriz RACI (Responsible, Accountable, Consulted, Informed) para cada hito del proyecto:")

raci_headers = ["Módulo / Entregable", "PO (Int. 1)", "SM/Back (Int. 2)", "Dev Lead (Int. 3)", "Dev UI (Int. 4)", "Dev QA (Int. 5)"]
raci_data = [
    ["Definición de Historias & Backlog", "A (Accountable)", "C (Consulted)", "C (Consulted)", "C (Consulted)", "C (Consulted)"],
    ["Configuración de Servidores & BD", "I (Informed)", "A / R (Resp.)", "C (Consulted)", "I (Informed)", "I (Informed)"],
    ["Arquitectura Flutter & Networking", "I (Informed)", "C (Consulted)", "A / R (Resp.)", "R (Support)", "C (Consulted)"],
    ["Diseño de Interfaces & Widgets", "C (Consulted)", "I (Informed)", "C (Consulted)", "A / R (Resp.)", "I (Informed)"],
    ["Mapas & Geolocalización GPS", "I (Informed)", "I (Informed)", "C (Consulted)", "C (Consulted)", "A / R (Resp.)"],
    ["Integración Asistente IA (Gemini)", "C (Consulted)", "R (API Gateway)", "A / R (Resp.)", "R (Chat UI)", "C (Consulted)"],
    ["Pruebas Automatizadas Unit/Widget", "I (Informed)", "C (CI Pipeline)", "C (Consulted)", "C (Consulted)", "A / R (Resp.)"],
    ["Validación Funcional & Release", "A / R (Resp.)", "R (Deploy)", "C (Consulted)", "C (Consulted)", "R (Smoke Test)"]
]
create_table(doc, raci_headers, raci_data, [1.8, 1.0, 1.0, 1.0, 1.0, 1.0])

doc.add_page_break()

# ==============================================================================
# SECCIÓN 6: REQUISITOS Y CONFIGURACIÓN POR DISPOSITIVO
# ==============================================================================
add_header(doc, "6. Requisitos de Hardware, Software y Configuración por Dispositivo", level=1)

doc.add_paragraph(
    "Para erradicar definitivamente el síndrome de 'en mi máquina sí funciona', se define una línea base de hardware, "
    "software, herramientas y configuración de red que cada integrante debe poseer en su estación de trabajo:"
)

add_header(doc, "6.1 Matriz de Requisitos Técnicos por Rol", level=2)
hw_headers = ["Componente", "Product Owner (Int. 1)", "Scrum Master / Backend (Int. 2)", "Developers 1, 2 y 3 (Int. 3, 4, 5)"]
hw_data = [
    ["Sistema Operativo", "Windows 11 / macOS / Linux.", "Windows 11 / Linux Ubuntu 22+ / macOS.", "Windows 11 (con WSL2) o macOS Sonoma (para builds iOS)."],
    ["Procesador & RAM", "Core i5 / Ryzen 5, 8 GB RAM mínimo.", "Core i7 / Ryzen 7, 16 GB RAM mínimo.", "Core i7 / Ryzen 7 / Apple Silicon M1+, 16 GB RAM (32 GB recomendado)."],
    ["Almacenamiento", "256 GB SSD (50 GB libres).", "512 GB SSD (100 GB libres).", "512 GB SSD NVMe (mínimo 120 GB libres para SDKs y emuladores)."],
    ["Flutter SDK", "No requerido.", "Opcional (para pruebas de endpoints).", "Flutter 3.24+ Stable Channel (Dart 3.5+) obligatorio."],
    ["IDE Principal", "Navegador Web + Jira/Trello + Postman.", "VS Code / WebStorm + DBeaver.", "VS Code (con extensiones oficiales Flutter/Dart) o Android Studio."],
    ["Android Toolchain", "No requerido.", "Opcional.", "Android Studio Koala/Ladybug, Android SDK 34, JDK 17, Build Tools 34.0.0."],
    ["Node.js & BD Tools", "No requerido.", "Node.js v20.x LTS, npm 10+, DBeaver, Docker Desktop.", "Node.js v20.x (para pruebas locales de endpoints de backend)."],
    ["Dispositivo de Prueba", "Smartphone Android 11+ o iOS 15+ físico.", "Smartphone Android físico para pruebas de red.", "Smartphone físico con Modo Depuración USB (recomendado) + Emulador AVD Pixel 7."]
]
create_table(doc, hw_headers, hw_data, [1.4, 1.8, 1.8, 1.8])

add_header(doc, "6.2 Guía Paso a Paso de Configuración del Entorno de Desarrollo", level=2)
doc.add_paragraph("Cada desarrollador debe ejecutar y verificar rigurosamente el siguiente procedimiento antes de iniciar el Sprint 0:")

setup_steps = (
    "# 1. Instalar Flutter SDK y configurar variable PATH\n"
    "git clone https://github.com/flutter/flutter.git -b stable C:\\src\\flutter\n"
    "# Agregar C:\\src\\flutter\\bin a las Variables de Entorno del Sistema\n\n"
    "# 2. Instalar Java Development Kit (JDK 17 LTS)\n"
    "# Verificar que JAVA_HOME apunte al JDK 17 (evitar JDK 21+ por incompatibilidades con Gradle 7/8)\n"
    "java -version\n\n"
    "# 3. Instalar Android Studio y componentes SDK\n"
    "# Desde Android Studio SDK Manager instalar:\n"
    "# - Android SDK Platform 34 (UpsideDownCake)\n"
    "# - Android SDK Command-line Tools (latest)\n"
    "# - Android SDK Build-Tools 34.0.0\n"
    "# - Android Emulator\n\n"
    "# 4. Aceptar licencias de Android en terminal\n"
    "flutter doctor --android-licenses\n\n"
    "# 5. Verificar diagnóstico general del entorno\n"
    "flutter doctor -v\n"
    "# TODOS los checks deben estar en verde [✓] excepto Xcode si se está en Windows"
)
add_code_block(doc, setup_steps)

add_header(doc, "6.3 Configuración de Red para Pruebas Multidispositivo", level=2)
doc.add_paragraph(
    "Cuando la base de datos corre en un equipo y el backend en otro, los smartphones conectados por Wi-Fi necesitan alcanzar "
    "el API Gateway. Se estandarizan tres estrategias oficiales de conexión:"
)
add_bullet(doc, "Estrategia A (Red Local Wi-Fi con IP Fija)", 
           "El Integrante 2 (Backend) asigna una IP local estática a su computadora (ej. 192.168.1.150). En el archivo .env "
           "de la app Flutter se configura: API_BASE_URL=http://192.168.1.150:8080. Se debe abrir el puerto 8080 en el Firewall de Windows.")
add_bullet(doc, "Estrategia B (Túnel Seguro con ngrok - Recomendada para Trabajo Remoto)", 
           "Si los integrantes trabajan desde ubicaciones distintas, el Integrante 2 ejecuta: 'ngrok http 8080'. Esto genera una URL pública HTTPS "
           "(ej. https://farmalink-dev.ngrok-free.app) que se coloca en el .env de todos los desarrolladores sin importar su red.")
add_bullet(doc, "Estrategia C (Servidor Cloud Staging en Render)", 
           "El backend y gateway se despliegan en Render.com conectado a Neon PostgreSQL, proveyendo una URL permanente "
           "(ej. https://api-gateway.farmalink.onrender.com).")

doc.add_page_break()

# ==============================================================================
# SECCIÓN 7: ESTRATEGIA DE MIGRACIÓN POR FASES
# ==============================================================================
add_header(doc, "7. Estrategia de Migración por Fases y Desglose de Sprints", level=1)

doc.add_paragraph(
    "El proyecto se estructura en un ciclo de diez (10) Sprints distribuidos en seis (6) fases evolutivas, "
    "totalizando una duración estimada de veinte (20) semanas de desarrollo industrial:"
)

phases_headers = ["Fase", "Sprint", "Denominación del Hito", "Objetivos y Entregables Clave", "Criterio de Cierre Exitoso"]
phases_data = [
    ["Fase 0", "Sprint 0\n(Sem. 1-2)", "Setup, Tooling & Arquitectura Base",
     "• Configuración del entorno Flutter en las 5 máquinas.\n"
     "• Repositorio Git con ramas protegidas (main, develop).\n"
     "• Pipeline CI/CD básico en GitHub Actions.\n"
     "• Configuración de proyecto Firebase (Auth, FCM, Analytics).\n"
     "• Creación del esqueleto Clean Architecture en Flutter.", "flutter doctor validado en las 5 máquinas; repo compila y pasa CI."],
    
    ["Fase 1", "Sprint 1-2\n(Sem. 3-6)", "Core: Auth, Seguridad y Home",
     "• Servicio HTTP Dio con interceptores de Token JWT.\n"
     "• Pantallas de Login y Registro con validación de formularios.\n"
     "• Almacenamiento seguro en flutter_secure_storage.\n"
     "• Guardias de navegación con GoRouter.\n"
     "• Pantalla Home (Hero animado, Features y Slider de farmacias).", "Usuario puede registrarse, loguearse y ver Home con token persistido."],
    
    ["Fase 2", "Sprint 3-4\n(Sem. 7-10)", "Búsqueda, Catálogo y Precios",
     "• Widget SearchAutocomplete con debounce reactivo (300 ms).\n"
     "• Pantalla de Búsqueda avanzada con filtros dinámicos.\n"
     "• Catálogo interactivo de medicamentos por Categorías.\n"
     "• Vista de Detalle de Medicamento con comparador entre farmacias.\n"
     "• Gráfica interactiva de fluctuación histórica con fl_chart.", "Búsqueda por voz/texto en tiempo real y gráfica Keepa interactiva."],
    
    ["Fase 3", "Sprint 5-6\n(Sem. 11-14)", "Geolocalización, Mapas y Carrito",
     "• Mapa nativo de farmacias con flutter_map (OpenStreetMap).\n"
     "• Obtención de posición GPS en tiempo real con geolocator.\n"
     "• Cálculo y listado de farmacias cercanas por radio geodésico.\n"
     "• Carrito de compras local respaldado por Hive NoSQL.\n"
     "• Flujo completo de Checkout móvil simulado.", "Usuario visualiza farmacias en mapa en radio de 5 km y arma pedido en carrito."],
    
    ["Fase 4", "Sprint 7-8\n(Sem. 15-18)", "Dashboard, Admin y Asistente IA",
     "• Dashboard gerencial con métricas y gráficos analíticos.\n"
     "• Panel de administración móvil (CRUD de medicamentos y precios).\n"
     "• Asistente conversacional inteligente con Google Gemini 2.5 Flash.\n"
     "• Policy guard sanitario contra automedicación en la app.\n"
     "• Pantallas Mi Cuenta, Quiénes Somos y FAQ.", "Chat con Gemini funcionando con acciones automáticas de navegación en la app."],
    
    ["Fase 5", "Sprint 9-10\n(Sem. 19-20)", "QA Integral, Optimización y Release",
     "• Pruebas de regresión, estrés de red y modo offline.\n"
     "• Cobertura de pruebas unitarias superior al 80% en core.\n"
     "• Optimización de peso de APK (Tree shaking de fuentes y Proguard).\n"
     "• Generación de App Bundle (AAB) firmado para Google Play.\n"
     "• Despliegue en Firebase App Distribution para beta testers.", "APK Release firmada sin crashes y aprobada por el Product Owner."]
]
create_table(doc, phases_headers, phases_data, [0.8, 1.0, 1.3, 2.3, 1.4])

doc.add_page_break()

# ==============================================================================
# SECCIÓN 8: MIGRACIÓN DE BASE DE DATOS MULTIDISPOSITIVO
# ==============================================================================
add_header(doc, "8. Plan de Migración y Operación de la Base de Datos Multidispositivo", level=1)

add_header(doc, "8.1 Estrategia de Preservación de Datos Relacionales", level=2)
doc.add_paragraph(
    "Una de las mayores ventajas estratégicas de este plan es que NO se requiere una migración destructiva de datos. "
    "La base de datos PostgreSQL alojada en Neon Cloud (o en un servidor host dedicado) ya cuenta con una estructura relacional "
    "altamente normalizada derivada de la migración previa desde MongoDB. Las tablas existentes (usuarios, categorias, farmacias, "
    "medicamentos, precios, historial_precios) se conservan intactas."
)

add_header(doc, "8.2 Modificaciones al Esquema para Soporte Móvil", level=2)
doc.add_paragraph(
    "Para soportar funcionalidades nativas móviles como notificaciones push en segundo plano y perfiles avanzados, "
    "se debe ejecutar el siguiente script DDL en la base de datos:"
)

sql_migration = (
    "-- =====================================================\n"
    "-- MIGRACIÓN POSTGRESQL: SOPORTE NATIVO FARMALINK MOBILE\n"
    "-- =====================================================\n\n"
    "-- 1. Tabla para registrar dispositivos y tokens FCM\n"
    "CREATE TABLE IF NOT EXISTS device_tokens (\n"
    "    id BIGSERIAL PRIMARY KEY,\n"
    "    user_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,\n"
    "    token VARCHAR(500) NOT NULL UNIQUE,\n"
    "    platform VARCHAR(20) NOT NULL CHECK (platform IN ('android', 'ios', 'web')),\n"
    "    device_model VARCHAR(100),\n"
    "    os_version VARCHAR(50),\n"
    "    is_active BOOLEAN NOT NULL DEFAULT true,\n"
    "    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP\n"
    ");\n\n"
    "-- Indice para despacho masivo de notificaciones por usuario\n"
    "CREATE INDEX IF NOT EXISTS idx_device_tokens_user ON device_tokens(user_id);\n\n"
    "-- 2. Extensiones para busqueda textual optimizada\n"
    "CREATE EXTENSION IF NOT EXISTS pg_trgm;\n\n"
    "-- Indice GIN Trigram para busqueda difusa instantanea en nombres de medicamentos\n"
    "CREATE INDEX IF NOT EXISTS idx_medicamentos_trgm ON medicamentos USING gin (name gin_trgm_ops);\n\n"
    "-- 3. Campo de avatar y preferencias en usuarios\n"
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);\n"
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS push_notifications_enabled BOOLEAN DEFAULT true;\n"
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS dark_mode_preferred BOOLEAN DEFAULT false;"
)
add_code_block(doc, sql_migration)

add_header(doc, "8.3 Arquitectura de Conexión y Pooling Seguro", level=2)
doc.add_paragraph(
    "La base de datos no debe exponerse públicamente sin cifrado. Se exige el uso de SSL (sslmode=require) con el pooler de Neon "
    "o conexiones autenticadas por contraseña fuerte con límite de conexiones concurrentes para evitar la saturación del servidor."
)

doc.add_page_break()

# ==============================================================================
# SECCIÓN 9: MIGRACIÓN DE BACKEND Y API GATEWAY
# ==============================================================================
add_header(doc, "9. Migración y Adaptación del Backend Core y API Gateway", level=1)

add_header(doc, "9.1 Ajustes Obligatorios en el Backend Actual", level=2)
doc.add_paragraph(
    "Aunque el backend conserva su lógica de negocio central, la transición hacia clientes móviles exige adaptaciones obligatorias:"
)
add_bullet(doc, "Apertura y Configuración de CORS Móvil", 
           "Actualmente CORS está configurado para admitir dominios web específicos. Las aplicaciones móviles nativas envían un origen 'null' "
           "o cabeceras de cliente personalizadas. Se debe configurar cors() en packages/backend/server.ts y packages/gateway/index.js "
           "para permitir peticiones originadas desde clientes móviles sin restricción indebida de navegador.")
add_bullet(doc, "Resolución Definitiva del Bypass de Sugerencias", 
           "El API Gateway actual posee la ruta '/api/sugerencias' pero el frontend web la saltaba. En Flutter, se consumirá exclusivamente "
           "el Gateway en el puerto 8080, asegurando que todas las peticiones queden registradas en los logs analíticos.")
add_bullet(doc, "Implementación de Rate Limiting Adaptativo", 
           "Las aplicaciones móviles pueden reconectarse repetidamente ante pérdidas de señal celular, generando tormentas de peticiones. "
           "Se debe instalar express-rate-limit en el Gateway permitiendo hasta 120 peticiones por minuto por IP.")
add_bullet(doc, "Serialización JSON Eficiente y Compresión Gzip", 
           "Se agregará el middleware de compresión (compression) en Express para reducir el tamaño de las respuestas de catálogo en un 60%, "
           "optimizando el consumo del plan de datos del usuario.")

add_header(doc, "9.2 Nuevo Endpoint de Registro de Tokens Push", level=2)
doc.add_paragraph("El API Gateway incorporará el enrutamiento para gestionar tokens FCM de la aplicación Flutter:")

endpoint_code = (
    "// packages/gateway/index.js (O extension en TypeScript)\n"
    "app.post('/api/device-tokens', validateJWT, async (req, res) => {\n"
    "  try {\n"
    "    const { token, platform, deviceModel, osVersion } = req.body;\n"
    "    const userId = req.user.id;\n"
    "    \n"
    "    await db.query(`\n"
    "      INSERT INTO device_tokens (user_id, token, platform, device_model, os_version, updated_at)\n"
    "      VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)\n"
    "      ON CONFLICT (token) DO UPDATE \n"
    "      SET updated_at = CURRENT_TIMESTAMP, is_active = true;\n"
    "    `, [userId, token, platform, deviceModel, osVersion]);\n"
    "    \n"
    "    res.json({ success: true, message: 'Dispositivo registrado para notificaciones' });\n"
    "  } catch (err) {\n"
    "    res.status(500).json({ error: 'Error al registrar token de dispositivo' });\n"
    "  }\n"
    "});"
)
add_code_block(doc, endpoint_code)

doc.add_page_break()

# ==============================================================================
# SECCIÓN 10: DESARROLLO DEL FRONTEND MÓVIL EN FLUTTER
# ==============================================================================
add_header(doc, "10. Desarrollo del Frontend Móvil en Flutter", level=1)

add_header(doc, "10.1 Arquitectura de Software: Clean Architecture Feature-First", level=2)
doc.add_paragraph(
    "El código del frontend móvil se estructurará siguiendo los principios de Clean Architecture agrupada por funcionalidades "
    "(Feature-First), garantizando alta cohesión, bajo acoplamiento y facilidad de testing:"
)

folder_struct = (
    "lib/\n"
    "├── core/                        # Utilidades y configuración global transversal\n"
    "│   ├── config/                  # Constantes de entorno, themes Material 3\n"
    "│   ├── errors/                  # Manejo centralizado de fallos y excepciones\n"
    "│   ├── network/                 # Cliente Dio, interceptor JWT, network info\n"
    "│   └── storage/                 # SecureStorage y adaptadores Hive\n"
    "├── features/                    # Módulos funcionales desacoplados\n"
    "│   ├── auth/                    # Login, Registro, Splash screen\n"
    "│   │   ├── data/                # DTOs, AuthRemoteDataSource, AuthRepositoryImpl\n"
    "│   │   ├── domain/              # Modelos de usuario, casos de uso (LoginUseCase)\n"
    "│   │   └── presentation/        # Riverpod Providers, LoginScreen, RegisterScreen\n"
    "│   ├── home/                    # Dashboard inicial, banners y sliders\n"
    "│   ├── search/                  # Búsqueda fuzzy, autocompletado y filtros\n"
    "│   ├── products/                # Detalle de medicamento, comparador de precios\n"
    "│   ├── pharmacies/              # Mapa OSM, geolocalización de farmacias cercanas\n"
    "│   ├── cart/                    # Carrito persistente en Hive y Checkout\n"
    "│   ├── ai_assistant/            # Chat conversacional con Gemini 2.5 Flash\n"
    "│   └── admin/                   # Módulos de administración para farmacéuticos y admin\n"
    "├── shared/                      # Widgets reutilizables (Botones, SnackBar, AppBar)\n"
    "├── app.dart                     # Configuración de MaterialApp y GoRouter\n"
    "└── main.dart                    # Punto de entrada de la aplicación móvil"
)
add_code_block(doc, folder_struct)

add_header(doc, "10.2 Cliente HTTP Robusto con Dio y Manejo de JWT", level=2)
doc.add_paragraph(
    "Para asegurar que la app maneje pérdidas de señal y tokens vencidos sin cerrar la sesión abruptamente, "
    "se implementa un interceptor especializado en Dio:"
)

dio_interceptor = (
    "class AuthInterceptor extends Interceptor {\n"
    "  final FlutterSecureStorage _storage;\n"
    "  AuthInterceptor(this._storage);\n\n"
    "  @override\n"
    "  Future<void> onRequest(RequestOptions options, RequestInterceptorHandler handler) async {\n"
    "    final token = await _storage.read(key: 'jwt_token');\n"
    "    if (token != null) {\n"
    "      options.headers['Authorization'] = 'Bearer $token';\n"
    "    }\n"
    "    options.headers['Content-Type'] = 'application/json';\n"
    "    return handler.next(options);\n"
    "  }\n\n"
    "  @override\n"
    "  void onError(DioException err, ErrorInterceptorHandler handler) {\n"
    "    if (err.response?.statusCode == 401 || err.response?.statusCode == 403) {\n"
    "      // Notificar al AuthProvider para redirigir a pantalla de Login\n"
    "    }\n"
    "    return handler.next(err);\n"
    "  }\n"
    "}"
)
add_code_block(doc, dio_interceptor)

add_header(doc, "10.3 Integración del Asistente Inteligente Gemini IA", level=2)
doc.add_paragraph(
    "El asistente de IA se adaptará a la interfaz móvil como un Floating Action Button (FAB) accesible en todas las vistas, "
    "desplegando una hoja inferior modal (Modal BottomSheet) o pantalla de chat estilo mensajería instantánea. "
    "Se mantienen las salvaguardas sanitarias (PolicyGuard) contra automedicación que ya operan en el backend."
)

doc.add_page_break()

# ==============================================================================
# SECCIÓN 11: PRUEBAS QA Y VALIDACIÓN
# ==============================================================================
add_header(doc, "11. Estrategia de Pruebas QA, Automatización y Validación de Calidad", level=1)

add_header(doc, "11.1 Pirámide de Pruebas Móvil", level=2)
doc.add_paragraph(
    "La calidad del software se fundamenta en la clásica pirámide de automatización adaptada al ecosistema Flutter:"
)

qa_headers = ["Nivel de Prueba", "Herramientas Utilizadas", "Alcance de Validación", "Meta de Cobertura"]
qa_data = [
    ["Pruebas Unitarias (Unit Tests)", "flutter_test + mocktail", "Lógica de negocio pura, cálculo de distancias geodésicas, algoritmos de precios y parseo de DTOs JSON.", "≥ 80% en domain y data."],
    ["Pruebas de Widgets (Widget Tests)", "flutter_test", "Renderizado correcto de widgets, botones, inputs con debounce, visualización de errores y comportamientos táctiles.", "≥ 70% en componentes clave."],
    ["Pruebas de Integración (E2E)", "integration_test", "Flujos completos automatizados: Registro -> Login -> Buscar Medicamento -> Ver Comparador -> Añadir al Carrito.", "100% de los 4 flujos críticos."],
    ["Pruebas de Red y Offline", "Dio Interceptors mockeados", "Comportamiento ante desconexión de Wi-Fi, latencias de 2G/3G y recuperación transparente al reconectar.", "Validación manual y simulada."],
    ["Compatibilidad Multi-Dispositivo", "Firebase Test Lab + Dispositivos Físicos", "Verificación visual en pantallas pequeñas (5.5\"), estándar (6.5\") y tablets (10\"), modo claro/oscuro.", "Android 8.0 a 15, iOS 14+."]
]
create_table(doc, qa_headers, qa_data, [1.5, 1.6, 2.3, 1.4])

add_header(doc, "11.2 Ejemplo de Prueba Unitaria Automatizada (Dart)", level=2)
test_code = (
    "void main() {\n"
    "  group('MedicamentoRepository Tests', () {\n"
    "    late MockDio mockDio;\n"
    "    late MedicamentoRepositoryImpl repository;\n\n"
    "    setUp(() {\n"
    "      mockDio = MockDio();\n"
    "      repository = MedicamentoRepositoryImpl(dio: mockDio);\n"
    "    });\n\n"
    "    test('debe retornar lista de sugerencias cuando la respuesta API es 200', () async {\n"
    "      // Arrange\n"
    "      when(() => mockDio.get(any(), queryParameters: any(named: 'queryParameters')))\n"
    "          .thenAnswer((_) async => Response(\n"
    "                data: {'success': true, 'sugerencias': [{'id': 1, 'name': 'Acetaminofen'}]},\n"
    "                statusCode: 200,\n"
    "                requestOptions: RequestOptions(path: '/api/sugerencias'),\n"
    "              ));\n"
    "      // Act\n"
    "      final result = await repository.obtenerSugerencias('aceta');\n"
    "      // Assert\n"
    "      expect(result.length, 1);\n"
    "      expect(result.first.name, 'Acetaminofen');\n"
    "    });\n"
    "  });\n"
    "}"
)
add_code_block(doc, test_code)

doc.add_page_break()

# ==============================================================================
# SECCIÓN 12: INFRAESTRUCTURA, CLOUD Y DEVOPS
# ==============================================================================
add_header(doc, "12. Infraestructura, Redes, Cloud y Estrategia DevOps Móvil", level=1)

add_header(doc, "12.1 Flujo de Integración y Despliegue Continuo (CI/CD)", level=2)
doc.add_paragraph(
    "Para garantizar que cada cambio en el repositorio sea validado automáticamente, se implementa un pipeline "
    "de integración continua en GitHub Actions (.github/workflows/flutter_ci.yml):"
)

ci_flow = (
    "name: Farmalink Mobile CI/CD Pipeline\n"
    "on:\n"
    "  push:\n"
    "    branches: [ main, develop ]\n"
    "  pull_request:\n"
    "    branches: [ main, develop ]\n\n"
    "jobs:\n"
    "  analyze-and-test:\n"
    "    runs-on: ubuntu-latest\n"
    "    steps:\n"
    "      - uses: actions/checkout@v4\n"
    "      - uses: subosito/flutter-action@v2\n"
    "        with:\n"
    "          flutter-version: '3.24.x'\n"
    "          channel: 'stable'\n"
    "      - name: Instalar dependencias\n"
    "        run: flutter pub get\n"
    "      - name: Analisis estatico de codigo (Linter)\n"
    "        run: flutter analyze\n"
    "      - name: Ejecutar pruebas unitarias\n"
    "        run: flutter test --coverage\n"
    "      - name: Compilar APK de depuracion\n"
    "        run: flutter build apk --debug\n"
    "      - name: Subir artefacto APK a GitHub Releases\n"
    "        uses: actions/upload-artifact@v4\n"
    "        with:\n"
    "          name: farmalink-debug-apk\n"
    "          path: build/app/outputs/flutter-apk/app-debug.apk"
)
add_code_block(doc, ci_flow)

add_header(doc, "12.2 Distribución de Versiones de Prueba (Beta Testing)", level=2)
doc.add_paragraph(
    "Para que el Product Owner y los integrantes del equipo puedan instalar y validar las versiones de la aplicación "
    "directamente en sus teléfonos móviles sin cables, se utilizará Firebase App Distribution. Con cada merge en la rama develop, "
    "el pipeline generará automáticamente una nueva versión descargable para los probadores autorizados."
)

doc.add_page_break()

# ==============================================================================
# SECCIÓN 13: GESTIÓN DE RIESGOS Y CONTINGENCIAS
# ==============================================================================
add_header(doc, "13. Matriz de Gestión de Riesgos, Contingencias y Mitigación", level=1)

doc.add_paragraph(
    "Todo proyecto de migración tecnológica conlleva incertidumbres inherentes. Se ha formulado una matriz de riesgos preventiva "
    "para blindar la continuidad del proyecto:"
)

risk_headers = ["ID", "Riesgo Identificado", "Impacto", "Probabilidad", "Estrategia de Mitigación Activa", "Plan de Contingencia"]
risk_data = [
    ["R-01", "Falla de conectividad Wi-Fi local entre teléfono y servidor backend.", "Alto", "Media", 
     "Estandarizar el uso de túneles ngrok / Cloudflare con URLs HTTPS públicas en el archivo .env.", 
     "Conmutar temporalmente a la API de staging desplegada en Render."],
    ["R-02", "Incompatibilidad de emuladores con procesadores AMD / Intel HAXM.", "Medio", "Alta", 
     "Configurar teléfonos físicos Android con depuración USB como dispositivo de desarrollo principal.", 
     "Usar emulador web de Flutter temporalmente para maquetación rápida."],
    ["R-03", "Agotamiento de cuota de API gratuita de Gemini 2.5 Flash.", "Medio", "Baja", 
     "Implementar respuestas mock y limitador de llamadas en desarrollo local (AI_USE_GEMINI=false).", 
     "Habilitar fallback a respuestas heurísticas basadas en reglas de regex."],
    ["R-04", "Problemas de CORS al realizar llamadas desde emulador/dispositivo.", "Alto", "Media", 
     "Configurar cors({ origin: '*' }) en el API Gateway durante la fase de desarrollo.", 
     "Utilizar reverse proxy local o cabeceras Bearer sin validación estricta de origen."],
    ["R-05", "Sobrecarga de trabajo en desarrolladores por cambio de alcance.", "Alto", "Baja", 
     "Estricto apego a la Definition of Ready (DoR) y control férreo del alcance por parte del Scrum Master.", 
     "Reprogramar historias secundarias para el siguiente Sprint en el Sprint Planning."]
]
create_table(doc, risk_headers, risk_data, [0.6, 1.8, 0.8, 0.8, 1.5, 1.3])

doc.add_page_break()

# ==============================================================================
# SECCIÓN 14: CRONOGRAMA, RESPONSABLES Y CRITERIOS DE ACEPTACIÓN
# ==============================================================================
add_header(doc, "14. Cronograma Detallado, Criterios de Aceptación y DoD", level=1)

add_header(doc, "14.1 Cronograma Maestro de Sprints y Responsables", level=2)
doc.add_paragraph("A continuación se desglosa el cronograma operativo de los 10 Sprints con asignación nominal de responsables:")

crono_headers = ["Sprint", "Semanas", "Épica / Entregable Principal", "Responsable Líder", "Soporte Técnico"]
crono_data = [
    ["Sprint 0", "Sem. 1 - 2", "Entornos listos, Git CI/CD, base Flutter compilando.", "Scrum Master (Int. 2)", "Mobile Lead (Int. 3)"],
    ["Sprint 1", "Sem. 3 - 4", "Auth Module: Login, Register, Secure JWT Storage.", "Mobile Lead (Int. 3)", "Scrum Master (Int. 2)"],
    ["Sprint 2", "Sem. 5 - 6", "Home Screen: Hero animado, Sliders, Bottom Navigation.", "UI Specialist (Int. 4)", "Mobile Lead (Int. 3)"],
    ["Sprint 3", "Sem. 7 - 8", "Search Module: Autocompletado reactivo, Filtros, Categorías.", "UI Specialist (Int. 4)", "QA Automator (Int. 5)"],
    ["Sprint 4", "Sem. 9 - 10", "Product Detail: Comparador de precios y gráfica Keepa (fl_chart).", "UI Specialist (Int. 4)", "Mobile Lead (Int. 3)"],
    ["Sprint 5", "Sem. 11 - 12", "Maps Module: Mapa OSM interactivo, Geolocalización GPS.", "QA Automator (Int. 5)", "Mobile Lead (Int. 3)"],
    ["Sprint 6", "Sem. 13 - 14", "Cart & Checkout: Carrito offline (Hive), persistencia local.", "UI Specialist (Int. 4)", "QA Automator (Int. 5)"],
    ["Sprint 7", "Sem. 15 - 16", "AI Assistant: Chat inteligente con Gemini 2.5 Flash.", "Mobile Lead (Int. 3)", "Scrum Master (Int. 2)"],
    ["Sprint 8", "Sem. 17 - 18", "Admin & Settings: CRUD móvil, Mi Cuenta, Quiénes Somos, FAQ.", "UI Specialist (Int. 4)", "QA Automator (Int. 5)"],
    ["Sprint 9", "Sem. 19", "Testing & Hardening: Cobertura >80%, pruebas de estrés de red.", "QA Automator (Int. 5)", "Product Owner (Int. 1)"],
    ["Sprint 10", "Sem. 20", "Release Candidate: Generación de APK/AAB firmado y entrega.", "Product Owner (Int. 1)", "Todo el Equipo (5)"]
]
create_table(doc, crono_headers, crono_data, [0.8, 0.9, 2.3, 1.4, 1.4])

add_header(doc, "14.2 Criterios de Aceptación Formato BDD / Gherkin para Épicas Críticas", level=2)
doc.add_paragraph("Para ilustrar los estándares de aceptación de historias de usuario, se presentan tres ejemplos de especificación formal:")

bdd_examples = (
    "Escenario 1: Autocompletado de Búsqueda de Medicamentos\n"
    "  Dado que el usuario se encuentra en la pantalla de búsqueda de Farmalink,\n"
    "  Cuando escribe 'ibup' en el campo de texto y transcurren 300 milisegundos sin teclear,\n"
    "  Entonces la aplicación debe enviar la consulta al endpoint /api/sugerencias?q=ibup\n"
    "  Y desplegar en un máximo de 800 ms una lista flotante con las presentaciones de Ibuprofeno disponibles.\n\n"
    "Escenario 2: Comparación de Precios entre Farmacias\n"
    "  Dado que el usuario ha seleccionado el medicamento 'Amoxicilina 500mg',\n"
    "  Cuando abre la pestaña de 'Comparador de Precios',\n"
    "  Entonces debe visualizar una lista ordenada de menor a mayor precio con las farmacias que lo ofrecen,\n"
    "  Y la farmacia con el mejor precio debe estar resaltada con una insignia verde indicando el ahorro en pesos COP.\n\n"
    "Escenario 3: Consulta Segura con el Asistente IA Gemini\n"
    "  Dado que el usuario abre el chat del asistente y pregunta '¿Dónde consigo el Losartán más barato?',\n"
    "  Cuando el mensaje es procesado por el PolicyGuard del backend y validado con Gemini,\n"
    "  Entonces el asistente debe responder con un texto cordial indicando el precio más bajo\n"
    "  Y proporcionar un botón interactivo 'Ver en Mapa' que dirija automáticamente al usuario a la farmacia correspondiente."
)
add_code_block(doc, bdd_examples)

doc.add_page_break()

# ==============================================================================
# SECCIÓN 15: RECOMENDACIONES TÉCNICAS Y HERRAMIENTAS ADICIONALES
# ==============================================================================
add_header(doc, "15. Recomendaciones Técnicas de Experto y Sugerencias de Alto Valor", level=1)

doc.add_paragraph(
    "Con base en la experiencia de modernización de aplicaciones y el análisis profundo del repositorio actual de Farmalink SAS, "
    "se formulan las siguientes recomendaciones de ingeniería de alto impacto:"
)

add_bullet(doc, "1. Implementar Local Caching Agresivo para Búsquedas Frecuentes", 
           "Medicamentos de alta rotación como Acetaminofén o Ibuprofeno deben almacenarse en la base de datos local Hive "
           "con un Time-To-Live (TTL) de 1 hora. Esto reduce las llamadas al servidor en un 40% y hace que la app se sienta instantánea.")
add_bullet(doc, "2. Unificar el API Gateway a TypeScript", 
           "Actualmente gateway/index.js es JavaScript puro con Axios, mientras el backend es TypeScript. Migrar el gateway a TypeScript "
           "permitirá compartir interfaces de datos (DTOs) y evitar errores de tipado en tiempo de ejecución.")
add_bullet(doc, "3. Adoptar una Paleta Visual Material You (Material 3)", 
           "Aprovechar las capacidades de Flutter 3 para generar temas dinámicos que se adapten automáticamente a las preferencias "
           "del sistema operativo del usuario (Modo Claro / Modo Oscuro), utilizando los colores corporativos azul marino (#1E3A8A) y cian (#0284C7).")
add_bullet(doc, "4. Utilizar DBeaver Community para Administración de PostgreSQL", 
           "Se recomienda DBeaver como cliente gráfico universal para que los desarrolladores y el Scrum Master inspeccionen la base de datos "
           "PostgreSQL en Neon sin necesidad de instalar clientes pesados locales.")
add_bullet(doc, "5. Monitoreo de Crashes en Tiempo Real con Firebase Crashlytics", 
           "Integrar Crashlytics en el Sprint 9 para recibir reportes automáticos en tiempo real de cualquier excepción no controlada "
           "en los dispositivos de los usuarios, indicando la línea exacta de código Dart.")

doc.add_page_break()

# ==============================================================================
# SECCIÓN 16: PREGUNTAS Y DECISIONES ESTRATÉGICAS
# ==============================================================================
add_header(doc, "16. Preguntas y Decisiones Estratégicas Pendientes para el Equipo", level=1)

doc.add_paragraph(
    "Para asegurar la alineación total antes de iniciar el Sprint 0, se somete a consideración del Product Owner y del equipo "
    "las siguientes cinco (5) decisiones estratégicas:"
)

questions_headers = ["No.", "Decisión / Pregunta Clave", "Alternativa Recomendada", "Impacto en el Proyecto"]
questions_data = [
    ["1", "¿La base de datos seguirá alojada en Neon Cloud o se levantará un servidor PostgreSQL en una computadora física local del equipo?",
     "Mantener Neon Cloud. Ofrece alta disponibilidad, SSL nativo, copias de seguridad automáticas y elimina la necesidad de mantener un PC encendido 24/7.",
     "Afecta la configuración de variables de entorno y conectividad."],
    ["2", "¿El mapa de farmacias se implementará con OpenStreetMap (flutter_map) o con Google Maps SDK nativo?",
     "OpenStreetMap (flutter_map). Es 100% gratuito, de código abierto, no requiere registrar tarjetas de crédito en Google Cloud y cumple totalmente con los requerimientos.",
     "Afecta costos operativos de la empresa y configuración de API Keys en AndroidManifest.xml."],
    ["3", "¿Qué alcance tendrá el Carrito de Compras en la versión móvil (pedidos reales con pasarela de pago o reserva/cotización)?",
     "Fase inicial: Reserva y cotización de pedido con envío de orden por WhatsApp/API. Fase futura: Pasarela Wompi/MercadoPago.",
     "Define la complejidad de la Fase 3 y requerimientos de pasarela financiera."],
    ["4", "¿Se compilará la versión para iOS (iPhone) desde el día uno o se priorizará Android?",
     "Priorizar Android para pruebas diarias en dispositivos físicos y generar el build de iOS en fases avanzadas mediante GitHub Actions con runner de macOS.",
     "Afecta la necesidad inmediata de contar con hardware Mac y cuenta de Apple Developer ($99 USD/año)."],
    ["5", "¿El Asistente Gemini 2.5 Flash mantendrá solo respuesta en texto o se desea añadir reconocimiento de voz (Speech-to-Text)?",
     "Iniciar con chat de texto limpio y robusto en Sprint 7. Incorporar el paquete speech_to_text en un Sprint complementario si el tiempo lo permite.",
     "Agrega una experiencia de usuario de vanguardia para personas mayores."]
]
create_table(doc, questions_headers, questions_data, [0.4, 2.2, 2.2, 1.9])

add_callout(doc, "Próximo Paso Inmediato Recomendado", 
    "Celebrar la reunión de Kick-off del Sprint 0, aprobar formalmente este documento de arquitectura, validar las decisiones estratégicas "
    "de la Sección 16 y proceder a la instalación del entorno Flutter siguiendo la guía de la Sección 6.", "success")

# Guardar documento
doc.save(OUTPUT_FILE)
print(f"Documento Word generado exitosamente en: {OUTPUT_FILE}")

