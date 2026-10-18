#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Complete rooms diagnostic - finds EXACTLY where it breaks."""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from game.models import Game, Player
User = get_user_model()

print("\n" + "="*70)
print("ROOMS COMPLETE DIAGNOSTIC")
print("="*70)

# ============================================================
# STEP 1: Create fresh test user (like a real player)
# ============================================================
print("\n[STEP 1] Creating fresh test user (simulates real player)")
tu, created = User.objects.get_or_create(
    username="__room_user__",
    defaults={
        "alias": "roomtest",
        "is_active": True,
        "has_chosen_avatar": True,
        "has_completed_registration": True,
    }
)
if created:
    tu.set_password("test123")
    tu.save()
    print(f"  ✓ Created: {tu.username}")
else:
    print(f"  ✓ Using: {tu.username}")

print(f"  → has_chosen_avatar: {tu.has_chosen_avatar}")
print(f"  → has_completed_registration: {tu.has_completed_registration}")
print(f"  → is_active: {tu.is_active}")
print(f"  → is_guest: {tu.is_guest}")

# ============================================================
# STEP 2: Login with test client
# ============================================================
print("\n[STEP 2] Login")
c = Client()
c.force_login(tu)
c.session["beta_unlocked"] = True
c.session.save()
print("  ✓ Logged in + beta unlocked")

# ============================================================
# STEP 3: Check current rooms in DB
# ============================================================
print("\n[STEP 3] Current rooms in DB")
all_rooms = Game.objects.all().order_by("-created_at")[:10]
print(f"  Total rooms: {Game.objects.count()}")
for r in all_rooms:
    print(f"    {r.code} - '{r.room_name}' - mode={r.mode} - status={r.status} - host={r.host.alias} - players={r.players.count()}/{r.max_players}")

# ============================================================
# STEP 4: GET /game/rooms/manage/
# ============================================================
print("\n[STEP 4] GET /game/rooms/manage/")
r = c.get("/game/rooms/manage/", follow=False)
print(f"  Status: {r.status_code}")
if r.status_code == 302:
    print(f"  ⚠ REDIRECT to: {r.get('Location')}")
    print(f"     (this means _require_complete is blocking)")
if r.status_code == 500:
    print(f"  ❌ ERROR: {r.content.decode()[:500]}")

# ============================================================
# STEP 5: POST create room (simulate form submit)
# ============================================================
print("\n[STEP 5] POST create room (simulate user filling form)")
rooms_before = Game.objects.count()
print(f"  Rooms before: {rooms_before}")

r = c.post("/game/rooms/manage/", {
    "room_name": "__DIAG_ROOM__",
    "password": "",
    "max_players": "8",
    "categories": ["اسم", "فامیل", "میوه"],
}, follow=False)

print(f"  Status: {r.status_code}")
if r.status_code == 302:
    redirect_url = r.get("Location", "")
    print(f"  → Redirect to: {redirect_url}")
elif r.status_code == 200:
    print(f"  ⚠ Status 200 (no redirect) - form validation error?")
elif r.status_code == 500:
    print(f"  ❌ ERROR: {r.content.decode()[:800]}")

rooms_after = Game.objects.count()
print(f"  Rooms after: {rooms_after}")

