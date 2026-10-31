import os
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

BASE_DIR = r"c:\Users\crack\Farmalink-SAS"
OUTPUT_DOCX = os.path.join(BASE_DIR, "Alcance_y_Restricciones_FarmaLink.docx")

# FarmaLink Brand Palette
COLOR_PRIMARY_HEX = "0B7DB8"      # FarmaLink Blue
COLOR_DARK_HEX = "0F172A"         # Slate 900
COLOR_SECONDARY_HEX = "0369A1"    # Cyan / Dark Blue
COLOR_LIGHT_BG_HEX = "F8FAFC"     # Slate 50
COLOR_BORDER_HEX = "CBD5E1"       # Slate 300
COLOR_MUTED_HEX = "64748B"        # Slate 500
COLOR_SUCCESS_HEX = "059669"      # Emerald 600
COLOR_WARNING_HEX = "D97706"      # Amber 600
COLOR_DANGER_HEX = "DC2626"       # Red 600

COLOR_PRIMARY = RGBColor(11, 125, 184)
COLOR_SECONDARY = RGBColor(3, 105, 161)
COLOR_DARK = RGBColor(15, 23, 42)
COLOR_MUTED = RGBColor(100, 116, 139)
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_SUCCESS = RGBColor(5, 150, 105)
COLOR_WARNING = RGBColor(217, 119, 6)
COLOR_DANGER = RGBColor(220, 38, 38)

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'))

def set_cell_margins(cell, top=140, bottom=140, left=180, right=180):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_cell_borders(cell, top="CBD5E1", bottom="CBD5E1", left="CBD5E1", right="CBD5E1", sz=4):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{top}"/>'
        f'<w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{bottom}"/>'
        f'<w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{left}"/>'
        f'<w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{right}"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)

print("Creando documento de Alcance y Restricciones...")
doc = Document()

# Márgenes
for s in doc.sections:
    s.top_margin = Inches(0.8)
    s.bottom_margin = Inches(0.8)
    s.left_margin = Inches(0.8)
    s.right_margin = Inches(0.8)

# Estilo base
style_normal = doc.styles['Normal']
style_normal.font.name = 'Segoe UI'
style_normal.font.size = Pt(10)
style_normal.font.color.rgb = COLOR_DARK

def add_callout(doc, title, text, border_color="0B7DB8", bg_color="F0F9FF", title_color=COLOR_PRIMARY):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    c = t.rows[0].cells[0]
    c.width = Inches(6.9)
    set_cell_background(c, bg_color)
    set_cell_margins(c, top=140, bottom=140, left=200, right=180)
    set_cell_borders(c, top=border_color, bottom=border_color, left=border_color, right=border_color, sz=12)
    
    p = c.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    r1 = p.add_run(f"📌 {title}\n")
    r1.font.bold = True
    r1.font.size = Pt(10.5)
    r1.font.color.rgb = title_color
    
    r2 = p.add_run(text)
    r2.font.size = Pt(9.5)
    r2.font.color.rgb = COLOR_DARK
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

def add_section_h1(doc, number, title):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(18)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    
    r_num = h.add_run(f"{number}. ")
    r_num.font.bold = True
    r_num.font.size = Pt(15)
    r_num.font.color.rgb = COLOR_PRIMARY
    
    r_txt = h.add_run(title)
    r_txt.font.bold = True
    r_txt.font.size = Pt(15)
    r_txt.font.color.rgb = COLOR_DARK

def add_section_h2(doc, number, title):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    
    r_num = h.add_run(f"{number} ")
    r_num.font.bold = True
    r_num.font.size = Pt(12)
    r_num.font.color.rgb = COLOR_SECONDARY
    
    r_txt = h.add_run(title)
    r_txt.font.bold = True
    r_txt.font.size = Pt(12)
    r_txt.font.color.rgb = COLOR_DARK

def add_bullet(doc, strong_prefix, text):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    r_pre = p.add_run(strong_prefix)
    r_pre.font.bold = True
    r_pre.font.color.rgb = COLOR_DARK
    r_txt = p.add_run(f" {text}")
    r_txt.font.color.rgb = COLOR_DARK

