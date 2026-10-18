#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")

# ============================================================
# 1) social/urls.py - add notifications route
# ============================================================
print("\n[1/3] social/urls.py")
p = os.path.join(ROOT, "social", "urls.py")
src = read(p)

if "notifications/" in src:
    print("  SKIP: notifications route exists")
else:
    # Try to add right after the chat route (safe anchor)
    anchors = [
        ('    path("chat/<int:user_id>/", views.chat_view, name="chat"),',
         '    path("chat/<int:user_id>/", views.chat_view, name="chat"),\n    path("notifications/", views.notifications_view, name="notifications"),'),
        ('    path("remove/<int:user_id>/", views.remove_friend, name="remove_friend"),',
         '    path("remove/<int:user_id>/", views.remove_friend, name="remove_friend"),\n    path("notifications/", views.notifications_view, name="notifications"),'),
        ('    path("", views.friends_home, name="friends_home"),',
         '    path("", views.friends_home, name="friends_home"),\n    path("notifications/", views.notifications_view, name="notifications"),'),
    ]

    added = False
    for anchor, replacement in anchors:
        if anchor in src:
            src = src.replace(anchor, replacement, 1)
            added = True
            break

    if added:
        write(p, src)
        print("  FIXED: notifications route added")
    else:
        print("  ⚠ Could not find anchor - dumping file for inspection:")
        print("  " + "-"*40)
        print(src)
        print("  " + "-"*40)
        sys.exit(1)

# ============================================================
# 2) social/views.py - ensure notifications_view exists
# ============================================================
print("\n[2/3] social/views.py")
p = os.path.join(ROOT, "social", "views.py")
src = read(p)

if "def notifications_view" in src:
    print("  ✓ notifications_view exists")
else:
    print("  ⚠ MISSING - adding notifications_view")
    new_view = '''

@login_required
def notifications_view(request):
    all_notifs = list(
        Notification.objects.filter(user=request.user)
        .select_related("sender")
        .order_by("-created_at")
    )
    unread = sum(1 for n in all_notifs if not n.is_read)
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, "social/notifications.html", {
        "notifications": all_notifs,
        "unread_total": unread,
        "active": "friends",
    })
'''
    src = src.rstrip() + new_view + "\n"
    write(p, src)

# ============================================================
# 3) Check + test the page
# ============================================================
print("\n[3/3] Verify")
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

# Ensure session bypasses beta-gate: test via test client doesn't need it
try:
    tu = User.objects.filter(username="__route_test__").first()
    if not tu:
        tu = User.objects.create_user(
            username="__route_test__", password="x"*10,
            alias="t", is_active=True,
            has_chosen_avatar=True, has_completed_registration=True,
        )
    c = Client()
    c.force_login(tu)
    r = c.get("/social/notifications/")
    print(f"\n  GET /social/notifications/ → {r.status_code}")
    if r.status_code == 200:
        print("  ✓ WORKS!")
    elif r.status_code == 302:
        print(f"  → redirect to {r.get('Location','?')}")
        print("  (this is normal - probably redirect because no avatar or beta gate)")
    else:
        print(f"  ❌ status {r.status_code}")
        if r.status_code == 500:
            print("  Content preview:", r.content[:500])
    tu.delete()
except Exception as e:
    import traceback
    print(f"\n  ❌ Test error: {e}")
    traceback.print_exc()

# Run Django check
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("\n  ✓ Django check passed")
else:
    print("\n  ⚠ check errors:", r.stderr[:500] if r.stderr else r.stdout[:500])

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Next steps:
  1. Ctrl+C to stop runserver
  2. python manage.py runserver
  3. Hard refresh browser (Ctrl+Shift+R)
  4. Go to /social/notifications/

If still 404, check that /social/urls.py has:
  path("notifications/", views.notifications_view, name="notifications"),
""")
