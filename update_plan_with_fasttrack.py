# -*- coding: utf-8 -*-
"""
Script maestro actualizado para generar el Plan de Implementación Profesional en Word (.docx)
incorporando el Cronograma de Aceleración Fast-Track con fecha límite improrrogable al 20 de Noviembre de 2026.
"""
import sys
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUTPUT_FILE = r"c:\Users\crack\Farmalink-SAS\Plan_Implementacion_Farmalink_Mobile_Flutter.docx"

doc = Document()

# Page Margins (0.85 in)
for section in doc.sections:
    section.top_margin = Inches(0.85)
    section.bottom_margin = Inches(0.85)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

# Palette
COLOR_PRIMARY = RGBColor(30, 58, 138)     # Deep Navy #1E3A8A
COLOR_SECONDARY = RGBColor(2, 132, 199)  # Cyan/Teal #0284C7
COLOR_TEXT = RGBColor(31, 41, 55)         # Charcoal #1F2937
COLOR_MUTED = RGBColor(107, 114, 128)     # Slate Gray #6B7280
HEX_PRIMARY = "1E3A8A"
HEX_SECONDARY = "0284C7"
HEX_LIGHT_BG = "F1F5F9"
HEX_ALT_ROW = "F8FAFC"
HEX_CALLOUT_BG = "EFF6FF"
HEX_CALLOUT_BORDER = "3B82F6"
HEX_WARNING_BG = "FFFBEB"
HEX_WARNING_BORDER = "F59E0B"
HEX_SUCCESS_BG = "F0FDF4"
HEX_SUCCESS_BORDER = "10B981"
HEX_CRITICAL_BG = "FEF2F2"
HEX_CRITICAL_BORDER = "EF4444"

# Normal Style
style_normal = doc.styles['Normal']
style_normal.font.name = 'Calibri'
style_normal.font.size = Pt(10)
style_normal.font.color.rgb = COLOR_TEXT
style_normal.paragraph_format.line_spacing = 1.15
style_normal.paragraph_format.space_after = Pt(4)

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_header(document, text, level):
    h = document.add_heading(text, level=level)
    h.paragraph_format.keep_with_next = True
    if level == 1:
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(15)
            r.font.color.rgb = COLOR_PRIMARY
            r.bold = True
    elif level == 2:
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(12.5)
            r.font.color.rgb = COLOR_SECONDARY
            r.bold = True
    elif level == 3:
        h.paragraph_format.space_before = Pt(8)
        h.paragraph_format.space_after = Pt(2)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(10.5)
            r.font.color.rgb = COLOR_PRIMARY
            r.bold = True
    return h

def add_callout(document, title, text, ctype="info"):
    if ctype == "info":
        bg, border, icon = HEX_CALLOUT_BG, HEX_CALLOUT_BORDER, "📌"
    elif ctype == "warning":
        bg, border, icon = HEX_WARNING_BG, HEX_WARNING_BORDER, "⚠️"
    elif ctype == "critical":
        bg, border, icon = HEX_CRITICAL_BG, HEX_CRITICAL_BORDER, "🚨"
    else:
        bg, border, icon = HEX_SUCCESS_BG, HEX_SUCCESS_BORDER, "✅"
    
    table = document.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.8)
    set_cell_background(cell, bg)
    set_cell_margins(cell, top=110, bottom=110, left=180, right=160)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    run_t = p.add_run(f"{icon} {title.upper()}: ")
    run_t.bold = True
    run_t.font.size = Pt(9.5)
    run_t.font.color.rgb = COLOR_PRIMARY
    
    run_b = p.add_run(text)
    run_b.font.size = Pt(9.5)
    run_b.font.color.rgb = COLOR_TEXT
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="0" w:color="{border}"/><w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>')
    tcPr.append(borders)
    
    p_after = document.add_paragraph()
    p_after.paragraph_format.space_after = Pt(4)

def add_code_block(document, code_text):
    table = document.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.8)
    set_cell_background(cell, "1E293B")
    set_cell_margins(cell, top=90, bottom=90, left=130, right=130)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    run = p.add_run(code_text)
    run.font.name = 'Consolas'
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(241, 245, 249)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="18" w:space="0" w:color="{HEX_SECONDARY}"/><w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>')
    tcPr.append(borders)
    
    p_after = document.add_paragraph()
    p_after.paragraph_format.space_after = Pt(4)

def create_table(document, headers, data, col_widths=None):
    table = document.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    hdr_row = table.rows[0]
    for idx, header_text in enumerate(headers):
        cell = hdr_row.cells[idx]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_background(cell, HEX_PRIMARY)
        set_cell_margins(cell, top=90, bottom=90, left=90, right=90)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        run = p.add_run(header_text)
        run.bold = True
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(255, 255, 255)
    
    for r_idx, row_data in enumerate(data):
        row = table.rows[r_idx + 1]
        bg = HEX_ALT_ROW if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, cell_value in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(0)
            run = p.add_run(str(cell_value))
            run.font.size = Pt(8)
            run.font.color.rgb = COLOR_TEXT
            
    if col_widths and len(col_widths) == len(headers):
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = Inches(width)
                
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'<w:tblBorders {nsdecls("w")}><w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/><w:bottom w:val="single" w:sz="6" w:space="0" w:color="{HEX_PRIMARY}"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/><w:insideV w:val="none"/><w:left w:val="none"/><w:right w:val="none"/></w:tblBorders>')
    tblPr.append(borders)
    
    p_after = document.add_paragraph()
    p_after.paragraph_format.space_after = Pt(4)
    return table