# ==========================================
# PORTADA / HEADER
# ==========================================
cover_table = doc.add_table(rows=1, cols=1)
cover_table.alignment = WD_TABLE_ALIGNMENT.CENTER
c_cell = cover_table.rows[0].cells[0]
c_cell.width = Inches(6.9)
set_cell_background(c_cell, "F0F9FF")
set_cell_margins(c_cell, top=240, bottom=240, left=280, right=280)
set_cell_borders(c_cell, top="0B7DB8", bottom="0B7DB8", left="0B7DB8", right="0B7DB8", sz=16)

# Insert logo if available
logo_path = os.path.join(BASE_DIR, "src", "assets", "logo-farmalink.png")
if os.path.exists(logo_path):
    p_logo = c_cell.paragraphs[0]
    p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_logo.paragraph_format.space_after = Pt(6)
    p_logo.add_run().add_picture(logo_path, width=Inches(1.8))
    cp1 = c_cell.add_paragraph()
else:
    cp1 = c_cell.paragraphs[0]

cp1.alignment = WD_ALIGN_PARAGRAPH.CENTER
cp1.paragraph_format.space_after = Pt(4)
r_org = cp1.add_run("FARMALINK S.A.S.")
r_org.font.size = Pt(20)
r_org.font.bold = True
r_org.font.color.rgb = COLOR_PRIMARY

cp2 = c_cell.add_paragraph()
cp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
cp2.paragraph_format.space_after = Pt(6)
r_doc_title = cp2.add_run("Documento de Especificación: Alcance y Restricciones")
r_doc_title.font.size = Pt(16)
r_doc_title.font.bold = True
r_doc_title.font.color.rgb = COLOR_DARK

cp3 = c_cell.add_paragraph()
cp3.alignment = WD_ALIGN_PARAGRAPH.CENTER
cp3.paragraph_format.space_after = Pt(12)
r_doc_sub = cp3.add_run("Delimitación funcional, límites del sistema, exclusiones operativas, supuestos de negocio y dependencias tecnológicas de la plataforma")
r_doc_sub.font.size = Pt(10)
r_doc_sub.font.color.rgb = COLOR_MUTED

cp4 = c_cell.add_paragraph()
cp4.alignment = WD_ALIGN_PARAGRAPH.CENTER
cp4.paragraph_format.space_after = Pt(0)
r_meta = cp4.add_run("Versión: 1.0   |   Fecha: Septiembre 2026   |   Estado: Aprobado / Producción   |   Entorno: Bogotá D.C., Colombia")
r_meta.font.size = Pt(8.5)
r_meta.font.bold = True
r_meta.font.color.rgb = COLOR_PRIMARY

doc.add_paragraph().paragraph_format.space_after = Pt(10)

# ==========================================
# RESUMEN EJECUTIVO
# ==========================================
add_callout(
    doc,
    "Propósito del Documento",
    "El presente documento formaliza los límites funcionales, técnicos y legales de la solución tecnológica desarrollada por FarmaLink S.A.S. "
    "Define con absoluta precisión qué componentes, servicios y capacidades están garantizados en la entrega (Qué está incluido), "
    "las fronteras operativas deliberadas (Qué queda fuera), las condiciones normativas y arquitectónicas no negociables (Restricciones del sistema), "
    "así como las premisas y requerimientos de terceros necesarios para su óptimo funcionamiento (Supuestos y dependencias).",
    border_color="0B7DB8",
    bg_color="F0F9FF",
    title_color=COLOR_PRIMARY
)

# ==========================================
# 1. ALCANCE Y RESTRICCIONES
# ==========================================
add_section_h1(doc, "1", "Alcance y Restricciones del Sistema")

p_intro = doc.add_paragraph()
p_intro.paragraph_format.space_after = Pt(10)
p_intro.paragraph_format.line_spacing = 1.15
p_intro.add_run(
    "FarmaLink es una plataforma digital orientada a democratizar el acceso a información farmacéutica transparente en Colombia, "
    "permitiendo a los ciudadanos buscar, comparar precios en tiempo real y geolocalizar medicamentos disponibles en farmacias afiliadas de Bogotá D.C. "
    "Para garantizar la sostenibilidad técnica, la viabilidad regulatoria y la excelencia operativa, el sistema se rige bajo los siguientes cuatro pilares:"
)

# Tabla resumen inicial de los 4 ejes
t_summary = doc.add_table(rows=5, cols=2)
t_summary.alignment = WD_TABLE_ALIGNMENT.CENTER
t_summary.autofit = False

