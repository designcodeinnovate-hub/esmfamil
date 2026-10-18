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
    bak = p + ".bak5"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

print("\n[1/2] rooms.html - super cards for player + group")
p = os.path.join(ROOT, "game", "templates", "game", "rooms.html")
src = read(p)

# ---- 1a) Replace player card ----
old_player = '''  <a href="/game/match/" class="big-card player">
    <div class="bc-icon">🌐</div>
    <div class="bc-body">
      <div class="bc-title">بازی با پلیر</div>
      <div class="bc-desc">رقابت آنی با یک حریف تصادفی</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>'''

new_player = '''  <a href="/game/match/" class="super-card super-player">
    <div class="super-glow"></div>
    <div class="super-badge">
      <span class="live-dot"></span>
      آنلاین
    </div>
    <div class="super-icon-wrap">
      <div class="super-icon">⚔️</div>
      <div class="super-icon-ring"></div>
    </div>
    <div class="super-body">
      <div class="super-title">بازی با پلیر</div>
      <div class="super-desc">یک حریف واقعی، همین الان!</div>
      <div class="super-tags">
        <span class="tag-mini">🎯 ۱v۱</span>
        <span class="tag-mini">⚡ آنی</span>
        <span class="tag-mini">🌍 جهانی</span>
      </div>
    </div>
    <div class="super-arrow">→</div>
  </a>'''

if old_player in src:
    src = src.replace(old_player, new_player, 1)
    print("  FIXED: player card upgraded")
elif 'super-player' in src:
    print("  SKIP: player card already super")
else:
    print("  WARN: player card not found")

# ---- 1b) Replace group card ----
old_group = '''  <a href="/game/team/start/" class="big-card group">
    <div class="bc-icon">👥</div>
    <div class="bc-body">
      <div class="bc-title">بازی گروهی</div>
      <div class="bc-desc">۴ نفره · دو تیم ۲ نفره · ۳ راند</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>'''

new_group = '''  <a href="/game/team/start/" class="super-card super-group">
    <div class="super-glow"></div>
    <div class="super-badge super-badge-team">
      <span>👥</span>
      ۴ نفره
    </div>
    <div class="super-icon-wrap">
      <div class="super-icon">🛡️</div>
      <div class="super-icon-ring"></div>
    </div>
    <div class="super-body">
      <div class="super-title">بازی گروهی</div>
      <div class="super-desc">تیم بساز، با هم ببرید!</div>
      <div class="super-tags">
        <span class="tag-mini">👥 ۲v۲</span>
        <span class="tag-mini">🔄 ۳ راند</span>
        <span class="tag-mini">🏆 جایزه</span>
      </div>
    </div>
    <div class="super-arrow">→</div>
  </a>'''

if old_group in src:
    src = src.replace(old_group, new_group, 1)
    print("  FIXED: group card upgraded")
elif 'super-group' in src:
    print("  SKIP: group card already super")
else:
    print("  WARN: group card not found")

