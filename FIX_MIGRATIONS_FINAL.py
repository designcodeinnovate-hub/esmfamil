#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix broken migrations + create UserUnlockedAvatar table"""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

def read(p):
    try:
        with open(p, "r", encoding="utf-8") as f: return f.read()
    except: return ""
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# STEP 1: Show current migrations
# ============================================================
print("\n" + "="*70)
print("STEP 1: Current migration files")
print("="*70)

for app in ["accounts", "support", "game", "social", "alliance"]:
    mig_dir = f"{app}/migrations"
    if os.path.exists(mig_dir):
        files = sorted([f for f in os.listdir(mig_dir) if f.startswith("0") and f.endswith(".py")])
        print(f"\n{app}/migrations:")
        for f in files:
            print(f"  - {f}")

# ============================================================
# STEP 2: Find migrations with Support references (broken)
# ============================================================
print("\n" + "="*70)
print("STEP 2: Finding broken migrations")
print("="*70)

broken_files = []
for app in ["accounts"]:
    mig_dir = f"{app}/migrations"
    if not os.path.exists(mig_dir):
        continue
    for f in os.listdir(mig_dir):
        if not (f.startswith("0") and f.endswith(".py")):
            continue
        path = f"{mig_dir}/{f}"
        content = read(path)
        if "SupportTicket" in content or "SupportMessage" in content:
            print(f"  ❌ BROKEN: {path}")
            broken_files.append(path)

# ============================================================
# STEP 3: Fix or delete broken migrations
# ============================================================
print("\n" + "="*70)
print("STEP 3: Fixing broken migrations")
print("="*70)

for path in broken_files:
    content = read(path)
    
    # If it only creates SupportTicket → delete it
    if "CreateModel" in content and "name='SupportTicket'" in content:
        # Check if it does anything else
        other_models = re.findall(r"name='(\w+)'", content)
        other_models = [m for m in other_models if m not in ("SupportTicket", "SupportMessage")]
        
        if not other_models:
            # Delete the file
            os.remove(path)
            print(f"  ✓ Deleted {path}")
            continue
    
    # Otherwise, remove SupportTicket references
    # Remove the CreateModel for SupportTicket
    content = re.sub(
        r"migrations\.CreateModel\(\s*name='SupportTicket'.*?\),?\s*\n",
        '',
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r"migrations\.CreateModel\(\s*name='SupportMessage'.*?\),?\s*\n",
        '',
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r"migrations\.DeleteModel\(\s*name='SupportTicket'.*?\),?\s*\n",
        '',
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r"migrations\.DeleteModel\(\s*name='SupportMessage'.*?\),?\s*\n",
        '',
        content,
        flags=re.DOTALL
    )
    
    write(path, content)
    print(f"  ✓ Cleaned {path}")

# ============================================================
# STEP 4: Reset migration history for broken apps
# ============================================================
print("\n" + "="*70)
print("STEP 4: Checking migration records in DB")
print("="*70)

import django
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Check which tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = set(r[0] for r in cursor.fetchall())
    
    print("\nDatabase tables:")
    for t in sorted(tables):
        print(f"  - {t}")
    
    print(f"\nNeed to create:")
    if "accounts_userunlockedavatar" not in tables:
        print("  - accounts_userunlockedavatar ← MISSING")
    if "support_supportticket" not in tables:
        print("  - support_supportticket ← MISSING")
    
    # Check django_migrations records
    cursor.execute("SELECT app, name FROM django_migrations WHERE app IN ('accounts', 'support')")
    migrations_in_db = cursor.fetchall()
    
    print(f"\nMigration records in DB ({len(migrations_in_db)}):")
    for app, name in migrations_in_db:
        print(f"  - {app}.{name}")

# ============================================================
# STEP 5: Fake the broken migration (if it's recorded but file is deleted)
# ============================================================
print("\n" + "="*70)
print("STEP 5: Cleaning DB records for deleted migrations")
print("="*70)

# Get existing migration files
existing_migrations = {
    "accounts": set(),
    "support": set(),
}

for app in ["accounts", "support"]:
    mig_dir = f"{app}/migrations"
    if os.path.exists(mig_dir):
        for f in os.listdir(mig_dir):
            if f.startswith("0") and f.endswith(".py"):
                existing_migrations[app].add(f[:-3])  # Remove .py