col_w = [Inches(2.2), Inches(4.7)]
headers_s = ["Dimensión", "Definición y Alcance Estratégico"]
for i, h in enumerate(headers_s):
    c = t_summary.rows[0].cells[i]
    c.width = col_w[i]
    set_cell_background(c, "0B7DB8")
    set_cell_margins(c, top=80, bottom=80, left=80, right=80)
    set_cell_borders(c, top="0B7DB8", bottom="0B7DB8", left="0B7DB8", right="0B7DB8", sz=4)
    p = c.paragraphs[0]
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(9)
    r.font.color.rgb = COLOR_WHITE

rows_data_s = [
    ("1.1 Restricciones del sistema", "Límites técnicos, arquitectónicos, de seguridad y normativos (INVIMA, MinSalud, Ley de Habeas Data) que condicionan el diseño y operación de la plataforma."),
    ("1.2 Qué está incluido (In-Scope)", "Conjunto de características, módulos, roles y servicios completamente desarrollados, probados e implementados en la versión actual."),
    ("1.3 Qué queda fuera (Out-of-Scope)", "Procesos, funcionalidades y servicios que deliberadamente no forman parte de esta fase (ej. transacciones de pago, domicilios propios, validación RIPS/MIPRES)."),
    ("1.4 Supuestos y dependencias", "Factores externos, premisas de usuario, infraestructura de red, servicios de terceros (Leaflet, CartoDB, MongoDB, IA) indispensables para la ejecución.")
]

for idx, (dim, desc) in enumerate(rows_data_s):
    row = t_summary.rows[idx + 1]
    bg = "FFFFFF" if idx % 2 == 0 else "F8FAFC"
    for c_i, val in enumerate([dim, desc]):
        c = row.cells[c_i]
        c.width = col_w[c_i]
        set_cell_background(c, bg)
        set_cell_margins(c, top=70, bottom=70, left=80, right=80)
        set_cell_borders(c, top="CBD5E1", bottom="CBD5E1", left="CBD5E1", right="CBD5E1", sz=4)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(val)
        r.font.size = Pt(8.5)
        if c_i == 0:
            r.font.bold = True
            r.font.color.rgb = COLOR_PRIMARY

doc.add_paragraph().paragraph_format.space_after = Pt(12)

# ==========================================
# 1.1 RESTRICCIONES DEL SISTEMA
# ==========================================
add_section_h2(doc, "1.1", "Restricciones del Sistema")

p_res = doc.add_paragraph()
p_res.paragraph_format.space_after = Pt(6)
p_res.add_run(
    "Las restricciones del sistema representan condiciones obligatorias, técnicas y normativas que imponen límites al comportamiento, "
    "a la arquitectura del software y a la operación del negocio. Se clasifican en cuatro categorías críticas:"
)

# 1.1.1 Restricciones Legales y Normativas
doc.add_paragraph().paragraph_format.space_after = Pt(2)
p_sub1 = doc.add_paragraph()
r_sub1 = p_sub1.add_run("A. Restricciones Legales, Sanitarias y Regulatorias (Colombia):")
r_sub1.font.bold = True
r_sub1.font.size = Pt(10.5)
r_sub1.font.color.rgb = COLOR_DARK

add_bullet(doc, "Normativa Farmacéutica INVIMA y Ministerio de Salud:", 
           "La plataforma opera estrictamente como un portal de información y comparación ciudadana. No sustituye la prescripción de profesionales facultados por la Ley 23 de 1981.")

add_bullet(doc, "Medicamentos Bajo Fórmula y de Control Especial:", 
           "Medicamentos que requieren prescripción médica obligatoria (como antibióticos: Ciprofloxacino, Azitromicina) o sustancias psicotrópicas de control especial (como Diazepam 5mg/10mg) se visualizan con fines informativos de precio y disponibilidad, pero no pueden comercializarse ni dispensarse sin la presentación física de la fórmula médica en la farmacia dispensadora.")

add_bullet(doc, "Ley 1581 de 2012 (Habeas Data):", 
           "El almacenamiento y tratamiento de información de los usuarios (nombres, correos electrónicos, historiales de cotización) cumple rigurosamente con los principios de confidencialidad, autorización previa y seguridad de datos personales.")

add_bullet(doc, "Exoneración de Responsabilidad Médica (Disclaimers Obligatorios):", 
           "El Asistente Virtual y el catálogo incluyen advertencias explícitas en cada interacción: FarmaLink no emite diagnósticos médicos, no recomienda automedicación y exhorta a consultar a un médico o químico farmacéutico antes de ingerir cualquier fármaco.")

