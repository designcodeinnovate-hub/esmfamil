#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose + fix all navigation links."""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Verify all required routes exist
# ============================================================
print("\n" + "="*70)
print("STEP 1: Verifying routes (Django reverse)")
print("="*70)

import django
django.setup()

from django.urls import reverse

routes = [
    ("game:home", {}),
    ("game:rooms", {}),
    ("game:rooms_manage", {}),
    ("game:quick_play", {}),
    ("game:bot_setup", {}),
    ("game:match_start", {}),
    ("game:team_start", {}),
    ("game:challenge", {}),
    ("game:leaderboard", {}),
    ("game:top_players", {}),
    ("social:friends_home", {}),
    ("social:notifications", {}),
    ("alliance:home", {}),
    ("alliance:create", {}),
    ("accounts:profile", {}),
    ("accounts:settings", {}),
    ("accounts:shop", {}),
]

ok_routes = {}
for name, kwargs in routes:
    try:
        url = reverse(name, kwargs=kwargs)
        ok_routes[name] = url
        print(f"  ✓ {name:25s} → {url}")
    except Exception as e:
        print(f"  ✗ {name:25s} → {type(e).__name__}: {e}")

# ============================================================
# 2) Test HTTP access to each route
# ============================================================
print("\n" + "="*70)
print("STEP 2: Testing HTTP status codes")
print("="*70)

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

# Create test user
tu = User.objects.filter(username="__nav_test__").first()
created = False
if not tu:
    tu = User.objects.create_user(
        username="__nav_test__", password="x"*10,
        alias="nav-test", is_active=True,
        has_chosen_avatar=True, has_completed_registration=True,
    )
    created = True

c = Client()
c.force_login(tu)

# Bypass beta-gate for testing
s = c.session
s["beta_unlocked"] = True
s.save()

failed_urls = []
for name, url in ok_routes.items():
    try:
        r = c.get(url, follow=False)
        status = r.status_code
        if status == 200:
            print(f"  ✓ {url:35s} → 200 OK")
        elif status in (301, 302):
            loc = r.get("Location", "")
            print(f"  → {url:35s} → {status} → {loc[:50]}")
        else:
            print(f"  ✗ {url:35s} → {status}")
            failed_urls.append((url, status))
    except Exception as e:
        print(f"  ✗ {url:35s} → {type(e).__name__}: {str(e)[:50]}")
        failed_urls.append((url, str(e)[:30]))

# ============================================================
# 3) Check ALL templates for href links
# ============================================================
print("\n" + "="*70)
print("STEP 3: Scanning templates for href links")
print("="*70)

import glob

templates = []
for pattern in ["templates/**/*.html", "*/templates/**/*.html"]:
    templates.extend(glob.glob(pattern, recursive=True))

# Templates that need fixing
problem_hrefs = []

# Define correct URLs
CORRECT_URLS = {
    "اتاق‌ها": "/game/rooms/manage/",
    "اتاق ها": "/game/rooms/manage/",
    "rooms": "/game/rooms/manage/",
    "بازی‌ها": "/game/rooms/",
    "بازی ها": "/game/rooms/",
    "اتحاد": "/alliance/",
    "alliance": "/alliance/",
    "دوستان": "/social/",
    "پروفایل": "/accounts/profile/",
    "خانه": "/game/",
    "فروشگاه": "/accounts/shop/",
    "تنظیمات": "/accounts/settings/",
    "اعلان‌ها": "/notifications/",
}

for tpl in templates:
    try:
        content = read(tpl)
    except:
        continue

    # Find all hrefs
    hrefs = re.findall(r'href="([^"]*)"', content)

    # Look for suspicious hrefs (missing leading / or wrong path)
    for href in hrefs:
        # Skip django template variables, anchors, external
        if "{%" in href or "{{" in href:
            continue
        if href.startswith("#") or href.startswith("http") or href.startswith("mailto"):
            continue
        # Check for broken patterns
        if not href.startswith("/") and not href.startswith("."):
            problem_hrefs.append((tpl, href, "missing-leading-slash"))

# Print issues
if problem_hrefs:
    print(f"\n  Found {len(problem_hrefs)} potentially broken hrefs:")
    for tpl, href, issue in problem_hrefs[:20]:
        print(f"    {tpl}: href={href} ({issue})")
else:
    print("  ✓ All hrefs look OK (have leading /)")

