#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")
def backup(p):
    bak = p + ".bak3"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) menu.html - coin HUD right + better frames + remove version badge
# ============================================================
print("\n[1/3] menu.html")
p = os.path.join(ROOT, "game", "templates", "game", "menu.html")
src = read(p)
changed = False

# 1a) Remove version badge (top-left)
old_version = '''    <div class="version-badge">
      <span>🧪</span>
      <span>نسخه آزمایشی</span>
    </div>
'''
if old_version in src:
    src = src.replace(old_version, "", 1)
    changed = True
    print("  FIXED: version badge removed")

# 1b) Also remove any leftover empty top-bar wrapper (keep just settings)
old_top_wrap = '''  <div class="top-bar">
    
    <a href="/accounts/settings/" class="settings-icon" title="تنظیمات">⚙️</a>
  </div>'''
new_top_wrap = '''  <div class="top-bar" style="justify-content: flex-end;">
    <a href="/accounts/settings/" class="settings-icon" title="تنظیمات">⚙️</a>
  </div>'''
if old_top_wrap in src:
    src = src.replace(old_top_wrap, new_top_wrap, 1)
    changed = True
    print("  FIXED: top-bar compacted")

# 1c) Coin HUD CSS - right aligned, better framing
old_css_start = "  .coin-hud {"
old_css_end_marker = "  .hud-lbl { font-size: 10px; opacity: 0.7; }"

if old_css_start in src and old_css_end_marker in src:
    start_idx = src.find(old_css_start)
    end_idx = src.find(old_css_end_marker) + len(old_css_end_marker)
    
    new_css = '''  .coin-hud {
    display: flex; gap: 8px; margin-bottom: 14px;
    justify-content: flex-end;
  }
  .hud-chip {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 4px 16px 4px 6px;
    border-radius: 999px;
    font-size: 12px; font-weight: bold;
    font-family: monospace;
    box-shadow: 0 4px 15px rgba(0,0,0,0.35);
  }
  .hud-coins {
    background: linear-gradient(135deg, rgba(234,179,8,0.25), rgba(244,197,66,0.1));
    border: 2px solid rgba(234,179,8,0.65);
    box-shadow: 0 4px 15px rgba(234,179,8,0.25);
  }
  .hud-gems {
    background: linear-gradient(135deg, rgba(139,92,246,0.25), rgba(6,182,212,0.1));
    border: 2px solid rgba(139,92,246,0.65);
    box-shadow: 0 4px 15px rgba(139,92,246,0.25);
  }
  .hud-circle {
    width: 30px; height: 30px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
    border: 2px solid rgba(255,255,255,0.35);
  }
  .hud-coins .hud-circle {
    background: radial-gradient(circle, #fde68a 0%, #f4c542 50%, #ca8a04 100%);
    box-shadow: 0 0 12px rgba(244,197,66,0.7), inset 0 1px 2px rgba(255,255,255,0.5);
  }
  .hud-gems .hud-circle {
    background: radial-gradient(circle, #c4b5fd 0%, #8b5cf6 50%, #6b4eff 100%);
    box-shadow: 0 0 12px rgba(139,92,246,0.7), inset 0 1px 2px rgba(255,255,255,0.5);
  }
  .hud-num { font-size: 14px; color: #fff; font-weight: 900; font-family: monospace; }
  .hud-lbl { font-size: 10px; opacity: 0.75; font-weight: bold; }'''
    
    src = src[:start_idx] + new_css + src[end_idx:]
    changed = True
    print("  FIXED: coin HUD CSS (right + framed)")

if changed:
    backup(p); write(p, src)

# ============================================================
# 2) social/friends.html - remove page-head title
# ============================================================
print("\n[2/3] friends.html - remove title")
p = os.path.join(ROOT, "social", "templates", "social", "friends.html")
src = read(p)

old_title = '''  <div class="page-head">
    <h1>👥 <span>دوستان</span></h1>
  </div>

'''
if old_title in src:
    src = src.replace(old_title, "", 1)
    backup(p); write(p, src)
    print("  FIXED: page title removed")
else:
    print("  SKIP: page title not found (already removed or different)")

# ============================================================
# 3) Verification
# ============================================================
print("\n[3/3] Verification")
menu_src = read(os.path.join(ROOT, "game", "templates", "game", "menu.html"))
friends_src = read(os.path.join(ROOT, "social", "templates", "social", "friends.html"))

print("  menu.html:")
print(f"    نسخه آزمایشی present: {'نسخه آزمایشی' in menu_src}")
print(f"    coin-hud right: {'justify-content: flex-end' in menu_src}")
print(f"    circle frame: {'.hud-circle {' in menu_src}")

print("  friends.html:")
print(f"    page-head title present: {'👥 <span>دوستان</span>' in friends_src}")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Changes:
  1. Coin/Gem HUD moved to RIGHT side
  2. Better styling: circular gradient icons + pill with 2px border + glow shadow
  3. Version badge "🧪 نسخه آزمایشی" removed from menu top
  4. Friends page title "👥 دوستان" removed (redundant with bottom nav)

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R
""")