# 1.1.2 Restricciones Arquitectónicas y Técnicas
doc.add_paragraph().paragraph_format.space_after = Pt(2)
p_sub2 = doc.add_paragraph()
r_sub2 = p_sub2.add_run("B. Restricciones Técnicas y Arquitectónicas:")
r_sub2.font.bold = True
r_sub2.font.size = Pt(10.5)
r_sub2.font.color.rgb = COLOR_DARK

add_bullet(doc, "Arquitectura Híbrida con API Gateway:", 
           "El sistema implementa una arquitectura distribuida basada en un API Gateway centralizado (Node.js/Express en puerto 4000) y un Backend Core (Node.js/Express/TypeScript en puerto 3001). Todo acceso autenticado a recursos críticos requiere la mediación del Gateway mediante validación de tokens JWT.")

add_bullet(doc, "Persistencia en Base de Datos NoSQL Única:", 
           "Los datos residen en una única instancia de MongoDB ('farmalink'), gestionada a través del ODM Mongoose mediante el patrón Singleton (Database.getInstance()). El sistema no cuenta con particionamiento ni sharding distribuido en la versión actual.")

add_bullet(doc, "Procesamiento de Sugerencias en Memoria:", 
           "El módulo de sugerencias predictivas (sugerenciasRouter.ts) filtra en memoria RAM los documentos activos precargados mediante los patrones Factory y Strategy (CoincidenciaParcial, PorCategoria, SimilitudBasica). Esta arquitectura impone un límite de concurrencia cuando el volumen de catálogo supere los miles de registros.")

# 1.1.3 Restricciones Operativas y de Entorno
doc.add_paragraph().paragraph_format.space_after = Pt(2)
p_sub3 = doc.add_paragraph()
r_sub3 = p_sub3.add_run("C. Restricciones Operativas y Geográficas:")
r_sub3.font.bold = True
r_sub3.font.size = Pt(10.5)
r_sub3.font.color.rgb = COLOR_DARK

add_bullet(doc, "Delimitación Geográfica Inicial:", 
           "La geolocalización, coordenadas y sedes de farmacias están calibradas exclusivamente para la ciudad de Bogotá D.C. (coordenadas 4.60971, -74.08175 y sus respectivas localidades). No contempla cobertura en otros municipios de Cundinamarca ni a nivel nacional en esta versión.")

add_bullet(doc, "Compatibilidad de Navegadores:", 
           "La interfaz web Single Page Application (SPA en React 18 / Vite) requiere navegadores modernos con soporte completo para ES6+, WebGL/Canvas para mapas interactivos y CSS Grid/Flexbox (Google Chrome 90+, Mozilla Firefox 88+, Safari 14+, Microsoft Edge 90+).")

doc.add_paragraph().paragraph_format.space_after = Pt(10)

# ==========================================
# 1.2 QUÉ ESTÁ INCLUIDO (IN-SCOPE)
# ==========================================
doc.add_page_break()
add_section_h2(doc, "1.2", "Qué Está Incluido (Alcance Funcional - In-Scope)")

p_inc = doc.add_paragraph()
p_inc.paragraph_format.space_after = Pt(8)
p_inc.add_run(
    "A continuación se detallan los módulos, funcionalidades y capacidades técnicas desarrolladas, "
    "probadas e integradas dentro del alcance de la versión actual de FarmaLink:"
)

# Tabla de módulos incluidos
t_inc = doc.add_table(rows=7, cols=3)
t_inc.alignment = WD_TABLE_ALIGNMENT.CENTER
t_inc.autofit = False

col_wi = [Inches(1.5), Inches(3.6), Inches(1.8)]
headers_inc = ["Módulo del Sistema", "Funcionalidades y Capacidades Incluidas", "Componentes / Archivos"]
for i, h in enumerate(headers_inc):
    c = t_inc.rows[0].cells[i]
    c.width = col_wi[i]
    set_cell_background(c, "0B7DB8")
    set_cell_margins(c, top=80, bottom=80, left=70, right=70)
    set_cell_borders(c, top="0B7DB8", bottom="0B7DB8", left="0B7DB8", right="0B7DB8", sz=4)
    p = c.paragraphs[0]
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(8.5)
    r.font.color.rgb = COLOR_WHITE

