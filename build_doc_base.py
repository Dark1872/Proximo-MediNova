import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUTPUT_FILE = r"c:\Users\crack\Farmalink-SAS\Plan_Implementacion_Farmalink_Mobile_Flutter.docx"

doc = Document()

# Define Margins (2.5 cm all around)
for section in doc.sections:
    section.top_margin = Inches(0.9)
    section.bottom_margin = Inches(0.9)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)

# Colors
COLOR_PRIMARY = RGBColor(30, 58, 138)    # #1E3A8A (Navy Blue)
COLOR_SECONDARY = RGBColor(2, 132, 199) # #0284C7 (Light Blue)
COLOR_TEXT = RGBColor(31, 41, 55)        # #1F2937 (Charcoal)
COLOR_MUTED = RGBColor(107, 114, 128)    # #6B7280 (Gray)
HEX_PRIMARY = "1E3A8A"
HEX_LIGHT_BG = "F1F5F9"
HEX_ALT_ROW = "F8FAFC"
HEX_CALLOUT_BG = "EFF6FF"
HEX_CALLOUT_BORDER = "3B82F6"

# Base Styles
style_normal = doc.styles['Normal']
style_normal.font.name = 'Calibri'
style_normal.font.size = Pt(10.5)
style_normal.font.color.rgb = COLOR_TEXT
style_normal.paragraph_format.line_spacing = 1.15
style_normal.paragraph_format.space_after = Pt(4)

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_callout(document, title, text, alert_type="info"):
    table = document.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.7)
    set_cell_background(cell, HEX_CALLOUT_BG)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=180)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    run_t = p.add_run(f"📌 {title.upper()}: ")
    run_t.bold = True
    run_t.font.size = Pt(10)
    run_t.font.color.rgb = COLOR_PRIMARY
    
    run_b = p.add_run(text)
    run_b.font.size = Pt(10)
    run_b.font.color.rgb = COLOR_TEXT
    
    # Border
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="0" w:color="{HEX_CALLOUT_BORDER}"/><w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>')
    tcPr.append(borders)
    
    document.add_paragraph().paragraph_format.space_after = Pt(4)

def add_header_styled(document, text, level):
    h = document.add_heading(text, level=level)
    h.paragraph_format.keep_with_next = True
    if level == 1:
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(18)
            r.font.color.rgb = COLOR_PRIMARY
            r.bold = True
    elif level == 2:
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(14)
            r.font.color.rgb = COLOR_SECONDARY
            r.bold = True
    elif level == 3:
        h.paragraph_format.space_before = Pt(8)
        h.paragraph_format.space_after = Pt(2)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(11.5)
            r.font.color.rgb = COLOR_PRIMARY
            r.bold = True
    return h

def create_table(document, headers, data, col_widths=None):
    table = document.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    hdr_row = table.rows[0]
    # Header format
    for idx, header_text in enumerate(headers):
        cell = hdr_row.cells[idx]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_background(cell, HEX_PRIMARY)
        set_cell_margins(cell, top=120, bottom=120, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        run = p.add_run(header_text)
        run.bold = True
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(255, 255, 255)
    
    # Rows format
    for r_idx, row_data in enumerate(data):
        row = table.rows[r_idx + 1]
        bg = HEX_ALT_ROW if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, cell_value in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=90, bottom=90, left=110, right=110)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(0)
            run = p.add_run(str(cell_value))
            run.font.size = Pt(9)
            run.font.color.rgb = COLOR_TEXT
            
    # Widths
    if col_widths and len(col_widths) == len(headers):
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = Inches(width)
                
    # Add thin light borders
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'<w:tblBorders {nsdecls("w")}><w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/><w:bottom w:val="single" w:sz="6" w:space="0" w:color="{HEX_PRIMARY}"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/><w:insideV w:val="none"/><w:left w:val="none"/><w:right w:val="none"/></w:tblBorders>')
    tblPr.append(borders)
    
    p_after = document.add_paragraph()
    p_after.paragraph_format.space_after = Pt(6)
    return table

print("Base setup ready.")

