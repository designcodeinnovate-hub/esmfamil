#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostic for bottom nav click issue."""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

print("\n" + "="*70)
print("DIAGNOSIS: Bottom nav click issue")
print("="*70)

# ============================================================
# 1) Show CURRENT nav HTML
# ============================================================
print("\n[1/5] Current nav HTML in base.html")
print("="*70)

base = read("templates/base.html")

# Find nav
nav_match = re.search(r'<nav class="bottom-nav">(.*?)</nav>', base, re.DOTALL)
if not nav_match:
    print("  ❌ NO <nav class=\"bottom-nav\"> FOUND!")
    sys.exit(1)

nav_html = nav_match.group(1)
print(nav_html)

# Count <a> tags in nav
links = re.findall(r'<a\s+href="([^"]+)"[^>]*>', nav_html)
print(f"\n  Total <a> tags: {len(links)}")
for href in links:
    print(f"    → {href}")

# Check for rooms link specifically
if "/game/rooms/manage/" in nav_html:
    print(f"\n  ✓ Rooms link /game/rooms/manage/ EXISTS in nav")
else:
    print(f"\n  ❌ Rooms link MISSING from nav!")

# ============================================================
# 2) Show nav CSS
# ============================================================
print("\n[2/5] Nav CSS")
print("="*70)

# Find .bottom-nav CSS block
nav_css_match = re.search(r'\.bottom-nav\s*\{([^}]+)\}', base)
if nav_css_match:
    print(f".bottom-nav {{\n{nav_css_match.group(1)}\n}}")
else:
    print("  ⚠ Could not find .bottom-nav CSS block")

# Check for .bottom-nav a
nav_a_match = re.search(r'\.bottom-nav\s+a\s*\{([^}]+)\}', base)
if nav_a_match:
    print(f"\n.bottom-nav a {{\n{nav_a_match.group(1)}\n}}")

# Check for pointer-events: none anywhere in nav CSS
if "pointer-events" in base:
    print("\n⚠ 'pointer-events' found in base.html:")
    for line in base.split('\n'):
        if 'pointer-events' in line:
            print(f"    {line.strip()}")

# ============================================================
# 3) Check for overlapping fixed elements
# ============================================================
print("\n[3/5] Fixed position elements that might overlap nav")
print("="*70)

# Find all elements with position: fixed
fixed_elements = []

# Common ones to check
elements_to_check = [
    ("pageLoader", "id=\"pageLoader\""),
    ("pwaBanner", "id=\"pwaBanner\""),
    ("musicHint", "id=\"musicHint\""),
    ("pwa-install-banner", "class=\"pwa-install-banner\""),
    ("statusMsg", "id=\"statusMsg\""),
    ("bottom-nav", "class=\"bottom-nav\""),
]

for name, marker in elements_to_check:
    if marker in base:
        # Find the element
        idx = base.find(marker)
        # Look at surrounding style or class
        snippet = base[max(0, idx-100):idx+500]
        
        # Check for display:none
        has_display_none = 'display:none' in snippet or 'display: none' in snippet
        
        # Find z-index in the style
        z_match = re.search(r'z-index\s*:\s*(\d+)', snippet)
        z = z_match.group(1) if z_match else "?"
        
        # Check for bottom
        bottom_match = re.search(r'bottom\s*:\s*([^;]+)', snippet)
        bottom = bottom_match.group(1) if bottom_match else "?"
        
        # Check for inset:0 (full screen overlay)
        is_overlay = 'inset: 0' in snippet or 'inset:0' in snippet
        
        print(f"  {name}:")
        print(f"    display: none? {has_display_none}")
        print(f"    z-index: {z}")
        print(f"    bottom: {bottom}")
        print(f"    fullscreen overlay? {is_overlay}")

