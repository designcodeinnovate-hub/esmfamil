#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix game/urls.py to match actual views in game/views.py"""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def read(p):
    try:
        with open(p, "r", encoding="utf-8") as f: return f.read()
    except: return ""
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) List all functions in game/views.py
# ============================================================
print("\n[1/4] Checking views...")
views_src = read("game/views.py")
functions = re.findall(r'^def ([a-zA-Z_][a-zA-Z0-9_]*)\(', views_src, re.MULTILINE)
functions = set(functions)
print(f"  Found {len(functions)} views:")
for f in sorted(functions):
    print(f"    ✓ {f}")

# ============================================================
# 2) Build clean urls.py based on actual views
# ============================================================
print("\n[2/4] Building clean game/urls.py")

# Define all routes with their required view
ROUTES = [
    ("", "home", "home"),
    ("rooms/", "rooms_list", "rooms"),
    ("rooms/manage/", "rooms_manage", "rooms_manage"),
    ("rooms/join/<str:room_code>/", "join_room", "join_room"),
    ("rooms/leave/<str:room_code>/", "leave_room", "leave_room"),
    ("room/<str:room_code>/", "room", "room"),
    ("friends/", "friends_page", "friends"),
    ("leaderboard/", "leaderboard_view", "leaderboard"),
    ("top-players/", "top_players_view", "top_players"),
    ("quick/", "quick_play", "quick_play"),
    ("quick/bot/", "bot_setup", "bot_setup"),
    ("quick/bot/play/<uuid:game_id>/", "bot_play", "bot_play"),
    ("quick/bot/submit/<uuid:game_id>/", "bot_submit", "bot_submit"),
    ("challenge/", "challenge_home", "challenge"),
    ("challenge/<int:tournament_id>/join/", "tournament_join", "tournament_join"),
    ("match/", "match_start", "match_start"),
    ("match/wait/", "match_wait", "match_wait"),
    ("match/cancel/", "match_cancel", "match_cancel"),
    ("match/status/", "match_status", "match_status"),
    ("team/start/", "team_start", "team_start"),
    ("team/wait/", "team_wait", "team_wait"),
    ("team/cancel/", "team_cancel", "team_cancel"),
    ("team/status/", "team_status", "team_status"),
    ("team/select/<str:room_code>/", "team_select", "team_select"),
    ("team/play/<str:room_code>/", "team_play", "team_play"),
    ("team/play-status/<str:room_code>/", "team_status_ajax", "team_status_ajax"),
    ("team/round-end/<str:room_code>/", "team_round_end", "team_round_end"),
    ("team/result/<str:room_code>/", "team_result", "team_result"),
    ("puzzle/", "puzzle_home", "puzzle"),
    ("puzzle/submit/", "puzzle_submit", "puzzle_submit"),
    ("memory/", "memory_home", "memory"),
    ("memory/status/", "memory_status", "memory_status"),
    ("guess/", "guess_home", "guess"),
    ("guess/attempt/", "guess_attempt", "guess_attempt"),
]

# Filter to only include routes whose view exists
valid_routes = [r for r in ROUTES if r[1] in functions]
missing_routes = [r for r in ROUTES if r[1] not in functions]

print(f"\n  Valid routes: {len(valid_routes)}")
print(f"  Missing views: {len(missing_routes)}")
for r in missing_routes:
    print(f"    ✗ {r[2]} → {r[1]}")

# Build urls.py content
url_patterns = "\n".join([
    f'    path("{r[0]}", views.{r[1]}, name="{r[2]}"),'
    for r in valid_routes
])

urls_content = f'''from django.urls import path
from . import views

app_name = "game"

urlpatterns = [
{url_patterns}
]
'''

write("game/urls.py", urls_content)

# ============================================================
# 3) Add missing critical views
# ============================================================
print("\n[3/4] Checking critical missing views")

need_puzzle_status = any(r[1] == "puzzle_status" for r in missing_routes)
need_memory_status = any(r[1] == "memory_status" for r in missing_routes)

# Check if puzzle_home and memory_home exist - if not, add basic versions
if "puzzle_home" not in functions:
    print("  ⚠ puzzle_home missing - need to add")
if "memory_home" not in functions:
    print("  ⚠ memory_home missing - need to add")
if "guess_home" not in functions:
    print("  ⚠ guess_home missing - need to add")

# ============================================================
# 4) Django check
# ============================================================
print("\n[4/4] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ PASSED")
else:
    err = r.stderr if r.stderr else r.stdout
    print(f"  ⚠ Error: {err[:800]}")
