#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

print("="*70)
print("FIXING BROKEN MIGRATIONS")
print("="*70)

# Find all migration files with syntax errors
broken = []
for app in ["accounts", "support", "game", "social", "alliance"]:
    mig_dir = f"{app}/migrations"
    if not os.path.exists(mig_dir):
        continue
    for f in os.listdir(mig_dir):
        if not (f.startswith("0") and f.endswith(".py")):
            continue
        path = f"{mig_dir}/{f}"
        try:
            with open(path, "r", encoding="utf-8") as fp:
                code = fp.read()
            compile(code, path, "exec")
        except SyntaxError as e:
            print(f"\n❌ BROKEN: {path}")
            print(f"   Line {e.lineno}: {e.msg}")
            broken.append(path)

print("\n" + "="*70)

# Delete broken files
if broken:
    print(f"Deleting {len(broken)} broken migration file(s):")
    for path in broken:
        os.remove(path)
        print(f"  ✓ Deleted {path}")
else:
    print("No syntax errors found")

# Check for any migration file that mentions SupportTicket (broken refs)
print("\n→ Looking for orphan SupportTicket references...")
for app in ["accounts"]:
    mig_dir = f"{app}/migrations"
    if not os.path.exists(mig_dir):
        continue
    for f in os.listdir(mig_dir):
        if not (f.startswith("0") and f.endswith(".py")):
            continue
        path = f"{mig_dir}/{f}"
        with open(path, "r", encoding="utf-8") as fp:
            content = fp.read()
        if "SupportTicket" in content:
            # Delete this file too (it's the accounts one, we want support app to own it)
            os.remove(path)
            print(f"  ✓ Deleted (has SupportTicket): {path}")

# Clean DB records
print("\n→ Cleaning DB records for deleted migrations...")
import django
django.setup()
from django.db import connection

with connection.cursor() as c:
    c.execute("SELECT id, app, name FROM django_migrations")
    records = c.fetchall()

# Get remaining migration files
existing = {}
for app in ["accounts", "support", "game", "social", "alliance"]:
    mig_dir = f"{app}/migrations"
    if not os.path.exists(mig_dir):
        continue
    existing[app] = set()
    for f in os.listdir(mig_dir):
        if f.startswith("0") and f.endswith(".py"):
            existing[app].add(f[:-3])

with connection.cursor() as c:
    for rid, app, name in records:
        if app in existing and name not in existing[app]:
            c.execute("DELETE FROM django_migrations WHERE id = %s", [rid])
            print(f"  ✓ Removed DB record: {app}.{name}")

# Now makemigrations + migrate
print("\n" + "="*70)
print("MAKING FRESH MIGRATIONS")
print("="*70)

# Ensure __init__.py
for app in ["accounts", "support", "game", "social", "alliance"]:
    mig_dir = f"{app}/migrations"
    if os.path.exists(mig_dir):
        init = f"{mig_dir}/__init__.py"
        if not os.path.exists(init):
            open(init, "w").close()
            print(f"  ✓ Created {init}")

for cmd in [
    [sys.executable, "manage.py", "makemigrations", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    print(f"\n$ {' '.join(cmd[1:])}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode == 0:
        print(r.stdout[:1000] if r.stdout.strip() else "  ✓ OK")
    else:
        print(f"  ⚠ Error:")
        print(r.stderr[:1200] if r.stderr else r.stdout[:1200])
        sys.exit(1)

# Verify
print("\n" + "="*70)
print("VERIFYING TABLES")
print("="*70)

with connection.cursor() as c:
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = set(r[0] for r in c.fetchall())

for t in ["accounts_user", "accounts_userunlockedavatar", "support_supportticket", "game_game"]:
    print(f"  {'✅' if t in tables else '❌'} {t}")

# Final check
print("\n" + "="*70)
print("FINAL CHECK")
print("="*70)
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True, timeout=30)
print(f"  {'✅ PASSED' if r.returncode == 0 else '⚠ ' + r.stderr[:300]}")

print("\n" + "="*70)
print("DONE — حالا سرور رو ران کن")
print("="*70)
