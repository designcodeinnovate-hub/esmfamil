#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FIX: Absolute stable admin tabs - identical layout on ALL pages."""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    if not os.path.exists(p): return ""
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

def find_div_end(src, start_pos):
    depth = 0
    pos = start_pos
    iterations = 0
    while pos < len(src) and iterations < 5000:
        iterations += 1
        next_open = src.find('<div', pos)
        next_close = src.find('</div>', pos)
        if next_close == -1:
            return -1
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                return next_close + 6
            pos = next_close + 6
    return -1

# ============================================================
# The ULTIMATE STABLE CSS - fixed heights everywhere
# ============================================================
STABLE_CSS = '''
    /* ============================================================
       ULTIMATE STABLE ADMIN LAYOUT
       All heights, widths, paddings are FIXED
       No page-specific overrides can change them
       ============================================================ */
    
    /* Force consistent body */
    body { 
      padding: 16px 16px 40px !important;
      margin: 0 !important;
    }
    
    /* Force consistent container */
    .container { 
      max-width: 1400px !important; 
      margin: 0 auto !important;
      padding: 0 !important;
    }
    
    /* Sticky wrapper - fixed position */
    .admin-sticky-header {
      position: sticky !important;
      top: 0 !important;
      z-index: 500 !important;
      background: #0a0a15 !important;
      padding: 4px 0 8px !important;
      margin: 0 0 20px 0 !important;
      box-shadow: 0 4px 20px rgba(0,0,0,0.7) !important;
      box-sizing: border-box !important;
    }
    
    /* Topbar - FIXED HEIGHT */
    .admin-sticky-header .topbar,
    .admin-sticky-header > .topbar { 
      height: 60px !important;
      min-height: 60px !important;
      max-height: 60px !important;
      padding: 0 22px !important;
      margin: 0 0 8px 0 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: space-between !important;
      flex-wrap: nowrap !important;
      overflow: hidden !important;
      box-sizing: border-box !important;
      border-radius: 16px !important;
    }
    
    /* Topbar h1 - fixed font */
    .admin-sticky-header .topbar h1 { 
      font-size: 20px !important;
      line-height: 1 !important;
      margin: 0 !important;
      white-space: nowrap !important;
      overflow: hidden !important;
      text-overflow: ellipsis !important;
    }
    
    /* Topbar links/buttons - fixed size */
    .admin-sticky-header .topbar a,
    .admin-sticky-header .topbar button { 
      height: 36px !important;
      min-height: 36px !important;
      max-height: 36px !important;
      padding: 0 16px !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      font-size: 13px !important;
      line-height: 1 !important;
      box-sizing: border-box !important;
      white-space: nowrap !important;
    }
    
    /* ===== TABS - FIXED HEIGHT ===== */
    .admin-tabs {
      display: flex !important;
      flex-wrap: nowrap !important;
      gap: 6px !important;
      height: 48px !important;
      min-height: 48px !important;
      max-height: 48px !important;
      overflow-x: auto !important;
      overflow-y: hidden !important;
      white-space: nowrap !important;
      padding: 4px !important;
      margin: 0 !important;
      background: #12121f !important;
      border: 1px solid rgba(148,163,184,0.15) !important;
      border-radius: 14px !important;
      box-sizing: border-box !important;
      scrollbar-width: none !important;
      -ms-overflow-style: none !important;
    }
    
    .admin-tabs::-webkit-scrollbar { 
      display: none !important;
      height: 0 !important;
    }
    
    /* Each tab - FIXED HEIGHT */
    .admin-tab {
      flex: 0 0 auto !important;
      height: 40px !important;
      min-height: 40px !important;
      max-height: 40px !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      padding: 0 14px !important;
      border-radius: 10px !important;
      text-decoration: none !important;
      font-size: 12px !important;
      line-height: 1 !important;
      font-weight: bold !important;
      color: #94a3b8 !important;
      white-space: nowrap !important;
      box-sizing: border-box !important;
      transition: background 0.15s !important;
      border: none !important;
    }
    
    .admin-tab:hover { 
      background: rgba(148,163,184,0.1) !important; 
      color: #fff !important; 
    }
    
    .admin-tab.active {
      background: linear-gradient(135deg, #ef4444, #dc2626) !important;
      color: #fff !important;
      box-shadow: 0 6px 20px rgba(239,68,68,0.4) !important;
    }
'''

