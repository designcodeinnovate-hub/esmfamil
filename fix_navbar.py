#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix bottom-nav overlap bug."""
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
# FIX 1: templates/base.html
# ============================================================
print("\n[1/2] Fixing templates/base.html ...")
base = os.path.join(ROOT, "templates", "base.html")
src = read(base)
backup(base)
changes = 0

# ---- 1a) height: 100% -> only on html (remove from body) ----
old_rule = "    html, body { height: 100%; }"
new_rule = "    html { height: 100%; }"
if old_rule in src:
    src = src.replace(old_rule, new_rule, 1)
    print("  FIXED: html,body height -> html only")
    changes += 1
elif new_rule in src:
    print("  SKIP: html height already fixed")
else:
    print("  WARN: html,body rule not found!")

# ---- 1b) body padding-bottom with safe-area support ----
if "calc(72px + env(safe-area-inset-bottom, 0px) + 20px)" in src:
    print("  SKIP: body padding-bottom already fixed")
else:
    old_pad = "      padding-bottom: 92px;\n"
    new_pad = (
        "      padding-bottom: 92px;\n"
        "      padding-bottom: calc(72px + env(safe-area-inset-bottom, 0px) + 20px);\n"
    )
    if old_pad in src:
        src = src.replace(old_pad, new_pad, 1)
        print("  FIXED: body padding-bottom -> calc(72 + safe-area + 20)")
        changes += 1
    else:
        print("  WARN: body padding-bottom not found!")

# ---- 1c) .bottom-nav height with safe-area ----
old_nav_block = (
    "    .bottom-nav {\n"
    "      position: fixed;\n"
    "      bottom: 0; left: 0; right: 0;\n"
    "      height: 72px;\n"
    "      background: var(--nav-bg);"
)
new_nav_block = (
    "    .bottom-nav {\n"
    "      position: fixed;\n"
    "      bottom: 0; left: 0; right: 0;\n"
    "      height: 72px;\n"
    "      height: calc(72px + env(safe-area-inset-bottom, 0px));\n"
    "      background: var(--nav-bg);"
)
if "height: calc(72px + env(safe-area-inset-bottom, 0px));\n      background: var(--nav-bg);" in src:
    print("  SKIP: bottom-nav height already fixed")
elif old_nav_block in src:
    src = src.replace(old_nav_block, new_nav_block, 1)
    print("  FIXED: bottom-nav height -> calc(72 + safe-area)")
    changes += 1
else:
    print("  WARN: .bottom-nav block not found!")

# ---- 1d) bottom-nav padding-bottom: add 0px fallback ----
old_pad_nav = "      padding-bottom: env(safe-area-inset-bottom);\n"
new_pad_nav = (
    "      padding-bottom: 0;\n"
    "      padding-bottom: env(safe-area-inset-bottom, 0px);\n"
)
if "padding-bottom: env(safe-area-inset-bottom, 0px);" in src:
    print("  SKIP: bottom-nav padding-bottom already fixed")
elif old_pad_nav in src:
    src = src.replace(old_pad_nav, new_pad_nav, 1)
    print("  FIXED: bottom-nav padding-bottom -> env with 0px fallback")
    changes += 1
else:
    print("  WARN: bottom-nav padding-bottom not found!")

if changes > 0:
    write(base, src)

# ============================================================
# FIX 2: game/templates/game/bot_play.html
# ============================================================
print("\n[2/2] Fixing game/templates/game/bot_play.html ...")
bp = os.path.join(ROOT, "game", "templates", "game", "bot_play.html")
src = read(bp)
backup(bp)
changes = 0

old_stop = (
    "  .stop-wrapper {\n"
    "    position: fixed; bottom: 80px; left: 16px; right: 16px; max-width: 520px; margin: 0 auto; z-index: 50;\n"
    "  }"
)
new_stop = (
    "  .stop-wrapper {\n"
    "    position: fixed; left: 16px; right: 16px; max-width: 520px; margin: 0 auto; z-index: 50;\n"
    "    bottom: 80px;\n"
    "    bottom: calc(72px + env(safe-area-inset-bottom, 0px) + 8px);\n"
    "  }"
)
if "bottom: calc(72px + env(safe-area-inset-bottom, 0px) + 8px);" in src:
    print("  SKIP: stop-wrapper already fixed")
elif old_stop in src:
    src = src.replace(old_stop, new_stop, 1)
    print("  FIXED: stop-wrapper bottom -> calc(72 + safe-area + 8)")
    changes += 1
else:
    print("  WARN: .stop-wrapper not found!")
    # Try looser match
    import re
    pat = re.compile(r"\.stop-wrapper\s*\{[^}]*bottom:\s*80px;[^}]*\}")
    m = pat.search(src)
    if m:
        new_block = m.group(0).replace(
            "bottom: 80px;",
            "bottom: 80px;\n    bottom: calc(72px + env(safe-area-inset-bottom, 0px) + 8px);"
        )
        src = src.replace(m.group(0), new_block, 1)
        print("  FIXED: stop-wrapper (loose match)")
        changes += 1

if changes > 0:
    write(bp, src)

# ============================================================
print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
What was fixed:
  1. base.html:  body no longer stuck at 100vh (content can grow)
  2. base.html:  padding-bottom now uses safe-area-inset for iPhone
  3. base.html:  bottom-nav height adjusts for safe-area (not squeezed)
  4. bot_play:   stop-button position adjusts for safe-area

Next steps:
  - Restart server: Ctrl+C then `python manage.py runserver`
  - Hard-refresh browser: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
""")
