#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add missing messages import."""
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

print("\n[1/3] Adding messages import to accounts/views.py")
p = "accounts/views.py"
src = read(p)

if "from django.contrib import messages" in src:
    print("  ✓ messages already imported")
else:
    # Add after the first django import
    old = "from django.contrib.auth import authenticate, get_user_model, login, logout"
    new = "from django.contrib import messages\nfrom django.contrib.auth import authenticate, get_user_model, login, logout"
    if old in src:
        src = src.replace(old, new, 1)
        write(p, src)
        print("  ✓ messages imported")
    else:
        # Fallback: add at very top after imports
        lines = src.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("from django"):
                lines.insert(i, "from django.contrib import messages")
                break
        src = "\n".join(lines)
        write(p, src)
        print("  ✓ messages imported (fallback)")

print("\n[2/3] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ PASSED")
else:
    print(f"  ⚠ {r.stderr[:500]}")

print("\n[3/3] Testing support ticket creation")
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

tu, created = User.objects.get_or_create(
    username="__support_test__",
    defaults={"alias": "sup-test", "is_active": True, "has_chosen_avatar": True, "has_completed_registration": True}
)
if created:
    tu.set_password("x")
    tu.save()

c = Client()
c.force_login(tu)
c.session["beta_unlocked"] = True
c.session.save()

# Test GET
r = c.get("/accounts/support/", follow=False)
print(f"\n  GET /accounts/support/ → {r.status_code}")

# Test POST create
r = c.post("/accounts/support/", {
    "subject": "__test_support_ticket__",
    "body": "این یه پیام تستی است",
}, follow=False)
print(f"  POST create ticket → {r.status_code}")

if r.status_code == 302:
    print(f"    → redirect to: {r.get('Location')}")
    # Follow redirect
    r2 = c.get(r.get("Location"), follow=False)
    print(f"    → {r.get('Location')} → {r2.status_code}")
    if r2.status_code == 200:
        print(f"    ✓ Ticket detail page works!")

# Cleanup
from accounts.models import SupportTicket
SupportTicket.objects.filter(user=tu, subject="__test_support_ticket__").delete()

if created:
    tu.delete()

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
Fix applied:
  ✓ from django.contrib import messages added

Test:
  - /accounts/support/ — should open
  - Create a ticket → should work now
  - Bot reply appears automatically

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R

Test all new features:
  1. /accounts/support/ → create ticket → see bot reply
  2. /game/rooms/manage/ → create room → pick game type
  3. /game/room/<code>/ → ready/start buttons
  4. /panel-admin/support/ → reply to tickets
  5. /panel-admin/announcements/ → send + see readers
""")
