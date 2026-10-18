#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")
def backup(p):
    bak = p + ".bak2"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) base.html - برگردوندن ۵ آیتم به نوار پایین
# ============================================================
print("\n[1/3] base.html - restore 5-item bottom nav")
p = os.path.join(ROOT, "templates", "base.html")
src = read(p)

# Find and replace entire nav
pat = re.compile(r'<nav class="bottom-nav">.*?</nav>', re.DOTALL)
m = pat.search(src)
if m:
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
    src = src[:m.start()] + new_nav + src[m.end():]
    backup(p); write(p, src)
    print("  FIXED: nav has 5 items (خانه، بازی‌ها، اتاق‌ها، دوستان، پروفایل)")
else:
    print("  WARN: bottom-nav not found")

# ============================================================
# 2) menu.html - حذف آیکن دوستان از top-bar
# ============================================================
print("\n[2/3] menu.html - remove friends icon from top-bar")
p = os.path.join(ROOT, "game", "templates", "game", "menu.html")
src = read(p)

# Remove friends icon - the wrapper div with both icons
old = '''    <div style="display:flex; gap:8px;">
      <a href="/social/" class="settings-icon" title="دوستان">👥</a>
      <a href="/accounts/settings/" class="settings-icon" title="تنظیمات">⚙️</a>
    </div>'''
new = '''    <a href="/accounts/settings/" class="settings-icon" title="تنظیمات">⚙️</a>'''

if old in src:
    src = src.replace(old, new, 1)
    backup(p); write(p, src)
    print("  FIXED: friends icon removed from top-bar")
else:
    print("  SKIP: friends icon not found (already removed)")

# ============================================================
# 3) Verification - چک کنیم چیزی نمونده
# ============================================================
print("\n[3/3] Verification")
src = read(os.path.join(ROOT, "templates", "base.html"))

# Count nav items
nav_match = re.search(r'<nav class="bottom-nav">(.*?)</nav>', src, re.DOTALL)
if nav_match:
    nav_content = nav_match.group(1)
    count = nav_content.count('<a href=')
    print(f"  ✓ Bottom nav has {count} items")
    for label in ["خانه", "بازی‌ها", "اتاق‌ها", "دوستان", "پروفایل"]:
        if label in nav_content:
            print(f"    ✓ {label}")

# Check menu for stray friends icon
menu_src = read(os.path.join(ROOT, "game", "templates", "game", "menu.html"))
if '/social/' in menu_src and 'settings-icon' in menu_src.split('/social/')[1][:100]:
    print("  ⚠ WARNING: /social/ still near settings-icon in menu.html - check manually")
else:
    print("  ✓ No friends icon in menu top-bar")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Changes:
  1. Bottom nav restored to 5 items:
     🏠 خانه | 🎮 بازی‌ها | 🚪 اتاق‌ها | 👥 دوستان | 👤 پروفایل
  2. Removed 👥 friends icon from menu.html top-bar (was only ⚙️ there)
  3. Coin/gem HUD stays (as you requested earlier)

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R
""")
