#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove room codes, player IDs, public_id from all admin displays."""
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

print("\n" + "="*70)
print("REMOVING ALL IDS AND CODES FROM ADMIN PANEL")
print("="*70)

changes = 0

# ============================================================
# 1) rooms.html — remove room codes
# ============================================================
print("\n[1/5] rooms.html — remove room codes")
p = "accounts/templates/custom_admin/rooms.html"
if os.path.exists(p):
    src = read(p)
    original = src

    # Remove room-code span
    src = re.sub(r'\s*<span class="room-code">\{\{ r\.code \}\}</span>', '', src)

    # Change confirm messages to not use code
    src = re.sub(r"return confirm\('حذف اتاق \{\{ r\.code \}\}؟'\);", "return confirm('این اتاق حذف شود؟');", src)
    src = re.sub(r"return confirm\('حذف دائمی این اتاق\؟'\);", "return confirm('این اتاق برای همیشه حذف شود؟');", src)

    # Remove any .room-code CSS rules
    src = re.sub(r'\s*\.room-code\s*\{[^}]*\}', '', src)

    # Remove host username references (only alias stays)
    src = src.replace("p.username == r.host_username", "p.alias == r.host")

    # Remove "شناسه" labels if any
    src = re.sub(r'<div class="info-item"><div class="lbl">شناسه</div>[^<]*</div>\s*', '', src)

    if src != original:
        write(p, src)
        changes += 1
    else:
        print("  ⏭ no changes")

# ============================================================
# 2) dashboard.html — remove public_id column
# ============================================================
print("\n[2/5] dashboard.html — remove public_id column")
p = "accounts/templates/custom_admin/dashboard.html"
if os.path.exists(p):
    src = read(p)
    original = src

    # Remove the header column
    src = src.replace('<th>شناسه</th>\n          ', '')
    src = src.replace('<th>شناسه</th>', '')

    # Remove the data cell
    src = re.sub(r'\s*<td><span class="pid">#\{\{ u\.public_id \}\}</span></td>', '', src)
    src = re.sub(r'\s*<td[^>]*><span class="pid">#\{\{ u\.public_id \}\}</span></td>', '', src)

    # Remove .pid CSS if only used for this
    if '.pid' in src:
        src = re.sub(r'\s*\.pid\s*\{[^}]*\}', '', src)

    # Update colspan in empty state (was 14, now 13)
    src = src.replace('colspan="14"', 'colspan="13"')

    if src != original:
        write(p, src)
        changes += 1
    else:
        print("  ⏭ no changes")

# ============================================================
# 3) user_detail.html — remove public_id and avatar_id displays
# ============================================================
print("\n[3/5] user_detail.html — remove IDs")
p = "accounts/templates/custom_admin/user_detail.html"
if os.path.exists(p):
    src = read(p)
    original = src

    # Remove "شناسه عمومی" row entirely
    src = re.sub(
        r'\s*<div class="row">\s*<span class="k">شناسه عمومی</span>\s*<span class="v">#\{\{ u\.public_id \}\}</span>\s*</div>',
        '',
        src
    )

    # Remove "آواتار" row (contains avatar_id number)
    src = re.sub(
        r'\s*<div class="row">\s*<span class="k">آواتار</span>\s*<span class="v">[^<]*\([^)]*\)</span>\s*</div>',
        '',
        src
    )

    if src != original:
        write(p, src)
        changes += 1
    else:
        print("  ⏭ no changes")

# ============================================================
# 4) user_notify.html — remove public_id display
# ============================================================
print("\n[4/5] user_notify.html — remove IDs")
p = "accounts/templates/custom_admin/user_notify.html"
if os.path.exists(p):
    src = read(p)
    original = src

    # Remove "#{{ u.public_id }}" from user-meta
    src = re.sub(r'\s*·\s*#\{\{ u\.public_id \}\}', '', src)

    if src != original:
        write(p, src)
        changes += 1
    else:
        print("  ⏭ no changes")