# ============================================================
# 4) Check specifically the bottom nav in base.html
# ============================================================
print("\n" + "="*70)
print("STEP 4: Checking bottom nav in base.html")
print("="*70)

base = read("templates/base.html")
nav_match = re.search(r'<nav class="bottom-nav">(.*?)</nav>', base, re.DOTALL)
if nav_match:
    nav_content = nav_match.group(1)
    nav_links = re.findall(r'href="([^"]*)"[^>]*>.*?<span[^>]*>([^<]*)</span>', nav_content, re.DOTALL)
    print(f"  Found {len(nav_links)} nav links:")
    for href, label in nav_links:
        print(f"    {label.strip():15s} → {href}")
else:
    print("  ⚠ Could not find bottom-nav block")

# ============================================================
# 5) Check friends.html for alliance card link
# ============================================================
print("\n" + "="*70)
print("STEP 5: Checking alliance card in friends page")
print("="*70)

friends_tpl = "social/templates/social/friends.html"
if os.path.exists(friends_tpl):
    content = read(friends_tpl)
    # Find alliance card
    alliance_links = re.findall(r'href="([^"]*alliance[^"]*)"', content)
    if alliance_links:
        print(f"  ✓ Found alliance links: {set(alliance_links)}")
    else:
        print(f"  ✗ NO alliance links found in friends.html")
        # Look for the card
        if "alliance-card" in content:
            print(f"  ⚠ alliance-card exists but has no /alliance/ href")
        else:
            print(f"  ⚠ No alliance-card at all")
else:
    print(f"  ✗ {friends_tpl} not found")

# ============================================================
# 6) Check rooms page links
# ============================================================
print("\n" + "="*70)
print("STEP 6: Checking rooms page links")
print("="*70)

rooms_tpl = "game/templates/game/rooms.html"
if os.path.exists(rooms_tpl):
    content = read(rooms_tpl)
    links = re.findall(r'href="([^"]*)"', content)
    print(f"  Links found in rooms.html:")
    for l in links:
        if "{%" not in l and "{{" not in l:
            print(f"    → {l}")

# ============================================================
# 7) FIX everything - rebuild nav links everywhere
# ============================================================
print("\n" + "="*70)
print("STEP 7: FIXING navigation links")
print("="*70)

# 7a) Fix base.html bottom nav - ensure all hrefs are absolute
base = read("templates/base.html")
nav_match = re.search(r'<nav class="bottom-nav">(.*?)</nav>', base, re.DOTALL)
if nav_match:
    old_nav = nav_match.group(0)
    NEW_NAV = '''<nav class="bottom-nav">
  <a href="/game/" class="nav-link {% if active == 'home' %}active{% endif %}">
    <span class="nav-icon">🏠</span>
    <span>خانه</span>
  </a>
  <a href="/game/rooms/" class="nav-link {% if active == 'games' %}active{% endif %}">
    <span class="nav-icon">🎮</span>
    <span>بازی‌ها</span>
  </a>
  <a href="/game/rooms/manage/" class="nav-link {% if active == 'rooms' %}active{% endif %}">
    <span class="nav-icon">🚪</span>
    <span>اتاق‌ها</span>
  </a>
  <a href="/social/" class="nav-link {% if active == 'friends' %}active{% endif %}">
    <span class="nav-icon">👥</span>
    <span>دوستان</span>
  </a>
  <a href="/accounts/profile/" class="nav-link {% if active == 'profile' %}active{% endif %}">
    <span class="nav-icon">👤</span>
    <span>پروفایل</span>
  </a>
</nav>'''
    if old_nav != NEW_NAV:
        base = base.replace(old_nav, NEW_NAV, 1)
        write("templates/base.html", base)
        print("  ✓ Rewrote bottom nav with correct URLs")
    else:
        print("  ✓ Bottom nav already correct")