# Find records in DB that don't have files
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT id, app, name FROM django_migrations WHERE app IN ('accounts', 'support')")
    records = cursor.fetchall()
    
    for rid, app, name in records:
        if name not in existing_migrations.get(app, set()):
            cursor.execute("DELETE FROM django_migrations WHERE id = %s", [rid])
            print(f"  ✓ Removed DB record: {app}.{name} (file doesn't exist)")

# ============================================================
# STEP 6: Create missing migrations
# ============================================================
print("\n" + "="*70)
print("STEP 6: Creating fresh migrations")
print("="*70)

# Ensure support migration folder has __init__.py
os.makedirs("support/migrations", exist_ok=True)
if not os.path.exists("support/migrations/__init__.py"):
    write("support/migrations/__init__.py", "")

for app in ["accounts", "support"]:
    print(f"\n  $ makemigrations {app}")
    r = subprocess.run(
        [sys.executable, "manage.py", "makemigrations", app, "--noinput"],
        capture_output=True, text=True, timeout=60
    )
    if r.returncode == 0:
        out = r.stdout.strip()
        if "No changes" in out:
            print(f"    ✓ No changes needed")
        else:
            print(f"    ✓ {out[:300]}")
    else:
        print(f"    ⚠ {r.stderr[:400] if r.stderr else 'unknown'}")

# ============================================================
# STEP 7: Run migrate
# ============================================================
print("\n" + "="*70)
print("STEP 7: Running migrate")
print("="*70)

r = subprocess.run(
    [sys.executable, "manage.py", "migrate", "--noinput"],
    capture_output=True, text=True, timeout=120
)
if r.returncode == 0:
    print("  ✓ Migration OK")
    if r.stdout.strip():
        print("\n" + r.stdout.strip()[:1000])
else:
    print(f"  ⚠ Error:")
    print(r.stderr[:1500] if r.stderr else r.stdout[:1500])

# ============================================================
# STEP 8: Verify tables exist
# ============================================================
print("\n" + "="*70)
print("STEP 8: Verifying tables")
print("="*70)

from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = set(r[0] for r in cursor.fetchall())
    
    for t in ["accounts_userunlockedavatar", "support_supportticket"]:
        if t in tables:
            print(f"  ✓ {t}")
        else:
            print(f"  ❌ {t} MISSING")

# ============================================================
# STEP 9: TEST all pages
# ============================================================
print("\n" + "="*70)
print("STEP 9: Testing all pages")
print("="*70)

from django.test import Client
from accounts.models import User

User.objects.filter(username__startswith="__final_test_").delete()
u = User.objects.create_user(
    username="__final_test_u", password="x"*10, alias="تست",
    is_active=True, has_chosen_avatar=True, has_completed_registration=True,
    coins=200,
)

c = Client()
c.force_login(u)
c.session["beta_unlocked"] = True
c.session.save()

tests = [
    ("/game/", "خانه"),
    ("/support/", "پشتیبانی"),
    ("/game/puzzle/", "بازی معما"),
    ("/game/guess/", "بازی ۰-۱۰۰"),
    ("/game/memory/", "بازی حافظه"),
    ("/game/rooms/", "بازی‌ها"),
    ("/accounts/avatar/", "آواتار"),
    ("/accounts/shop/", "فروشگاه"),
]

for url, name in tests:
    try:
        r = c.get(url, follow=False)
        if r.status_code == 200:
            print(f"  ✅ {url:25s} ({name})")
        elif r.status_code == 302:
            print(f"  → {url:25s} ({name}) → {r.get('Location', '')[:40]}")
        else:
            print(f"  ❌ {url:25s} ({name}) → {r.status_code}")
    except Exception as e:
        print(f"  ❌ {url:25s} ({name}) → {type(e).__name__}: {str(e)[:60]}")

u.delete()

# Final check
print("\n" + "="*70)
print("STEP 10: Final Django check")
print("="*70)

r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True, timeout=30)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:400] if r.stderr else r.stdout[:400]}")

print("\n" + "="*70)
print("DONE")
print("="*70)
print("""
اگر همه ✅ بود:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R
""")
