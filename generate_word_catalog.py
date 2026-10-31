import os
import sys
import resvg_py
from PIL import Image
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

BASE_DIR = r"c:\Users\crack\Farmalink-SAS"
OUTPUT_DOCX = os.path.join(BASE_DIR, "Catalogo_Imagenes_FarmaLink.docx")
TEMP_IMG_DIR = os.path.join(BASE_DIR, "scratch_images")
os.makedirs(TEMP_IMG_DIR, exist_ok=True)

# FarmaLink Brand Palette
COLOR_PRIMARY_HEX = "0B7DB8"      # FarmaLink Blue
COLOR_DARK_HEX = "0F172A"         # Slate 900
COLOR_SECONDARY_HEX = "0369A1"    # Dark Cyan / Blue
COLOR_LIGHT_BG_HEX = "F8FAFC"     # Slate 50
COLOR_CARD_BORDER_HEX = "E2E8F0"  # Slate 200
COLOR_MUTED_HEX = "64748B"        # Slate 500

COLOR_PRIMARY = RGBColor(11, 125, 184)
COLOR_SECONDARY = RGBColor(3, 105, 161)
COLOR_DARK = RGBColor(15, 23, 42)
COLOR_MUTED = RGBColor(100, 116, 139)
COLOR_WHITE = RGBColor(255, 255, 255)

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

def set_cell_borders(cell, top="E2E8F0", bottom="E2E8F0", left="E2E8F0", right="E2E8F0", sz=4):
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

def set_no_borders(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)

def render_svg_to_png(svg_path, out_png_path, width=400):
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    png_bytes = resvg_py.svg_to_bytes(svg_content)
    with open(out_png_path, 'wb') as f:
        f.write(png_bytes)
    return out_png_path

def get_image_info(path):
    if not os.path.exists(path):
        return None
    size_bytes = os.path.getsize(path)
    size_kb = size_bytes / 1024
    if path.lower().endswith('.svg'):
        return {
            'path': path,
            'size_kb': size_kb,
            'dims': 'Vectorial (SVG)',
            'format': 'SVG',
            'is_svg': True
        }
    try:
        im = Image.open(path)
        w, h = im.size
        fmt = im.format or os.path.splitext(path)[1][1:].upper()
        return {
            'path': path,
            'size_kb': size_kb,
            'dims': f"{w} x {h} px",
            'format': fmt,
            'is_svg': False,
            'aspect': w / h if h > 0 else 1.0
        }
    except Exception:
        return {
            'path': path,
            'size_kb': size_kb,
            'dims': 'N/A',
            'format': os.path.splitext(path)[1][1:].upper(),
            'is_svg': False,
            'aspect': 1.0
        }

print("Iniciando generación del catálogo Word...")
doc = Document()

# Configurar márgenes estándar de 1 pulgada
sections = doc.sections
for section in sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

# Configurar estilo Normal
style_normal = doc.styles['Normal']
font = style_normal.font
font.name = 'Segoe UI'
font.size = Pt(10.5)
font.color.rgb = COLOR_DARK

def add_header_badge(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text.upper())
    run.font.name = 'Segoe UI'
    run.font.size = Pt(9)
    run.font.bold = True
    run.font.color.rgb = COLOR_PRIMARY
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)

def add_section_title(doc, number, title):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(18)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    run_num = h.add_run(f"{number}. ")
    run_num.font.name = 'Segoe UI'
    run_num.font.size = Pt(15)
    run_num.font.bold = True
    run_num.font.color.rgb = COLOR_PRIMARY
    
    run_title = h.add_run(title)
    run_title.font.name = 'Segoe UI'
    run_title.font.size = Pt(15)
    run_title.font.bold = True
    run_title.font.color.rgb = COLOR_DARK

