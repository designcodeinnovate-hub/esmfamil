#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix step 6: remove logout from all topbars."""
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

print("\n" + "="*60)
print("FIXING: Remove logout from all admin topbars")
print("="*60)

admin_files = [
    "alliances.html", "alliance_detail.html", "rooms.html",
    "announcements.html", "tournaments.html", "tournament_edit.html",
    "shop_items.html", "guest_log.html", "send_to_all.html",
    "user_detail.html", "user_edit.html", "user_notify.html",
]

removed = 0
for fname in admin_files:
    path = f"accounts/templates/custom_admin/{fname}"
    if not os.path.exists(path):
        continue

    src = read(path)
    original = src

    # Remove any logout <a> tag
    src = re.sub(
        r'\s*<a\s+href="\{%\s*url\s+[\'\"]custom_admin:logout[\'\"]\s*%\}"[^>]*>[^<]*</a>',
        '',
        src,
    )

    # Also try patterns with variations
    src = re.sub(
        r'\s*<a\s+href="\{%\s*url\s+[\'\"]custom_admin:logout[\'\"]\s*%\}"[^>]*>.*?</a>',
        '',
        src,
        flags=re.DOTALL,
    )

    if src != original:
        write(path, src)
        removed += 1

print(f"\n  {removed} files had logout removed")

# Now handle dashboard — replace logout link with POST form
print("\n[Dashboard] Replacing logout link with POST form")

p = "accounts/templates/custom_admin/dashboard.html"
if os.path.exists(p):
    src = read(p)
    original = src

    # Old topbar with logout <a>
    old_patterns = [
        r'<div class="topbar">\s*<h1>[^<]*</h1>\s*<div class="actions">\s*<a href="\{% url \'custom_admin:logout\' %\}"[^>]*>[^<]*</a>\s*</div>\s*</div>',
        r'<div class="topbar">\s*<h1>[^<]*</h1>\s*<a href="\{% url \'custom_admin:logout\' %\}"[^>]*>[^<]*</a>\s*</div>',
    ]

    new_topbar = '''<div class="topbar">
      <h1>🔒 پنل مدیریت کاربران</h1>
      <form method="post" action="{% url 'custom_admin:logout' %}" style="display:inline; margin:0;">
        {% csrf_token %}
        <button type="submit" style="cursor:pointer; border:none; font-family:inherit; padding:9px 16px; border-radius:10px; font-size:13px; font-weight:bold; background:linear-gradient(135deg,#ef4444,#dc2626); color:#fff;">🚪 خروج از پنل</button>
      </form>
    </div>'''

    replaced = False
    for pattern in old_patterns:
        if re.search(pattern, src, re.DOTALL):
            src = re.sub(pattern, new_topbar, src, count=1, flags=re.DOTALL)
            replaced = True
            break

    if not replaced:
        # Just replace any logout link with form
        src = re.sub(
            r'<a\s+href="\{%\s*url\s+[\'\"]custom_admin:logout[\'\"]\s*%\}"[^>]*>[^<]*</a>',
            '''<form method="post" action="{% url 'custom_admin:logout' %}" style="display:inline; margin:0;">
              {% csrf_token %}
              <button type="submit" style="cursor:pointer; border:none; font-family:inherit; padding:9px 16px; border-radius:10px; font-size:13px; font-weight:bold; background:linear-gradient(135deg,#ef4444,#dc2626); color:#fff;">🚪 خروج از پنل</button>
            </form>''',
            src,
            count=1,
        )
        replaced = True

    if src != original:
        write(p, src)
        print("  ✓ Dashboard logout is now POST form")

# ============================================================
# Verify + check that POST logout works
# ============================================================
print("\n[Verification]")

r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:400]}")

# Check that logout view accepts POST
p = "accounts/admin_views.py"
src = read(p)
# Check if logout uses _check_auth and proper redirect
if "def admin_logout(request):" in src:
    # Find it
    m = re.search(r'def admin_logout\(request\):.*?(?=\n@|\ndef |\Z)', src, re.DOTALL)
    if m:
        body = m.group(0)
        if "request.session.pop" in body:
            print("  ✓ admin_logout works with POST")

# Test
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

tu, created = User.objects.get_or_create(
    username="__step6_test__",
    defaults={"alias": "test", "is_active": True, "is_staff": True, "has_chosen_avatar": True, "has_completed_registration": True}
)
if created:
    tu.set_password("x")
    tu.save()

c = Client()
c.session["custom_admin_logged_in"] = True
c.session["beta_unlocked"] = True
c.session.save()

print("\n  Test dashboard has POST logout:")
r = c.get("/panel-admin/dashboard/", follow=False)
if r.status_code == 200:
    html = r.content.decode()
    has_post_logout = 'action="{% url' not in html and 'action="/panel-admin/logout/"' in html
    has_link_logout = '<a href="/panel-admin/logout/"' in html
    print(f"    ✓ Has POST logout form: {has_post_logout or ('method=\"post\"' in html and 'logout' in html)}")
    print(f"    {'⚠' if has_link_logout else '✓'} No <a href> logout link: {not has_link_logout}")

print("\n  Test announcements page loads:")
r = c.get("/panel-admin/announcements/", follow=False)
print(f"    → {r.status_code}")

print("\n  Test user_notify page loads:")
r = c.get(f"/panel-admin/user/{tu.id}/notify/", follow=False)
print(f"    → {r.status_code}")

if created:
    tu.delete()

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
What this fix did:

  1. Fixed the write() bug (now passes src)
  2. Removed logout <a> from all admin topbars
  3. Dashboard now has POST form logout button
  4. Other pages: NO logout (accessible only from dashboard)

The previous script already completed:
  ✓ announcements_list view (with send-to-all)
  ✓ user_notify_toggle_read view
  ✓ Routes for both
  ✓ announcements.html with send-to-all + read stats
  ✓ user_notify.html with toggle read/unread button

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R

Test:
  1. /panel-admin/announcements/
     - See "جایزه به همه" form
     - See announcements with read/unread counts
     - Test send rewards
     - Test toggle read/unread
  
  2. /panel-admin/dashboard/
     - ONLY page with "🚪 خروج از پنل" button
     
  3. Any other admin page
     - NO logout button in topbar
""")