modules_data = [
    ("Búsqueda y Sugerencias Predictivas", 
     "• Input de búsqueda con técnica Debounce (300ms) para optimizar el tráfico de red.\n"
     "• Algoritmos inteligentes basados en patrones Factory y Strategy.\n"
     "• Estrategia de coincidencia por nombre comercial, principio activo o categoría médica.\n"
     "• Fallback por similitud básica si no hay coincidencia exacta.", 
     "SearchAutocomplete.tsx\nFiltrosBusqueda.tsx\nsugerenciasRouter.ts\nSugerenciaFactory.ts"),
    
    ("Comparador de Precios en Tiempo Real", 
     "• Tabla comparativa de precios entre farmacias aliadas para un mismo fármaco.\n"
     "• Identificación del precio más bajo, precio promedio y porcentaje de ahorro estimado.\n"
     "• Actualización dinámica vinculada a la colección de precios en MongoDB.", 
     "ProductoDetalle.tsx\nHero.tsx\nFeatures.tsx\n4_precios.js"),
    
    ("Geolocalización y Mapa Interactivo", 
     "• Mapa con Leaflet y mosaicos CartoDB Voyager centrado en Bogotá.\n"
     "• Marcadores personalizados de droguerías con popups informativos.\n"
     "• Visualización de dirección, teléfono de contacto y horarios de atención.\n"
     "• Índices geoespaciales 2dsphere en la colección Farmacias.", 
     "PharmacyMap.tsx\nFarmacia.ts\n2_farmacias.js"),
    
    ("Asistente Virtual con Inteligencia Artificial", 
     "• Interfaz de chat flotante interactiva disponible 24/7.\n"
     "• Reconocimiento semántico con tolerancia a errores tipográficos (fuzzy matching).\n"
     "• Orientación farmacéutica sobre dosis comunes, formas farmacéuticas y sustitutos.\n"
     "• Visualización de productos sugeridos directamente en la conversación.", 
     "AssistantChat.tsx\naiService.ts\nassistant-icon.png"),
    
    ("Panel Administrativo y Control de Acceso (RBAC)", 
     "• Autenticación con JSON Web Tokens (JWT) y cifrado seguro de contraseñas.\n"
     "• Control de acceso basado en 3 roles: Cliente, Farmacéutico y Administrador.\n"
     "• Panel de analítica (Dashboard): Métricas de farmacias, medicamentos y precios.\n"
     "• CRUD administrativo para alta y edición de medicamentos y farmacias.", 
     "Dashboard.tsx\nAdminMedicamentos.tsx\ngateway/index.js\nUser.ts"),
    
    ("Cotizador y Carrito de Presupuesto", 
     "• Selección y agregación de productos a una lista de cotización.\n"
     "• Consolidación del valor estimado de la canasta farmacéutica por droguería.\n"
     "• Visualización de imágenes reales de medicamentos y fallback automático (placeholder.svg).", 
     "CartView.tsx\nProductoDetalle.tsx\npublic/medicamentos/")
]

for idx, (mod, cap, comp) in enumerate(modules_data):
    row = t_inc.rows[idx + 1]
    bg = "FFFFFF" if idx % 2 == 0 else "F8FAFC"
    for c_i, val in enumerate([mod, cap, comp]):
        c = row.cells[c_i]
        c.width = col_wi[c_i]
        set_cell_background(c, bg)
        set_cell_margins(c, top=60, bottom=60, left=70, right=70)
        set_cell_borders(c, top="CBD5E1", bottom="CBD5E1", left="CBD5E1", right="CBD5E1", sz=4)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(val)
        r.font.size = Pt(8)
        if c_i == 0:
            r.font.bold = True
            r.font.color.rgb = COLOR_PRIMARY
        elif c_i == 2:
            r.font.color.rgb = COLOR_MUTED

doc.add_paragraph().paragraph_format.space_after = Pt(12)

# ==========================================
# 1.3 QUÉ QUEDA FUERA (OUT-OF-SCOPE)
# ==========================================
add_section_h2(doc, "1.3", "Qué Queda Fuera (Límites y Exclusiones - Out-of-Scope)")

p_out = doc.add_paragraph()
p_out.paragraph_format.space_after = Pt(6)
p_out.add_run(
    "Para evitar ambigüedades operativas y expectativas desalineadas, se declaran explícitamente "
    "los servicios, procesos y requerimientos que NO forman parte del alcance de esta versión del sistema:"
)