def add_section_subtitle(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run(text)
    run.font.name = 'Segoe UI'
    run.font.size = Pt(10)
    run.font.color.rgb = COLOR_MUTED

# ==========================================
# PORTADA / ENCABEZADO PRINCIPAL
# ==========================================
cover_table = doc.add_table(rows=1, cols=1)
cover_table.alignment = WD_TABLE_ALIGNMENT.CENTER
c_cell = cover_table.rows[0].cells[0]
c_cell.width = Inches(6.9)
set_cell_background(c_cell, "F0F9FF")
set_cell_margins(c_cell, top=260, bottom=260, left=300, right=300)
set_cell_borders(c_cell, top="0B7DB8", bottom="0B7DB8", left="0B7DB8", right="0B7DB8", sz=16)

cp1 = c_cell.paragraphs[0]
cp1.alignment = WD_ALIGN_PARAGRAPH.CENTER
cp1.paragraph_format.space_after = Pt(6)
run_logo_text = cp1.add_run("FARMALINK S.A.S.")
run_logo_text.font.size = Pt(22)
run_logo_text.font.bold = True
run_logo_text.font.color.rgb = COLOR_PRIMARY

cp2 = c_cell.add_paragraph()
cp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
cp2.paragraph_format.space_after = Pt(8)
run_main_title = cp2.add_run("Catálogo Oficial de Recursos Visuales e Imágenes")
run_main_title.font.size = Pt(16)
run_main_title.font.bold = True
run_main_title.font.color.rgb = COLOR_DARK

cp3 = c_cell.add_paragraph()
cp3.alignment = WD_ALIGN_PARAGRAPH.CENTER
cp3.paragraph_format.space_after = Pt(14)
run_sub = cp3.add_run("Inventario técnico, visualización en alta definición y guía de implementación de todos los activos gráficos de la plataforma web")
run_sub.font.size = Pt(10.5)
run_sub.font.color.rgb = COLOR_MUTED

# Insignias de la portada
cp4 = c_cell.add_paragraph()
cp4.alignment = WD_ALIGN_PARAGRAPH.CENTER
cp4.paragraph_format.space_after = Pt(0)
run_meta = cp4.add_run("📍 Bogotá, Colombia   |   📅 Septiembre 2026   |   📊 48 Activos Locales + Recursos CDN   |   ⚡ Versión 1.0")
run_meta.font.size = Pt(8.5)
run_meta.font.bold = True
run_meta.font.color.rgb = COLOR_PRIMARY

doc.add_paragraph().paragraph_format.space_after = Pt(12)

# ==========================================
# 1. IDENTIDAD DE MARCA Y ASISTENTE IA
# ==========================================
add_section_title(doc, "1", "Identidad Corporativa y Marca (Branding)")
add_section_subtitle(doc, "Recursos gráficos principales que definen la identidad visual de FarmaLink y la interfaz del asistente inteligente.")

brand_items = [
    {
        "title": "Logotipo Principal Oficial — FarmaLink",
        "file": "logo-farmalink.png",
        "path": os.path.join(BASE_DIR, "src", "assets", "logo-farmalink.png"),
        "display_width": Inches(2.6),
        "usage": "Encabezado principal (Header.tsx), pie de página (Footer.tsx), favicon de la aplicación y metadatos SEO/OpenGraph (index.html).",
        "description": "Isotipo y logotipo combinados con cruz médica estilizada, ondas de enlace digital y tipografía moderna en azul clínico."
    },
    {
        "title": "Ícono del Asistente Virtual IA",
        "file": "assistant-icon.png",
        "path": os.path.join(BASE_DIR, "public", "assistant-icon.png"),
        "display_width": Inches(2.4),
        "usage": "Botón flotante del Asistente Virtual (AssistantChat.tsx), avatar en el chat conversacional y cabecera del modal de asistencia.",
        "description": "Robot estilizado con cruz farmacéutica y expresión amigable, diseñado para transmitir confianza y tecnología avanzada a los usuarios."
    }
]

for item in brand_items:
    info = get_image_info(item["path"])
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    
    cell_img = t.rows[0].cells[0]
    cell_img.width = Inches(2.8)
    cell_info = t.rows[0].cells[1]
    cell_info.width = Inches(4.1)
    
    set_cell_background(cell_img, "F8FAFC")
    set_cell_borders(cell_img, top="CBD5E1", bottom="CBD5E1", left="CBD5E1", right="E2E8F0", sz=6)
    set_cell_margins(cell_img, top=140, bottom=140, left=140, right=140)
    cell_img.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    
    # Insert image
    p_img = cell_img.paragraphs[0]
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if os.path.exists(item["path"]):
        p_img.add_run().add_picture(item["path"], width=item["display_width"])
    
    set_cell_background(cell_info, "FFFFFF")
    set_cell_borders(cell_info, top="CBD5E1", bottom="CBD5E1", left="E2E8F0", right="CBD5E1", sz=6)
    set_cell_margins(cell_info, top=160, bottom=160, left=180, right=180)
    
    p_info = cell_info.paragraphs[0]
    p_info.paragraph_format.space_after = Pt(4)
    run_t = p_info.add_run(item["title"])
    run_t.font.size = Pt(12)
    run_t.font.bold = True
    run_t.font.color.rgb = COLOR_PRIMARY
    
    p_desc = cell_info.add_paragraph()
    p_desc.paragraph_format.space_after = Pt(8)
    run_d = p_desc.add_run(item["description"])
    run_d.font.size = Pt(9.5)
    
    # Specs table/bullets
    p_specs = cell_info.add_paragraph()
    p_specs.paragraph_format.space_after = Pt(2)
    p_specs.paragraph_format.line_spacing = 1.15
    
    def add_meta_line(p, label, val):
        r1 = p.add_run(f"• {label}: ")
        r1.font.bold = True
        r1.font.size = Pt(9)
        r1.font.color.rgb = COLOR_DARK
        r2 = p.add_run(f"{val}\n")
        r2.font.size = Pt(9)
        r2.font.color.rgb = COLOR_MUTED
    
    add_meta_line(p_specs, "Archivo", item["file"])
    add_meta_line(p_specs, "Dimensiones", info['dims'] if info else "N/A")
    add_meta_line(p_specs, "Peso en disco", f"{info['size_kb']:.1f} KB" if info else "N/A")
    add_meta_line(p_specs, "Formato", info['format'] if info else "PNG")
    add_meta_line(p_specs, "Implementación", item["usage"])
    
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

# ==========================================
# 2. ÍCONOS DE NAVEGACIÓN Y CARACTERÍSTICAS
# ==========================================
add_section_title(doc, "2", "Íconos de Navegación y Funcionalidades")
add_section_subtitle(doc, "Elementos visuales ilustrativos para las secciones Hero y Features de la página principal.")

feature_icons = [
    {
        "title": "Búsqueda Inteligente",
        "file": "icon-busqueda.png",
        "path": os.path.join(BASE_DIR, "src", "assets", "icon-busqueda.png"),
        "width": Inches(1.5),
        "usage": "Hero.tsx y Features.tsx",
        "desc": "Representa el motor de búsqueda por nombre comercial, principio activo o categoría terapéutica."
    },
    {
        "title": "Comparación de Precios",
        "file": "icon-precios.png",
        "path": os.path.join(BASE_DIR, "src", "assets", "icon-precios.png"),
        "width": Inches(1.5),
        "usage": "Hero.tsx y Features.tsx",
        "desc": "Simboliza la comparativa de tarifas entre droguerías para identificar el máximo ahorro disponible."
    },
    {
        "title": "Mapa de Farmacias",
        "file": "icon-mapa.png",
        "path": os.path.join(BASE_DIR, "src", "assets", "icon-mapa.png"),
        "width": Inches(1.5),
        "usage": "Hero.tsx y Features.tsx",
        "desc": "Geolocalización de droguerías aliadas en tiempo real con indicaciones de cercanía y horarios."
    },
    {
        "title": "Recomendaciones con IA",
        "file": "icon-ia.png",
        "path": os.path.join(BASE_DIR, "src", "assets", "icon-ia.png"),
        "width": Inches(1.5),
        "usage": "Hero.tsx y Features.tsx",
        "desc": "Asesoramiento virtual impulsado por IA para resolver dudas y orientar opciones equivalentes."
    }
]

# Grid 2x2 para los íconos de features
t_feat = doc.add_table(rows=2, cols=2)
t_feat.alignment = WD_TABLE_ALIGNMENT.CENTER
t_feat.autofit = False

for idx, item in enumerate(feature_icons):
    r_idx = idx // 2
    c_idx = idx % 2
    cell = t_feat.rows[r_idx].cells[c_idx]
    cell.width = Inches(3.45)
    set_cell_background(cell, "FFFFFF")
    set_cell_borders(cell, top="E2E8F0", bottom="E2E8F0", left="E2E8F0", right="E2E8F0", sz=6)
    set_cell_margins(cell, top=140, bottom=140, left=140, right=140)
    
    info = get_image_info(item["path"])
    
    # Imagen centrada
    p_img = cell.paragraphs[0]
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_after = Pt(6)
    if os.path.exists(item["path"]):
        p_img.add_run().add_picture(item["path"], width=item["width"])
    
    # Título
    p_txt = cell.add_paragraph()
    p_txt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_txt.paragraph_format.space_after = Pt(2)
    run_ti = p_txt.add_run(item["title"])
    run_ti.font.size = Pt(11)
    run_ti.font.bold = True
    run_ti.font.color.rgb = COLOR_PRIMARY
    
    # Descripción
    p_d = cell.add_paragraph()
    p_d.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_d.paragraph_format.space_after = Pt(6)
    run_de = p_d.add_run(item["desc"])
    run_de.font.size = Pt(8.5)
    run_de.font.color.rgb = COLOR_MUTED
    
    # Meta
    p_m = cell.add_paragraph()
    p_m.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_m.paragraph_format.space_after = Pt(0)
    run_me = p_m.add_run(f"Archivo: {item['file']} ({info['dims']}, {info['size_kb']:.1f} KB)")
    run_me.font.size = Pt(8)
    run_me.font.bold = True
    run_me.font.color.rgb = COLOR_DARK

doc.add_paragraph().paragraph_format.space_after = Pt(8)

# ==========================================
# 3. ÍCONOS DEL PANEL DE CONTROL (DASHBOARD)
# ==========================================
add_section_title(doc, "3", "Métricas y Estadísticas (Dashboard Administrativo)")
add_section_subtitle(doc, "Activos visuales para las tarjetas de analítica y estadísticas clave del sistema (Dashboard.tsx).")

dash_icons = [
    {
        "title": "Red de Farmacias Afiliadas",
        "file": "icon-dash-farmacias.png",
        "path": os.path.join(BASE_DIR, "src", "assets", "icon-dash-farmacias.png"),
        "width": Inches(1.3),
        "desc": "Representa el censo y control de farmacias geolocalizadas registradas en el sistema."
    },
    {
        "title": "Catálogo de Medicamentos",
        "file": "icon-dash-medicamentos.png",
        "path": os.path.join(BASE_DIR, "src", "assets", "icon-dash-medicamentos.png"),
        "width": Inches(1.3),
        "desc": "Control del inventario maestro de medicamentos, principios activos y laboratorios."
    },
    {
        "title": "Actualizaciones de Precios",
        "file": "icon-dash-precios.png",
        "path": os.path.join(BASE_DIR, "src", "assets", "icon-dash-precios.png"),
        "width": Inches(1.3),
        "desc": "Seguimiento al histórico y fluctuaciones de precios reportados en Bogotá."
    }
]

t_dash = doc.add_table(rows=1, cols=3)
t_dash.alignment = WD_TABLE_ALIGNMENT.CENTER
t_dash.autofit = False

for idx, item in enumerate(dash_icons):
    cell = t_dash.rows[0].cells[idx]
    cell.width = Inches(2.3)
    set_cell_background(cell, "F8FAFC")
    set_cell_borders(cell, top="E2E8F0", bottom="E2E8F0", left="E2E8F0", right="E2E8F0", sz=6)
    set_cell_margins(cell, top=140, bottom=140, left=120, right=120)
    
    info = get_image_info(item["path"])
    
    p_img = cell.paragraphs[0]
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_after = Pt(4)
    if os.path.exists(item["path"]):
        p_img.add_run().add_picture(item["path"], width=item["width"])
    
    p_txt = cell.add_paragraph()
    p_txt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_txt.paragraph_format.space_after = Pt(2)
    r_ti = p_txt.add_run(item["title"])
    r_ti.font.size = Pt(10)
    r_ti.font.bold = True
    r_ti.font.color.rgb = COLOR_PRIMARY
    
    p_desc = cell.add_paragraph()
    p_desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_desc.paragraph_format.space_after = Pt(4)
    r_de = p_desc.add_run(item["desc"])
    r_de.font.size = Pt(8.5)
    r_de.font.color.rgb = COLOR_MUTED
    
    p_sub = cell.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(0)
    r_sb = p_sub.add_run(f"{item['file']}\n{info['dims']} | {info['size_kb']:.1f} KB")
    r_sb.font.size = Pt(7.5)
    r_sb.font.bold = True
    r_sb.font.color.rgb = COLOR_DARK

doc.add_paragraph().paragraph_format.space_after = Pt(12)

# ==========================================
# 4. DIAPOSITIVAS DEL CARRUSEL (SLIDER)
# ==========================================
doc.add_page_break()
add_section_title(doc, "4", "Banners y Diapositivas del Carrusel Principal")
add_section_subtitle(doc, "Imágenes panorámicas de alta resolución integradas en el carrusel interactivo de la página de inicio (Slider.tsx).")

slides = [
    {
        "num": "Slide 1",
        "title": "Comparador de precios en tiempo real",
        "file": "slide-1-compara-precios.png",
        "path": os.path.join(BASE_DIR, "src", "assets", "slide-1-compara-precios.png"),
        "caption": "Destaca la capacidad de consultar más de 200 medicamentos en droguerías de Bogotá y encontrar la mejor oferta con un solo clic."
    },
    {
        "num": "Slide 2",
        "title": "Asistente Virtual con Inteligencia Artificial",
        "file": "slide-2-recomendaciones-ia.png",
        "path": os.path.join(BASE_DIR, "src", "assets", "slide-2-recomendaciones-ia.png"),
        "caption": "Promociona el soporte 24/7 de IA para orientar al ciudadano con información verificada de principios activos y recetas médicas."
    },
    {
        "num": "Slide 3",
        "title": "Encuentra farmacias cercanas a ti",
        "file": "slide-3-encuentra-farmacias.png",
        "path": os.path.join(BASE_DIR, "src", "assets", "slide-3-encuentra-farmacias.png"),
        "caption": "Ilustra el mapa interactivo de cobertura en todas las localidades de Bogotá con distancias y rutas sugeridas."
    },
    {
        "num": "Slide 4",
        "title": "Ahorra en cada compra de medicamentos",
        "file": "slide-4-ahorro.png",
        "path": os.path.join(BASE_DIR, "src", "assets", "slide-4-ahorro.png"),
        "caption": "Comunica el impacto en el bolsillo de las familias, con ahorros promedio de hasta $15.000 por mes mediante la comparativa informada."
    },
    {
        "num": "Slide 5",
        "title": "Red de farmacias aliadas en Bogotá",
        "file": "slide-5-farmacias-aliadas.png",
        "path": os.path.join(BASE_DIR, "src", "assets", "slide-5-farmacias-aliadas.png"),
        "caption": "Presenta el ecosistema de droguerías de barrio y grandes cadenas conectadas a la red de precios FarmaLink."
    }
]

for s in slides:
    info = get_image_info(s["path"])
    
    st = doc.add_table(rows=2, cols=1)
    st.alignment = WD_TABLE_ALIGNMENT.CENTER
    st.autofit = False
    
    c_banner = st.rows[0].cells[0]
    c_banner.width = Inches(6.8)
    set_cell_background(c_banner, "0F172A")
    set_cell_margins(c_banner, top=100, bottom=100, left=100, right=100)
    set_cell_borders(c_banner, top="0B7DB8", bottom="0B7DB8", left="0B7DB8", right="0B7DB8", sz=6)
    
    p_bimg = c_banner.paragraphs[0]
    p_bimg.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if os.path.exists(s["path"]):
        p_bimg.add_run().add_picture(s["path"], width=Inches(6.4))
    
    c_meta = st.rows[1].cells[0]
    c_meta.width = Inches(6.8)
    set_cell_background(c_meta, "F8FAFC")
    set_cell_margins(c_meta, top=100, bottom=120, left=140, right=140)
    set_cell_borders(c_meta, top="E2E8F0", bottom="E2E8F0", left="E2E8F0", right="E2E8F0", sz=6)
    
    p_minfo = c_meta.paragraphs[0]
    p_minfo.paragraph_format.space_after = Pt(2)
    run_snum = p_minfo.add_run(f"{s['num'].upper()} — {s['title']}\n")
    run_snum.font.bold = True
    run_snum.font.size = Pt(11)
    run_snum.font.color.rgb = COLOR_PRIMARY
    
    run_scap = p_minfo.add_run(f"{s['caption']}\n")
    run_scap.font.size = Pt(9.5)
    run_scap.font.color.rgb = COLOR_DARK
    
    run_sdet = p_minfo.add_run(f"📁 Archivo: {s['file']}   |   📐 Resolución: {info['dims']}   |   ⚖️ Peso: {info['size_kb']:.1f} KB")
    run_sdet.font.size = Pt(8.5)
    run_sdet.font.color.rgb = COLOR_MUTED
    run_sdet.font.bold = True
    
    doc.add_paragraph().paragraph_format.space_after = Pt(10)

# ==========================================
# 5. CATÁLOGO MAESTRO DE MEDICAMENTOS (30)
# ==========================================
doc.add_page_break()
add_section_title(doc, "5", "Catálogo Maestro de Medicamentos (30 Productos Farmacéuticos)")
add_section_subtitle(doc, "Imágenes de envases y blísteres asociadas a los productos del inventario (public/medicamentos/{id}.png).")

# Placeholder SVG de respaldo
ph_svg = os.path.join(BASE_DIR, "public", "medicamentos", "placeholder.svg")
ph_png = os.path.join(TEMP_IMG_DIR, "placeholder.png")
if os.path.exists(ph_svg):
    render_svg_to_png(ph_svg, ph_png, width=300)

ph_table = doc.add_table(rows=1, cols=2)
ph_table.alignment = WD_TABLE_ALIGNMENT.CENTER
c_ph_img = ph_table.rows[0].cells[0]
c_ph_img.width = Inches(1.8)
c_ph_info = ph_table.rows[0].cells[1]
c_ph_info.width = Inches(5.0)

set_cell_background(c_ph_img, "F0F9FF")
set_cell_borders(c_ph_img, top="0B7DB8", bottom="0B7DB8", left="0B7DB8", right="E2E8F0", sz=6)
set_cell_margins(c_ph_img, top=100, bottom=100, left=100, right=100)
c_ph_img.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

p_phi = c_ph_img.paragraphs[0]
p_phi.alignment = WD_ALIGN_PARAGRAPH.CENTER
if os.path.exists(ph_png):
    p_phi.add_run().add_picture(ph_png, width=Inches(1.3))

set_cell_background(c_ph_info, "FFFFFF")
set_cell_borders(c_ph_info, top="0B7DB8", bottom="0B7DB8", left="E2E8F0", right="0B7DB8", sz=6)
set_cell_margins(c_ph_info, top=100, bottom=100, left=140, right=140)

p_phd = c_ph_info.paragraphs[0]
p_phd.paragraph_format.space_after = Pt(2)
r_pht = p_phd.add_run("Imagen de Respaldo por Defecto (Fallback Placeholder)\n")
r_pht.font.bold = True
r_pht.font.size = Pt(10.5)
r_pht.font.color.rgb = COLOR_PRIMARY

r_phdesc = p_phd.add_run("Archivo: placeholder.svg | Ubicación: public/medicamentos/placeholder.svg (535 bytes)\n"
                         "Se renderiza automáticamente en la vista de detalle (ProductoDetalle.tsx), en el carrito de compras (CartView.tsx) "
                         "y en el chat inteligente (AssistantChat.tsx) cuando un producto no tiene foto física asignada o falla la carga.")
r_phdesc.font.size = Pt(8.5)
r_phdesc.font.color.rgb = COLOR_MUTED

doc.add_paragraph().paragraph_format.space_after = Pt(10)

# Lista completa de los 30 medicamentos extraídos de la base de datos seed
medicamentos_data = [
    {"id": 1, "name": "Acetaminofén 500mg", "lab": "Bayer S.A.", "cat": "Analgésicos", "desc": "Analgésico y antipirético. Alivia el dolor leve a moderado y reduce la fiebre."},
    {"id": 2, "name": "Acetaminofén 1000mg", "lab": "Bayer S.A.", "cat": "Analgésicos", "desc": "Analgésico de alta dosis indicado para episodios de dolor intenso o agudo."},
    {"id": 3, "name": "Amoxicilina 500mg Cápsulas", "lab": "Roche S.A.", "cat": "Antibióticos", "desc": "Antibiótico bactericida de amplio espectro perteneciente al grupo de las penicilinas."},
    {"id": 4, "name": "Amoxicilina 250mg Suspensión", "lab": "Roche S.A.", "cat": "Antibióticos", "desc": "Antibiótico en formulación de suspensión oral pediátrica para infecciones respiratorias."},
    {"id": 5, "name": "Ibuprofeno 400mg", "lab": "Pfizer Colombia", "cat": "Antiinflamatorios", "desc": "Antiinflamatorio no esteroideo (AINE) con acción analgésica y antipirética rápida."},
    {"id": 6, "name": "Ibuprofeno 600mg", "lab": "Pfizer Colombia", "cat": "Antiinflamatorios", "desc": "Antiinflamatorio de concentración media para procesos inflamatorios y dolores musculares."},
    {"id": 7, "name": "Loratadina 10mg", "lab": "Merck Colombia", "cat": "Antialérgicos", "desc": "Antihistamínico de segunda generación sin efecto sedante para rinitis y urticaria."},
    {"id": 8, "name": "Loratadina 5mg/5ml Jarabe", "lab": "Merck Colombia", "cat": "Antialérgicos", "desc": "Antihistamínico pediátrico líquido para el alivio de alergias estacionales e irritaciones."},
    {"id": 9, "name": "Omeprazol 20mg", "lab": "AstraZeneca", "cat": "Gastrointestinales", "desc": "Inhibidor de la bomba de protones para el tratamiento del reflujo gástrico y gastritis."},
    {"id": 10, "name": "Omeprazol 40mg", "lab": "AstraZeneca", "cat": "Gastrointestinales", "desc": "Inhibidor de bomba de protones de alta potencia para úlceras gástricas y esofagitis severa."},
    {"id": 11, "name": "Metformina 500mg", "lab": "Novartis", "cat": "Antidiabéticos", "desc": "Normoglucemiante oral de primera línea para el control de la diabetes mellitus tipo 2."},
    {"id": 12, "name": "Metformina 850mg", "lab": "Novartis", "cat": "Antidiabéticos", "desc": "Antidiabético oral de concentración reforzada para el control glucémico sostenido."},
    {"id": 13, "name": "Losartán 50mg", "lab": "Boehringer Ingelheim", "cat": "Cardiovasculares", "desc": "Antihipertensivo antagonista de los receptores de angiotensina II (ARA II)."},
    {"id": 14, "name": "Losartán 100mg", "lab": "Boehringer Ingelheim", "cat": "Cardiovasculares", "desc": "Antihipertensivo de alta concentración para pacientes con hipertensión arterial severa."},
    {"id": 15, "name": "Atorvastatina 20mg", "lab": "Pfizer Colombia", "cat": "Cardiovasculares", "desc": "Estatina hipolipemiante para la reducción del colesterol LDL y triglicéridos en sangre."},
    {"id": 16, "name": "Atorvastatina 40mg", "lab": "Pfizer Colombia", "cat": "Cardiovasculares", "desc": "Estatina de alta potencia para prevención secundaria de eventos coronarios agudos."},
    {"id": 17, "name": "Salbutamol 100mcg Inhalador", "lab": "GlaxoSmithKline", "cat": "Respiratorios", "desc": "Broncodilatador de acción rápida en aerosol para el alivio agudo del asma y EPOC."},
    {"id": 18, "name": "Salbutamol 2mg/5ml Jarabe", "lab": "GlaxoSmithKline", "cat": "Respiratorios", "desc": "Broncodilatador sistémico en jarabe para afecciones obstructivas de vías aéreas en niños."},
    {"id": 19, "name": "Prednisona 5mg", "lab": "Bayer S.A.", "cat": "Corticosteroides", "desc": "Glucocorticoide sintético con potente actividad antiinflamatoria e inmunosupresora."},
    {"id": 20, "name": "Prednisona 50mg", "lab": "Bayer S.A.", "cat": "Corticosteroides", "desc": "Corticosteroide de alta concentración para choque inflamatorio, brotes agudos y autoinmunes."},
    {"id": 21, "name": "Diazepam 5mg", "lab": "Roche S.A.", "cat": "Psicofármacos", "desc": "Benzodiazepina de acción prolongada con propiedades ansiolíticas, sedantes y miorrelajantes."},
    {"id": 22, "name": "Diazepam 10mg", "lab": "Roche S.A.", "cat": "Psicofármacos", "desc": "Ansiolítico y anticonvulsivante de alta potencia bajo prescripción médica controlada."},
    {"id": 23, "name": "Ciprofloxacino 500mg", "lab": "Bayer S.A.", "cat": "Antibióticos", "desc": "Fluoroquinolona antibacteriana de amplio espectro para infecciones urinarias y digestivas."},
    {"id": 24, "name": "Azitromicina 500mg", "lab": "Pfizer Colombia", "cat": "Antibióticos", "desc": "Antibiótico macrólido de toma diaria corta para infecciones de vías respiratorias y piel."},
    {"id": 25, "name": "Naproxeno 500mg", "lab": "AstraZeneca", "cat": "Antiinflamatorios", "desc": "Antiinflamatorio no esteroideo de acción analgésica prolongada para artritis y dolores."},
    {"id": 26, "name": "Ranitidina 150mg", "lab": "Boehringer Ingelheim", "cat": "Gastrointestinales", "desc": "Antagonista H2 reductor de la secreción ácida gástrica para alivio del ardor estomacal."},
    {"id": 27, "name": "Enalapril 10mg", "lab": "Novartis", "cat": "Cardiovasculares", "desc": "Inhibidor de la enzima convertidora de angiotensina (IECA) para hipertensión e insuficiencia."},
    {"id": 28, "name": "Enalapril 20mg", "lab": "Novartis", "cat": "Cardiovasculares", "desc": "Inhibidor de ECA de dosificación reforzada para protección cardiovascular y renal."},
    {"id": 29, "name": "Cetirizina 10mg", "lab": "Merck Colombia", "cat": "Antialérgicos", "desc": "Antihistamínico de segunda generación con rápido inicio de acción para rinitis y picazón."},
    {"id": 30, "name": "Vitamina C 1000mg", "lab": "Bayer S.A.", "cat": "Suplementos", "desc": "Ácido ascórbico de alta concentración para fortalecimiento inmunológico y antioxidante."}
]

# Creamos una cuadrícula de 2 columnas de medicamentos para que las fotos sean grandes y claras
# 15 filas x 2 medicamentos por fila
med_table = doc.add_table(rows=15, cols=2)
med_table.alignment = WD_TABLE_ALIGNMENT.CENTER
med_table.autofit = False

for index, med in enumerate(medicamentos_data):
    row_idx = index // 2
    col_idx = index % 2
    cell = med_table.rows[row_idx].cells[col_idx]
    cell.width = Inches(3.42)
    
    set_cell_background(cell, "FFFFFF")
    set_cell_borders(cell, top="E2E8F0", bottom="E2E8F0", left="E2E8F0", right="E2E8F0", sz=6)
    set_cell_margins(cell, top=120, bottom=120, left=120, right=120)
    
    img_path = os.path.join(BASE_DIR, "public", "medicamentos", f"{med['id']}.png")
    info = get_image_info(img_path)
    
    # Imagen del medicamento
    p_mimg = cell.paragraphs[0]
    p_mimg.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_mimg.paragraph_format.space_after = Pt(4)
    if os.path.exists(img_path):
        # Asegurar tamaño visible y armónico (1.7 pulgadas)
        p_mimg.add_run().add_picture(img_path, width=Inches(1.7))
    
    # Nombre
    p_name = cell.add_paragraph()
    p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_name.paragraph_format.space_after = Pt(1)
    run_mn = p_name.add_run(f"#{med['id']} — {med['name']}")
    run_mn.font.bold = True
    run_mn.font.size = Pt(10)
    run_mn.font.color.rgb = COLOR_PRIMARY
    
    # Lab y Categoría
    p_sub = cell.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(3)
    run_ml = p_sub.add_run(f"{med['lab']}  •  ")
    run_ml.font.size = Pt(8.5)
    run_ml.font.bold = True
    run_ml.font.color.rgb = COLOR_DARK
    
    run_mc = p_sub.add_run(f"{med['cat']}")
    run_mc.font.size = Pt(8.5)
    run_mc.font.color.rgb = COLOR_SECONDARY
    
    # Descripción
    p_desc = cell.add_paragraph()
    p_desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_desc.paragraph_format.space_after = Pt(3)
    run_md = p_desc.add_run(med['desc'])
    run_md.font.size = Pt(8)
    run_md.font.color.rgb = COLOR_MUTED
    
    # Metadatos del archivo
    p_file = cell.add_paragraph()
    p_file.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_file.paragraph_format.space_after = Pt(0)
    size_str = f"{info['size_kb']:.1f} KB" if info else "N/A"
    dims_str = info['dims'] if info else "N/A"
    run_mf = p_file.add_run(f"📁 {med['id']}.png  ({dims_str} | {size_str})")
    run_mf.font.size = Pt(7.5)
    run_mf.font.color.rgb = COLOR_MUTED

doc.add_paragraph().paragraph_format.space_after = Pt(12)

# ==========================================
# 6. ASSETS DE PLANTILLA Y MAPAS EXTERNOS
# ==========================================
doc.add_page_break()
add_section_title(doc, "6", "Archivos de Plantilla y Recursos Externos")
add_section_subtitle(doc, "Logos del ecosistema de desarrollo y fuentes remotas para mapas y geolocalización.")

extra_items = [
    {
        "title": "Logotipo de Vite",
        "file": "vite.svg",
        "path": os.path.join(BASE_DIR, "public", "vite.svg"),
        "desc": "Asset por defecto del empaquetador Vite utilizado en el entorno de desarrollo frontend."
    },
    {
        "title": "Logotipo de React",
        "file": "react.svg",
        "path": os.path.join(BASE_DIR, "src", "assets", "react.svg"),
        "desc": "Asset por defecto de la librería React para la interfaz de componentes."
    }
]

t_extra = doc.add_table(rows=1, cols=2)
t_extra.alignment = WD_TABLE_ALIGNMENT.CENTER
t_extra.autofit = False

for idx, item in enumerate(extra_items):
    cell = t_extra.rows[0].cells[idx]
    cell.width = Inches(3.42)
    set_cell_background(cell, "F8FAFC")
    set_cell_borders(cell, top="E2E8F0", bottom="E2E8F0", left="E2E8F0", right="E2E8F0", sz=6)
    set_cell_margins(cell, top=140, bottom=140, left=140, right=140)
    
    png_tmp = os.path.join(TEMP_IMG_DIR, f"{os.path.splitext(item['file'])[0]}.png")
    if os.path.exists(item["path"]):
        render_svg_to_png(item["path"], png_tmp, width=200)
    
    p_img = cell.paragraphs[0]
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_after = Pt(4)
    if os.path.exists(png_tmp):
        p_img.add_run().add_picture(png_tmp, width=Inches(1.2))
    
    p_t = cell.add_paragraph()
    p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t.paragraph_format.space_after = Pt(2)
    r_et = p_t.add_run(item["title"])
    r_et.font.size = Pt(10)
    r_et.font.bold = True
    r_et.font.color.rgb = COLOR_PRIMARY
    
    p_d = cell.add_paragraph()
    p_d.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_d.paragraph_format.space_after = Pt(2)
    r_ed = p_d.add_run(item["desc"])
    r_ed.font.size = Pt(8.5)
    r_ed.font.color.rgb = COLOR_MUTED
    
    p_f = cell.add_paragraph()
    p_f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_f.paragraph_format.space_after = Pt(0)
    r_ef = p_f.add_run(f"Archivo: {item['file']}")
    r_ef.font.size = Pt(8)
    r_ef.font.bold = True
    r_ef.font.color.rgb = COLOR_DARK

doc.add_paragraph().paragraph_format.space_after = Pt(10)

# Cuadro informativo de Leaflet / CDN
p_ext = doc.add_paragraph()
p_ext.paragraph_format.space_before = Pt(8)
p_ext.paragraph_format.space_after = Pt(2)
r_ext_title = p_ext.add_run("Marcadores Remotos de Mapas (Leaflet en PharmacyMap.tsx):\n")
r_ext_title.font.bold = True
r_ext_title.font.size = Pt(10.5)
r_ext_title.font.color.rgb = COLOR_PRIMARY

r_ext_body = p_ext.add_run(
    "• Marcador normal: https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png\n"
    "• Marcador Retina 2x: https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png\n"
    "• Sombra de marcador: https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png\n"
    "• Mosaicos de mapa (Tiles CartoDB Voyager): https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
)
r_ext_body.font.size = Pt(9)
r_ext_body.font.color.rgb = COLOR_MUTED

# ==========================================
# 7. TABLA RESUMEN GENERAL DE INVENTARIO
# ==========================================
doc.add_page_break()
add_section_title(doc, "7", "Matriz Resumen de Inventario y Especificaciones Técnicas")
add_section_subtitle(doc, "Consolidado total de los 48 archivos de imagen locales del repositorio FarmaLink.")

summary_items = [
    # Branding
    ("logo-farmalink.png", "src/assets/logo-farmalink.png", "Branding / Logo", "Header, Footer, Meta tags"),
    ("logo-farmalink.png (copia)", "public/logo-farmalink.png", "Branding / Logo", "Acceso estático público"),
    ("assistant-icon.png", "public/assistant-icon.png", "Asistente IA", "AssistantChat.tsx"),
    # Funcionalidades
    ("icon-busqueda.png", "src/assets/icon-busqueda.png", "Ícono UI", "Hero.tsx, Features.tsx"),
    ("icon-precios.png", "src/assets/icon-precios.png", "Ícono UI", "Hero.tsx, Features.tsx"),
    ("icon-mapa.png", "src/assets/icon-mapa.png", "Ícono UI", "Hero.tsx, Features.tsx"),
    ("icon-ia.png", "src/assets/icon-ia.png", "Ícono UI", "Hero.tsx, Features.tsx"),
    # Dashboard
    ("icon-dash-farmacias.png", "src/assets/icon-dash-farmacias.png", "Métrica Dashboard", "Dashboard.tsx"),
    ("icon-dash-medicamentos.png", "src/assets/icon-dash-medicamentos.png", "Métrica Dashboard", "Dashboard.tsx"),
    ("icon-dash-precios.png", "src/assets/icon-dash-precios.png", "Métrica Dashboard", "Dashboard.tsx"),
    # Sliders
    ("slide-1-compara-precios.png", "src/assets/slide-1-compara-precios.png", "Banner Slider", "Slider.tsx"),
    ("slide-2-recomendaciones-ia.png", "src/assets/slide-2-recomendaciones-ia.png", "Banner Slider", "Slider.tsx"),
    ("slide-3-encuentra-farmacias.png", "src/assets/slide-3-encuentra-farmacias.png", "Banner Slider", "Slider.tsx"),
    ("slide-4-ahorro.png", "src/assets/slide-4-ahorro.png", "Banner Slider", "Slider.tsx"),
    ("slide-5-farmacias-aliadas.png", "src/assets/slide-5-farmacias-aliadas.png", "Banner Slider", "Slider.tsx"),
    # Placeholder
    ("placeholder.svg", "public/medicamentos/placeholder.svg", "Fallback Médico", "ProductoDetalle, CartView, Chat"),
    # Medicamentos 1 a 30
]
for i in range(1, 31):
    med_name = medicamentos_data[i-1]["name"]
    summary_items.append((f"{i}.png", f"public/medicamentos/{i}.png", "Medicamento", f"ProductoDetalle ({med_name})"))

summary_items.append(("vite.svg", "public/vite.svg", "Template", "Asset base Vite"))
summary_items.append(("react.svg", "src/assets/react.svg", "Template", "Asset base React"))

headers = ["#", "Nombre Archivo", "Ruta Relativa", "Categoría", "Dimensiones", "Peso", "Uso"]
col_widths = [Inches(0.35), Inches(1.3), Inches(1.8), Inches(1.0), Inches(0.9), Inches(0.65), Inches(0.9)]

sum_table = doc.add_table(rows=len(summary_items) + 1, cols=7)
sum_table.alignment = WD_TABLE_ALIGNMENT.CENTER
sum_table.autofit = False

# Estilo Header
hdr_row = sum_table.rows[0]
for idx, title in enumerate(headers):
    c = hdr_row.cells[idx]
    c.width = col_widths[idx]
    set_cell_background(c, "0B7DB8")
    set_cell_margins(c, top=80, bottom=80, left=60, right=60)
    set_cell_borders(c, top="0B7DB8", bottom="0B7DB8", left="0B7DB8", right="0B7DB8", sz=4)
    p = c.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(title)
    run.font.bold = True
    run.font.size = Pt(8)
    run.font.color.rgb = COLOR_WHITE

# Filas
for idx, (fname, rpath, cat, usage) in enumerate(summary_items):
    row = sum_table.rows[idx + 1]
    full_path = os.path.join(BASE_DIR, rpath.replace("/", os.sep))
    info = get_image_info(full_path)
    
    bg = "FFFFFF" if idx % 2 == 0 else "F8FAFC"
    dims_txt = info['dims'] if info else "-"
    size_txt = f"{info['size_kb']:.1f} KB" if info else "-"
    
    vals = [str(idx + 1), fname, rpath, cat, dims_txt, size_txt, usage]
    for c_idx, val in enumerate(vals):
        c = row.cells[c_idx]
        c.width = col_widths[c_idx]
        set_cell_background(c, bg)
        set_cell_margins(c, top=50, bottom=50, left=60, right=60)
        set_cell_borders(c, top="E2E8F0", bottom="E2E8F0", left="E2E8F0", right="E2E8F0", sz=4)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(val)
        r.font.size = Pt(7.5)
        r.font.color.rgb = COLOR_DARK

print(f"Guardando documento en: {OUTPUT_DOCX}")
doc.save(OUTPUT_DOCX)
print("¡Documento generado exitosamente!")
