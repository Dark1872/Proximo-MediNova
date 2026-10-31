# -*- coding: utf-8 -*-
"""
Script maestro para generar el Plan de Implementacion Profesional en Word (.docx)
para la migracion de Farmalink SAS a Flutter (Version Movil).
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

# Page Margins
for section in doc.sections:
    section.top_margin = Inches(0.85)
    section.bottom_margin = Inches(0.85)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

# Palette
COLOR_PRIMARY = RGBColor(30, 58, 138)     # Deep Navy
COLOR_SECONDARY = RGBColor(2, 132, 199)  # Cyan/Teal Accent
COLOR_TEXT = RGBColor(31, 41, 55)         # Charcoal
COLOR_MUTED = RGBColor(107, 114, 128)     # Slate Gray
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

# Normal Style
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
            r.font.size = Pt(16)
            r.font.color.rgb = COLOR_PRIMARY
            r.bold = True
    elif level == 2:
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(13)
            r.font.color.rgb = COLOR_SECONDARY
            r.bold = True
    elif level == 3:
        h.paragraph_format.space_before = Pt(8)
        h.paragraph_format.space_after = Pt(2)
        for r in h.runs:
            r.font.name = 'Calibri'
            r.font.size = Pt(11)
            r.font.color.rgb = COLOR_PRIMARY
            r.bold = True
    return h

def add_callout(document, title, text, ctype="info"):
    bg = HEX_CALLOUT_BG if ctype=="info" else (HEX_WARNING_BG if ctype=="warning" else HEX_SUCCESS_BG)
    border = HEX_CALLOUT_BORDER if ctype=="info" else (HEX_WARNING_BORDER if ctype=="warning" else HEX_SUCCESS_BORDER)
    icon = "📌" if ctype=="info" else ("⚠️" if ctype=="warning" else "✅")
    
    table = document.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.8)
    set_cell_background(cell, bg)
    set_cell_margins(cell, top=120, bottom=120, left=180, right=160)
    
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
    set_cell_background(cell, "1E293B") # Dark slate
    set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
    
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
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        run = p.add_run(header_text)
        run.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(255, 255, 255)
    
    for r_idx, row_data in enumerate(data):
        row = table.rows[r_idx + 1]
        bg = HEX_ALT_ROW if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, cell_value in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(0)
            run = p.add_run(str(cell_value))
            run.font.size = Pt(8.5)
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

print("Helper functions compiled.")

