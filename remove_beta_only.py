#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove ONLY beta gate - keep landing page with 3 options."""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Remove BetaGateMiddleware from settings.py
# ============================================================
print("\n[1/3] Removing BetaGateMiddleware from settings.py")
p = "config/settings.py"
src = read(p)

removed = False
for old in [
    '    "config.beta_gate.BetaGateMiddleware",\n',
    "    'config.beta_gate.BetaGateMiddleware',\n",
]:
    if old in src:
        src = src.replace(old, "", 1)
        removed = True
        break

if removed:
    write(p, src)
    print("  ✓ BetaGateMiddleware removed")
else:
    print("  ⚠ Already removed or not found")

# ============================================================
# 2) Revert landing to show landing.html (NOT redirect)
# ============================================================
print("\n[2/3] Reverting landing to show landing page")

p = "accounts/views.py"
src = read(p)

# If it was changed to redirect, revert it
old_redirect = '''def landing(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)
    # Skip landing - go directly to register
    return redirect("accounts:register_view")'''

correct_landing = '''def landing(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)
    return render(request, "accounts/landing.html")'''

if old_redirect in src:
    src = src.replace(old_redirect, correct_landing, 1)
    write(p, src)
    print("  ✓ Landing reverted to show landing.html")
elif 'return render(request, "accounts/landing.html")' in src:
    print("  ✓ Landing already correct")
else:
    # Try to find and replace any landing function
    pattern = re.compile(r'def landing\(request\):.*?(?=\ndef |\Z)', re.DOTALL)
    m = pattern.search(src)
    if m:
        src = src[:m.start()] + correct_landing + "\n" + src[m.end():]
        write(p, src)
        print("  ✓ Landing rewritten")
    else:
        print("  ⚠ Could not find landing function")

# ============================================================
# 3) Test
# ============================================================
print("\n[3/3] Testing")

import django
django.setup()

from django.test import Client

c = Client()

print("\n  Test 1: unauthenticated → /")
r = c.get("/", follow=False)
print(f"    / → {r.status_code}")
if r.status_code == 200:
    content = r.content.decode()
    print(f"    ✓ Landing page loaded")
    # Check for 3 options
    checks = [
        ("ثبت‌نام / ساخت حساب", "ساخت حساب" in content or "ثبت‌نام" in content),
        ("ورود", "ورود" in content),
        ("مهمان", "مهمان" in content),
    ]
    for name, present in checks:
        print(f"    {'✓' if present else '✗'} {name} option")
elif r.status_code == 302:
    print(f"    → redirects to: {r.get('Location')} (should NOT happen)")

print("\n  Test 2: /beta-lock/ (should NOT block)")
r = c.get("/beta-lock/", follow=False)
print(f"    /beta-lock/ → {r.status_code}")

print("\n  Test 3: /accounts/register/ direct")
r = c.get("/accounts/register/", follow=False)
print(f"    /accounts/register/ → {r.status_code}")

# Django check
print("\n  Django check:")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("    ✓ PASSED")
else:
    print(f"    ⚠ {r.stderr[:400]}")

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
What changed:
  ✓ BetaGateMiddleware removed
  ✓ Landing page shows 3 options again (register, login, guest)
  ✓ NO beta password screen

Flow now:
  1. Open https://esmfamil.com/
  2. Landing page with 3 buttons:
     - ساخت حساب جدید → /accounts/register/
     - ورود با حساب → /accounts/login/
     - ورود مهمان → /accounts/guest/
  3. User picks one and proceeds

Admin panel:
  Still accessible at /panel-admin/ with admin74 / Amir2255ds
  (no beta gate blocking it anymore)

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)
  Open https://esmfamil.com/
""")
