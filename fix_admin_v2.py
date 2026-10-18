#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fixed: sticky admin tabs + remove stats - corrected write() bug."""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    if not os.path.exists(p): return ""
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    """Write content to file - FIXED to require both args."""
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

def find_div_end(src, start_pos):
    """Return index just after matching </div> for <div at start_pos."""
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
# Consistent tabs HTML (uses Django context to highlight active)
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
# CSS for sticky header
# ============================================================
STICKY_CSS = '''
    /* ===== FIXED ADMIN HEADER ===== */
    body { padding: 16px 16px 40px !important; }
    .admin-sticky-header {
      position: sticky;
      top: 0;
      z-index: 500;
      background: #0a0a15;
      padding: 4px 0 8px;
      margin-bottom: 20px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.7);
    }
    .admin-sticky-header .topbar {
      margin-bottom: 8px !important;
    }
    .admin-sticky-header .admin-tabs {
      margin-bottom: 0 !important;
    }
    .admin-tabs {
      display: flex !important;
      gap: 6px !important;
      overflow-x: auto !important;
      overflow-y: hidden !important;
      white-space: nowrap !important;
      padding: 8px !important;
      background: #12121f !important;
      border: 1px solid rgba(148,163,184,0.15) !important;
      border-radius: 14px !important;
      scrollbar-width: thin !important;
    }
    .admin-tabs::-webkit-scrollbar { height: 6px; }
    .admin-tabs::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.5); border-radius: 6px; }
    .admin-tab {
      flex: 0 0 auto !important;
      padding: 10px 14px !important;
      border-radius: 10px !important;
      text-decoration: none !important;
      font-size: 12px !important;
      font-weight: bold !important;
      color: #94a3b8 !important;
      white-space: nowrap !important;
      transition: 0.2s !important;
    }
    .admin-tab:hover { background: rgba(148,163,184,0.1) !important; color: #fff !important; }
    .admin-tab.active {
      background: linear-gradient(135deg, #ef4444, #dc2626) !important;
      color: #fff !important;
      box-shadow: 0 6px 20px rgba(239,68,68,0.4) !important;
    }
'''

# ============================================================
# Process files
# ============================================================
print("\n" + "="*70)
print("PROCESSING ADMIN TEMPLATES")
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

    # 1) Add sticky CSS
    if 'FIXED ADMIN HEADER' not in src:
        if '</style>' in src:
            src = src.replace('</style>', STICKY_CSS + '\n  </style>', 1)

    # 2) Remove stats block from dashboard only
    if fname == "dashboard.html":
        stats_start = src.find('<div class="stats">')
        if stats_start >= 0:
            next_markers = ['<form method="get" class="search-row"', '<div class="card"', '<div class="msg"', '</div>']
            stats_end = len(src)
            for marker in next_markers:
                pos = src.find(marker, stats_start + 20)
                if pos > stats_start and pos < stats_end:
                    stats_end = pos
            if stats_end < len(src) and stats_end > stats_start:
                src = src[:stats_start] + src[stats_end:]

    # 3) Find/replace tabs
    tabs_start = src.find('<div class="admin-tabs"')
    if tabs_start >= 0:
        tabs_end = find_div_end(src, tabs_start)
        if tabs_end > 0:
            src = src[:tabs_start] + NEW_TABS + src[tabs_end:]
    else:
        topbar_start = src.find('<div class="topbar"')
        if topbar_start >= 0:
            topbar_end = find_div_end(src, topbar_start)
            if topbar_end > 0:
                src = src[:topbar_end] + "\n  " + NEW_TABS + src[topbar_end:]

    # 4) Wrap in sticky header
    if 'admin-sticky-header' not in src:
        topbar_start = src.find('<div class="topbar"')
        tabs_start = src.find('<div class="admin-tabs"')

        if topbar_start >= 0 and tabs_start >= 0:
            topbar_end = find_div_end(src, topbar_start)
            tabs_end = find_div_end(src, tabs_start)

            if topbar_end > 0 and tabs_end > 0:
                start = min(topbar_start, tabs_start)
                end = max(topbar_end, tabs_end)

                content = src[start:end]
                wrapped = '<div class="admin-sticky-header">\n    ' + content + '\n  </div>'
                src = src[:start] + wrapped + src[end:]

    if src != original:
        try:
            write(path, src)  # ✅ FIX: pass content
            success += 1
        except Exception as e:
            print(f"  ❌ ERROR writing {fname}: {e}")
            failed += 1
    else:
        print(f"  ⏭ {fname} - no changes")

print(f"\n  Result: {success} updated, {failed} failed")

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

    has_tabs = '<div class="admin-tabs"' in src
    has_sticky = 'admin-sticky-header' in src
    has_stats = '<div class="stats">' in src

    status = "✓" if (has_tabs and has_sticky and not has_stats) else "⚠"
    print(f"  {status} {fname}: tabs={has_tabs}, sticky={has_sticky}, stats={has_stats}")

# ============================================================
# Django check
# ============================================================
print("\n" + "="*70)
print("DJANGO CHECK")
print("="*70)

r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ PASSED")
else:
    print(f"  ⚠ {r.stderr[:600]}")

# ============================================================
# HTTP test
# ============================================================
print("\n" + "="*70)
print("HTTP TEST")
print("="*70)

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

tu, created = User.objects.get_or_create(
    username="__admin_test_v2__",
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
        mark = "✓" if r.status_code == 200 else ("→" if r.status_code in (301, 302) else "✗")
        print(f"  {mark} {url:35s} → {r.status_code}")
    except Exception as e:
        print(f"  ✗ {url:35s} → {type(e).__name__}")

if created:
    tu.delete()

print("\n" + "="*70)
print("DONE")
print("="*70)
print("""
Fixed:
  1. write() bug - now passes content
  2. Sticky header CSS added
  3. Tabs rebuilt with request.path detection
  4. Stats removed from dashboard

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)
""")
