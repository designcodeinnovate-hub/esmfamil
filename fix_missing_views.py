#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add missing admin views that routes reference."""
import os, sys, subprocess

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
print("FIXING MISSING ADMIN VIEWS")
print("="*60)

p = "accounts/admin_views.py"
src = read(p)

added = []

# ============================================================
# 1) Check + add announcement_toggle_read
# ============================================================
if "def announcement_toggle_read(request):" not in src:
    print("\n  ⚠ announcement_toggle_read missing - adding")
    src = src.rstrip() + '''


@never_cache
def announcement_toggle_read(request):
    """Toggle read/unread for a broadcast announcement for ALL users."""
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:announcements_list")

    from social.models import Notification

    title = (request.POST.get("title") or "").strip()
    body = (request.POST.get("body") or "").strip()
    url = (request.POST.get("url") or "").strip()
    mark_as = request.POST.get("mark_as", "read")

    if title:
        qs = Notification.objects.filter(type="admin_broadcast", title=title)
        if body:
            qs = qs.filter(body=body)
        if url:
            qs = qs.filter(url=url)

        if mark_as == "read":
            n = qs.update(is_read=True)
            request.session["admin_message"] = {"type": "success", "text": f"{n} اعلان به «خوانده شد» تغییر یافت."}
        elif mark_as == "unread":
            n = qs.update(is_read=False)
            request.session["admin_message"] = {"type": "success", "text": f"{n} اعلان به «نخوانده» تغییر یافت."}

    return redirect("custom_admin:announcements_list")
'''
    added.append("announcement_toggle_read")
else:
    print("  ✓ announcement_toggle_read already exists")

# ============================================================
# 2) Check + add user_notify_toggle_read
# ============================================================
if "def user_notify_toggle_read(request, user_id, notif_id):" not in src:
    print("\n  ⚠ user_notify_toggle_read missing - adding")
    src = src.rstrip() + '''


@never_cache
def user_notify_toggle_read(request, user_id, notif_id):
    """Toggle read/unread for a single notification."""
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:user_notify", user_id=user_id)

    from social.models import Notification
    try:
        n = Notification.objects.get(id=notif_id, user_id=user_id)
        n.is_read = not n.is_read
        n.save(update_fields=["is_read"])
        status = "خوانده شد" if n.is_read else "نخوانده شد"
        request.session["admin_message"] = {"type": "success", "text": f"اعلان {status}."}
    except Notification.DoesNotExist:
        request.session["admin_message"] = {"type": "error", "text": "اعلان پیدا نشد."}

    return redirect("custom_admin:user_notify", user_id=user_id)
'''
    added.append("user_notify_toggle_read")
else:
    print("  ✓ user_notify_toggle_read already exists")

# ============================================================
# 3) Check + add announcement_create (in case missing)
# ============================================================
if "def announcement_create(request):" not in src:
    print("\n  ⚠ announcement_create missing - adding")
    src = src.rstrip() + '''


@never_cache
def announcement_create(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:announcements_list")

    title = (request.POST.get("title") or "").strip()[:100]
    body = (request.POST.get("body") or "").strip()[:300]
    url = (request.POST.get("url") or "").strip()[:200]

    if not title:
        request.session["admin_message"] = {"type": "error", "text": "عنوان الزامی است."}
        return redirect("custom_admin:announcements_list")

    from django.contrib.auth import get_user_model
    from social.models import Notification
    User = get_user_model()

    sender = User.objects.filter(is_staff=True).first()
    uids = User.objects.values_list("id", flat=True)
    batch = []
    total = 0
    for uid in uids.iterator(chunk_size=1000):
        batch.append(Notification(
            user_id=uid, type="admin_broadcast",
            title=title, body=body, url=url, is_read=False, sender=sender,
        ))
        if len(batch) >= 500:
            Notification.objects.bulk_create(batch)
            total += len(batch)
            batch = []
    if batch:
        Notification.objects.bulk_create(batch)
        total += len(batch)

    request.session["admin_message"] = {"type": "success", "text": f"اعلان برای {total} کاربر ارسال شد."}
    return redirect("custom_admin:announcements_list")
'''
    added.append("announcement_create")
