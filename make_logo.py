#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate beautiful app icon/logo for PWA."""
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def read(p):
    if not os.path.exists(p): return ""
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 0) Install Pillow if missing
# ============================================================
print("\n[0/6] Checking Pillow")
try:
    from PIL import Image, ImageDraw, ImageFilter
    print("  ✓ Pillow installed")
except ImportError:
    print("  Installing Pillow...")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        from PIL import Image, ImageDraw, ImageFilter
        print("  ✓ Pillow installed")
    else:
        print("  ❌ Failed to install Pillow")
        sys.exit(1)

# ============================================================
# 1) Create icons directory
# ============================================================
print("\n[1/6] Creating static/icons/")
os.makedirs("static/icons", exist_ok=True)

# ============================================================
# 2) Draw the icon function
# ============================================================
print("\n[2/6] Drawing logo...")

def draw_icon(size=512, maskable=False):
    """Draw a beautiful crown icon for the game."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # --- Background: rounded square with radial gradient ---
    # Create gradient manually
    bg_img = Image.new('RGB', (size, size), (10, 10, 21))
    grad = ImageDraw.Draw(bg_img)
    
    # Radial gradient (from center-ish, purple-blue to dark)
    cx, cy = size // 2, int(size * 0.45)
    max_dist = size * 0.75
    
    for y in range(size):
        for x in range(size):
            # Distance from center
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            ratio = min(1.0, d / max_dist)
            
            # Colors: center is (30, 27, 75) - dark purple, edge is (10, 10, 21) - near black
            r = int(30 + (10 - 30) * ratio)
            g = int(27 + (10 - 27) * ratio)
            b = int(75 + (21 - 75) * ratio)
            grad.point((x, y), fill=(r, g, b))
    
    # Apply rounded corner mask
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = int(size * 0.22)  # ~22% radius for iOS-like rounded corners
    mask_draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    
    # For maskable, we want to use a circle mask (so any crop looks good)
    if maskable:
        # Use full square for maskable (system will crop it)
        mask = Image.new('L', (size, size), 255)
    
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    img.paste(bg_img, (0, 0), mask)
    draw = ImageDraw.Draw(img)
    
    # --- Scale factor for maskable (make crown smaller) ---
    scale = 0.75 if maskable else 1.0
    offset = (1 - scale) * size / 2
    
    def S(v):
        """Scale a value"""
        return int(offset + v * scale)
    
    # --- Crown design ---
    # Gold gradient colors
    gold_main = (244, 197, 66)     # #f4c542
    gold_dark = (202, 138, 4)      # #ca8a04
    gold_light = (253, 230, 138)   # #fde68a
    
    # Crown base points (before scale)
    crown_outline = [
        (140, 340),   # bottom-left
        (140, 290),   # top-left of base
        (170, 220),   # left peak
        (210, 280),   # left valley
        (256, 180),   # center peak (tallest)
        (302, 280),   # right valley
        (342, 220),   # right peak
        (372, 290),   # top-right of base
        (372, 340),   # bottom-right
    ]
    
    # Scale the points
    scaled_crown = [(S(x), S(y)) for (x, y) in crown_outline]
    
    # --- Draw glow behind crown ---
    glow_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.polygon(scaled_crown, fill=(244, 197, 66, 80))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=size * 0.06))
    img = Image.alpha_composite(img, glow_layer)
    draw = ImageDraw.Draw(img)
    
    # --- Draw crown base with gradient effect ---
    # Fill main crown (solid gold)
    draw.polygon(scaled_crown, fill=gold_main, outline=gold_dark, width=max(2, int(size * 0.006)))
    
    # Add darker outline
    draw.line(scaled_crown + [scaled_crown[0]], fill=gold_dark, width=max(2, int(size * 0.008)))
    
    # --- Crown base band (rectangle at bottom) ---
    band_top = S(330)
    band_bottom = S(360)
    band_left = S(130)
    band_right = S(382)
    draw.rectangle([band_left, band_top, band_right, band_bottom], fill=gold_dark)
    draw.rectangle([band_left, band_top, band_right, band_top + max(2, int(size * 0.005))], fill=gold_main)
    
    # --- Gems on crown peaks ---
    gems = [
        (S(170), S(240), S(14)),   # left peak
        (S(256), S(200), S(16)),   # center peak
        (S(342), S(240), S(14)),   # right peak
    ]
    
    for (gx, gy, gr) in gems:
        # Draw gem (circle with highlight)
        draw.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=(255, 255, 255), outline=gold_dark, width=2)
        # Inner highlight
        hr = max(2, gr // 2)
        draw.ellipse([gx - hr, gy - hr - hr//2, gx + hr, gy + hr - hr//2], fill=(253, 230, 138))
    
    # --- Add star decorations ---
    def draw_star(cx, cy, r, color):
        points = []
        for i in range(10):
            angle = (i * 36 - 90) * 3.14159 / 180
            dist = r if i % 2 == 0 else r / 2.5
            points.append((cx + dist * __import__('math').cos(angle),
                          cy + dist * __import__('math').sin(angle)))
        draw.polygon(points, fill=color)
    
    # Small gold stars around the crown
    star_positions = [
        (S(90), S(200), S(10)),
        (S(422), S(200), S(10)),
        (S(100), S(400), S(8)),
        (S(412), S(400), S(8)),
    ]
    for (sx, sy, sr) in star_positions:
        draw_star(sx, sy, sr, (253, 230, 138))
    
    # --- Draw Persian text at bottom (if possible) ---
    # Try to find a Persian font
    persian_font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    font = None
    for fp in persian_font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, size=int(size * 0.075))
                break
            except:
                pass
    
    if font:
        text = "اسم فامیل"
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (size - tw) // 2
        ty = int(size * 0.82)
        # Shadow
        draw.text((tx + 2, ty + 2), text, font=font, fill=(202, 138, 4, 200))
        # Main text
        draw.text((tx, ty), text, font=font, fill=gold_light)
    
    return img


# ============================================================
# 3) Generate all sizes
# ============================================================
print("\n[3/6] Generating icon sizes")

# Main icons
master = draw_icon(512, maskable=False)
master.save("static/icons/icon-512.png", "PNG")
print("  ✓ icon-512.png")

sizes_to_make = [512, 384, 192, 180, 167, 152, 144, 128, 120, 114, 96, 72, 60, 48, 32]
for s in sizes_to_make:
    if s == 512:
        continue
    icon = master.resize((s, s), Image.LANCZOS)
    icon.save(f"static/icons/icon-{s}.png", "PNG")
    print(f"  ✓ icon-{s}.png")

# Maskable version (larger safe zone padding)
maskable = draw_icon(512, maskable=True)
maskable.save("static/icons/icon-maskable-512.png", "PNG")
print("  ✓ icon-maskable-512.png")
maskable_192 = maskable.resize((192, 192), Image.LANCZOS)
maskable_192.save("static/icons/icon-maskable-192.png", "PNG")
print("  ✓ icon-maskable-192.png")

# Apple touch icon (needs to be non-transparent)
apple = Image.new('RGB', (180, 180), (10, 10, 21))
apple.paste(master.resize((180, 180), Image.LANCZOS), (0, 0), master.resize((180, 180), Image.LANCZOS))
apple.save("static/icons/apple-touch-icon.png", "PNG")
print("  ✓ apple-touch-icon.png")

# Favicon (multi-size ICO)
favicon_sizes = [(16, 16), (32, 32), (48, 48)]
master_fav = master.resize((48, 48), Image.LANCZOS)
master_fav.save("static/icons/favicon.ico", format='ICO', sizes=favicon_sizes)
print("  ✓ favicon.ico")

# ============================================================
# 4) Update manifest.json
# ============================================================
print("\n[4/6] Updating manifest.json")

MANIFEST = '''{
  "name": "اسم فامیل آنلاین",
  "short_name": "اسم فامیل",
  "description": "بازی نوستالژیک اسم فامیل، آنلاین و هیجان‌انگیز",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#0a0a15",
  "theme_color": "#f4c542",
  "lang": "fa",
  "dir": "rtl",
  "categories": ["games", "entertainment"],
  "icons": [
    {
      "src": "/static/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-maskable-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": "/static/icons/icon-maskable-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ]
}
'''
write("static/manifest.json", MANIFEST)

# ============================================================
# 5) Update base.html with icon links
# ============================================================
print("\n[5/6] Updating templates/base.html with icon links")

p = "templates/base.html"
src = read(p)

# Remove old manifest link
src = src.replace('<link rel="manifest" href="/static/manifest.json">', '')
# Remove old apple meta
src = src.replace('<meta name="apple-mobile-web-app-capable" content="yes">', '')
src = src.replace('<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">', '')
src = src.replace('<meta name="apple-mobile-web-app-title" content="اسم فامیل">', '')
src = src.replace('<meta name="mobile-web-app-capable" content="yes">', '')

# Add new icon block after theme-color meta
anchor = '<meta name="theme-color" content="#f4c542">'
if anchor in src:
    icon_block = '''<meta name="theme-color" content="#f4c542">

  <!-- ===== PWA & Icons ===== -->
  <link rel="manifest" href="/static/manifest.json">
  <link rel="icon" type="image/png" sizes="32x32" href="/static/icons/icon-32.png">
  <link rel="icon" type="image/png" sizes="192x192" href="/static/icons/icon-192.png">
  <link rel="icon" type="image/png" sizes="512x512" href="/static/icons/icon-512.png">
  <link rel="shortcut icon" href="/static/icons/favicon.ico">
  <link rel="apple-touch-icon" sizes="180x180" href="/static/icons/apple-touch-icon.png">
  <link rel="apple-touch-icon" sizes="152x152" href="/static/icons/icon-152.png">
  <link rel="apple-touch-icon" sizes="167x167" href="/static/icons/icon-167.png">

  <!-- iOS PWA meta -->
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="اسم فامیل">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="application-name" content="اسم فامیل">
'''
    src = src.replace(anchor, icon_block, 1)
    write(p, src)
    print("  ✓ base.html updated with all icon links")
else:
    print("  ⚠ theme-color meta not found")

# Also update the OLD theme-color to new gold
if '<meta name="theme-color" content="#0a0a15">' in src:
    src = src.replace('<meta name="theme-color" content="#0a0a15">', '<meta name="theme-color" content="#f4c542">')
    write(p, src)

# ============================================================
# 6) Test + verify
# ============================================================
print("\n[6/6] Verification")

# List all generated files
icon_files = sorted(os.listdir("static/icons"))
print(f"\n  Generated {len(icon_files)} icon files:")
for f in icon_files:
    size = os.path.getsize(f"static/icons/{f}")
    print(f"    ✓ {f} ({size:,} bytes)")

# Django check
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("\n  ✓ Django check PASSED")
else:
    print(f"\n  ⚠ {r.stderr[:400]}")

# Check base.html
src = read("templates/base.html")
checks = [
    ("manifest link", 'rel="manifest"' in src),
    ("favicon link", 'rel="shortcut icon"' in src),
    ("apple-touch-icon", 'rel="apple-touch-icon"' in src),
    ("theme-color gold", 'content="#f4c542"' in src),
]
print("\n  base.html checks:")
for name, ok in checks:
    print(f"    {'✓' if ok else '✗'} {name}")

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
What was created:

  🎨 Logo/Icon files in static/icons/:
     - icon-512.png (main)
     - icon-192.png (PWA standard)
     - icon-32.png, icon-48.png, icon-72.png, icon-96.png, etc.
     - icon-maskable-192.png, icon-maskable-512.png (Android adaptive)
     - apple-touch-icon.png (iOS home screen)
     - favicon.ico (browser tab)
     - icon-152.png, icon-167.png (iPad/iPhone specific)

  📱 manifest.json updated:
     - Uses new PNG icons
     - Both "any" and "maskable" purposes
     - RTL Persian support

  🌐 base.html updated:
     - <link rel="manifest">
     - <link rel="icon"> for browser tab
     - <link rel="apple-touch-icon"> for iOS
     - <link rel="shortcut icon">
     - iOS PWA meta tags

Icon design:
  👑 Gold crown with 3 peaks
  ✨ Small gold stars around
  💎 White gems on crown peaks
  🌌 Dark purple gradient background
  📝 "اسم فامیل" text at bottom (in gold)
  ⭕ Rounded corners (22%)
  🎭 Maskable version with safe zone padding

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)

Test:
  1. Browser tab → shows crown icon ✓
  2. Chrome install prompt → crown icon shows ✓
  3. Install PWA → home screen shows crown ✓
  4. iOS Safari → Add to Home Screen → crown icon ✓
  5. Android Chrome → install → adaptive icon works ✓

For Runflare deploy:
  runflare deploy
  (icons will be uploaded and served)
""")
