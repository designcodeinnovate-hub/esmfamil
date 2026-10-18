#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")
def backup(p):
    bak = p + ".bak6"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

p = os.path.join(ROOT, "game", "templates", "game", "rooms.html")
src = read(p)

# ---- 1) بازی با بات ----
old_bot = '''  <a href="/game/quick/" class="big-card bot">
    <div class="bc-icon">⚡</div>
    <div class="bc-body">
      <div class="bc-title">بازی با بات</div>
      <div class="bc-desc">رقیب هوشمند، سه سطح سختی</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>'''

new_bot = '''  <a href="/game/quick/" class="super-card super-bot">
    <div class="super-glow"></div>
    <div class="super-badge super-badge-bot">
      <span>🤖</span>
      هوش مصنوعی
    </div>
    <div class="super-icon-wrap">
      <div class="super-icon">⚡</div>
      <div class="super-icon-ring"></div>
    </div>
    <div class="super-body">
      <div class="super-title">بازی با بات</div>
      <div class="super-desc">هر وقت خواستی، بدون انتظار!</div>
      <div class="super-tags">
        <span class="tag-mini">🎯 ۳ سطح</span>
        <span class="tag-mini">⚡ آنی</span>
        <span class="tag-mini">🚀 بی‌پایان</span>
      </div>
    </div>
    <div class="super-arrow">→</div>
  </a>'''

if old_bot in src:
    src = src.replace(old_bot, new_bot, 1)
    print("  FIXED: bot card upgraded")
elif 'super-bot' in src:
    print("  SKIP: bot card already super")
else:
    print("  WARN: bot card not found")

# ---- 2) بازی سرعتی ----
old_speed = '''  <a href="/game/quick/bot/?mode=speed" class="big-card speed">
    <div class="bc-icon">⏱️</div>
    <div class="bc-body">
      <div class="bc-title">بازی سرعتی</div>
      <div class="bc-desc">مستقیم با حرف رندوم، فقط ۲۰ ثانیه!</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>'''

new_speed = '''  <a href="/game/quick/bot/?mode=speed" class="super-card super-speed">
    <div class="super-glow"></div>
    <div class="super-badge super-badge-speed">
      <span>⏱️</span>
      ۲۰ ثانیه
    </div>
    <div class="super-icon-wrap">
      <div class="super-icon">🔥</div>
      <div class="super-icon-ring"></div>
    </div>
    <div class="super-body">
      <div class="super-title">بازی سرعتی</div>
      <div class="super-desc">فقط ۲۰ ثانیه! سریع فکر کن</div>
      <div class="super-tags">
        <span class="tag-mini">⏱️ ۲۰s</span>
        <span class="tag-mini">🎲 حرف رندوم</span>
        <span class="tag-mini">💥 فشار</span>
      </div>
    </div>
    <div class="super-arrow">→</div>
  </a>'''

if old_speed in src:
    src = src.replace(old_speed, new_speed, 1)
    print("  FIXED: speed card upgraded")
elif 'super-speed' in src:
    print("  SKIP: speed card already super")
else:
    print("  WARN: speed card not found")

# ---- 3) بازی معما (soon) ----
old_puzzle = '''  <div class="big-card puzzle soon" onclick="alert('🎯 بازی معما به زودی فعال می‌شود!')">
    <span class="soon-badge">به زودی</span>
    <div class="bc-icon">🎯</div>
    <div class="bc-body">
      <div class="bc-title">بازی معما</div>
      <div class="bc-desc">حدس کلمه از روی سرنخ</div>
    </div>
    <div class="bc-arrow">←</div>
  </div>'''

new_puzzle = '''  <div class="super-card super-puzzle soon" onclick="alert('🎯 بازی معما به زودی فعال می‌شود!')">
    <div class="super-glow" style="animation: none; opacity: 0.3;"></div>
    <div class="super-badge super-badge-soon">
      <span>⏳</span>
      به زودی
    </div>
    <div class="super-icon-wrap">
      <div class="super-icon">🎯</div>
      <div class="super-icon-ring" style="animation: none;"></div>
    </div>
    <div class="super-body">
      <div class="super-title">بازی معما</div>
      <div class="super-desc">حدس کلمه از روی سرنخ</div>
      <div class="super-tags">
        <span class="tag-mini">🧩 پازل</span>
        <span class="tag-mini">🤔 سرنخ</span>
        <span class="tag-mini">🔍 حدس</span>
      </div>
    </div>
    <div class="super-arrow">→</div>
  </div>'''

if old_puzzle in src:
    src = src.replace(old_puzzle, new_puzzle, 1)
    print("  FIXED: puzzle card upgraded")
elif 'super-puzzle' in src:
    print("  SKIP: puzzle card already super")
else:
    print("  WARN: puzzle card not found")