# ---- 1c) Add CSS for super cards ----
if ".super-card {" not in src:
    # Insert before closing </style>
    style_end = src.find("</style>")
    if style_end > 0:
        super_css = '''

  /* ===== Super Cards (Player & Group) ===== */
  .super-card {
    position: relative;
    display: flex; align-items: center; gap: 16px;
    padding: 22px 20px;
    border-radius: 24px;
    text-decoration: none;
    color: #fff;
    margin-bottom: 14px;
    overflow: hidden;
    border: 2px solid;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    isolation: isolate;
  }
  .super-card:hover { transform: translateY(-4px) scale(1.01); }
  .super-card:active { transform: scale(0.98); }

  .super-player {
    background:
      radial-gradient(circle at 100% 0%, rgba(59,130,246,0.4), transparent 55%),
      radial-gradient(circle at 0% 100%, rgba(139,92,246,0.25), transparent 55%),
      linear-gradient(135deg, #0a1428, #0a1a2a, #0f0f1e);
    border-color: rgba(59,130,246,0.55);
    box-shadow: 0 12px 35px rgba(59,130,246,0.25), 0 0 60px rgba(59,130,246,0.1);
  }
  .super-player:hover {
    border-color: rgba(96,165,250,0.95);
    box-shadow: 0 18px 50px rgba(59,130,246,0.5), 0 0 80px rgba(59,130,246,0.25);
  }

  .super-group {
    background:
      radial-gradient(circle at 100% 0%, rgba(139,92,246,0.45), transparent 55%),
      radial-gradient(circle at 0% 100%, rgba(236,72,153,0.25), transparent 55%),
      linear-gradient(135deg, #1a0f2e, #1a0f28, #0f0f1e);
    border-color: rgba(139,92,246,0.6);
    box-shadow: 0 12px 35px rgba(139,92,246,0.3), 0 0 60px rgba(139,92,246,0.15);
  }
  .super-group:hover {
    border-color: rgba(167,139,250,0.95);
    box-shadow: 0 18px 50px rgba(139,92,246,0.55), 0 0 80px rgba(139,92,246,0.3);
  }

  /* animated glow layer */
  .super-glow {
    position: absolute;
    inset: -50%;
    background: conic-gradient(
      from 0deg,
      transparent 0deg,
      rgba(96,165,250,0.15) 90deg,
      transparent 180deg,
      rgba(139,92,246,0.15) 270deg,
      transparent 360deg
    );
    animation: superRotate 8s linear infinite;
    z-index: -1;
    opacity: 0.7;
  }
  .super-group .super-glow {
    background: conic-gradient(
      from 0deg,
      transparent 0deg,
      rgba(236,72,153,0.2) 90deg,
      transparent 180deg,
      rgba(139,92,246,0.2) 270deg,
      transparent 360deg
    );
  }
  @keyframes superRotate {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }

  /* badge */
  .super-badge {
    position: absolute; top: 12px; left: 12px;
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 10.5px; font-weight: 900;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: #fff;
    box-shadow: 0 4px 12px rgba(34,197,94,0.5);
    letter-spacing: 0.3px;
    z-index: 3;
  }
  .super-badge-team {
    background: linear-gradient(135deg, #ec4899, #8b5cf6);
    box-shadow: 0 4px 12px rgba(236,72,153,0.5);
  }
  .live-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #fff;
    box-shadow: 0 0 8px #fff;
    animation: livePulse 1.5s ease-in-out infinite;
  }
  @keyframes livePulse {
    0%,100% { opacity: 1; transform: scale(1); }
    50%     { opacity: 0.5; transform: scale(0.7); }
  }

  /* icon with pulsing ring */
  .super-icon-wrap {
    position: relative;
    flex-shrink: 0;
    width: 68px; height: 68px;
  }
  .super-icon {
    position: relative;
    width: 68px; height: 68px;
    border-radius: 20px;
    display: flex; align-items: center; justify-content: center;
    font-size: 36px;
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(10px);
    border: 1.5px solid rgba(255,255,255,0.2);
    z-index: 2;
    transition: transform 0.3s;
  }
  .super-card:hover .super-icon {
    transform: scale(1.1) rotate(-5deg);
  }
  .super-icon-ring {
    position: absolute;
    inset: -6px;
    border-radius: 26px;
    border: 2px solid;
    animation: ringPulse 2.5s ease-in-out infinite;
    z-index: 1;
  }
  .super-player .super-icon-ring { border-color: rgba(96,165,250,0.5); }
  .super-group .super-icon-ring  { border-color: rgba(167,139,250,0.5); }
  @keyframes ringPulse {
    0%   { transform: scale(0.9); opacity: 0.8; }
    50%  { transform: scale(1.15); opacity: 0.2; }
    100% { transform: scale(0.9); opacity: 0.8; }
  }

  /* body */
  .super-body { flex: 1; min-width: 0; z-index: 2; }
  .super-title {
    font-size: 19px;
    font-weight: 900;
    margin-bottom: 3px;
    letter-spacing: -0.2px;
  }
  .super-player .super-title {
    background: linear-gradient(135deg, #bfdbfe, #60a5fa, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .super-group .super-title {
    background: linear-gradient(135deg, #e9d5ff, #a78bfa, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .super-desc {
    font-size: 12.5px;
    color: rgba(226,232,240,0.85);
    margin-bottom: 8px;
    line-height: 1.4;
  }
  .super-tags {
    display: flex; gap: 5px; flex-wrap: wrap;
  }
  .tag-mini {
    font-size: 9.5px;
    font-weight: bold;
    padding: 3px 8px;
    border-radius: 6px;
    background: rgba(255,255,255,0.1);
    color: #e2e8f0;
    border: 1px solid rgba(255,255,255,0.15);
    white-space: nowrap;
  }

  /* arrow */
  .super-arrow {
    font-size: 22px;
    color: rgba(255,255,255,0.5);
    flex-shrink: 0;
    z-index: 2;
    transition: transform 0.3s;
  }
  .super-card:hover .super-arrow {
    transform: translateX(-4px);
    color: rgba(255,255,255,0.9);
  }

  @media (max-width: 420px) {
    .super-icon-wrap, .super-icon { width: 58px; height: 58px; font-size: 30px; }
    .super-title { font-size: 17px; }
    .super-card { padding: 18px 16px; gap: 12px; }
    .tag-mini { font-size: 9px; padding: 2px 6px; }
  }'''
        src = src[:style_end] + super_css + "\n" + src[style_end:]
        print("  FIXED: super card CSS added")
else:
    print("  SKIP: super card CSS already exists")

backup(p); write(p, src)

# ============================================================
# Verify
# ============================================================
print("\n[2/2] Verification")
final = read(p)
checks = [
    ("super-player", "Player card"),
    ("super-group", "Group card"),
    ("superRotate", "Rotation animation"),
    ("ringPulse", "Ring pulse animation"),
    ("livePulse", "Live dot pulse"),
    ("super-icon-wrap", "Icon wrapper"),
    ("tag-mini", "Mini tags"),
]
for needle, label in checks:
    print(f"  {'✓' if needle in final else '✗'} {label}")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
What's new:
  🎨 Bigger cards (24px radius, more padding)
  ✨ Rotating conic gradient glow behind each
  💫 Pulsing icon ring animation
  ⚔️ Player: blue theme + "آنلاین" green badge with live dot
  🛡️ Group: purple/pink theme + "۴ نفره" badge
  🏷 Mini tags (1v1, آنی, جهانی / 2v2, 3 راند, جایزه)
  🎯 Gradient text titles
  ➡️ Animated arrow on hover
  🔍 Hover: lift + scale + glow shadow

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R
""")