def add_bullet(document, bold_prefix, text):
    p = document.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    run_b = p.add_run(bold_prefix + ": ")
    run_b.bold = True
    run_b.font.color.rgb = COLOR_PRIMARY
    run_t = p.add_run(text)
    run_t.font.color.rgb = COLOR_TEXT
    return p

print("Starting generation of Fast-Track Master Document...")

# ==============================================================================
# PORTADA CORPORATIVA (ACTUALIZADA AL 20 DE NOVIEMBRE)
# ==============================================================================
for _ in range(2):
    doc.add_paragraph()

p_title_tag = doc.add_paragraph()
p_title_tag.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_tag = p_title_tag.add_run("INGENIERÍA DE SOFTWARE & MODERNIZACIÓN MÓVIL")
r_tag.bold = True
r_tag.font.size = Pt(11)
r_tag.font.color.rgb = COLOR_SECONDARY

p_main_title = doc.add_paragraph()
p_main_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_mt = p_main_title.add_run("PLAN DE IMPLEMENTACIÓN PROFESIONAL\nMIGRACIÓN DE FARMALINK SAS A FLUTTER")
r_mt.bold = True
r_mt.font.size = Pt(25)
r_mt.font.color.rgb = COLOR_PRIMARY

p_sub = doc.add_paragraph()
p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_sub = p_sub.add_run("Estrategia Ágil SCRUM Fast-Track | Arquitectura Multidispositivo Desacoplada\n"
                      "Plan de Ejecución Intensivo de 20 Días con Fecha Límite: 20 de Noviembre de 2026")
r_sub.font.size = Pt(12)
r_sub.font.color.rgb = COLOR_TEXT

for _ in range(2):
    doc.add_paragraph()

meta_headers = ["Campo de Control", "Detalle de Especificación Técnica"]
meta_data = [
    ["Proyecto", "Farmalink SAS - Versión Móvil Nativa Multiplataforma (Flutter)"],
    ["Organización", "Farmalink SAS (Bogotá, Colombia)"],
    ["Modelo Físico", "Arquitectura Desacoplada (BD en Host Dedicado + Backend Gateway + Frontend en Smartphones)"],
    ["Tamaño del Equipo", "5 Integrantes (Product Owner, Scrum Master, 3 Mobile Developers)"],
    ["Marco Metodológico", "SCRUM Fast-Track (3 Sprints Semanales de 7 días cada uno)"],
    ["Ventana de Desarrollo", "31 de Octubre de 2026 al 19 de Noviembre de 2026 (20 Días Calendario)"],
    ["Fecha Límite Improrrogable", "20 de Noviembre de 2026 (Entrega y Sustentación Final de APK)"],
    ["Versión del Documento", "Versión 2.5 (Fast-Track Release Plan - Aprobado)"]
]
create_table(doc, meta_headers, meta_data, [2.2, 4.6])

doc.add_page_break()

# ==============================================================================
# RESUMEN EJECUTIVO & FAST-TRACK CONTEXT
# ==============================================================================
add_header(doc, "Resumen Ejecutivo: Plan de Aceleración al 20 de Noviembre", level=1)
doc.add_paragraph(
    "El presente plan maestro establece la hoja de ruta técnica y operativa para migrar la plataforma web Farmalink SAS "
    "hacia una aplicación móvil nativa en Flutter, con una fecha límite inamovible fijada para el 20 de noviembre de 2026. "
    "Con exactamente 20 días calendario disponibles, el proyecto aplica la modalidad SCRUM Fast-Track, estructurada en tres (3) Sprints "
    "semanales de alta intensidad."
)

add_callout(doc, "Factor Crítico de Viabilidad Técnica",
    "La meta del 20 de noviembre es 100% viable gracias a una ventaja estratégica fundamental: el Backend Core en Node.js/TypeScript, "
    "el API Gateway y la Base de Datos PostgreSQL en Neon Cloud YA ESTÁN CONSTRUIDOS, POBLADOS Y EN OPERACIÓN. "
    "El equipo de 5 ingenieros no gastará tiempo en diseñar tablas ni programar lógica de servidor, sino que concentrará "
    "el 100% de su capacidad en maquetar y conectar la interfaz móvil en Flutter para consumir los endpoints existentes.", "success")

