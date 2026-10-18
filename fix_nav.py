#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Move rooms to bottom nav, move alliance to friends page."""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()

def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")

def backup(p):
    bak = p + ".bak"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) base.html - نوار پایین جدید
# ============================================================
print("\n[1/5] base.html - bottom nav")
base = os.path.join(ROOT, "templates", "base.html")
src = read(base)

if "/game/rooms/manage/" in src and "active == 'rooms'" in src:
    print("  SKIP: already updated")
else:
    old_nav = '''<nav class="bottom-nav">
  <a href="/game/" class="nav-link {% if active == 'home' %}active{% endif %}">
    <span class="nav-icon">🏠</span>
    <span>خانه</span>
  </a>
  <a href="/game/rooms/" class="nav-link {% if active == 'games' %}active{% endif %}">
    <span class="nav-icon">🎮</span>
    <span>بازی‌ها</span>
  </a>
  <a href="/alliance/" class="nav-link {% if active == 'alliance' %}active{% endif %}">
    <span class="nav-icon">🛡️</span>
    <span>اتحاد</span>
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
    new_nav = '''<nav class="bottom-nav">
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
    if old_nav in src:
        backup(base)
        src = src.replace(old_nav, new_nav, 1)
        write(base, src)
        print("  FIXED: nav updated")
    else:
        print("  WARN: old nav block not found! Run: cat templates/base.html | grep -A30 bottom-nav")

# ============================================================
# 2) game/templates/game/rooms.html - حذف کارت اتاق‌ها
# ============================================================
print("\n[2/5] game/rooms.html - remove room card")
rooms_tpl = os.path.join(ROOT, "game", "templates", "game", "rooms.html")
src = read(rooms_tpl)

old_card = '''  <a href="/game/rooms/manage/" class="big-card room">
    <div class="bc-icon">🚪</div>
    <div class="bc-body">
      <div class="bc-title">اتاق‌های بازی</div>
      <div class="bc-desc">ساخت اتاق جدید یا پیوستن به دوستان</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>'''

if 'class="big-card room"' not in src:
    print("  SKIP: card already removed")
else:
    backup(rooms_tpl)
    src = src.replace(old_card + "\n", "", 1)
    write(rooms_tpl, src)
    print("  FIXED: room card removed")

# ============================================================
# 3) social/friends.html - کارت اتحاد
# ============================================================
print("\n[3/5] social/friends.html - alliance card")
friends = os.path.join(ROOT, "social", "templates", "social", "friends.html")
src = read(friends)

if "alliance-card" in src:
    print("  SKIP: alliance card already exists")
else:
    backup(friends)
    old_css_anchor = '''  .page-head { margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }'''
    new_css_anchor = old_css_anchor + '''
  
  /* ===== کارت اتحاد ===== */
  .alliance-card {
    display: flex; align-items: center; gap: 14px;
    padding: 16px 18px;
    background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.25), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #0f0f1e);
    border: 1.5px solid rgba(139,92,246,0.4);
    border-radius: 18px;
    text-decoration: none;
    color: #fff;
    margin-bottom: 16px;
    transition: all 0.22s;
    box-shadow: 0 8px 25px rgba(139,92,246,0.15);
  }
  .alliance-card:hover {
    transform: translateY(-3px);
    border-color: rgba(139,92,246,0.8);
    box-shadow: 0 15px 35px rgba(139,92,246,0.3);
  }
  .ac-icon {
    font-size: 32px;
    width: 54px; height: 54px;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(139,92,246,0.3), rgba(6,182,212,0.15));
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    border: 1px solid rgba(255,255,255,0.1);
  }
  .ac-body { flex: 1; }
  .ac-title { font-size: 16px; font-weight: bold; margin-bottom: 3px; color: #c4b5fd; }
  .ac-desc { font-size: 12px; color: var(--muted); }
  .ac-arrow { font-size: 20px; color: #c4b5fd; }'''
    if old_css_anchor in src:
        src = src.replace(old_css_anchor, new_css_anchor, 1)

    old_head = '''  <div class="page-head">
    <h1>👥 <span>دوستان</span></h1>
  </div>

  <!-- بنر دعوت‌های دریافتی -->'''
    new_head = '''  <div class="page-head">
    <h1>👥 <span>دوستان</span></h1>
  </div>

  <!-- کارت اتحاد -->
  <a href="/alliance/" class="alliance-card">
    <div class="ac-icon">🛡️</div>
    <div class="ac-body">
      <div class="ac-title">اتحاد</div>
      <div class="ac-desc">با دوستات یه تیم بساز و با هم بازی کن</div>
    </div>
    <div class="ac-arrow">←</div>
  </a>

  <!-- بنر دعوت‌های دریافتی -->'''
    if old_head in src:
        src = src.replace(old_head, new_head, 1)
        write(friends, src)
        print("  FIXED: alliance card added")
    else:
        print("  WARN: page-head anchor not found!")

