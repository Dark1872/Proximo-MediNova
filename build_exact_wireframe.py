# -*- coding: utf-8 -*-
"""
Generates the exact wireframe/mockup layout provided in the user's reference image.
Pixel-perfect SVG formatted for direct copy-paste into Figma.
"""

def generate_exact_wireframe(use_farmalink_labels=True):
    # Labels
    if use_farmalink_labels:
        cart_label = "Ver Carrito"
        history_label = "Historial de Pedidos"
        search_ph = "Buscar medicamentos, laboratorios, farmacias..."
        search_btn = "Buscar"
        nav_items = ["Inicio", "Quiénes Somos", "Medicamentos", "Farmacias", "Blog", "Soporte", "Contacto"]
        phone = "800-888-8888"
        cats = [
            "Analgésicos",
            "Antibióticos",
            "Antiinflamatorios",
            "Antialérgicos",
            "Gastrointestinales",
            "Cardiovasculares",
            "Respiratorios",
            "Vitaminas / Suplementos",
            "Cuidado Personal"
        ]
        sec_title = "Medicamentos Destacados (Featured Products)"
        prods = [
            ("Acetaminofén 500mg", "SKU: GEN-500", "Caja x 100 tabletas. Analgésico y antipirético."),
            ("Amoxicilina 500mg", "SKU: MK-30CAP", "Caja x 30 cápsulas. Antibiótico de amplio espectro."),
            ("Ibuprofeno 800mg", "SKU: LAF-800", "Caja x 20 tabletas. Antiinflamatorio no esteroideo."),
            ("Loratadina 10mg", "SKU: TEC-10MG", "Caja x 10 tabletas. Antihistamínico para alergias.")
        ]
        btn_txt = "Más Info »"
    else:
        cart_label = "View Cart"
        history_label = "Order History"
        search_ph = "Products, Parts, Keywords Search"
        search_btn = "Search"
        nav_items = ["Home", "About Us", "Products", "Blog", "News", "Support", "Contact"]
        phone = "800-888-8888"
        cats = [
            "Rainfall Sensors",
            "Wind Anemometer",
            "Weather Stations",
            "Controllers",
            "Indicators/Displays",
            "Temp/Humidity Sensors",
            "Barometric Pressure",
            "Solar Radiation",
            "Replacement Parts"
        ]
        sec_title = "Featured Products"
        prods = [
            ("Product Title", "SKU", "Lorem ipsum dolor sit amet, consectetur adipiscing elit."),
            ("Product Title", "SKU", "Lorem ipsum dolor sit amet, consectetur adipiscing elit."),
            ("Product Title", "SKU", "Lorem ipsum dolor sit amet, consectetur adipiscing elit."),
            ("Product Title", "SKU", "Lorem ipsum dolor sit amet, consectetur adipiscing elit.")
        ]
        btn_txt = "More Info »"

    svg = []
    svg.append('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 950" width="1200" height="950">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap');
      text { font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
      .wf-box { fill: #FFFFFF; stroke: #000000; stroke-width: 2; stroke-linejoin: round; }
      .wf-box-gray { fill: #F1F5F9; stroke: #000000; stroke-width: 1.5; stroke-linejoin: round; }
      .wf-line { stroke: #000000; stroke-width: 1.5; }
      .wf-line-bold { stroke: #000000; stroke-width: 2; }
      .wf-text { fill: #000000; font-size: 13px; }
      .wf-text-title { fill: #000000; font-size: 16px; font-weight: 700; }
      .wf-text-bold { fill: #000000; font-size: 13px; font-weight: 700; }
      .wf-link { fill: #2563EB; font-size: 12px; font-weight: 500; text-decoration: underline; }
    </style>
  </defs>

  <!-- Background Canvas -->
  <rect width="1200" height="950" fill="#FFFFFF"/>
''')

    # 1. Top Logo Box with X
    svg.append('''
  <!-- Logo Box with Cross -->
  <g id="logo-box">
    <rect x="30" y="30" width="240" height="100" class="wf-box"/>
    <line x1="30" y1="30" x2="270" y2="130" class="wf-line-bold"/>
    <line x1="270" y1="30" x2="30" y2="130" class="wf-line-bold"/>
    <rect x="75" y="65" width="150" height="30" rx="4" fill="#FFFFFF" opacity="0.9"/>
    <text x="90" y="86" font-size="14" font-weight="700" fill="#000000">LOGO / FARMALINK</text>
  </g>
''')

    # 2. Top Right Area: View Cart, Order History, Search, Nav
    svg.append(f'''
  <!-- Top Right Header Navigation -->
  <g id="header-top-right">
    <!-- View Cart & Order History -->
    <text x="880" y="45" class="wf-text" font-weight="500">{cart_label}</text>
    <text x="965" y="45" class="wf-text" font-weight="500">{history_label}</text>

    <!-- Search Input & Button -->
    <rect x="690" y="65" width="260" height="28" class="wf-box"/>
    <text x="702" y="84" font-size="12" fill="#64748B">{search_ph}</text>

    <rect x="960" y="65" width="75" height="28" rx="14" class="wf-box"/>
    <text x="978" y="84" font-size="12" font-weight="600" fill="#000000">{search_btn}</text>

    <!-- Nav Links Row -->
    <g transform="translate(290, 125)">
''')

    cur_x = 0
    for idx, item in enumerate(nav_items):
        svg.append(f'      <text x="{cur_x}" y="0" class="wf-link">{item}</text>\n')
        cur_x += len(item) * 7 + 16
        if idx < len(nav_items) - 1:
            svg.append(f'      <text x="{cur_x - 8}" y="0" font-size="12" font-weight="700" fill="#000000">|</text>\n')
            cur_x += 8

    svg.append(f'''      <text x="780" y="0" font-size="13" font-weight="600" fill="#000000">{phone}</text>
    </g>
  </g>
''')

    # 3. Middle Section: Left Category Sidebar & Big Banner with X
    svg.append('''
  <!-- Sidebar Categories & Main Hero Banner -->
  <g id="middle-section">
    <!-- Left Sidebar (Stacked Rectangles) -->
    <g id="category-sidebar" transform="translate(30, 150)">
''')

    cat_h = 37
    for idx, cat in enumerate(cats):
        svg.append(f'''      <rect x="0" y="{idx * cat_h}" width="215" height="{cat_h}" class="wf-box-gray"/>
      <text x="12" y="{idx * cat_h + 23}" font-size="12" font-weight="600" fill="#000000">{cat}</text>
''')

    total_sidebar_h = len(cats) * cat_h  # approx 333
    svg.append(f'''    </g>

    <!-- Right Large Banner with Cross -->
    <g id="main-banner" transform="translate(260, 150)">
      <rect x="0" y="0" width="910" height="{total_sidebar_h}" class="wf-box"/>
      <line x1="0" y1="0" x2="910" y2="{total_sidebar_h}" class="wf-line-bold"/>
      <line x1="910" y1="0" x2="0" y2="{total_sidebar_h}" class="wf-line-bold"/>
      <rect x="360" y="{total_sidebar_h//2 - 20}" width="200" height="40" rx="6" fill="#FFFFFF" opacity="0.92"/>
      <text x="382" y="{total_sidebar_h//2 + 5}" font-size="15" font-weight="700" fill="#000000">MAIN BANNER / HERO</text>
    </g>
  </g>
''')

    # 4. Featured Products Title Bar
    grid_top = 150 + total_sidebar_h + 25
    svg.append(f'''
  <!-- Featured Products Section -->
  <g id="featured-products-section" transform="translate(30, {grid_top})">
    <!-- Title Bar -->
    <rect x="0" y="0" width="700" height="34" class="wf-box"/>
    <text x="16" y="22" font-size="13" font-weight="700" fill="#000000">{sec_title}</text>

    <!-- 2x2 Product Grid (Left) -->
    <g transform="translate(0, 48)">
''')

    # 4 Product Cards (2 rows x 2 cols)
    card_w = 342
    card_h = 145
    col_gap = 16
    row_gap = 16

    coords = [
        (0, 0),
        (card_w + col_gap, 0),
        (0, card_h + row_gap),
        (card_w + col_gap, card_h + row_gap)
    ]

    for i, (cx, cy) in enumerate(coords):
        title, sku, desc = prods[i]
        svg.append(f'''      <!-- Card {i+1} -->
      <g transform="translate({cx}, {cy})">
        <rect x="0" y="0" width="{card_w}" height="{card_h}" class="wf-box"/>
        
        <!-- Image Box with X -->
        <rect x="10" y="10" width="125" height="125" class="wf-box"/>
        <line x1="10" y1="10" x2="135" y2="135" class="wf-line"/>
        <line x1="135" y1="10" x2="10" y2="135" class="wf-line"/>

        <!-- Details -->
        <text x="145" y="32" class="wf-text-title">{title}</text>
        <text x="145" y="54" font-size="12" font-weight="600" fill="#475569">{sku}</text>
        <text x="145" y="72" font-size="11" fill="#334155">{desc[:35]}</text>
        <text x="145" y="88" font-size="11" fill="#334155">{desc[35:]}</text>

        <!-- Button -->
        <rect x="145" y="102" width="125" height="28" rx="14" class="wf-box-gray"/>
        <text x="165" y="121" font-size="12" font-weight="700" fill="#000000">{btn_txt}</text>
      </g>
''')

    # Right Tall Promotional Box
    tall_h = (card_h * 2) + row_gap + 48  # aligned with title and cards
    svg.append(f'''    </g>

    <!-- Right Side Tall Promo Box -->
    <g transform="translate(720, 0)">
      <rect x="0" y="0" width="420" height="{tall_h}" class="wf-box"/>
      <rect x="130" y="{tall_h//2 - 20}" width="160" height="40" rx="6" fill="#F1F5F9"/>
      <text x="148" y="{tall_h//2 + 5}" font-size="14" font-weight="700" fill="#475569">SIDEBAR / AD</text>
    </g>
  </g>
''')

    # 5. Full-width Black Footer Bar
    footer_y = grid_top + tall_h + 25
    svg.append(f'''
  <!-- Black Footer Bar -->
  <rect x="30" y="{footer_y}" width="1140" height="34" fill="#000000"/>
</svg>''')

    return "".join(svg)

if __name__ == '__main__':
    # 1. Exact as image (with Farmalink labels)
    farmalink_wf = generate_exact_wireframe(use_farmalink_labels=True)
    with open('wireframe_exacto_farmalink.svg', 'w', encoding='utf-8') as f:
        f.write(farmalink_wf)

    # 2. Exact 1:1 original mockup (with generic / sensor labels matching the image literally)
    literal_wf = generate_exact_wireframe(use_farmalink_labels=False)
    with open('wireframe_exacto_literal.svg', 'w', encoding='utf-8') as f:
        f.write(literal_wf)

    print("Generated wireframe_exacto_farmalink.svg and wireframe_exacto_literal.svg successfully!")