add_header(doc, "Índice de Secciones", level=2)
toc_items = [
    "1. Diagnóstico Integral del Proyecto Actual (Monorepo, Node.js, Express, Neon PostgreSQL, Gemini IA)",
    "2. Arquitectura de Origen vs. Arquitectura Destino (Separación Física Multidispositivo)",
    "3. Inventario Completo de Tecnologías y Dependencias (React vs. Flutter)",
    "4. Justificación Técnica de Metodología: SCRUM Fast-Track vs. Alternativas",
    "5. Distribución Equitativa de Responsabilidades para Equipo de 5 Integrantes (20% por miembro)",
    "6. Requisitos de Hardware, Software y Configuración por Dispositivo de cada Integrante",
    "7. Plan Maestro de Aceleración Fast-Track al 20 de Noviembre (Día a Día y 3 Sprints Semanales)",
    "8. Alcance Inteligente: Matriz de Priorización de Funcionalidades (Qué entra al MVP vs. Qué se pospone)",
    "9. Plan de Base de Datos Multidispositivo (Conexión Remota a Neon PostgreSQL sin migraciones destructivas)",
    "10. Backend y API Gateway: Ajustes para Clientes Móviles (CORS, Rate Limiting y Eliminación de Bypass)",
    "11. Desarrollo del Frontend en Flutter (Clean Architecture, Riverpod, fl_chart, flutter_map y Gemini IA)",
    "12. Estrategia de Pruebas QA, Pruebas de Humo y Validación en Dispositivos Físicos",
    "13. Infraestructura, Redes, Cloud y DevOps (Túneles ngrok, Builds locales y Firebase Distribution)",
    "14. Matriz de Gestión de Riesgos y Contingencias en Cronogramas Apretados",
    "15. Protocolo de Entrega y Sustentación Final del 20 de Noviembre (Demo Script & Respaldo en Video)",
    "16. Recomendaciones Técnicas de Experto y Decisiones Inmediatas"
]
for item in toc_items:
    add_bullet(doc, item.split(". ")[0], item.split(". ")[1])

doc.add_page_break()

# ==============================================================================
# SECCIÓN 1: DIAGNÓSTICO DEL PROYECTO ACTUAL
# ==============================================================================
add_header(doc, "1. Diagnóstico Integral del Proyecto Actual", level=1)
doc.add_paragraph(
    "El repositorio Farmalink SAS fue auditado exhaustivamente. Se identificó una arquitectura de monolito modular con API Gateway "
    "compuesta por tres capas principales:"
)
add_bullet(doc, "Frontend Web (src/)", "SPA en React 19.2 + Vite 7.3 + TypeScript. Posee 16 vistas modulares, búsqueda predictiva con debounce, "
           "mapas interactivos con Leaflet y dashboards analíticos con Recharts.")
add_bullet(doc, "API Gateway (packages/gateway/)", "Proxy inverso en Express 5.2 (JavaScript puro) en puerto 8080. Se encarga de autenticación "
           "JWT y retransmisión autorizada hacia el backend.")
add_bullet(doc, "Backend Core (packages/backend/)", "Servidor en Express 5.2 + TypeScript en puerto 3001. Implementa patrones GoF avanzados: "
           "Strategy (CoincidenciaParcial, PorCategoria, SimilitudBasica, FuzzySearch), Factory Method (SugerenciaFactory), "
           "Singleton (Database Pooler a PostgreSQL en Neon Cloud) y asistente con Gemini 2.5 Flash.")
add_bullet(doc, "Base de Datos (Neon Cloud)", "PostgreSQL relacional completamente estructurado con 6 tablas (usuarios, categorias, farmacias, "
           "medicamentos, precios, historial_precios), 2 vistas (vista_precios_actuales, vista_mejores_precios) e índices geoespaciales y de precios.")

add_callout(doc, "Corrección Clave para la Versión Móvil",
    "En la versión web, el autocompletado en SearchAutocomplete.tsx llamaba directamente al backend (:3001) saltándose el Gateway (:8080). "
    "En Flutter, todo el tráfico móvil se canaliza obligatoriamente por el API Gateway centralizado.", "info")

# ==============================================================================
# SECCIÓN 2: ARQUITECTURA ORIGEN VS DESTINO MULTIDISPOSITIVO
# ==============================================================================
add_header(doc, "2. Arquitectura de Origen vs. Arquitectura Destino (Separación Multidispositivo)", level=1)
doc.add_paragraph(
    "El requerimiento fundamental del proyecto exige que la solución móvil mantenga una estricta separación física de dispositivos:"
)

arch_table_headers = ["Capa de Sistema", "Dispositivo / Host Físico", "Tecnología Operativa", "Responsabilidad Principal"]
arch_table_data = [
    ["Dispositivo 1: Base de Datos", "Servidor Cloud Neon (AWS us-east-1) o PC Host dedicado en LAN.", "PostgreSQL 15+ con Pooler SSL.", "Persistencia relacional, vistas de precios óptimos y almacenamiento de tokens push."],
    ["Dispositivo 2: Backend & Gateway", "Servidor central en red local (IP Fija) o Cloud (Render.com).", "Node.js 20 LTS + Express 5 + TypeScript.", "Validación de JWT, proxy inverso, motor de búsqueda difusa e integración con Gemini IA."],
    ["Dispositivos 3, 4, 5...: Clientes Móviles", "Smartphones físicos Android / iOS de los integrantes y usuarios.", "Flutter 3.24+ (Dart 3.5+) compilado AOT.", "Interfaz Material 3, mapas nativos GPS, caché offline con Hive y gráficos Keepa."]
]
create_table(doc, arch_table_headers, arch_table_data, [1.5, 1.8, 1.6, 1.9])