# ============================================================
# 4) alliance/views.py - active = friends
# ============================================================
print("\n[4/5] alliance/views.py - active friends")
al_views = os.path.join(ROOT, "alliance", "views.py")
src = read(al_views)
orig = src

if '"active": "alliance"' in src:
    src = src.replace('"active": "alliance"', '"active": "friends"')
    print("  FIXED: active alliance -> friends")

old = '''    return render(request, "alliance/create.html", {
        "error": error,
        "emojis": emojis,
    })'''
if old in src:
    src = src.replace(old, '''    return render(request, "alliance/create.html", {
        "error": error,
        "emojis": emojis,
        "active": "friends",
    })''', 1)
    print("  FIXED: create active")

old = '    return render(request, "alliance/join.html", {"error": error})'
if old in src:
    src = src.replace(old, '    return render(request, "alliance/join.html", {"error": error, "active": "friends"})', 1)
    print("  FIXED: join active")

old = '''    return render(request, "alliance/detail.html", {
        "alliance": a,
        "members": members_data,
        "my_role": my_membership.role,
        "is_leader": my_membership.role == "leader",
        "recent_messages": recent_messages,
        "member_count": len(members_data),
    })'''
if old in src:
    src = src.replace(old, '''    return render(request, "alliance/detail.html", {
        "alliance": a,
        "members": members_data,
        "my_role": my_membership.role,
        "is_leader": my_membership.role == "leader",
        "recent_messages": recent_messages,
        "member_count": len(members_data),
        "active": "friends",
    })''', 1)
    print("  FIXED: detail active")

old = '''    return render(request, "alliance/chat.html", {
        "alliance": a,
        "messages": messages_data,
    })'''
if old in src:
    src = src.replace(old, '''    return render(request, "alliance/chat.html", {
        "alliance": a,
        "messages": messages_data,
        "active": "friends",
    })''', 1)
    print("  FIXED: chat active")

if src != orig:
    backup(al_views)
    write(al_views, src)

# ============================================================
# 5) game/views.py - active = rooms
# ============================================================
print("\n[5/5] game/views.py - active rooms")
gv = os.path.join(ROOT, "game", "views.py")
src = read(gv)
orig = src

old = '''    return render(request, "game/rooms_manage.html", {
        "categories": DEFAULT_CATEGORIES,
        "rooms": rooms_data,
        "query": query,
        "active": "games",
    })'''
if old in src:
    src = src.replace(old, old.replace('"active": "games"', '"active": "rooms"'), 1)
    print("  FIXED: rooms_manage active")

old = '''        return render(request, "game/rooms_manage.html", {
            "categories": DEFAULT_CATEGORIES,
            "rooms": [],
            "error": "ظرفیت این اتاق پر شده است.",
            "query": "",
            "active": "games",
        })'''
if old in src:
    src = src.replace(old, old.replace('"active": "games"', '"active": "rooms"'), 1)
    print("  FIXED: join_room error active")

old = '''        if room_obj.password and room_obj.password != password:
            return render(request, "game/room_password.html", {
                "room": room_obj,
                "error": "رمز عبور اشتباه است."
            })'''
if old in src:
    src = src.replace(old, '''        if room_obj.password and room_obj.password != password:
            return render(request, "game/room_password.html", {
                "room": room_obj,
                "error": "رمز عبور اشتباه است.",
                "active": "rooms",
            })''', 1)
    print("  FIXED: password error active")

old = '''    if room_obj.password and not is_member:
        return render(request, "game/room_password.html", {"room": room_obj})'''
if old in src:
    src = src.replace(old, '''    if room_obj.password and not is_member:
        return render(request, "game/room_password.html", {
            "room": room_obj,
            "active": "rooms",
        })''', 1)
    print("  FIXED: password page active")

old = '''    return render(request, "game/room.html", {
        "room": room_obj,
        "categories": room_obj.categories,
        "players": players,
        "is_host": is_host,
        "my_is_ready": my_is_ready,
        "host": room_obj.host,
        "host_avatar": get_emoji(room_obj.host.avatar_id),
    })'''
if old in src:
    src = src.replace(old, '''    return render(request, "game/room.html", {
        "room": room_obj,
        "categories": room_obj.categories,
        "players": players,
        "is_host": is_host,
        "my_is_ready": my_is_ready,
        "host": room_obj.host,
        "host_avatar": get_emoji(room_obj.host.avatar_id),
        "active": "rooms",
    })''', 1)
    print("  FIXED: room active")

if src != orig:
    backup(gv)
    write(gv, src)

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Bottom nav:  خانه | بازی‌ها | اتاق‌ها | دوستان | پروفایل
- Alliance removed from bottom nav, now a card inside Friends page
- Rooms card removed from Games page

Next steps:
  1. Ctrl+C to stop server
  2. python manage.py runserver
  3. Hard refresh browser: Ctrl+Shift+R
""")