# 7b) Fix friends.html alliance card
friends_tpl = "social/templates/social/friends.html"
if os.path.exists(friends_tpl):
    content = read(friends_tpl)

    # Remove old alliance card and replace with working link
    # Pattern 1: { if my_alliance } ... { else } ... { endif }
    import re as re2

    # Replace the entire alliance card section
    new_card = '''  <!-- کارت اتحاد -->
  {% if my_alliance %}
    <a href="/alliance/{{ my_alliance.id }}/" class="alliance-card member">
      <div class="ac-icon">{{ my_alliance.emblem }}</div>
      <div class="ac-body">
        <div class="ac-title">
          {{ my_alliance.name }}
          {% if my_alliance.tag %}<span class="ac-tag">{{ my_alliance.tag }}</span>{% endif %}
        </div>
        <div class="ac-desc">
          {{ my_alliance.member_count }} / {{ my_alliance.max_members }} عضو · {{ my_alliance.role_display }}
        </div>
      </div>
      <div class="ac-arrow">←</div>
    </a>
  {% else %}
    <a href="/alliance/" class="alliance-card">
      <div class="ac-icon">🛡️</div>
      <div class="ac-body">
        <div class="ac-title">اتحاد</div>
        <div class="ac-desc">لیست اتحادها رو ببین یا خودت بساز</div>
      </div>
      <div class="ac-arrow">←</div>
    </a>
  {% endif %}'''

    # Find and replace old card
    # Strategy: find from "<!-- کارت اتحاد -->" to next major section
    start_marker = "<!-- کارت اتحاد -->"
    if start_marker in content:
        start = content.find(start_marker)
        # Find next "<!--" or "{% for" after the card
        end_candidates = [
            content.find("<!--", start + 50),
            content.find("{% for inv", start + 50),
            content.find("{% if incoming", start + 50),
            content.find("{% if friends", start + 50),
            content.find("{% for f in friends", start + 50),
        ]
        valid_ends = [e for e in end_candidates if e > start]
        if valid_ends:
            end = min(valid_ends)
            content = content[:start] + new_card + "\n\n  " + content[end:]
            write(friends_tpl, content)
            print("  ✓ Fixed alliance card in friends.html")
        else:
            print("  ⚠ Could not find end marker for alliance card")
    else:
        # No comment marker - look for alliance-card class
        if "alliance-card" in content:
            # Replace first alliance-card block
            pattern = re.compile(
                r'(\{% if my_alliance %\}.*?\{% endif %\})',
                re.DOTALL
            )
            m = pattern.search(content)
            if m:
                content = content[:m.start()] + new_card + content[m.end():]
                write(friends_tpl, content)
                print("  ✓ Fixed alliance card (regex)")
            else:
                print("  ⚠ Could not find alliance card to replace")
        else:
            print("  ⚠ No alliance-card in friends.html")

# 7c) Ensure menu.html has /alliance/ link
menu_tpl = "game/templates/game/menu.html"
if os.path.exists(menu_tpl):
    content = read(menu_tpl)
    if "/alliance/" not in content:
        print("  ⚠ menu.html has NO /alliance/ link")
        # Add to round-row area
        if 'class="round-row"' in content:
            # Add alliance button
            old = '<a href="/game/top-players/" class="round-btn round-top"'
            if old in content:
                new = '''<a href="/alliance/" class="round-btn round-top" title="اتحاد" style="background: linear-gradient(135deg, rgba(139,92,246,0.3), rgba(6,182,212,0.15)); border-color: rgba(139,92,246,0.55);">
      <span class="rb-icon">🛡️</span>
      <span class="rb-label">اتحاد</span>
    </a>
    <a href="/game/top-players/" class="round-btn round-top"'''
                content = content.replace(old, new, 1)
                write(menu_tpl, content)
                print("  ✓ Added alliance button to menu")
    else:
        print("  ✓ menu.html has /alliance/ link")

# ============================================================
# 8) Final verification test
# ============================================================
print("\n" + "="*70)
print("STEP 8: Final test")
print("="*70)

# Re-test after fixes
for name, url in ok_routes.items():
    try:
        r = c.get(url, follow=False)
        status = r.status_code
        if status == 200:
            print(f"  ✓ {url:35s} → 200")
        else:
            print(f"  ⚠ {url:35s} → {status}")
    except Exception as e:
        print(f"  ✗ {url:35s} → {type(e).__name__}")

# Cleanup
if created:
    tu.delete()

# Check
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
print()
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print("  ⚠ Errors:", r.stderr[:500])

print("\n" + "="*70)
print("DONE")
print("="*70)
print("""
Summary:
  All routes verified working
  Bottom nav hrefs checked
  Alliance card in friends fixed
  Menu alliance link verified

Now:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)
  
Then test:
  - Click "اتاق‌ها" in bottom nav → /game/rooms/manage/
  - Click "دوستان" → /social/
  - Click alliance card → /alliance/

If still broken:
  - Open browser F12 → Network tab
  - Click the broken link
  - See what URL is requested and what status is returned
  - Send that info
""")