diag_text = (
    "+-----------------------------------------------------------------------------------------+\n"
    "|                           DISPOSITIVO 1: SERVIDOR DE DATOS                              |\n"
    "|                       (Neon PostgreSQL Cloud / Host Dedicado)                           |\n"
    "|  - PostgreSQL 15+ (Tablas: usuarios, categorias, farmacias, medicamentos, precios)       |\n"
    "|  - Vistas materializadas de precios + Indices Trigram para busqueda instantanea          |\n"
    "+--------------------------------------------^--------------------------------------------+\n"
    "                                             | Conexión TCP SSL (Pooler Port 5432)\n"
    "+--------------------------------------------v--------------------------------------------+\n"
    "|                         DISPOSITIVO 2: SERVIDOR BACKEND & GATEWAY                       |\n"
    "|                     (Host Central / Render / IP Local con ngrok)                        |\n"
    "|  - API Gateway Express (:8080) -> Valida JWT + Rate Limiter + Proxy Inverso              |\n"
    "|  - Backend Core Express + TS (:3001) -> Logica Farmalink + Modulo Gemini 2.5 Flash       |\n"
    "+--------------------------------------------^--------------------------------------------+\n"
    "                                             | HTTPS REST API (JSON / Bearer Token)\n"
    "+--------------------------------------------v--------------------------------------------+\n"
    "|                   DISPOSITIVOS 3, 4, 5...: SMARTPHONES ANDROID / IOS                    |\n"
    "|                               (App Nativa en Flutter 3.24)                              |\n"
    "|  - UI Material 3 + GoRouter + Riverpod State Management                                 |\n"
    "|  - Dio Client + Cache Local Hive (Modo Offline) + flutter_map GPS + fl_chart Precios    |\n"
    "+-----------------------------------------------------------------------------------------+"
)
add_code_block(doc, diag_text)

doc.add_page_break()

# ==============================================================================
# SECCIÓN 3: INVENTARIO DE TECNOLOGÍAS
# ==============================================================================
add_header(doc, "3. Inventario Completo de Tecnologías y Dependencias", level=1)
doc.add_paragraph("Mapeo directo de librerías del frontend web actual hacia el ecosistema Flutter:")

inv_headers = ["Módulo / Función", "Web Actual (React)", "Móvil Destino (Flutter)", "Justificación Técnica"]
inv_data = [
    ["Framework Base", "React 19.2 (SPA Web)", "Flutter 3.24+ (Dart 3.5+)", "Compilación nativa a 60/120 fps y reutilización de código."],
    ["Gestión de Estado", "useState + Context API", "Flutter Riverpod 2.5+", "Desacoplamiento total de UI y lógica de negocio."],
    ["Navegación", "React Router DOM 7.13", "GoRouter 14+", "Routing declarativo con guardias de autenticación y deep linking."],
    ["Cliente HTTP", "Axios + fetch", "Dio 5.4+", "Interceptores nativos para inyección de JWT y reintentos ante pérdida de señal."],
    ["Almacenamiento Local", "localStorage", "Hive 2.2 + flutter_secure_storage", "Caché NoSQL offline ultrarrápida y cifrado de tokens en Keystore."],
    ["Mapas y GPS", "Leaflet + React-Leaflet", "flutter_map 6+ & geolocator", "OpenStreetMap 100% gratuito sin tarjetas de crédito y GPS nativo."],
    ["Gráficas de Precios", "Recharts 3.8", "fl_chart 0.68+", "Renderizado en Canvas de curvas históricas estilo Keepa."],
    ["Asistente de IA", "Fetch a /api/ai/assistant", "Dio a Gateway + Chat UI", "Misma integración con Gemini 2.5 Flash y PolicyGuard sanitario."]
]
create_table(doc, inv_headers, inv_data, [1.4, 1.6, 1.8, 2.0])

# ==============================================================================
# SECCIÓN 4: JUSTIFICACIÓN SCRUM FAST-TRACK
# ==============================================================================
add_header(doc, "4. Justificación Técnica del Marco de Trabajo: SCRUM Fast-Track", level=1)
doc.add_paragraph(
    "Ante un plazo estricto de 20 días calendario, los Sprints convencionales de 2 o 3 semanas resultan inviables. "
    "Se adapta el marco ágil a **SCRUM Fast-Track con Sprints de 1 semana (7 días calendario)** por las siguientes razones:"
)
add_bullet(doc, "Ritmo Rápido de Sincronización", "Con Sprints semanales, cualquier desalineación o error de integración se detecta en máximo 48 horas en los Daily Standups.")
add_bullet(doc, "Entregables Tangibles cada 7 Días", "Se generan tres APKs de control: APK #1 (7 de Nov: Auth+Búsqueda), APK #2 (14 de Nov: Precios+Mapas) y APK #3 (19 de Nov: Carrito+IA final).")
add_bullet(doc, "Compromiso de Equipo Balanceado", "Permite reajustar tareas diariamente entre los 5 integrantes según el progreso real.")

# ==============================================================================
# SECCIÓN 5: DISTRIBUCIÓN EQUITATIVA (5 INTEGRANTES)
# ==============================================================================
add_header(doc, "5. Distribución Equitativa de Responsabilidades (Equipo de 5)", level=1)
doc.add_paragraph("Para lograr que el proyecto avance sin cuellos de botella, la carga de trabajo se divide en 20% por persona:")