out_scope_items = [
    {
        "title": "Pasarela de Pagos Transaccionales (No E-Commerce Transaccional):",
        "desc": "FarmaLink es una plataforma de comparación, cotización y localización, NO una tienda transaccional directa. No procesa pagos electrónicos vía PSE, tarjetas de crédito/débito, transferencias bancarias ni billeteras digitales (Nequi, Daviplata). El usuario realiza la compra directamente con la farmacia seleccionada."
    },
    {
        "title": "Logística, Flota y Despacho de Domicilios:",
        "desc": "La plataforma no opera mensajería propia, no despacha pedidos a domicilio ni asume custodia física de productos. FarmaLink suministra la ruta hacia la farmacia o el enlace de contacto telefónico para que el cliente coordine con el establecimiento."
    },
    {
        "title": "Validación Digital de Fórmulas Médicas (MIPRES / RIPS / OCR):",
        "desc": "El sistema no está integrado con las plataformas de prescripción del Ministerio de Salud (MIPRES) ni efectúa validación óptica (OCR) de recetas escaneadas. La revisión y retención de fórmulas médicas es responsabilidad indelegable del químico farmacéutico en el punto de dispensación."
    },
    {
        "title": "Diagnóstico y Prescripción Médica Automatizada:",
        "desc": "El Asistente Virtual con IA tiene estrictamente un rol de orientación informativa sobre nombres comerciales, principios activos y educación farmacéutica general. No realiza diagnósticos, no formula tratamientos ni sustituye el criterio médico."
    },
    {
        "title": "Sincronización en Tiempo Real con ERPs / Inventarios de Farmacias:",
        "desc": "No se incluyen conectores en vivo hacia sistemas ERP propietarios de cadenas farmacéuticas (SAP, Oracle, SIIGO, etc.). La actualización de precios y disponibilidad se realiza mediante carga periódica del farmacéutico o scripts de ingesta controlada."
    },
    {
        "title": "Cobertura Fuera del Distrito Capital de Bogotá:",
        "desc": "No se incluye soporte para farmacias ni inventarios de ciudades fuera de Bogotá D.C. en esta fase de lanzamiento."
    }
]

for item in out_scope_items:
    add_bullet(doc, item["title"], item["desc"])

doc.add_paragraph().paragraph_format.space_after = Pt(10)

# ==========================================
# 1.4 SUPUESTOS Y DEPENDENCIAS
# ==========================================
doc.add_page_break()
add_section_h2(doc, "1.4", "Supuestos y Dependencias")

p_dep = doc.add_paragraph()
p_dep.paragraph_format.space_after = Pt(6)
p_dep.add_run(
    "El éxito de la implantación, la estabilidad del servicio y la precisión de la información dependen "
    "de supuestos operativos y de la disponibilidad de componentes tecnológicos de terceros:"
)

# 1.4.1 Supuestos de Negocio y de Usuario
p_sup_title = doc.add_paragraph()
r_supt = p_sup_title.add_run("A. Supuestos del Negocio y Operación:")
r_supt.font.bold = True
r_supt.font.size = Pt(10.5)
r_supt.font.color.rgb = COLOR_DARK

add_bullet(doc, "Disponibilidad y Conectividad del Usuario:", 
           "Se asume que los ciudadanos cuentan con dispositivos con conexión a internet estable y navegadores web compatibles para interactuar con la plataforma y cargar mapas interactivos.")

add_bullet(doc, "Veracidad y Actualización de Precios:", 
           "Se asume que las farmacias afiliadas reportan con honestidad y puntualidad sus listas de precios oficiales, asumiendo la responsabilidad comercial ante discrepancias en el punto de venta.")

add_bullet(doc, "Registro Sanitario INVIMA:", 
           "Se asume que todos los productos catalogados cuentan con registro sanitario vigente y cumplen los estándares de farmacovigilancia exigidos en Colombia.")

# 1.4.2 Dependencias Tecnológicas y de Terceros
p_dept_title = doc.add_paragraph()
p_dept_title.paragraph_format.space_before = Pt(6)
r_dept = p_dept_title.add_run("B. Dependencias Tecnológicas y Servicios Externos:")
r_dept.font.bold = True
r_dept.font.size = Pt(10.5)
r_dept.font.color.rgb = COLOR_DARK

t_dep = doc.add_table(rows=6, cols=3)
t_dep.alignment = WD_TABLE_ALIGNMENT.CENTER
t_dep.autofit = False

