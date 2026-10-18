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
    bak = p + ".bak"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) rooms.html - حذف tournament، اضافه challenge
# ============================================================
print("\n[1/5] rooms.html")
p = os.path.join(ROOT, "game", "templates", "game", "rooms.html")
src = read(p)

# 1a) Add challenge CSS after speed
if ".big-card.challenge {" not in src:
    anchor = '  .big-card.speed  { background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.25), transparent 60%), linear-gradient(135deg, #0a1e2a, #0f0f1e); border-color: rgba(6,182,212,0.4); }'
    add = anchor + '\n  .big-card.challenge { background: radial-gradient(circle at 100% 0%, rgba(239,68,68,0.3), transparent 60%), linear-gradient(135deg, #2a0a0a, #0f0f1e); border-color: rgba(239,68,68,0.5); }'
    if anchor in src:
        src = src.replace(anchor, add, 1)
        print("  FIXED: challenge CSS added")
    else:
        print("  WARN: speed CSS not found")

# 1b) Replace tournament card with challenge card
old_tournament = '''  <div class="big-card tournament soon" onclick="alert('🏆 تورنمنت هفتگی به زودی فعال می‌شود!')">
    <span class="soon-badge">به زودی</span>
    <div class="bc-icon">🏆</div>
    <div class="bc-body">
      <div class="bc-title">تورنمنت هفتگی</div>
      <div class="bc-desc">رقابت با بهترین‌ها، جوایز ویژه</div>
    </div>
    <div class="bc-arrow">←</div>
  </div>'''

new_challenge = '''  <a href="/game/challenge/" class="big-card challenge">
    <div class="bc-icon">⚔️</div>
    <div class="bc-body">
      <div class="bc-title">چالش</div>
      <div class="bc-desc">تورنمنت هفتگی، مسابقه روزانه و ساعتی</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>'''

if old_tournament in src:
    src = src.replace(old_tournament, new_challenge, 1)
    print("  FIXED: tournament -> challenge")
elif 'href="/game/challenge/"' in src:
    print("  SKIP: challenge already exists")
else:
    print("  WARN: tournament card not found")

backup(p)
write(p, src)

# ============================================================
# 2) game/views.py - challenge_home
# ============================================================
print("\n[2/5] game/views.py")
p = os.path.join(ROOT, "game", "views.py")
src = read(p)

if "def challenge_home(request):" in src:
    print("  SKIP: challenge_home exists")
else:
    view = '''

@login_required
def challenge_home(request):
    check = _require_complete(request.user)
    if check:
        return check

    return render(request, "game/challenge.html", {
        "active": "games",
    })
'''
    marker = "@login_required\ndef rooms_manage(request):"
    if marker in src:
        src = src.replace(marker, view + "\n" + marker, 1)
    else:
        src = src.rstrip() + "\n" + view + "\n"
    backup(p)
    write(p, src)
    print("  FIXED: challenge_home added")

# ============================================================
# 3) game/urls.py - route
# ============================================================
print("\n[3/5] game/urls.py")
p = os.path.join(ROOT, "game", "urls.py")
src = read(p)

if 'path("challenge/"' in src:
    print("  SKIP: route exists")
else:
    old = '    path("quick/", views.quick_play, name="quick_play"),'
    new = old + '\n    path("challenge/", views.challenge_home, name="challenge"),'
    if old in src:
        src = src.replace(old, new, 1)
        backup(p)
        write(p, src)
        print("  FIXED: route added")
    else:
        print("  WARN: quick route not found")

# ============================================================
# 4) challenge.html - صفحه جدید
# ============================================================
print("\n[4/5] challenge.html")
p = os.path.join(ROOT, "game", "templates", "game", "challenge.html")