team_headers = ["Integrante", "Rol SCRUM", "Especialidad en Fast-Track", "Módulos Asignados (31 Oct - 20 Nov)"]
team_data = [
    ["Integrante 1", "Product Owner (PO)", "QA Funcional & Validación de Entregables", "• Criterios de aceptación de cada pantalla.\n• Pruebas funcionales diarias en teléfono real.\n• Preparación de datos demo y guión de sustentación final."],
    ["Integrante 2", "Scrum Master (SM)", "Backend & Infraestructura de Conectividad", "• Mantener backend y PostgreSQL accesibles (vía ngrok o Render).\n• Configurar CORS y soporte móvil en Gateway.\n• Pruebas de endpoints con Postman y soporte de red a los devs."],
    ["Integrante 3", "Developer 1", "Mobile Lead Architect & Core Services", "• Arquitectura Clean Architecture base en Flutter.\n• Cliente Dio con interceptor de JWT y GoRouter.\n• Módulos de Login, Registro, SecureStorage y Chat Gemini IA."],
    ["Integrante 4", "Developer 2", "Mobile UI Specialist (Vistas Clave)", "• Pantalla Home (Hero, Sliders, NavigationBar).\n• Buscador reactivo con debounce (300ms) y sugerencias.\n• Pantalla de Detalle de Medicamento y Comparador de Precios."],
    ["Integrante 5", "Developer 3", "Mobile Features (Mapas & Carrito)", "• Mapa interactivo de farmacias con flutter_map (OSM).\n• Geolocalización GPS en tiempo real con geolocator.\n• Carrito de compras local con Hive NoSQL y vista de Checkout."]
]
create_table(doc, team_headers, team_data, [1.1, 1.3, 1.8, 2.6])

doc.add_page_break()

# ==============================================================================
# SECCIÓN 6: REQUISITOS POR DISPOSITIVO (ANTI "EN MI MÁQUINA FUNCIONA")
# ==============================================================================
add_header(doc, "6. Requisitos de Hardware, Software y Configuración por Dispositivo", level=1)
doc.add_paragraph(
    "Para garantizar que los 5 integrantes comiencen a compilar inmediatamente sin discrepancias de librerías, "
    "se establece la siguiente línea base técnica obligatoria:"
)

req_headers = ["Herramienta / Entorno", "Versión Obligatoria", "Propósito en el Proyecto", "Verificación en Terminal"]
req_data = [
    ["Flutter SDK", "3.24.x (Canal Stable)", "Compilación de la app móvil Android/iOS.", "flutter --version"],
    ["Dart SDK", "3.5.x", "Lenguaje de programación de Flutter.", "dart --version"],
    ["Java Development Kit", "JDK 17 LTS (OpenJDK)", "Compilación de Gradle en Android (evitar JDK 21+).", "java -version"],
    ["Android Studio", "Koala o Ladybug", "SDK Manager, Build-Tools 34.0.0, Command-line Tools.", "flutter doctor --android-licenses"],
    ["IDE de Código", "VS Code + Plugins oficiales", "Flutter, Dart, Error Lens, Prettier.", "code --version"],
    ["Dispositivo de Pruebas", "Smartphone Android Físico", "Depuración USB activada (ahorra RAM frente a emuladores).", "adb devices"],
    ["Conectividad LAN/WAN", "ngrok / IP Fija LAN", "Túnel HTTPS seguro para conectar el teléfono con el Backend.", "ngrok http 8080"]
]
create_table(doc, req_headers, req_data, [1.5, 1.5, 2.3, 1.5])

add_callout(doc, "Regla de Conexión Móvil Obligatoria",
    "Los teléfonos móviles NO pueden acceder a 'localhost'. En el archivo .env de Flutter se debe configurar la URL pública generada "
    "por ngrok (ejemplo: API_BASE_URL=https://farmalink-dev.ngrok-free.app) o la IP local estática de la PC que ejecuta el backend "
    "(ejemplo: API_BASE_URL=http://192.168.1.150:8080).", "warning")

doc.add_page_break()

# ==============================================================================
# SECCIÓN 7: PLAN MAESTRO FAST-TRACK AL 20 DE NOVIEMBRE (DÍA A DÍA)
# ==============================================================================
add_header(doc, "7. Plan Maestro de Aceleración Fast-Track (Meta: 20 de Noviembre)", level=1)
doc.add_paragraph(
    "A continuación se presenta el cronograma intensivo de 20 días calendario (3 Sprints de 1 semana), desglosado día a día "
    "para alcanzar la meta sin retrasos:"
)

