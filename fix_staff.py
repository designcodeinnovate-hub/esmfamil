#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")

p = os.path.join(ROOT, "accounts", "admin_views.py")
src = read(p)

if "def user_toggle_staff" in src:
    print("  SKIP: user_toggle_staff already exists")
else:
    # Add before tournament section or at end
    new_fn = '''

@never_cache
def user_toggle_staff(request, user_id):
    """ارتقا/حذف ادمینی کاربر."""
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:dashboard")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("custom_admin:dashboard")

    action = request.POST.get("action", "toggle")
    if action == "promote":
        u.is_staff = True
        u.save(update_fields=["is_staff"])
        request.session["admin_message"] = {"type": "success", "text": f"@{u.username} به ادمین ارتقا یافت."}
    elif action == "demote":
        u.is_staff = False
        u.save(update_fields=["is_staff"])
        request.session["admin_message"] = {"type": "success", "text": f"@{u.username} از ادمینی خارج شد."}
    else:
        u.is_staff = not u.is_staff
        u.save(update_fields=["is_staff"])
        request.session["admin_message"] = {"type": "success", "text": f"وضعیت ادمین @{u.username}: {'فعال' if u.is_staff else 'غیرفعال'}."}

    redirect_to = request.POST.get("redirect_to", "dashboard")
    if redirect_to == "edit":
        return redirect("custom_admin:user_edit", user_id=u.id)
    elif redirect_to == "detail":
        return redirect("custom_admin:user_detail", user_id=u.id)
    return redirect("custom_admin:dashboard")
'''
    src = src.rstrip() + new_fn + "\n"
    write(p, src)
    print("  FIXED: user_toggle_staff added")

# Now check for other missing views referenced in admin_urls
p_urls = os.path.join(ROOT, "accounts", "admin_urls.py")
urls_src = read(p_urls)

# Extract all admin_views.X names
import re
view_names = re.findall(r'admin_views\.([a-zA-Z_][a-zA-Z0-9_]*)', urls_src)
view_names = set(view_names)

# Get actual attributes
sys.path.insert(0, ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from accounts import admin_views
missing = [v for v in view_names if not hasattr(admin_views, v)]

if missing:
    print(f"\n  ⚠ Missing views: {missing}")
else:
    print(f"\n  ✓ All {len(view_names)} views referenced in admin_urls exist")

# Run check
print("\n[check] manage.py check")
r = subprocess.run([sys.executable, "manage.py", "check"], cwd=ROOT, capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check passed")
    print("\n  ✓ Now run: python manage.py runserver")
else:
    print("  ⚠ errors:")
    print(r.stderr[:1500] if r.stderr else r.stdout[:1500])