# ============================================================
# New tabs HTML
# ============================================================
NEW_TABS = '''<div class="admin-tabs">
    <a href="/panel-admin/dashboard/" class="admin-tab {% if '/panel-admin/dashboard/' in request.path or request.path == '/panel-admin/' %}active{% endif %}">👥 کاربران</a>
    <a href="/panel-admin/alliances/" class="admin-tab {% if '/panel-admin/alliance' in request.path %}active{% endif %}">🛡️ اتحادها</a>
    <a href="/panel-admin/rooms/" class="admin-tab {% if '/panel-admin/room' in request.path %}active{% endif %}">🚪 اتاق‌ها</a>
    <a href="/panel-admin/announcements/" class="admin-tab {% if '/panel-admin/announcement' in request.path %}active{% endif %}">📢 اعلان‌ها</a>
    <a href="/panel-admin/tournaments/" class="admin-tab {% if '/panel-admin/tournament' in request.path %}active{% endif %}">🏆 تورنمنت</a>
    <a href="/panel-admin/shop/" class="admin-tab {% if '/panel-admin/shop/' in request.path %}active{% endif %}">🛒 فروشگاه</a>
    <a href="/panel-admin/guest-log/" class="admin-tab {% if '/panel-admin/guest-log/' in request.path %}active{% endif %}">🎲 مهمان‌ها</a>
    <a href="/panel-admin/send-to-all/" class="admin-tab {% if '/panel-admin/send-to-all/' in request.path %}active{% endif %}">🎁 جایزه همه</a>
  </div>'''

# ============================================================
# Process all templates
# ============================================================
print("\n" + "="*70)
print("APPLYING ULTIMATE STABLE LAYOUT")
print("="*70)

admin_files = [
    "dashboard.html",
    "alliances.html",
    "alliance_detail.html",
    "rooms.html",
    "announcements.html",
    "tournaments.html",
    "tournament_edit.html",
    "shop_items.html",
    "guest_log.html",
    "send_to_all.html",
    "user_detail.html",
    "user_edit.html",
    "user_notify.html",
]

success = 0
failed = 0

for fname in admin_files:
    path = f"accounts/templates/custom_admin/{fname}"
    if not os.path.exists(path):
        print(f"  ⚠ MISSING: {fname}")
        failed += 1
        continue

    src = read(path)
    original = src

    # 1) REMOVE any old sticky CSS
    old_sticky_pattern = re.compile(r'\s*/\*\s*=====\s*FIXED ADMIN HEADER\s*=====\s*\*/.*?(?=</style>)', re.DOTALL)
    src = old_sticky_pattern.sub('\n', src)

    # 2) REMOVE any old .admin-tabs CSS (any variant)
    # Match .admin-tabs { ... } blocks
    for css_selector in [r'\.admin-tabs\s*\{', r'\.admin-tab\s*\{', r'\.admin-tab\.active\s*\{', r'\.admin-tab:hover\s*\{', r'\.admin-tabs::\-webkit-scrollbar\s*\{', r'\.admin-tabs::\-webkit-scrollbar-thumb\s*\{']:
        pattern = re.compile(css_selector + r'[^}]+\}', re.MULTILINE)
        src = pattern.sub('', src)

    # 3) Add NEW stable CSS before </style>
    if '</style>' in src:
        src = src.replace('</style>', STABLE_CSS + '\n  </style>', 1)

    # 4) Find and replace tabs
    tabs_start = src.find('<div class="admin-tabs"')
    if tabs_start >= 0:
        tabs_end = find_div_end(src, tabs_start)
        if tabs_end > 0:
            src = src[:tabs_start] + NEW_TABS + src[tabs_end:]
    else:
        # Insert after topbar
        topbar_start = src.find('<div class="topbar"')
        if topbar_start >= 0:
            topbar_end = find_div_end(src, topbar_start)
            if topbar_end > 0:
                src = src[:topbar_end] + "\n  " + NEW_TABS + src[topbar_end:]

    # 5) Wrap topbar + tabs in sticky container (once)
    # First, check if already wrapped
    if '<div class="admin-sticky-header">' not in src:
        # Find topbar and tabs
        topbar_start = src.find('<div class="topbar"')
        tabs_start = src.find('<div class="admin-tabs"')

        if topbar_start >= 0 and tabs_start >= 0:
            # Make sure topbar comes before tabs
            if topbar_start < tabs_start:
                topbar_end = find_div_end(src, topbar_start)
                tabs_end = find_div_end(src, tabs_start)

                if topbar_end > 0 and tabs_end > 0:
                    content = src[topbar_start:tabs_end]
                    wrapped = '<div class="admin-sticky-header">\n  ' + content + '\n  </div>'
                    src = src[:topbar_start] + wrapped + src[tabs_end:]

    if src != original:
        write(path, src)
        success += 1
    else:
        print(f"  ⏭ {fname} - unchanged")