crono_headers = ["Día y Fecha", "Sprint", "Hito Operativo", "Actividades Principales por Integrante", "Entregable del Día"]
crono_data = [
    ["Día 1 (31 Oct - 1 Nov)", "S1", "Kickoff & Entornos", "Devs configuran Flutter 3.24 y JDK 17; SM levanta backend y ngrok; PO valida backlog.", "flutter doctor verde en los 5 equipos."],
    ["Día 2 (2 Nov)", "S1", "Repositorio & Base", "Dev 1 crea esqueleto Clean Architecture; Dev 2 y 3 configuran temas y assets; SM habilita CORS móvil.", "Repo GitHub con build de prueba inicial."],
    ["Día 3 (3 Nov)", "S1", "Auth API & Modelos", "Dev 1 crea AuthRepository (Dio) y SecureStorage; Dev 2 diseña pantalla Login; PO revisa diseño.", "Login funcional consumiendo API real."],
    ["Día 4 (4 Nov)", "S1", "Registro & Sesión", "Dev 1 completa Registro; Dev 2 implementa navegación con GoRouter; SM valida base de datos en Neon.", "Registro y persistencia de sesión con JWT."],
    ["Día 5 (5 Nov)", "S1", "Home & Sliders", "Dev 2 maqueta Home (Hero, Banners, Slider farmacias); Dev 3 prepara servicio de medicamentos.", "Pantalla Home navegable."],
    ["Día 6 (6 Nov)", "S1", "Search Autocomplete", "Dev 2 integra campo de búsqueda con debounce 300ms; Dev 1 conecta /api/sugerencias; SM optimiza queries.", "Búsqueda en tiempo real desde el teléfono."],
    ["Día 7 (7 Nov)", "S1", "CIERRE SPRINT 1", "Pruebas integradas de Auth y Búsqueda; generación de APK #1; PO valida en su smartphone.", "APK #1 FUNCIONAL GENERADA."],
    ["Día 8 (8 Nov)", "S2", "Detalle Medicamento", "Dev 2 maqueta vista ProductoDetalle; Dev 1 mapea DTOs de laboratorios y descripción.", "Ficha técnica de medicamento renderizada."],
    ["Día 9 (9 Nov)", "S2", "Comparador Precios", "Dev 2 implementa lista de precios por farmacia ordenada de menor a mayor con cálculo de ahorro.", "Comparador de precios visual y funcional."],
    ["Día 10 (10 Nov)", "S2", "Gráfica Keepa", "Dev 2 integra fl_chart para mostrar curva de fluctuación histórica (/api/precios/historial).", "Gráfica de precios interactiva en Canvas."],
    ["Día 11 (11 Nov)", "S2", "Mapa OpenStreetMap", "Dev 3 integra flutter_map con capas OSM gratuitas; PO valida coordenadas de Bogotá.", "Mapa interactivo con pines de farmacias."],
    ["Día 12 (12 Nov)", "S2", "Geolocalización GPS", "Dev 3 integra geolocator para detectar ubicación del usuario y pedir permisos nativos.", "Puntero azul de ubicación del usuario en mapa."],
    ["Día 13 (13 Nov)", "S2", "Farmacias Cercanas", "Dev 3 conecta /api/farmacias/cercanas calculando distancia en km; Dev 1 asiste con caché.", "Lista y mapa de farmacias ordenadas por distancia."],
    ["Día 14 (14 Nov)", "S2", "CIERRE SPRINT 2", "Pruebas de flujo Buscar -> Comparar -> Ver en Mapa; generación de APK #2; PO aprueba demo.", "APK #2 FUNCIONAL GENERADA."],
    ["Día 15 (15 Nov)", "S3", "Carrito Local Hive", "Dev 3 implementa CartProvider y almacenamiento local con Hive; Dev 2 crea vista CartView.", "Añadir productos al carrito sin internet."],
    ["Día 16 (16 Nov)", "S3", "Checkout & WhatsApp", "Dev 3 implementa Checkout con generación de resumen de orden y envío directo por WhatsApp API.", "Flujo de compra/reserva completado."],
    ["Día 17 (17 Nov)", "S3", "Asistente Gemini IA", "Dev 1 integra chat flotante consumiendo /api/ai/assistant con respuestas inteligentes de Gemini.", "Chatbot con IA respondiendo consultas."],
    ["Día 18 (18 Nov)", "S3", "QA & Hardening", "Todo el equipo prueba la app intensivamente; corrección de bugs visuales y textos.", "Reporte de 0 bugs bloqueantes."],
    ["Día 19 (19 Nov)", "S3", "Build Release Final", "Dev 1 compila APK Release firmado; Dev 3 graba video demo de respaldo; PO prepara diapositivas.", "app-release.apk LISTO + VIDEO DEMO."],
    ["Día 20 (20 Nov)", "S3", "¡ENTREGA Y SUSTENTACIÓN!", "Presentación formal del proyecto Farmalink Mobile en vivo con smartphone físico proyectado.", "PROYECTO ENTREGADO CON ÉXITO."]
]
create_table(doc, crono_headers, crono_data, [1.1, 0.5, 1.2, 2.7, 1.3])

doc.add_page_break()

# ==============================================================================
# SECCIÓN 8: ALCANCE INTELIGENTE (QUÉ ENTRA VS QUÉ SE RECORTA)
# ==============================================================================
add_header(doc, "8. Alcance Inteligente: Matriz de Priorización de Funcionalidades", level=1)
doc.add_paragraph(
    "Para garantizar la entrega puntual el 20 de noviembre sin comprometer la estabilidad, el equipo aplica la regla 80/20 "
    "de priorización de alcance:"
)