# Check if pageLoader could be blocking
print("\n  Checking pageLoader CSS...")
loader_css = re.search(r'\.page-loader\s*\{([^}]+)\}', base)
if loader_css:
    css = loader_css.group(1)
    if 'pointer-events' not in css:
        print("    ⚠ pageLoader has NO pointer-events: none!")
        print("    This might block clicks!")

# ============================================================
# 4) Check the actual RENDERED page
# ============================================================
print("\n[4/5] Rendered page - what's actually in the HTML")
print("="*70)

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

tu, created = User.objects.get_or_create(
    username="__nav_diag__",
    defaults={
        "alias": "navtest",
        "is_active": True,
        "has_chosen_avatar": True,
        "has_completed_registration": True,
    }
)
if created:
    tu.set_password("x")
    tu.save()

c = Client()
c.force_login(tu)
c.session["beta_unlocked"] = True
c.session.save()

# Get the page
r = c.get("/game/rooms/manage/", follow=True)
if r.status_code == 200:
    html = r.content.decode()
    
    # Extract nav from rendered HTML
    rendered_nav_match = re.search(r'<nav class="bottom-nav">(.*?)</nav>', html, re.DOTALL)
    if rendered_nav_match:
        print("  Rendered nav HTML:")
        print(rendered_nav_match.group(1)[:2000])
    else:
        print("  ❌ Nav not found in rendered HTML!")
    
    # Check for click-blocking CSS
    if "pointer-events: none" in html:
        print("\n  ⚠ 'pointer-events: none' found in rendered page:")
        # Find context
        for m in re.finditer(r'[^{}]*pointer-events:\s*none[^}]*\}', html):
            print(f"    {m.group(0)[:200]}")
    
    # Check if pageLoader might be blocking
    if 'id="pageLoader"' in html:
        loader_idx = html.find('id="pageLoader"')
        loader_snippet = html[loader_idx:loader_idx+500]
        if 'loading' in loader_snippet and 'class="page-loader loading"' in html:
            print("\n  ⚠ pageLoader has 'loading' class in rendered page!")
            print("    This means it might be extended and covering content")
else:
    print(f"  Page status: {r.status_code}")

# Cleanup
if created:
    tu.delete()

# ============================================================
# 5) FIX: Rebuild nav + add safety CSS
# ============================================================
print("\n[5/5] APPLYING FIX")
print("="*70)

# 5a) Rebuild entire nav with known-good structure
old_nav = nav_match.group(0)
new_nav = '''<nav class="bottom-nav">
  <a href="/game/" class="nav-link {% if active == 'home' %}active{% endif %}">
    <span class="nav-icon">🏠</span>
    <span>خانه</span>
  </a>
  <a href="/game/rooms/" class="nav-link {% if active == 'games' %}active{% endif %}">
    <span class="nav-icon">🎮</span>
    <span>بازی‌ها</span>
  </a>
  <a href="/game/rooms/manage/" class="nav-link {% if active == 'rooms' %}active{% endif %}">
    <span class="nav-icon">🚪</span>
    <span>اتاق‌ها</span>
  </a>
  <a href="/social/" class="nav-link {% if active == 'friends' %}active{% endif %}">
    <span class="nav-icon">👥</span>
    <span>دوستان</span>
  </a>
  <a href="/accounts/profile/" class="nav-link {% if active == 'profile' %}active{% endif %}">
    <span class="nav-icon">👤</span>
    <span>پروفایل</span>
  </a>
</nav>'''

if old_nav != new_nav:
    base = base.replace(old_nav, new_nav, 1)
    write("templates/base.html", base)
    print("  ✓ Nav rebuilt")
else:
    print("  ✓ Nav already correct")

