#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess, traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")

# ============================================================
# STEP 1: Setup Django
# ============================================================
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.db import connection

print("\n" + "="*70)
print("DIAGNOSTIC: Testing actual page rendering")
print("="*60)

User = get_user_model()

# Create or get test user
try:
    test_user = User.objects.filter(username="__diag_test__").first()
    if not test_user:
        test_user = User.objects.create_user(
            username="__diag_test__",
            password="test123456",
            alias="دیباگ",
            is_active=True,
            has_chosen_avatar=True,
            has_completed_registration=True,
        )
        print(f"  Created test user: {test_user.username}")
    else:
        print(f"  Using existing test user: {test_user.username}")
except Exception as e:
    print(f"  ❌ Failed to create test user: {e}")
    test_user = None

if not test_user:
    print("\n❌ Cannot continue without test user.")
    sys.exit(1)

client = Client()
client.force_login(test_user)

# Test pages
pages = [
    ("/social/", "friends"),
    ("/social/notifications/", "notifications"),
    ("/alliance/", "alliance home"),
    ("/alliance/create/", "alliance create"),
]

print("\nTesting each page...\n")
errors = []
for url, name in pages:
    try:
        response = client.get(url, follow=False)
        status = response.status_code
        if status == 200:
            print(f"  ✓ {url} ({name}) → 200 OK")
        elif status in (301, 302):
            redirect_to = response.get("Location", "?")
            print(f"  → {url} ({name}) → {status} redirect to {redirect_to}")
        elif status == 500:
            print(f"  ❌ {url} ({name}) → 500 ERROR")
            errors.append((url, "500"))
        else:
            print(f"  ⚠ {url} ({name}) → {status}")
            errors.append((url, str(status)))
    except Exception as e:
        print(f"  ❌ {url} ({name}) → EXCEPTION")
        print(f"     {type(e).__name__}: {str(e)[:200]}")
        errors.append((url, f"{type(e).__name__}: {str(e)[:200]}"))

# ============================================================
# STEP 2: Deep check — see if specific view functions exist
# ============================================================
print("\n" + "="*60)
print("CHECK: view functions exist?")
print("="*60)

# Check alliance/views.py
try:
    from alliance import views as alliance_views
    checks = [
        ("alliance_home", hasattr(alliance_views, "alliance_home")),
        ("create_alliance", hasattr(alliance_views, "create_alliance")),
        ("join_by_code", hasattr(alliance_views, "join_by_code")),
        ("join_alliance", hasattr(alliance_views, "join_alliance")),
        ("alliance_detail", hasattr(alliance_views, "alliance_detail")),
        ("alliance_edit", hasattr(alliance_views, "alliance_edit")),
        ("alliance_chat", hasattr(alliance_views, "alliance_chat")),
        ("leave_alliance", hasattr(alliance_views, "leave_alliance")),
        ("kick_member", hasattr(alliance_views, "kick_member")),
    ]
    for name, exists in checks:
        print(f"  {'✓' if exists else '❌'} alliance.views.{name}")
except Exception as e:
    print(f"  ❌ Import error: {e}")

# Check social/views.py
try:
    from social import views as social_views
    checks = [
        ("friends_home", hasattr(social_views, "friends_home")),
        ("notifications_view", hasattr(social_views, "notifications_view")),
    ]
    for name, exists in checks:
        print(f"  {'✓' if exists else '❌'} social.views.{name}")
except Exception as e:
    print(f"  ❌ Import error: {e}")

# ============================================================
# STEP 3: Check DB schema — sender field on Notification
# ============================================================
print("\n" + "="*60)
print("CHECK: Database schema")
print("="*60)

try:
    with connection.cursor() as cursor:
        # Check Notification has sender_id
        cursor.execute("PRAGMA table_info(social_notification)")
        cols = [r[1] for r in cursor.fetchall()]
        has_sender = "sender_id" in cols
        print(f"  {'✓' if has_sender else '❌'} social_notification.sender_id")

        # Check Tournament table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='game_tournament'")
        has_tour = cursor.fetchone() is not None
        print(f"  {'✓' if has_tour else '❌'} game_tournament table")
except Exception as e:
    print(f"  ⚠ DB check error: {e}")

# ============================================================
# STEP 4: Report errors
# ============================================================
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

if not errors:
    print("\n✅ ALL PAGES RENDER WITHOUT ERROR!")
    print("\nIf you see a blank page in browser, the issue is:")
    print("  1. Browser cache → hard refresh Ctrl+Shift+R")
    print("  2. Server not restarted → Ctrl+C then runserver")
    print("  3. Beta gate blocking → visit /beta-lock/ first")
else:
    print(f"\n❌ {len(errors)} page(s) have errors:")
    for url, err in errors:
        print(f"  - {url}: {err}")

# Cleanup test user
try:
    test_user.delete()
    print("\n  (test user cleaned up)")
except Exception:
    pass

print("\n" + "="*60)
print("DONE!")
print("="*60)