CHALLENGE_HTML = '''{% extends "base.html" %}
{% block title %}چالش{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }

  .intro-card {
    text-align: center; padding: 24px 20px;
    background: radial-gradient(circle at 100% 0%, rgba(239,68,68,0.25), transparent 60%),
                radial-gradient(circle at 0% 100%, rgba(244,197,66,0.15), transparent 60%),
                linear-gradient(135deg, #2a0a0a, #0f0f1e);
    border: 1.5px solid rgba(239,68,68,0.4);
    border-radius: 20px; margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(239,68,68,0.15);
  }
  .intro-card .icon { font-size: 56px; margin-bottom: 8px; filter: drop-shadow(0 0 20px rgba(239,68,68,0.4)); }
  .intro-card h2 {
    font-size: 20px; font-weight: 900; margin-bottom: 8px;
    background: linear-gradient(135deg, #fca5a5, #f4c542);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .intro-card p { color: var(--muted); font-size: 13px; line-height: 1.7; }

  .challenge-card {
    display: flex; align-items: center; gap: 16px;
    padding: 20px; border-radius: 18px;
    margin-bottom: 14px; cursor: pointer;
    border: 1.5px solid; transition: 0.22s;
    position: relative; overflow: hidden;
  }
  .challenge-card:hover { transform: translateY(-3px); }
  .challenge-card.weekly {
    background: radial-gradient(circle at 100% 0%, rgba(234,179,8,0.3), transparent 60%),
                linear-gradient(135deg, #2a1e0a, #1a0f1a);
    border-color: rgba(234,179,8,0.5);
  }
  .challenge-card.weekly:hover { border-color: rgba(234,179,8,0.9); }
  .challenge-card.daily {
    background: radial-gradient(circle at 100% 0%, rgba(59,130,246,0.3), transparent 60%),
                linear-gradient(135deg, #0a1a2a, #0f0f1e);
    border-color: rgba(59,130,246,0.5);
  }
  .challenge-card.daily:hover { border-color: rgba(59,130,246,0.9); }
  .challenge-card.hourly {
    background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.3), transparent 60%),
                linear-gradient(135deg, #0a1e2a, #0f0f1e);
    border-color: rgba(6,182,212,0.5);
  }
  .challenge-card.hourly:hover { border-color: rgba(6,182,212,0.9); }

  .cc-icon {
    font-size: 38px; width: 64px; height: 64px;
    border-radius: 16px; background: rgba(255,255,255,0.08);
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .cc-body { flex: 1; }
  .cc-title { font-size: 17px; font-weight: bold; color: #fff; margin-bottom: 4px; }
  .cc-desc { font-size: 12px; color: #cbd5e1; line-height: 1.5; }
  .soon-badge {
    position: absolute; top: 12px; left: 12px;
    background: rgba(234,179,8,0.95); color: #1a1a1a;
    font-size: 10px; font-weight: 900;
    padding: 3px 9px; border-radius: 6px;
    z-index: 2;
  }
  .cc-arrow { font-size: 20px; color: rgba(255,255,255,0.4); }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <a href="/game/rooms/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>⚔️ <span>چالش</span></h1>
  </div>

  <div class="intro-card">
    <div class="icon">⚔️</div>
    <h2>میدون نبرد بازیکنان</h2>
    <p>با بهترین‌ها رقابت کن، امتیاز بگیر و به بالای جدول برس</p>
  </div>

  <div class="challenge-card weekly" onclick="alert('🏆 تورنمنت هفتگی به زودی فعال می‌شود!')">
    <span class="soon-badge">به زودی</span>
    <div class="cc-icon">🏆</div>
    <div class="cc-body">
      <div class="cc-title">تورنمنت هفتگی</div>
      <div class="cc-desc">هر هفته با بهترین بازیکنان رقابت کن، جوایز ویژه بگیر</div>
    </div>
    <div class="cc-arrow">←</div>
  </div>

  <div class="challenge-card daily" onclick="alert('📅 مسابقه روزانه به زودی فعال می‌شود!')">
    <span class="soon-badge">به زودی</span>
    <div class="cc-icon">📅</div>
    <div class="cc-body">
      <div class="cc-title">مسابقه روزانه</div>
      <div class="cc-desc">هر روز یک رقابت جدید — ۲۴ ساعت فرصت برای صدرنشینی</div>
    </div>
    <div class="cc-arrow">←</div>
  </div>

  <div class="challenge-card hourly" onclick="alert('⏰ مسابقه ساعتی به زودی فعال می‌شود!')">
    <span class="soon-badge">به زودی</span>
    <div class="cc-icon">⏰</div>
    <div class="cc-body">
      <div class="cc-title">مسابقه ساعتی</div>
      <div class="cc-desc">سرعت مهمه! هر ساعت یه مسابقه‌ی جدید با امتیاز دوبرابر</div>
    </div>
    <div class="cc-arrow">←</div>
  </div>
{% endblock %}
'''
backup(p)
write(p, CHALLENGE_HTML)

# ============================================================
# 5) menu.html - دکمه چالش لینک واقعی
# ============================================================
print("\n[5/5] menu.html")
p = os.path.join(ROOT, "game", "templates", "game", "menu.html")
src = read(p)

old_challenge = '''  <!-- چالش -->
  <div class="challenge-btn" onclick="alert('⚔️ چالش هنوز آماده نیست!\\\\n\\\\nبه‌زودی می‌تونی با دوستات به چالش بپردازی.')">
    <span class="soon-badge">به‌زودی</span>
    <div class="ch-icon">⚔️</div>
    <div class="ch-body">
      <div class="ch-title">چالش</div>
      <div class="ch-desc">با دوستات رقابت کن</div>
    </div>
  </div>'''

new_challenge = '''  <!-- چالش -->
  <a href="/game/challenge/" class="challenge-btn" style="text-decoration:none;">
    <div class="ch-icon">⚔️</div>
    <div class="ch-body">
      <div class="ch-title">چالش</div>
      <div class="ch-desc">تورنمنت، مسابقه روزانه و ساعتی</div>
    </div>
  </a>'''

if 'href="/game/challenge/"' in src:
    print("  SKIP: menu challenge already links")
elif old_challenge in src:
    src = src.replace(old_challenge, new_challenge, 1)
    backup(p)
    write(p, src)
    print("  FIXED: menu challenge is now a link")
else:
    # Try looser match
    import re
    pat = re.compile(r'  <!-- چالش -->\s*<div class="challenge-btn"[^>]*>.*?</div>\s*</div>', re.DOTALL)
    m = pat.search(src)
    if m:
        src = src[:m.start()] + new_challenge + src[m.end():]
        backup(p)
        write(p, src)
        print("  FIXED (loose): menu challenge replaced")
    else:
        print("  WARN: menu challenge block not found")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Summary:
  1. rooms.html: tournament removed, challenge card added (red)
  2. game/views.py: challenge_home view
  3. game/urls.py: /game/challenge/ route
  4. game/challenge.html: NEW page with 3 cards
       - weekly tournament (gold)
       - daily race (blue)
       - hourly race (cyan)
  5. menu.html: challenge button -> real link

New order in /game/rooms/:
  1. ⚡ بازی با بات
  2. 🌐 بازی با پلیر
  3. 🚪 بازی گروهی
  4. ⚔️ چالش (NEW - red)
  5. 🎯 بازی معما (soon)
  6. ⏱️ بازی سرعتی

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R
""")