# ---- 4) Add CSS for new themes ----
if ".super-bot {" not in src:
    css_anchor = "  @media (max-width: 420px) {\n    .super-icon-wrap, .super-icon { width: 58px; height: 58px; font-size: 30px; }"
    new_css = '''  /* ===== Bot card (gold) ===== */
  .super-bot {
    background:
      radial-gradient(circle at 100% 0%, rgba(244,197,66,0.4), transparent 55%),
      radial-gradient(circle at 0% 100%, rgba(249,115,22,0.25), transparent 55%),
      linear-gradient(135deg, #2a1a0e, #1f1408, #1a0f1a);
    border-color: rgba(244,197,66,0.55);
    box-shadow: 0 12px 35px rgba(244,197,66,0.25), 0 0 60px rgba(244,197,66,0.1);
  }
  .super-bot:hover {
    border-color: rgba(251,211,77,0.95);
    box-shadow: 0 18px 50px rgba(244,197,66,0.5), 0 0 80px rgba(244,197,66,0.25);
  }
  .super-bot .super-glow {
    background: conic-gradient(
      from 0deg,
      transparent 0deg,
      rgba(244,197,66,0.18) 90deg,
      transparent 180deg,
      rgba(249,115,22,0.18) 270deg,
      transparent 360deg
    );
  }
  .super-bot .super-title {
    background: linear-gradient(135deg, #fef3c7, #f4c542, #d97706);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  }
  .super-bot .super-icon-ring { border-color: rgba(251,211,77,0.5); }
  .super-badge-bot {
    background: linear-gradient(135deg, #f4c542, #d97706) !important;
    color: #1a1a1a !important;
    box-shadow: 0 4px 12px rgba(244,197,66,0.5) !important;
  }

  /* ===== Speed card (cyan) ===== */
  .super-speed {
    background:
      radial-gradient(circle at 100% 0%, rgba(6,182,212,0.45), transparent 55%),
      radial-gradient(circle at 0% 100%, rgba(59,130,246,0.25), transparent 55%),
      linear-gradient(135deg, #0a1e2a, #0a1928, #0f0f1e);
    border-color: rgba(6,182,212,0.6);
    box-shadow: 0 12px 35px rgba(6,182,212,0.3), 0 0 60px rgba(6,182,212,0.15);
  }
  .super-speed:hover {
    border-color: rgba(34,211,238,0.95);
    box-shadow: 0 18px 50px rgba(6,182,212,0.55), 0 0 80px rgba(6,182,212,0.3);
  }
  .super-speed .super-glow {
    background: conic-gradient(
      from 0deg,
      transparent 0deg,
      rgba(34,211,238,0.2) 90deg,
      transparent 180deg,
      rgba(6,182,212,0.2) 270deg,
      transparent 360deg
    );
    animation: superRotate 4s linear infinite;
  }
  .super-speed .super-title {
    background: linear-gradient(135deg, #a5f3fc, #22d3ee, #0891b2);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  }
  .super-speed .super-icon-ring { border-color: rgba(34,211,238,0.5); animation: ringPulse 1.5s ease-in-out infinite; }
  .super-badge-speed {
    background: linear-gradient(135deg, #22d3ee, #0891b2) !important;
    color: #fff !important;
    box-shadow: 0 4px 12px rgba(34,211,238,0.5) !important;
  }

  /* ===== Puzzle card (green, soon) ===== */
  .super-puzzle {
    background:
      radial-gradient(circle at 100% 0%, rgba(34,197,94,0.35), transparent 55%),
      radial-gradient(circle at 0% 100%, rgba(16,185,129,0.2), transparent 55%),
      linear-gradient(135deg, #0a2a1a, #0a1f15, #0f0f1e);
    border-color: rgba(34,197,94,0.55);
    box-shadow: 0 12px 35px rgba(34,197,94,0.2);
  }
  .super-puzzle.soon {
    cursor: not-allowed;
    opacity: 0.8;
  }
  .super-puzzle.soon:hover {
    transform: none;
    border-color: rgba(34,197,94,0.55);
    box-shadow: 0 12px 35px rgba(34,197,94,0.2);
  }
  .super-puzzle .super-glow {
    background: conic-gradient(
      from 0deg,
      transparent 0deg,
      rgba(34,197,94,0.15) 90deg,
      transparent 180deg,
      rgba(16,185,129,0.15) 270deg,
      transparent 360deg
    );
  }
  .super-puzzle .super-title {
    background: linear-gradient(135deg, #bbf7d0, #4ade80, #16a34a);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  }
  .super-puzzle .super-icon-ring { border-color: rgba(74,222,128,0.5); }
  .super-badge-soon {
    background: linear-gradient(135deg, #eab308, #ca8a04) !important;
    color: #1a1a1a !important;
    box-shadow: 0 4px 12px rgba(234,179,8,0.5) !important;
  }

  @media (max-width: 420px) {
    .super-icon-wrap, .super-icon { width: 58px; height: 58px; font-size: 30px; }'''
    
    if css_anchor in src:
        src = src.replace(css_anchor, new_css, 1)
        print("  FIXED: CSS for bot/speed/puzzle added")
    else:
        # fallback: insert before closing </style>
        style_end = src.find("</style>")
        if style_end > 0:
            src = src[:style_end] + new_css + "\n" + src[style_end:]
            print("  FIXED: CSS added (fallback)")
else:
    print("  SKIP: CSS already exists")

backup(p); write(p, src)

# Verify
print("\n[Verify]")
final = read(p)
checks = ["super-bot", "super-speed", "super-puzzle", "super-badge-bot", "super-badge-speed", "super-badge-soon"]
for c in checks:
    print(f"  {'✓' if c in final else '✗'} {c}")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
All game cards are now super cards:
  ⚡ باتی   → gold theme
  ⚔️ پلیر    → blue theme (was already)
  🛡️ گروهی   → purple/pink theme (was already)
  ⏱️ سرعتی  → cyan theme (faster animation)
  🎯 معما   → green theme (muted, soon)

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R
""")