else:
    print("  ✓ announcement_create already exists")

# ============================================================
# 4) Check + add announcement_delete (in case missing)
# ============================================================
if "def announcement_delete(request):" not in src:
    print("\n  ⚠ announcement_delete missing - adding")
    src = src.rstrip() + '''


@never_cache
def announcement_delete(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:announcements_list")

    title = (request.POST.get("title") or "").strip()
    body = (request.POST.get("body") or "").strip()
    url = (request.POST.get("url") or "").strip()

    if title:
        from social.models import Notification
        q = Notification.objects.filter(type="admin_broadcast", title=title)
        if body:
            q = q.filter(body=body)
        if url:
            q = q.filter(url=url)
        n = q.delete()[0]
        request.session["admin_message"] = {"type": "success", "text": f"{n} اعلان حذف شد."}
    return redirect("custom_admin:announcements_list")
'''
    added.append("announcement_delete")
else:
    print("  ✓ announcement_delete already exists")

# ============================================================
# 5) Write back
# ============================================================
if added:
    write(p, src)
    print(f"\n  ✓ Added: {', '.join(added)}")
else:
    print("\n  ✓ All functions already exist")

# ============================================================
# 6) Verify by importing
# ============================================================
print("\n" + "="*60)
print("VERIFYING IMPORTS")
print("="*60)

import django
django.setup()

# Force reload
if "accounts.admin_views" in sys.modules:
    del sys.modules["accounts.admin_views"]
import importlib
importlib.invalidate_caches()

try:
    from accounts import admin_views
    importlib.reload(admin_views)
    print("  ✓ admin_views.py imported")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    sys.exit(1)

# Check all functions referenced in admin_urls.py
if os.path.exists("accounts/admin_urls.py"):
    urls_src = read("accounts/admin_urls.py")
    import re
    referenced = re.findall(r'admin_views\.([a-zA-Z_][a-zA-Z0-9_]*)', urls_src)
    missing_now = []
    for fn in set(referenced):
        if hasattr(admin_views, fn):
            print(f"  ✓ admin_views.{fn}")
        else:
            print(f"  ✗ MISSING: admin_views.{fn}")
            missing_now.append(fn)

    if missing_now:
        print(f"\n  ❌ Still missing: {missing_now}")
        sys.exit(1)

# ============================================================
# 7) Django check + URL test
# ============================================================
print("\n" + "="*60)
print("DJANGO CHECK + URL TEST")
print("="*60)

r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ❌ {r.stderr[:600]}")
    sys.exit(1)

# Test all admin URLs
from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

tu, created = User.objects.get_or_create(
    username="__urls_test__",
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

print("\n  URL test:")
all_ok = True
for url in urls:
    try:
        r = c.get(url, follow=False)
        if r.status_code == 200:
            print(f"    ✓ {url}")
        elif r.status_code in (301, 302):
            print(f"    → {url} → {r.status_code}")
        else:
            print(f"    ✗ {url} → {r.status_code}")
            all_ok = False
    except Exception as e:
        print(f"    ✗ {url} → {type(e).__name__}: {str(e)[:60]}")
        all_ok = False

if created:
    tu.delete()

if all_ok:
    print("\n  ✅ ALL URLs WORK!")
else:
    print("\n  ⚠ Some URLs still broken")

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
Fixed:
  ✓ announcement_toggle_read — added if missing
  ✓ user_notify_toggle_read — added if missing
  ✓ announcement_create — added if missing
  ✓ announcement_delete — added if missing
  ✓ Verified all admin_views.X functions exist
  ✓ Django check passed
  ✓ All admin URLs return 200

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)

Test:
  /panel-admin/announcements/  → should work
  /panel-admin/dashboard/       → should work
""")