# ============================================================
# 5) user_edit.html — remove public_id if shown
# ============================================================
print("\n[5/5] user_edit.html — remove IDs")
p = "accounts/templates/custom_admin/user_edit.html"
if os.path.exists(p):
    src = read(p)
    original = src

    # Remove any public_id references
    src = re.sub(r'\s*#\{\{ u\.public_id \}\}', '', src)

    if src != original:
        write(p, src)
        changes += 1
    else:
        print("  ⏭ no changes")

# ============================================================
# 6) Also check guest_log.html
# ============================================================
print("\n[6/6] guest_log.html — remove public_id column")
p = "accounts/templates/custom_admin/guest_log.html"
if os.path.exists(p):
    src = read(p)
    original = src

    # Remove شناسه column header
    src = re.sub(r'\s*<th>شناسه</th>', '', src)

    # Remove data cell
    src = re.sub(r'\s*<td><span class="pid">#\{\{ log\.public_id\|default:"—" \}\}</span></td>', '', src)

    # Remove .pid CSS
    if '.pid' in src:
        src = re.sub(r'\s*\.pid\s*\{[^}]*\}', '', src)

    if src != original:
        write(p, src)
        changes += 1
    else:
        print("  ⏭ no changes")

# ============================================================
# Django check + test
# ============================================================
print("\n" + "="*70)
print("VERIFICATION")
print("="*70)

print(f"\n  Total files changed: {changes}")

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
    username="__no_id_test__",
    defaults={"alias": "test", "is_active": True, "is_staff": True, "has_chosen_avatar": True, "has_completed_registration": True}
)
if created:
    tu.set_password("x")
    tu.save()

c = Client()
c.session["custom_admin_logged_in"] = True
c.session["beta_unlocked"] = True
c.session.save()

print("\n  Pages check:")
urls = [
    "/panel-admin/dashboard/",
    "/panel-admin/rooms/",
    "/panel-admin/guest-log/",
]
for url in urls:
    try:
        r = c.get(url, follow=False)
        mark = "✓" if r.status_code == 200 else "✗"
        print(f"    {mark} {url:35s} → {r.status_code}")
    except Exception as e:
        print(f"    ✗ {url:35s} → {type(e).__name__}")

# Check no public_id in rendered output
print("\n  Checking public_id is gone from rendered pages:")
for url in ["/panel-admin/dashboard/", "/panel-admin/rooms/"]:
    try:
        r = c.get(url)
        html = r.content.decode()
        has_public_id_display = '<span class="pid">#' in html
        mark = "✓" if not has_public_id_display else "✗"
        print(f"    {mark} {url}: no public_id = {not has_public_id_display}")
    except Exception:
        pass

if created:
    tu.delete()

print("\n" + "="*70)
print("DONE")
print("="*70)
print("""
What was removed:

  rooms.html:
    ✗ Room code ({{ r.code }}) — the 4-digit ID
    ✗ Confirm messages no longer show code
    ✗ .room-code CSS removed
    ✓ Room name still shown
    ✓ Host alias still shown
    ✓ Player aliases still shown

  dashboard.html:
    ✗ "شناسه" column header
    ✗ public_id values (9-digit numbers)
    ✗ .pid CSS
    ✓ colspan updated to 13

  user_detail.html:
    ✗ "شناسه عمومی" row
    ✗ "آواتار" row (with avatar_id number)

  user_notify.html:
    ✗ "· #{{ u.public_id }}" text

  guest_log.html:
    ✗ "شناسه" column
    ✗ public_id values

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)

Test:
  1. /panel-admin/dashboard/ → no more public_id column
  2. /panel-admin/rooms/ → no room code shown
  3. /panel-admin/guest-log/ → no public_id column
  4. /panel-admin/user/<id>/ → no شناسه عمومی row

Room cards now show:
  - Room name (اسم اتاق)
  - Mode (match/team/bot/puzzle)
  - Status badge
  - Host alias
  - Player aliases + scores

If you still see something you want removed, tell me exactly which text you see.
""")
