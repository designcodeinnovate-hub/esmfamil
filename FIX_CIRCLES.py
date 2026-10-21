#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Make top-players + shop smaller and vertical"""
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

p = "game/templates/game/menu.html"
src = read(p)

# ============================================================
# 1) Replace .circle-row — make it vertical + smaller
# ============================================================
old_circle_css = re.compile(
    r'  \.circle-row \{.*?\}\n  \.circle-btn \{.*?\}\n  \.circle-btn:hover \{.*?\}\n  \.circle-btn:active \{.*?\}\n  \.cb-circle \{.*?\}\n  \.cb-circle::before \{.*?\}\n  \.cb-circle > \* \{.*?\}\n  @keyframes rotate360 \{ to \{ transform: rotate\(360deg\); \} \}\n\n  \.cb-top \{.*?\}\n  \.circle-btn:hover \.cb-top \{.*?\}\n  \.cb-shop \{.*?\}\n  \.circle-btn:hover \.cb-shop \{.*?\}\n  \.cb-label \{.*?\}\n  \.cb-top-label \{.*?\}\n  \.cb-shop-label \{.*?\}',
    re.DOTALL
)

new_css = '''  /* ============ CIRCLE BUTTONS (small, vertical) ============ */
  .circle-row {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 18px;
    position: relative;
    z-index: 2;
  }
  .circle-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    text-decoration: none;
    color: #fff;
    transition: transform 0.2s;
  }
  .circle-btn:hover { transform: translateX(-3px); }
  .circle-btn:active { transform: scale(0.95); }
  .cb-circle {
    width: 48px; height: 48px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; border: 2px solid;
    position: relative; overflow: hidden;
    transition: all 0.3s;
    flex-shrink: 0;
  }
  .cb-circle::before {
    content: ""; position: absolute; inset: -100%;
    background: conic-gradient(from 0deg, transparent, rgba(255,255,255,0.2), transparent);
    animation: rotate360 8s linear infinite;
    opacity: 0.6;
  }
  .cb-circle > * { position: relative; z-index: 1; }
  @keyframes rotate360 { to { transform: rotate(360deg); } }

  .cb-top {
    background: radial-gradient(circle at 30% 30%, rgba(244,197,66,0.4), rgba(234,179,8,0.15));
    border-color: rgba(244,197,66,0.7);
    box-shadow: 0 0 15px rgba(244,197,66,0.4), inset 0 0 10px rgba(244,197,66,0.2);
  }
  .circle-btn:hover .cb-top {
    box-shadow: 0 0 28px rgba(244,197,66,0.9), inset 0 0 15px rgba(244,197,66,0.4);
    border-color: #fde68a;
  }
  .cb-shop {
    background: radial-gradient(circle at 30% 30%, rgba(6,182,212,0.4), rgba(34,197,94,0.15));
    border-color: rgba(6,182,212,0.7);
    box-shadow: 0 0 15px rgba(6,182,212,0.4), inset 0 0 10px rgba(6,182,212,0.2);
  }
  .circle-btn:hover .cb-shop {
    box-shadow: 0 0 28px rgba(6,182,212,0.9), inset 0 0 15px rgba(6,182,212,0.4);
    border-color: #67e8f9;
  }
  .cb-label { font-size: 13px; font-weight: 900; letter-spacing: 0.3px; }
  .cb-top-label { color: #fde68a; }
  .cb-shop-label { color: #67e8f9; }'''

m = old_circle_css.search(src)
if m:
    src = src[:m.start()] + new_css + src[m.end():]
    write(p, src)
    print("  ✓ CSS replaced")
else:
    print("  ⚠ CSS pattern not found — doing line-based replacement")
    # Fallback: replace key CSS properties
    replacements = [
        # Make container vertical
        ('display: flex; gap: 16px; justify-content: space-around;', 'display: flex; flex-direction: column; align-items: flex-start; gap: 10px;'),
        # Smaller circles
        ('width: 76px; height: 76px; border-radius: 50%;', 'width: 48px; height: 48px; border-radius: 50%;'),
        # Smaller icon font
        ('font-size: 32px; border: 3px solid;', 'font-size: 22px; border: 2px solid;'),
        # Smaller border
        ('border: 3px solid;', 'border: 2px solid;'),
    ]
    changed = False
    for old, new in replacements:
        if old in src:
            src = src.replace(old, new)
            changed = True

    # Make circle-btn horizontal (icon + label side by side)
    old_cb = '''  .circle-btn {
    display: flex; flex-direction: column; align-items: center; gap: 8px;
    cursor: pointer; text-decoration: none; color: #fff;
    transition: transform 0.25s;
  }'''
    new_cb = '''  .circle-btn {
    display: flex; align-items: center; gap: 10px;
    cursor: pointer; text-decoration: none; color: #fff;
    transition: transform 0.2s;
  }'''
    if old_cb in src:
        src = src.replace(old_cb, new_cb)
        changed = True

    # Smaller label
    src = src.replace('font-size: 12px; font-weight: 900; letter-spacing: 0.3px;', 'font-size: 13px; font-weight: 900; letter-spacing: 0.3px;')
    src = src.replace('font-size: 13px; font-weight: 900; letter-spacing: 0.3px;', 'font-size: 13px; font-weight: 900; letter-spacing: 0.3px;')

    if changed:
        write(p, src)
        print("  ✓ CSS updated via replacements")
    else:
        print("  ✗ No changes applied — pattern didn't match")

# ============================================================
# Also add explicit override at end of <style> to force vertical
# ============================================================
print("\n[2/2] Adding override block")
src = read(p)

if "/* FORCE VERTICAL */" not in src:
    override = '''

  /* FORCE VERTICAL — top players & shop */
  .circle-row {
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 10px !important;
    margin-bottom: 18px !important;
  }
  .circle-btn {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
  }
  .cb-circle {
    width: 48px !important;
    height: 48px !important;
    font-size: 22px !important;
    border-width: 2px !important;
  }
  .cb-label { font-size: 13px !important; }
'''
    style_end = src.find("</style>")
    if style_end > 0:
        src = src[:style_end] + override + src[style_end:]
        write(p, src)
        print("  ✓ Override CSS added")

# Final check
print("\n[check] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True, timeout=30)
if r.returncode == 0:
    print("  ✓ PASSED")
else:
    print(f"  ⚠ {r.stderr[:300] if r.stderr else r.stdout[:300]}")

print("\n" + "="*60)
print("✅ تمام")
print("="*60)
print("""
تغییرات:

  ✓ دایره‌ها کوچیک‌تر شدن (76px → 48px)
  ✓ عمودی شدن (یکی بالا، یکی پایین)
  ✓ آیکون + متن کنار هم (نه زیر هم)
  ✓ alignment به سمت چپ (RTL: یعنی راست)

حالا:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)

بعد برو:
  http://127.0.0.1:8000/game/
""")