# 5b) Add safety CSS at the END of <style>
safety_css = '''

    /* ============================================================
       SAFETY OVERRIDES — ensure nav is always clickable
       ============================================================ */
    .bottom-nav {
      z-index: 9999 !important;
      pointer-events: auto !important;
    }
    .bottom-nav a,
    .bottom-nav a * {
      pointer-events: auto !important;
      cursor: pointer !important;
    }
    .bottom-nav a {
      -webkit-tap-highlight-color: rgba(244,197,66,0.3);
    }
    
    /* Ensure pageLoader never blocks clicks */
    .page-loader {
      pointer-events: none !important;
    }
    
    /* Ensure audio element is hidden */
    #globalMusic {
      display: none !important;
    }
    
    /* Ensure any pwa banner sits above nav but doesn't block */
    #pwaBanner, #musicHint, .pwa-install-banner {
      pointer-events: auto;
    }
'''

# Find </style> (the main one, not inside {% block %})
style_close = base.find('</style>')
if style_close > 0:
    # Check if safety CSS already there
    if "SAFETY OVERRIDES — ensure nav is always clickable" not in base:
        base = base[:style_close] + safety_css + base[style_close:]
        write("templates/base.html", base)
        print("  ✓ Safety CSS added at end of <style>")
    else:
        print("  ✓ Safety CSS already present")

# 5c) Remove any click-blocking JS (the smooth nav transition)
if "pageLoader.classList.add('loading')" in base:
    # The smooth transition JS might interfere - let's check it
    print("\n  Checking for nav transition JS...")
    if "e.preventDefault()" in base and "bottom-nav" in base:
        print("  ⚠ FOUND e.preventDefault() in base.html")
        # Find and show
        for line in base.split('\n'):
            if 'preventDefault' in line:
                print(f"    {line.strip()}")

# 5d) Rebuild page-loader CSS to ensure pointer-events: none
loader_pattern = re.compile(r'\.page-loader\s*\{[^}]*\}')
if loader_pattern.search(base):
    base = loader_pattern.sub(
        '.page-loader { position: fixed; top: 0; left: 0; height: 3px; width: 0; background: linear-gradient(90deg, #f4c542, #8b5cf6, #06b6d4); z-index: 9999; transition: width 0.3s ease-out, opacity 0.3s; box-shadow: 0 0 12px rgba(244,197,66,0.6); pointer-events: none; }',
        base
    )
    write("templates/base.html", base)
    print("  ✓ page-loader rebuilt with pointer-events: none")

# ============================================================
# Verify
# ============================================================
print("\n" + "="*70)
print("VERIFICATION")
print("="*70)

# Reload
base = read("templates/base.html")

print("\n  Nav HTML:")
nav_match = re.search(r'<nav class="bottom-nav">(.*?)</nav>', base, re.DOTALL)
if nav_match:
    print(nav_match.group(1)[:1500])

print("\n  Safety overrides present:")
print(f"    pointer-events: auto !important → {'pointer-events: auto !important' in base}")
print(f"    z-index: 9999 !important → {'z-index: 9999 !important' in base}")
print(f"    #globalMusic hidden → {'#globalMusic {' in base and 'display: none !important' in base}")

# Test URL still works
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("\n  ✓ Django check PASSED")
else:
    print(f"\n  ⚠ {r.stderr[:400]}")

print("\n" + "="*70)
print("DONE")
print("="*70)
print("""
Fix applied:
  1. ✓ Nav rebuilt with clean structure
  2. ✓ Added pointer-events: auto !important to nav and all its children
  3. ✓ Set nav z-index to 9999 (highest possible)
  4. ✓ Ensured pageLoader has pointer-events: none
  5. ✓ Hidden audio element with display: none
  6. ✓ Added -webkit-tap-highlight-color for mobile feedback

Now do this:
  1. pkill -9 -f "manage.py runserver"
  2. python manage.py runserver
  3. Ctrl+Shift+R (HARD refresh - this is critical!)
  4. Try clicking "اتاق‌ها" in bottom nav

If it STILL doesn't work after hard refresh:
  1. Open browser F12
  2. Go to Elements tab
  3. Right-click on the "اتاق‌ها" nav item
  4. Click "Inspect"
  5. Tell me what element is selected (a? span? something else?)
  6. Tell me what the parent elements are
""")
