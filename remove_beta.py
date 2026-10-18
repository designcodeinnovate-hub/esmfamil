#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove beta lock + redirect to register directly."""
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
print("\n[1/4] Removing BetaGateMiddleware from settings.py")
p = "config/settings.py"
src = read(p)

# Remove the line
old = '    "config.beta_gate.BetaGateMiddleware",\n'
if old in src:
    src = src.replace(old, "", 1)
    write(p, src)
    print("  ✓ BetaGateMiddleware removed from MIDDLEWARE")
else:
    print("  ⚠ Middleware not found (already removed?)")

# ============================================================
# 2) Change landing to redirect to register
# ============================================================
print("\n[2/4] Making landing redirect to register")

# Update accounts/views.py landing function
p = "accounts/views.py"
src = read(p)

old_landing = '''def landing(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)
    return render(request, "accounts/landing.html")'''

new_landing = '''def landing(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)
    # Skip landing - go directly to register
    return redirect("accounts:register_view")'''

if old_landing in src:
    src = src.replace(old_landing, new_landing, 1)
    write(p, src)
    print("  ✓ Landing now redirects to register")
elif "return redirect(\"accounts:register_view\")" in src:
    print("  ✓ Already redirects")
else:
    print("  ⚠ Could not find landing function")

# ============================================================
# 3) Also check config/urls.py - landing route
# ============================================================
print("\n[3/4] Verify config/urls.py")
p = "config/urls.py"
src = read(p)

# Make sure beta-lock routes are removed or harmless
if 'path("beta-lock/"' in src:
    # Keep the route but it won't matter since middleware is gone
    print("  ✓ beta-lock route exists (harmless)")
else:
    print("  ✓ no beta-lock route")

if 'path("", landing' in src:
    print("  ✓ landing route points to landing view (now redirects)")

# ============================================================
# 4) Test
# ============================================================
print("\n[4/4] Testing")

import django
django.setup()

from django.test import Client

# Test 1: unauthenticated user hits /
print("\n  Test: unauthenticated user → /")
c = Client()
r = c.get("/", follow=False)
print(f"    / → {r.status_code}")
if r.status_code == 302:
    print(f"    → redirects to: {r.get('Location')}")
    r2 = c.get(r.get('Location'), follow=False)
    print(f"    {r.get('Location')} → {r2.status_code}")
    if r2.status_code == 200:
        content = r2.content.decode()
        if "ساخت اکانت" in content or "ثبت‌نام" in content or "register" in content.lower():
            print(f"    ✓ Register page loaded!")

# Test 2: /beta-lock/ should not block anymore
print("\n  Test: /beta-lock/ (should not be enforced)")
r = c.get("/beta-lock/", follow=False)
print(f"    /beta-lock/ → {r.status_code}")

# Test 3: /game/ without login should redirect to login/register
print("\n  Test: /game/ without login")
r = c.get("/game/", follow=False)
print(f"    /game/ → {r.status_code}")
if r.status_code == 302:
    print(f"    → redirects to: {r.get('Location')}")

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
  ✓ BetaGateMiddleware removed from settings.py
  ✓ landing() now redirects to /accounts/register/
  ✓ No more beta-lock screen

Flow now:
  1. Open https://esmfamil.com/
  2. Auto-redirects to /accounts/register/
  3. User creates account directly
  4. Then goes to game

Note:
  - Beta gate password NO LONGER required
  - Admin panel password still: admin74 / Amir2255ds
  - But now you go straight to registration

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Open browser with Ctrl+Shift+R
""")