col_wd = [Inches(1.6), Inches(1.8), Inches(3.5)]
headers_dep = ["Componente / Proveedor", "Naturaleza de la Dependencia", "Impacto y Estrategia de Mitigación"]
for i, h in enumerate(headers_dep):
    c = t_dep.rows[0].cells[i]
    c.width = col_wd[i]
    set_cell_background(c, "0B7DB8")
    set_cell_margins(c, top=80, bottom=80, left=70, right=70)
    set_cell_borders(c, top="0B7DB8", bottom="0B7DB8", left="0B7DB8", right="0B7DB8", sz=4)
    p = c.paragraphs[0]
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(8.5)
    r.font.color.rgb = COLOR_WHITE

deps_data = [
    ("MongoDB (NoSQL Engine)", "Base de Datos Principal", 
     "Almacena usuarios, farmacias, medicamentos y precios. Requiere soporte para índices 2dsphere. Si cae el motor, la plataforma no puede consultar catálogo."),
    
    ("Leaflet & CartoDB Voyager", "Mosaicos y Mapas (CDN)", 
     "Provee capas geográficas y marcadores de farmacias. Requiere acceso HTTPS a cdnjs y basemaps.cartocdn.com. Si no hay conexión, se muestra vista de lista."),
    
    ("API Gateway (Node.js/Express)", "Capa de Enrutamiento y Auth", 
     "Valida tokens JWT y protege el backend. Si el Gateway en puerto 4000 está inactivo, las solicitudes administrativas y de login se interrumpen."),
    
    ("Node.js Runtime & TypeScript", "Entorno de Ejecución Backend", 
     "El servidor core opera sobre Node v18+ y TypeScript compilado. Requiere variables de entorno configuradas (PORT, MONGODB_URI, JWT_SECRET)."),
    
    ("Motor de IA / LLM Semántico", "Servicio Asistente Virtual", 
     "Procesa lenguaje natural en AssistantChat.tsx. En caso de latencia o desconexión del LLM, el sistema activa respuestas determinísticas de respaldo.")
]

for idx, (comp, nat, imp) in enumerate(deps_data):
    row = t_dep.rows[idx + 1]
    bg = "FFFFFF" if idx % 2 == 0 else "F8FAFC"
    for c_i, val in enumerate([comp, nat, imp]):
        c = row.cells[c_i]
        c.width = col_wd[c_i]
        set_cell_background(c, bg)
        set_cell_margins(c, top=60, bottom=60, left=70, right=70)
        set_cell_borders(c, top="CBD5E1", bottom="CBD5E1", left="CBD5E1", right="CBD5E1", sz=4)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(val)
        r.font.size = Pt(8)
        if c_i == 0:
            r.font.bold = True
            r.font.color.rgb = COLOR_PRIMARY
        elif c_i == 1:
            r.font.bold = True
            r.font.color.rgb = COLOR_DARK

doc.add_paragraph().paragraph_format.space_after = Pt(14)

# ==========================================
# CONCLUSIÓN Y MATRIZ DE CONFORMIDAD
# ==========================================
add_callout(
    doc,
    "Conclusión de Conformidad del Alcance",
    "La formalización de este documento asegura que el equipo de desarrollo, las directivas de FarmaLink S.A.S., "
    "los farmacéuticos afiliados y los usuarios finales compartan una comprensión idéntica sobre las capacidades reales del sistema. "
    "Cualquier modificación o ampliación de las capacidades aquí descritas (ej. incorporación de pagos digitales o cobertura nacional) "
    "deberá tramitarse mediante un requerimiento formal de cambio y una nueva fase de desarrollo.",
    border_color="059669",
    bg_color="F0FDF4",
    title_color=COLOR_SUCCESS
)

# Pie de firma
p_sign = doc.add_paragraph()
p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
p_sign.paragraph_format.space_before = Pt(16)
r_sig1 = p_sign.add_run("FARMALINK S.A.S. — Dirección de Tecnología e Innovación\n")
r_sig1.font.bold = True
r_sig1.font.size = Pt(9.5)
r_sig1.font.color.rgb = COLOR_PRIMARY

r_sig2 = p_sign.add_run("Comité de Arquitectura de Software y Aseguramiento de Calidad (QA)")
r_sig2.font.size = Pt(8.5)
r_sig2.font.color.rgb = COLOR_MUTED

print(f"Guardando documento de Alcance en: {OUTPUT_DOCX}")
doc.save(OUTPUT_DOCX)
print("¡Documento de Alcance y Restricciones generado con éxito!")