if rooms_after > rooms_before:
    print(f"  ✓ Room was created!")
    new_room = Game.objects.order_by("-created_at").first()
    print(f"    Code: {new_room.code}")
    print(f"    Name: {new_room.room_name}")
    print(f"    Host: {new_room.host.alias}")
    print(f"    Players: {new_room.players.count()}")
    print(f"    Max: {new_room.max_players}")
    print(f"    Mode: {new_room.mode}")
    print(f"    Status: {new_room.status}")
    
    # ============================================================
    # STEP 6: Access the room as the host
    # ============================================================
    print(f"\n[STEP 6] Access room as host")
    print(f"  GET /game/room/{new_room.code}/")
    r = c.get(f"/game/room/{new_room.code}/", follow=False)
    print(f"  Status: {r.status_code}")
    if r.status_code == 500:
        err = r.content.decode()[:1000]
        print(f"  ❌ ERROR:\n{err}")
    elif r.status_code == 302:
        print(f"  → Redirect to: {r.get('Location')}")
    elif r.status_code == 200:
        print(f"  ✓ Room page loaded")
        content = r.content.decode()
        # Check what's in it
        checks = [
            ("room_name", new_room.room_name in content),
            ("websocket", "WebSocket" in content),
            ("chat", "chatBody" in content or "chat" in content.lower()),
            ("players", "player" in content.lower()),
            ("roomCode JS", f'"{new_room.code}"' in content),
        ]
        print(f"  Page contents:")
        for name, present in checks:
            print(f"    {'✓' if present else '✗'} {name}")
    
    # ============================================================
    # STEP 7: Join the room as another user
    # ============================================================
    print(f"\n[STEP 7] Join room as another user")
    tu2, created2 = User.objects.get_or_create(
        username="__room_user2__",
        defaults={
            "alias": "player2",
            "is_active": True,
            "has_chosen_avatar": True,
            "has_completed_registration": True,
        }
    )
    if created2:
        tu2.set_password("test123")
        tu2.save()
        print(f"  ✓ Created second user: {tu2.username}")
    
    c2 = Client()
    c2.force_login(tu2)
    c2.session["beta_unlocked"] = True
    c2.session.save()
    
    print(f"  GET /game/rooms/join/{new_room.code}/")
    r = c2.get(f"/game/rooms/join/{new_room.code}/", follow=False)
    print(f"  Status: {r.status_code}")
    if r.status_code == 302:
        print(f"  → Redirect to: {r.get('Location')}")
    elif r.status_code == 500:
        print(f"  ❌ ERROR: {r.content.decode()[:800]}")
    
    # ============================================================
    # STEP 8: GET /game/rooms/ (list page)
    # ============================================================
    print(f"\n[STEP 8] GET /game/rooms/ (list)")
    r = c.get("/game/rooms/", follow=False)
    print(f"  Status: {r.status_code}")
    if r.status_code == 500:
        print(f"  ❌ ERROR: {r.content.decode()[:500]}")
    elif r.status_code == 200:
        content = r.content.decode()
        if "/game/quick/" in content:
            print("  ✓ Contains bot link")
        else:
            print("  ✗ MISSING bot link")
        if "/game/rooms/manage/" in content:
            print("  ✓ Contains rooms link")
        else:
            print("  ✗ MISSING rooms link")
    
    # Cleanup test room
    new_room.delete()
    print(f"\n  ✓ Test room cleaned up")
    
    # Cleanup second user
    if created2:
        tu2.delete()
else:
    print(f"  ❌ Room was NOT created!")

# ============================================================
# STEP 9: Check _require_complete duplicates
# ============================================================
print("\n[STEP 9] Check _require_complete function")
views_src = read("game/views.py")
count = views_src.count("def _require_complete")
print(f"  Function defined {count} times in game/views.py")
if count > 1:
    print(f"  ⚠ DUPLICATE! This causes the last definition to win")
    print(f"    Let's check the last one...")
    # Find all definitions
    matches = [(m.start(), views_src[m.start():m.start()+300]) for m in re.finditer(r'def _require_complete', views_src)]
    for i, (pos, snippet) in enumerate(matches):
        # Extract body
        body_end = views_src.find("\ndef ", pos + 20)
        if body_end < 0:
            body_end = pos + 500
        body = views_src[pos:body_end]
        print(f"\n  Definition {i+1} (at char {pos}):")
        print(f"    {'\n'.join('    ' + l for l in body.strip().split('\n')[:10])}")

# ============================================================
# STEP 10: Cleanup
# ============================================================
print("\n[STEP 10] Cleanup")
if created:
    tu.delete()
    print(f"  ✓ Deleted {tu.username}")

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
print("""
Look for ❌ and ⚠ in output above.
Send the FULL output back.
""")