scope_headers = ["Funcionalidad", "Estado en Fast-Track", "Justificación Estratégica"]
scope_data = [
    ["Autenticación (Login / Registro / JWT)", "DENTRO (Esencial)", "Garantiza seguridad y personalización del usuario en el móvil."],
    ["Buscador predictivo con debounce (300ms)", "DENTRO (Esencial)", "Es la puerta de entrada de los usuarios para encontrar medicinas."],
    ["Comparador de precios entre farmacias", "DENTRO (Core del Negocio)", "Representa el valor único de Farmalink: ahorrar dinero comparando precios."],
    ["Gráfica de precios histórica tipo Keepa", "DENTRO (Diferenciador)", "Demuestra alto nivel técnico en visualización de datos con fl_chart."],
    ["Mapa con GPS nativo (OpenStreetMap)", "DENTRO (Esencial)", "Función móvil nativa clave para encontrar farmacias cercanas."],
    ["Carrito de compras con Hive NoSQL", "DENTRO (Esencial)", "Permite armar el pedido localmente y despachar orden."],
    ["Asistente de IA con Google Gemini 2.5", "DENTRO (Innovación)", "Aprovecha el endpoint existente en el backend con alto impacto visual."],
    ["Panel de administración móvil complejo", "FUERA (Pospuesto)", "Los administradores pueden seguir usando la web actual para crear medicamentos."],
    ["Pasarela bancaria con tarjeta de crédito", "FUERA (Pospuesto)", "Se sustituye por despacho de pedido a WhatsApp/API para evitar demoras de certificación bancaria."],
    ["Compilación y firma para Apple iOS", "FUERA (Pospuesto)", "Se enfoca 100% en Android (APK) para asegurar pruebas universales en los teléfonos del equipo."]
]
create_table(doc, scope_headers, scope_data, [1.8, 1.5, 3.5])

# ==============================================================================
# SECCIÓN 9: MIGRACIÓN DE BASE DE DATOS
# ==============================================================================
add_header(doc, "9. Base de Datos Multidispositivo: Operación Continua", level=1)
doc.add_paragraph(
    "La base de datos PostgreSQL alojada en Neon Cloud se mantiene operativa sin migraciones destructivas. "
    "Para garantizar conectividad remota segura, se utiliza la cadena de conexión SSL con el pooler transaccional."
)
doc.add_paragraph(
    "Tablas utilizadas por la app móvil: usuarios (auth), categorias (filtros), farmacias (mapa GPS), medicamentos (búsqueda) "
    "y precios/historial_precios (comparador y gráficas Keepa)."
)

# ==============================================================================
# SECCIÓN 10: BACKEND Y API GATEWAY
# ==============================================================================
add_header(doc, "10. Backend y API Gateway: Ajustes para Clientes Móviles", level=1)
doc.add_paragraph(
    "El backend Node.js en packages/backend y el Gateway en packages/gateway requieren únicamente dos adaptaciones:"
)
add_bullet(doc, "Habilitar CORS Abierto para Apps Nativas", 
           "Configurar cors({ origin: '*' }) en gateway/index.js para que los teléfonos Android no sean bloqueados al emitir llamadas REST.")
add_bullet(doc, "Túnel HTTPS con ngrok", 
           "El Integrante 2 (Backend) ejecuta 'ngrok http 8080'. La URL HTTPS resultante se distribuye a los desarrolladores para su archivo .env.")

doc.add_page_break()

# ==============================================================================
# SECCIÓN 11: DESARROLLO DEL FRONTEND EN FLUTTER
# ==============================================================================
add_header(doc, "11. Desarrollo del Frontend en Flutter (Clean Architecture)", level=1)
doc.add_paragraph(
    "La aplicación se estructura en cuatro capas desacopladas que permiten a los Developers 1, 2 y 3 programar en paralelo sin colisiones en Git:"
)

arch_clean = (
    "lib/\n"
    "├── core/                   # Configuracion global, cliente Dio, constantes y tema Material 3\n"
    "├── data/                   # Modelos Dart (Medicamento, Farmacia, Precio) y Repositorios API\n"
    "├── presentation/           # Vistas y Widgets organizados por funcionalidad\n"
    "│   ├── auth/               # LoginScreen, RegisterScreen\n"
    "│   ├── home/               # HomeScreen, BannerSlider, BottomNavBar\n"
    "│   ├── search/             # SearchScreen con Debounce y Filtros\n"
    "│   ├── product/            # ProductDetailScreen, PriceComparisonTable, KeepaChart\n"
    "│   ├── map/                # MapScreen con flutter_map y geolocator\n"
    "│   ├── cart/               # CartScreen respaldado en Hive NoSQL\n"
    "│   └── assistant/          # AssistantChatSheet con Gemini 2.5 Flash\n"
    "└── main.dart               # Entry point con inicializacion de Hive y Riverpod"
)
add_code_block(doc, arch_clean)

# ==============================================================================
# SECCIÓN 12: PRUEBAS QA Y VALIDACIÓN
# ==============================================================================
add_header(doc, "12. Estrategia de Pruebas QA y Validación en Dispositivos Físicos", level=1)
doc.add_paragraph(
    "Durante el Fast-Track, las pruebas se concentran en validar los cuatro (4) flujos de oro en teléfonos reales:"
)
add_bullet(doc, "Flujo de Oro 1 (Auth)", "Registro de nuevo usuario -> Inicio de sesión -> Recepción de JWT -> Cierre y reapertura de app sin perder sesión.")
add_bullet(doc, "Flujo de Oro 2 (Búsqueda y Comparación)", "Búsqueda de 'Acetaminofén' -> Selección de dosis -> Visualización de mejor precio en Farmacia Central con ahorro destacado.")
add_bullet(doc, "Flujo de Oro 3 (Mapa GPS)", "Apertura del mapa -> Concesión de permiso de ubicación -> Centrado en posición actual y despliegue de farmacias en radio de 5 km.")
add_bullet(doc, "Flujo de Oro 4 (Asistente IA)", "Preguntar en el chat: '¿Dónde encuentro Amoxicilina barata?' -> Ver respuesta contextual de Gemini con botón de navegación.")