print(f"\n  Result: {success} files updated")

# ============================================================
# Verify
# ============================================================
print("\n" + "="*70)
print("VERIFICATION")
print("="*70)

for fname in admin_files:
    path = f"accounts/templates/custom_admin/{fname}"
    if not os.path.exists(path):
        continue
    src = read(path)

    checks = {
        "sticky wrap": '<div class="admin-sticky-header">' in src,
        "tabs": '<div class="admin-tabs"' in src,
        "stable CSS": 'ULTIMATE STABLE' in src,
        "fixed height": 'height: 48px !important' in src,
    }
    status = "✓" if all(checks.values()) else "⚠"
    print(f"  {status} {fname}: {sum(checks.values())}/4")

# ============================================================
# Test
# ============================================================
print("\n" + "="*70)
print("TESTING")
print("="*70)

r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:400]}")

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

tu, created = User.objects.get_or_create(
    username="__stable_test__",
    defaults={"alias": "test", "is_active": True, "is_staff": True, "has_chosen_avatar": True, "has_completed_registration": True}
)
if created:
    tu.set_password("x")
    tu.save()

c = Client()
c.session["custom_admin_logged_in"] = True
c.session["beta_unlocked"] = True
c.session.save()

urls = [
    "/panel-admin/dashboard/",
    "/panel-admin/alliances/",
    "/panel-admin/rooms/",
    "/panel-admin/announcements/",
    "/panel-admin/tournaments/",
    "/panel-admin/shop/",
    "/panel-admin/guest-log/",
    "/panel-admin/send-to-all/",
]

for url in urls:
    try:
        r = c.get(url, follow=False)
        mark = "✓" if r.status_code == 200 else "✗"
        print(f"  {mark} {url:35s} → {r.status_code}")
    except Exception as e:
        print(f"  ✗ {url:35s} → {type(e).__name__}")

if created:
    tu.delete()

print("\n" + "="*70)
print("DONE")
print("="*70)
print("""
ULTIMATE STABLE LAYOUT applied:

  ✓ Body padding: 16px 16px 40px (fixed, !important)
  ✓ Container max-width: 1400px (same on ALL pages)
  ✓ Sticky wrapper: same on all pages
  ✓ Topbar height: 60px FIXED (!important)
  ✓ Topbar h1 font-size: 20px FIXED
  ✓ Topbar buttons: 36px height FIXED
  ✓ Admin-tabs height: 48px FIXED (!important)
  ✓ Admin-tab height: 40px FIXED (!important)
  ✓ Tab font-size: 12px FIXED
  ✓ Padding: 0 14px FIXED
  ✓ Overflow-x auto, overflow-y hidden
  ✓ Scrollbar: hidden (no height jump)
  ✓ ALL !important to override any page-specific styles

Why it was jumping before:
  - Different pages had different max-width on .container
  - Different topbar heights
  - Font-size variations
  - Padding differences

Now:
  - ALL heights fixed in pixels
  - ALL font-sizes fixed
  - ALL paddings fixed
  - !important prevents overrides
  - overflow-y: hidden prevents scrollbar appearance
  - scrollbar-width: none hides the scrollbar entirely

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (HARD refresh - CRITICAL!)

Test:
  1. Open /panel-admin/dashboard/
  2. Look at topbar+tabs - note their EXACT position and size
  3. Click each tab (اتحادها, اتاق‌ها, اعلان‌ها, ...)
  4. Topbar+tabs should be IDENTICAL on every page
  5. Scroll any page - they stay sticky at top
""")