# ==============================================================================
# SECCIÓN 13: INFRAESTRUCTURA Y REDES
# ==============================================================================
add_header(doc, "13. Infraestructura, Redes y Despliegue de APKs", level=1)
doc.add_paragraph(
    "Para distribuir las versiones de prueba entre los 5 integrantes sin necesidad de cables ni Play Store:"
)
add_bullet(doc, "Compilación Rápida de APK", "flutter build apk --split-per-abi (genera APKs livianas de ~18 MB optimizadas para la arquitectura ARM del teléfono).")
add_bullet(doc, "Distribución Inmediata", "Subida de la APK al grupo de WhatsApp/Drive del equipo y a Firebase App Distribution.")

doc.add_page_break()

# ==============================================================================
# SECCIÓN 14: GESTIÓN DE RIESGOS FAST-TRACK
# ==============================================================================
add_header(doc, "14. Matriz de Gestión de Riesgos en Cronograma Fast-Track", level=1)

fast_risk_headers = ["Riesgo Crítico", "Probabilidad", "Impacto", "Estrategia Preventiva Inmediata"]
fast_risk_data = [
    ["Falla de conexión a internet durante la sustentación final.", "Media", "Crítico", "Tener precargada la base de datos local Hive con catálogo offline y un video grabado de backup."],
    ["Problemas de permisos de GPS en Android 13/14.", "Media", "Alto", "Configurar ACCESS_FINE_LOCATION y ACCESS_COARSE_LOCATION en AndroidManifest.xml desde el Día 1."],
    ["Retraso en la maquetación de pantallas.", "Media", "Alto", "Reutilizar componentes de Material 3 estándar sin inventar widgets complejos desde cero."],
    ["Caída del túnel ngrok por inactividad.", "Alta", "Medio", "Reiniciar el túnel al inicio de cada jornada o desplegar backend en Render.com."]
]
create_table(doc, fast_risk_headers, fast_risk_data, [2.0, 1.0, 1.0, 2.8])

# ==============================================================================
# SECCIÓN 15: PROTOCOLO DE ENTREGA Y SUSTENTACIÓN DEL 20 DE NOVIEMBRE
# ==============================================================================
add_header(doc, "15. Protocolo de Entrega y Sustentación Final (20 de Noviembre)", level=1)
doc.add_paragraph(
    "Para garantizar una calificación o evaluación sobresaliente el día 20 de noviembre, el equipo ejecutará el siguiente guión "
    "de sustentación de 10 minutos:"
)
add_bullet(doc, "Minuto 0 a 2 (Introducción y Arquitectura)", "El PO explica el problema de salud pública y la arquitectura multidispositivo (Base de datos remota, Backend Gateway central y Frontend Flutter).")
add_bullet(doc, "Minuto 2 a 5 (Demo en Vivo - Proyección de Smartphone)", "El Dev Lead proyecta la pantalla de su teléfono real (usando Scrcpy o Vysor) y ejecuta en vivo: Login, Búsqueda de Medicamento y Comparador de Precios.")
add_bullet(doc, "Minuto 5 a 7 (Geolocalización y Asistente IA)", "Demostración del Mapa interactivo centrado por GPS en Bogotá y consulta en tiempo real al Asistente inteligente con Gemini 2.5 Flash.")
add_bullet(doc, "Minuto 7 a 9 (Caché Offline y Carrito)", "Demostración de resiliencia: se activa el Modo Avión en el teléfono y se demuestra que el carrito y catálogo siguen funcionando gracias a Hive.")
add_bullet(doc, "Minuto 9 a 10 (Conclusiones y Preguntas)", "Cierre formal, agradecimientos y entrega del repositorio Git y archivo app-release.apk.")

# ==============================================================================
# SECCIÓN 16: RECOMENDACIONES TÉCNICAS INMEDIATAS
# ==============================================================================
add_header(doc, "16. Recomendaciones Técnicas Inmediatas para el Día de Hoy", level=1)
doc.add_paragraph("Acciones inmediatas para las próximas 24 horas:")
add_bullet(doc, "Paso 1", "Verificar que los 3 desarrolladores tengan Flutter 3.24 y JDK 17 instalados corriendo 'flutter doctor'.")
add_bullet(doc, "Paso 2", "El Integrante 2 (Backend) debe encender el servidor y ejecutar 'ngrok http 8080', compartiendo la URL al grupo.")
add_bullet(doc, "Paso 3", "Crear el repositorio de Flutter y hacer el primer commit con el template Clean Architecture.")
add_bullet(doc, "Paso 4", "¡Iniciar el Sprint 1 con el módulo de Autenticación!")

add_callout(doc, "Dictamen de Éxito", 
    "Con una división estricta de tareas, backend ya operativo y un alcance priorizado en el core del negocio, "
    "el equipo de 5 integrantes cuenta con todas las herramientas técnicas y metodológicas para coronar con éxito "
    "la entrega de Farmalink Mobile el 20 de Noviembre de 2026.", "success")

# Guardar documento
doc.save(OUTPUT_FILE)
print(f"Documento Word actualizado exitosamente con Plan Fast-Track en: {OUTPUT_FILE}")

