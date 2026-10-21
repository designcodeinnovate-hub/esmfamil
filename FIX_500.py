#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose 500 errors + fix + circular icons"""
import os, sys, re, subprocess, traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    try:
        with open(p, "r", encoding="utf-8") as f: return f.read()
    except: return ""
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# STEP 1: Django setup + actual error capture
# ============================================================
print("\n" + "="*70)
print("STEP 1: ACTUAL DIAGNOSTIC — what really breaks?")
print("="*70)

import django
django.setup()

from django.test import Client
from accounts.models import User

# Clean test user
User.objects.filter(username="__diag500__").delete()
u = User.objects.create_user(
    username="__diag500__", password="x"*10, alias="دیباگ",
    is_active=True, has_chosen_avatar=True, has_completed_registration=True,
)

c = Client()
c.force_login(u)
c.session["beta_unlocked"] = True
c.session.save()

urls = [
    ("/game/", "خانه"),
    ("/support/", "پشتیبانی"),
    ("/game/puzzle/", "معما"),
    ("/game/guess/", "۰ تا ۱۰۰"),
    ("/game/memory/", "حافظه"),
    ("/game/rooms/", "بازی‌ها"),
]

errors_found = []
for url, name in urls:
    try:
        r = c.get(url, follow=False)
        if r.status_code == 200:
            print(f"  ✓ {url:25s} ({name:15s}) → 200 OK")
        elif r.status_code == 500:
            print(f"  ❌ {url:25s} ({name:15s}) → 500 ERROR")
            # Extract error from response
            try:
                content = r.content.decode('utf-8', errors='ignore')
                # Find exception message
                exc_match = re.search(r'<pre class="exception_value">(.*?)</pre>', content, re.DOTALL)
                if exc_match:
                    err_msg = exc_match.group(1).strip()[:200]
                    print(f"     ERROR: {err_msg}")
                    errors_found.append((url, err_msg))
                else:
                    # Look for other error indicators
                    title_match = re.search(r'<title>(.*?)</title>', content)
                    if title_match:
                        print(f"     Title: {title_match.group(1)}")
                    errors_found.append((url, "500 (unknown)"))
            except Exception as e:
                print(f"     (could not decode error: {e})")
                errors_found.append((url, "500"))
        else:
            loc = r.get('Location', '')
            print(f"  → {url:25s} ({name:15s}) → {r.status_code} {loc[:40]}")
    except Exception as e:
        print(f"  ❌ {url:25s} ({name:15s}) → EXCEPTION")
        print(f"     {type(e).__name__}: {str(e)[:200]}")
        errors_found.append((url, f"{type(e).__name__}: {str(e)[:200]}"))

u.delete()

# ============================================================
# STEP 2: Print errors in detail
# ============================================================
if errors_found:
    print("\n" + "="*70)
    print(f"Found {len(errors_found)} errors:")
    print("="*70)
    for url, err in errors_found:
        print(f"\n  {url}")
        print(f"    → {err}")
else:
    print("\n  ✓ No errors found")

# ============================================================
# STEP 3: Fix known issues
# ============================================================
print("\n" + "="*70)
print("STEP 3: Applying fixes")
print("="*70)

# 3a) Ensure messages imported in game/views.py
print("\n[3a] game/views.py imports")
src = read("game/views.py")
if "from django.contrib import messages" not in src:
    src = src.replace(
        "from django.contrib.auth.decorators import login_required",
        "from django.contrib import messages\nfrom django.contrib.auth.decorators import login_required",
        1
    )
    write("game/views.py", src)
    print("  ✓ messages imported")
else:
    print("  ✓ messages already imported")

# 3b) Ensure support/views.py imports messages
print("\n[3b] support/views.py imports")
src = read("support/views.py")
if "from django.contrib import messages" not in src:
    src = "from django.contrib import messages\n" + src
    write("support/views.py", src)
    print("  ✓ messages imported in support")
else:
    print("  ✓ support imports OK")

# 3c) Ensure templates exist
print("\n[3c] Templates check")
required_templates = {
    "game/templates/game/puzzle.html": "puzzle",
    "game/templates/game/guess.html": "guess",
    "game/templates/game/memory.html": "memory",
    "support/templates/support/home.html": "support_home",
    "support/templates/support/ticket.html": "support_ticket",
}

missing_templates = []
for t, name in required_templates.items():
    if os.path.exists(t) and os.path.getsize(t) > 100:
        print(f"  ✓ {t}")
    else:
        print(f"  ✗ {t} MISSING")
        missing_templates.append((t, name))

# 3d) Rebuild missing templates
if missing_templates:
    print("\n[3d] Rebuilding missing templates")
    for t, name in missing_templates:
        if name == "puzzle":
            write(t, '''{% extends "base.html" %}
{% block title %}بازی معما{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;justify-content:space-between;margin-bottom:18px}
.head-left{display:flex;align-items:center;gap:12px}
.head h1{font-size:22px;font-weight:900;background:linear-gradient(135deg,#4ade80,#16a34a);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.timer-badge{background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff;padding:8px 18px;border-radius:999px;font-size:16px;font-weight:900;font-family:monospace;box-shadow:0 8px 25px rgba(239,68,68,0.4)}
.intro{background:linear-gradient(135deg,#0a2a1a,#0f0f1e);border:2px solid rgba(34,197,94,0.5);border-radius:20px;padding:18px 20px;margin-bottom:18px;text-align:center}
.intro h2{font-size:17px;color:#bbf7d0;margin-bottom:4px;font-weight:900}
.intro p{font-size:12px;color:#94a3b8;line-height:1.6}
.word-item{background:var(--card);border:1.5px solid rgba(34,197,94,0.3);border-radius:18px;padding:16px;margin-bottom:12px}
.word-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.word-num{font-size:11px;color:#94a3b8;font-weight:900;font-family:monospace}
.word-sec{font-size:10px;color:#4ade80;padding:2px 8px;background:rgba(34,197,94,0.15);border-radius:6px;font-family:monospace;font-weight:900}
.scrambled{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;margin-bottom:12px}
.letter-tile{width:42px;height:42px;border-radius:10px;background:linear-gradient(135deg,rgba(34,197,94,0.25),rgba(6,182,212,0.15));border:1.5px solid rgba(34,197,94,0.5);display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:900;color:#bbf7d0;box-shadow:0 4px 12px rgba(34,197,94,0.2)}
.answer-input{width:100%;padding:14px 16px;border-radius:12px;border:2px solid rgba(34,197,94,0.4);background:rgba(15,23,42,0.8);color:#fff;font-size:20px;text-align:center;font-weight:900;letter-spacing:4px;box-sizing:border-box;font-family:inherit}
.answer-input:focus{outline:none;border-color:#4ade80;box-shadow:0 0 20px rgba(34,197,94,0.3)}
.btn-submit{width:100%;padding:16px;border:none;border-radius:14px;background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;font-size:17px;font-weight:900;font-family:inherit;cursor:pointer;box-shadow:0 10px 30px rgba(34,197,94,0.4);margin-top:12px}
.btn-new{display:block;width:100%;padding:16px;border:none;border-radius:14px;background:linear-gradient(135deg,#f4c542,#eab308);color:#1a1a1a;font-size:16px;font-weight:900;font-family:inherit;cursor:pointer;text-decoration:none;text-align:center;box-shadow:0 10px 30px rgba(244,197,66,0.4);margin-top:12px}
.finished-panel{text-align:center;padding:30px 20px;border-radius:22px;background:radial-gradient(circle at 100% 0%,rgba(244,197,66,0.25),transparent 60%),linear-gradient(135deg,#2a1a0e,#0f0f1e);border:2px solid rgba(244,197,66,0.5);margin-bottom:16px}
.finished-panel .big-icon{font-size:70px;margin-bottom:12px}
.finished-panel h2{font-size:22px;font-weight:900;background:linear-gradient(135deg,#fde68a,#f4c542);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:10px}
.finished-panel .score-line{font-size:15px;color:#fff;font-family:monospace;margin-bottom:14px}
.finished-panel .score-line b{color:#fde68a}
</style>
{% endblock %}
{% block content %}
<div class="head">
  <div class="head-left">
    <a href="/game/rooms/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>🎯 بازی معما</h1>
  </div>
  {% if not finished %}
  <div class="timer-badge">⏱ <span id="timerNum">{{ remaining }}</span>ث</div>
  {% endif %}
</div>

{% if finished %}
  <div class="finished-panel">
    <div class="big-icon">🏆</div>
    <h2>نتیجه بازی</h2>
    <div class="score-line">امتیاز: <b>{{ score|default:0 }}</b> از {{ total|default:0 }}</div>
  </div>
  <form method="post" action="/game/puzzle/submit/">
    {% csrf_token %}
    <input type="hidden" name="action" value="new">
    <button type="submit" class="btn-new">🔄 بازی جدید</button>
  </form>
{% else %}
  <div class="intro">
    <h2>🧩 حروف رو مرتب کن!</h2>
    <p>هر کلمه از حروف به‌هم‌ریخته ساخته شده. کلمه‌ی درست رو تایپ کن.</p>
  </div>

  <form method="post" action="/game/puzzle/submit/" id="puzzleForm">
    {% csrf_token %}
    {% for it in items %}
      <div class="word-item">
        <div class="word-head">
          <span class="word-num">کلمه {{ forloop.counter }}</span>
          <span class="word-sec">{{ it.seconds }} ثانیه</span>
        </div>
        <div class="scrambled">
          {% for c in it.scrambled.split %}
            <div class="letter-tile">{{ c }}</div>
          {% endfor %}
        </div>
        <input type="text" name="ans_{{ it.idx }}" class="answer-input" placeholder="کلمه‌ی درست..." maxlength="10" autocomplete="off">
      </div>
    {% endfor %}
    <button type="submit" class="btn-submit">✅ ثبت همه</button>
  </form>
{% endif %}
{% endblock %}
{% block extra_js %}
{% if not finished %}
<script>
  let remaining = {{ remaining }};
  const timerEl = document.getElementById('timerNum');
  function updateTimer() {
    if (remaining <= 0) return;
    remaining--;
    if (timerEl) timerEl.textContent = remaining;
    if (remaining <= 0) {
      document.getElementById('puzzleForm').submit();
    } else {
      setTimeout(updateTimer, 1000);
    }
  }
  setTimeout(updateTimer, 1000);
</script>
{% endif %}
{% endblock %}
''')
            print(f"  ✓ Rebuilt {t}")

        elif name == "guess":
            write(t, '''{% extends "base.html" %}
{% block title %}بازی ۰ تا ۱۰۰{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.head h1{font-size:24px;font-weight:900;background:linear-gradient(135deg,#06b6d4,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero{background:radial-gradient(circle at 100% 0%,rgba(6,182,212,0.3),transparent 60%),linear-gradient(135deg,#0a1e2a,#0f0f1e);border:2px solid rgba(6,182,212,0.5);border-radius:22px;padding:26px 22px;margin-bottom:20px;text-align:center}
.hero-icon{font-size:64px;margin-bottom:10px;filter:drop-shadow(0 0 20px rgba(6,182,212,0.6))}
.hero-title{font-size:20px;font-weight:900;color:#a5f3fc;margin-bottom:6px}
.hero-desc{font-size:13px;color:#94a3b8;line-height:1.6}
.tries-info{display:flex;justify-content:center;gap:6px;margin-top:18px}
.tries-dot{width:24px;height:8px;border-radius:4px;background:rgba(148,163,184,0.2)}
.tries-dot.used{background:linear-gradient(90deg,#ef4444,#dc2626);box-shadow:0 0 8px rgba(239,68,68,0.5)}
.tries-dot.left{background:linear-gradient(90deg,#22c55e,#16a34a);box-shadow:0 0 8px rgba(34,197,94,0.5)}
.history{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:16px;margin-bottom:16px;max-height:220px;overflow-y:auto}
.history-item{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:10px;margin-bottom:6px;background:rgba(15,23,42,0.5);border:1px solid rgba(148,163,184,0.1);font-size:13px}
.history-item .num{font-family:monospace;font-weight:900;color:#fff;width:40px;text-align:center}
.history-item .arrow{font-size:18px}
.history-item.low{border-color:rgba(34,197,94,0.3);background:rgba(34,197,94,0.08)}
.history-item.low .arrow{color:#4ade80}
.history-item.high{border-color:rgba(239,68,68,0.3);background:rgba(239,68,68,0.08)}
.history-item.high .arrow{color:#f87171}
.history-item.win{border-color:rgba(244,197,66,0.5);background:rgba(244,197,66,0.15)}
.history-item.win .arrow{color:#fde68a}
.history-item .hint{font-size:11px;color:#94a3b8}
.input-form{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:22px}
.input-form input[type=number]{width:100%;padding:20px;border-radius:14px;border:2px solid rgba(6,182,212,0.4);background:rgba(15,23,42,0.8);color:#fff;font-size:32px;font-family:monospace;text-align:center;font-weight:900;margin-bottom:14px;box-sizing:border-box;-moz-appearance:textfield}
.input-form input[type=number]::-webkit-outer-spin-button,.input-form input[type=number]::-webkit-inner-spin-button{-webkit-appearance:none;margin:0}
.input-form input:focus{outline:none;border-color:#22d3ee;box-shadow:0 0 25px rgba(6,182,212,0.3)}
.btn-guess{width:100%;padding:16px;border:none;border-radius:14px;background:linear-gradient(135deg,#06b6d4,#3b82f6);color:#fff;font-size:17px;font-weight:900;font-family:inherit;cursor:pointer;box-shadow:0 10px 30px rgba(6,182,212,0.4)}
.finished-box{text-align:center;padding:30px 20px;border-radius:20px;margin-bottom:16px}
.finished-box.won{background:rgba(34,197,94,0.15);border:2px solid rgba(34,197,94,0.4)}
.finished-box.lost{background:rgba(239,68,68,0.15);border:2px solid rgba(239,68,68,0.4)}
.finished-box .fi{font-size:60px;margin-bottom:10px}
.finished-box .ft{font-size:20px;font-weight:900;margin-bottom:6px}
.finished-box.won .ft{color:#4ade80}
.finished-box.lost .ft{color:#f87171}
.finished-box .fw{font-size:16px;color:#fff;font-family:monospace}
.btn-new{display:block;width:100%;padding:16px;border:none;border-radius:14px;background:linear-gradient(135deg,#f4c542,#eab308);color:#1a1a1a;font-size:16px;font-weight:900;font-family:inherit;cursor:pointer;text-decoration:none;text-align:center;box-shadow:0 10px 30px rgba(244,197,66,0.4);margin-top:12px}
.flash{padding:12px 16px;border-radius:12px;margin-bottom:12px;font-size:13px;text-align:center}
.flash-success{background:rgba(34,197,94,0.15);color:#4ade80;border:1px solid rgba(34,197,94,0.3)}
.flash-error{background:rgba(239,68,68,0.15);color:#fca5a5;border:1px solid rgba(239,68,68,0.3)}
.flash-info{background:rgba(59,130,246,0.15);color:#93c5fd;border:1px solid rgba(59,130,246,0.3)}
</style>
{% endblock %}
{% block content %}
<div class="head">
  <a href="/game/rooms/" class="back-btn"><span class="arrow-icon">→</span></a>
  <h1>🎲 بازی ۰ تا ۱۰۰</h1>
</div>

{% if messages %}
  {% for m in messages %}<div class="flash flash-{{ m.tags }}">{{ m }}</div>{% endfor %}
{% endif %}

<div class="hero">
  <div class="hero-icon">🎲</div>
  <div class="hero-title">حدس عدد</div>
  <div class="hero-desc">یه عدد بین ۰ تا ۱۰۰ انتخاب شده.<br>با ۷ تلاش پیداش کن!</div>
  <div class="tries-info">
    {% for i in "1234567" %}
      {% if forloop.counter0 < tries %}
        <div class="tries-dot used"></div>
      {% elif not finished %}
        <div class="tries-dot left"></div>
      {% else %}
        <div class="tries-dot"></div>
      {% endif %}
    {% endfor %}
  </div>
</div>

{% if finished %}
  <div class="finished-box {% if won %}won{% else %}lost{% endif %}">
    <div class="fi">{% if won %}🏆{% else %}😢{% endif %}</div>
    <div class="ft">{% if won %}آفرین! درست حدس زدی{% else %}تموم شد!{% endif %}</div>
    <div class="fw">عدد: {{ number }}</div>
  </div>
  <form method="post">
    {% csrf_token %}
    <input type="hidden" name="action" value="new">
    <button type="submit" class="btn-new">🔄 بازی جدید</button>
  </form>
{% else %}
  {% if history %}
    <div class="history">
      {% for h in history %}
        <div class="history-item {% if h.result == 'win' %}win{% else %}{{ h.result }}{% endif %}">
          <div class="num">{{ h.guess }}</div>
          <div class="arrow">
            {% if h.result == 'win' %}🎯{% elif h.result == 'low' %}⬆️{% else %}⬇️{% endif %}
          </div>
          <div class="hint">
            {% if h.result == 'win' %}درسته!
            {% elif h.result == 'low' %}برو بالاتر
            {% else %}بیا پایین‌تر{% endif %}
          </div>
        </div>
      {% endfor %}
    </div>
  {% endif %}
  <form method="post" action="/game/guess/attempt/" class="input-form">
    {% csrf_token %}
    <input type="number" name="guess" min="0" max="100" required placeholder="50" autofocus>
    <button type="submit" class="btn-guess">🎯 حدس بزن</button>
  </form>
{% endif %}
{% endblock %}
''')
            print(f"  ✓ Rebuilt {t}")

        elif name == "memory":
            write(t, '''{% extends "base.html" %}
{% block title %}بازی حافظه{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;margin-bottom:18px}
.head h1{font-size:22px;font-weight:900;background:linear-gradient(135deg,#a78bfa,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.intro{background:radial-gradient(circle at 100% 0%,rgba(139,92,246,0.25),transparent 60%),linear-gradient(135deg,#1a0f2e,#0f0f1e);border:2px solid rgba(139,92,246,0.5);border-radius:20px;padding:16px 20px;margin-bottom:18px;text-align:center}
.intro h2{font-size:16px;color:#e9d5ff;margin-bottom:4px;font-weight:900}
.intro p{font-size:12px;color:#94a3b8;line-height:1.6}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:20px}
.card{aspect-ratio:1;position:relative;perspective:600px;cursor:pointer}
.card-inner{position:relative;width:100%;height:100%;transition:transform 0.5s;transform-style:preserve-3d}
.card.flipped .card-inner,.card.matched .card-inner{transform:rotateY(180deg)}
.card-face{position:absolute;inset:0;border-radius:14px;display:flex;align-items:center;justify-content:center;backface-visibility:hidden;-webkit-backface-visibility:hidden}
.card-back{background:linear-gradient(135deg,rgba(139,92,246,0.4),rgba(6,182,212,0.3));border:2px solid rgba(139,92,246,0.6);font-size:32px;color:rgba(255,255,255,0.3);box-shadow:0 4px 12px rgba(139,92,246,0.3)}
.card-front{background:linear-gradient(135deg,rgba(244,197,66,0.35),rgba(139,92,246,0.25));border:2px solid rgba(244,197,66,0.6);font-size:36px;transform:rotateY(180deg);box-shadow:0 4px 15px rgba(244,197,66,0.4)}
.card.matched .card-front{background:linear-gradient(135deg,rgba(34,197,94,0.35),rgba(6,182,212,0.25));border-color:rgba(34,197,94,0.7);box-shadow:0 0 20px rgba(34,197,94,0.6)}
.btn-new{display:block;width:100%;padding:16px;border:none;border-radius:14px;background:linear-gradient(135deg,#f4c542,#eab308);color:#1a1a1a;font-size:16px;font-weight:900;font-family:inherit;cursor:pointer;text-decoration:none;text-align:center;box-shadow:0 10px 30px rgba(244,197,66,0.4);margin-top:8px}
.stats-bar{display:flex;gap:8px;margin-bottom:16px}
.stat-chip{flex:1;background:linear-gradient(135deg,rgba(139,92,246,0.15),rgba(6,182,212,0.1));border:1.5px solid rgba(139,92,246,0.4);border-radius:12px;padding:10px;text-align:center}
.stat-chip .lbl{font-size:10px;color:#94a3b8;margin-bottom:2px}
.stat-chip .val{font-size:16px;font-weight:900;color:#c4b5fd;font-family:monospace}
</style>
{% endblock %}
{% block content %}
<div class="head">
  <a href="/game/rooms/" class="back-btn"><span class="arrow-icon">→</span></a>
  <h1>🧠 بازی حافظه</h1>
</div>

<div class="stats-bar">
  <div class="stat-chip"><div class="lbl">جفت‌ها</div><div class="val" id="matchedCount">0 / {{ total_pairs }}</div></div>
  <div class="stat-chip"><div class="lbl">حرکت</div><div class="val" id="movesCount">0</div></div>
</div>

<div class="intro">
  <h2>🧠 حافظه‌ت رو بسنج!</h2>
  <p>کارت‌ها رو باز کن، جفت‌های یکسان رو پیدا کن</p>
</div>

<div class="grid" id="memoryGrid">
  {% for c in cards %}
    <div class="card" data-id="{{ c.id }}" data-emoji="{{ c.emoji }}" onclick="flipCard(this)">
      <div class="card-inner">
        <div class="card-face card-back">❓</div>
        <div class="card-face card-front">{{ c.emoji }}</div>
      </div>
    </div>
  {% endfor %}
</div>

<form method="post" id="newGameForm" style="display:none;">
  {% csrf_token %}
  <input type="hidden" name="action" value="new">
</form>
<button onclick="document.getElementById('newGameForm').submit()" class="btn-new">🔄 بازی جدید</button>
{% endblock %}
{% block extra_js %}
<script>
  let firstCard = null, secondCard = null, lock = false, matched = 0, moves = 0;
  let totalPairs = {{ total_pairs }};

  function flipCard(card) {
    if (lock || card.classList.contains('flipped') || card.classList.contains('matched')) return;
    card.classList.add('flipped');
    if (!firstCard) { firstCard = card; return; }
    secondCard = card;
    lock = true;
    moves++;
    document.getElementById('movesCount').textContent = moves;
    const em1 = firstCard.dataset.emoji, em2 = secondCard.dataset.emoji;
    if (em1 === em2) {
      setTimeout(() => {
        firstCard.classList.add('matched');
        secondCard.classList.add('matched');
        matched++;
        document.getElementById('matchedCount').textContent = matched + " / " + totalPairs;
        reset();
        if (matched >= totalPairs) alert('🎉 بردی! در ' + moves + ' حرکت');
      }, 500);
    } else {
      setTimeout(() => {
        firstCard.classList.remove('flipped');
        secondCard.classList.remove('flipped');
        reset();
      }, 800);
    }
  }
  function reset() { firstCard = null; secondCard = null; lock = false; }
</script>
{% endblock %}
''')
            print(f"  ✓ Rebuilt {t}")

        elif name == "support_home":
            write(t, '''{% extends "base.html" %}
{% block title %}پشتیبانی{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.head h1{font-size:22px;font-weight:900;color:var(--gold)}
.hero{background:radial-gradient(circle at 100% 0%,rgba(6,182,212,0.35),transparent 60%),linear-gradient(135deg,#0a1e2a,#0f0f1e);border:2px solid rgba(6,182,212,0.5);border-radius:22px;padding:24px 20px;margin-bottom:20px;text-align:center}
.hero .icon{font-size:56px;margin-bottom:10px;filter:drop-shadow(0 0 20px rgba(6,182,212,0.6))}
.hero h2{font-size:20px;font-weight:900;background:linear-gradient(135deg,#67e8f9,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:6px}
.hero p{color:var(--muted);font-size:13px;line-height:1.6}
.form-box{background:var(--card);border:1.5px solid var(--border);border-radius:18px;padding:20px;margin-bottom:20px}
.form-box h3{font-size:15px;color:#67e8f9;margin-bottom:14px}
label{display:block;color:var(--muted);font-size:12px;margin:12px 0 6px;font-weight:bold}
input[type=text],textarea,select{width:100%;padding:12px 14px;border-radius:10px;border:1.5px solid var(--border);background:var(--bg);color:var(--text);font-size:14px;font-family:inherit;box-sizing:border-box}
textarea{resize:vertical;min-height:100px}
input:focus,textarea:focus,select:focus{outline:none;border-color:#06b6d4}
button.submit{width:100%;margin-top:16px;padding:14px;border:none;border-radius:12px;background:linear-gradient(135deg,#06b6d4,#3b82f6);color:#fff;font-size:15px;font-weight:900;font-family:inherit;cursor:pointer;box-shadow:0 8px 20px rgba(6,182,212,0.4)}
.flash{padding:12px 16px;border-radius:12px;margin-bottom:12px;font-size:13px}
.flash-success{background:rgba(34,197,94,0.15);color:#4ade80;border:1px solid rgba(34,197,94,0.3)}
.flash-error{background:rgba(239,68,68,0.15);color:#fca5a5;border:1px solid rgba(239,68,68,0.3)}
.ticket-card{display:flex;align-items:flex-start;gap:12px;padding:14px;background:var(--card);border:1.5px solid var(--border);border-radius:14px;margin-bottom:8px;text-decoration:none;color:var(--text);transition:0.2s}
.ticket-card:hover{border-color:#06b6d4;transform:translateX(-3px)}
.ticket-card .icon{font-size:28px;flex-shrink:0}
.ticket-card .info{flex:1;min-width:0}
.ticket-card .title{font-size:14px;font-weight:bold;margin-bottom:4px}
.ticket-card .meta{font-size:11px;color:var(--muted)}
.ticket-card .badge{font-size:10px;padding:3px 10px;border-radius:8px;font-weight:bold;flex-shrink:0}
.badge-open{background:rgba(234,179,8,0.2);color:#fde68a}
.badge-answered{background:rgba(34,197,94,0.2);color:#86efac}
.badge-closed{background:rgba(100,116,139,0.2);color:#cbd5e1}
.badge-in_progress{background:rgba(59,130,246,0.2);color:#93c5fd}
</style>
{% endblock %}
{% block content %}
<div class="head">
  <a href="/game/" class="back-btn"><span class="arrow-icon">→</span></a>
  <h1>💬 پشتیبانی</h1>
</div>

{% if messages %}
  {% for m in messages %}<div class="flash flash-{{ m.tags }}">{{ m }}</div>{% endfor %}
{% endif %}

<div class="hero">
  <div class="icon">💬</div>
  <h2>چطور می‌تونیم کمکت کنیم؟</h2>
  <p>سوال یا مشکلی داری؟ یه پیام بفرست.</p>
</div>

<div class="form-box">
  <h3>📝 ارسال پیام جدید</h3>
  <form method="post">
    {% csrf_token %}
    <label>موضوع</label>
    <input type="text" name="subject" required maxlength="100" placeholder="مثلاً: باگ در بازی گروهی">
    <label>دسته‌بندی</label>
    <select name="category">
      <option value="general">سوال عمومی</option>
      <option value="bug">باگ یا مشکل</option>
      <option value="idea">پیشنهاد و ایده</option>
      <option value="payment">پرداخت</option>
    </select>
    <label>متن پیام</label>
    <textarea name="body" required maxlength="2000" placeholder="مشکل رو با جزئیات بنویس..."></textarea>
    <button type="submit" class="submit">📤 ارسال</button>
  </form>
</div>

{% if tickets %}
  <h3 style="font-size:15px;color:var(--gold);margin-bottom:12px;">📜 تیکت‌های من</h3>
  {% for t in tickets %}
    <a href="/support/{{ t.id }}/" class="ticket-card">
      <div class="icon">{% if t.category == 'bug' %}🐛{% elif t.category == 'idea' %}💡{% elif t.category == 'payment' %}💳{% else %}📝{% endif %}</div>
      <div class="info">
        <div class="title">{{ t.subject }}</div>
        <div class="meta">#{{ t.id }} · {{ t.created_at|date:"Y/m/d H:i" }}</div>
      </div>
      <span class="badge badge-{{ t.status }}">{{ t.status_display }}</span>
    </a>
  {% endfor %}
{% endif %}
{% endblock %}
''')
            print(f"  ✓ Rebuilt {t}")

        elif name == "support_ticket":
            write(t, '''{% extends "base.html" %}
{% block title %}تیکت #{{ ticket.id }}{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.head h1{font-size:20px;font-weight:900;color:var(--gold)}
.ticket-box{background:var(--card);border:1.5px solid var(--border);border-radius:18px;padding:20px;margin-bottom:16px}
.t-header{display:flex;align-items:flex-start;gap:14px;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid var(--border)}
.t-icon{font-size:36px;flex-shrink:0}
.t-info{flex:1}
.t-title{font-size:18px;font-weight:900;margin-bottom:4px}
.t-meta{font-size:11px;color:var(--muted)}
.t-badge{font-size:10px;padding:4px 12px;border-radius:8px;font-weight:bold;flex-shrink:0}
.badge-open{background:rgba(234,179,8,0.2);color:#fde68a}
.badge-answered{background:rgba(34,197,94,0.2);color:#86efac}
.badge-closed{background:rgba(100,116,139,0.2);color:#cbd5e1}
.badge-in_progress{background:rgba(59,130,246,0.2);color:#93c5fd}
.t-body{padding:16px;background:rgba(15,23,42,0.5);border-radius:12px;font-size:14px;line-height:1.8;white-space:pre-wrap}
.reply-box{margin-top:18px;padding:18px;background:linear-gradient(135deg,rgba(34,197,94,0.1),rgba(6,182,212,0.08));border:1.5px solid rgba(34,197,94,0.4);border-radius:14px}
.reply-box h3{font-size:14px;color:#86efac;margin-bottom:10px}
.reply-body{font-size:14px;line-height:1.8;color:#fff;white-space:pre-wrap;padding:12px;background:rgba(15,23,42,0.5);border-radius:10px}
.reply-time{font-size:10px;color:#94a3b8;margin-top:8px;font-family:monospace}
.no-reply{text-align:center;padding:20px;background:rgba(234,179,8,0.08);border:1px dashed rgba(234,179,8,0.3);border-radius:12px;color:#fde68a;font-size:13px;margin-top:16px}
.actions{display:flex;gap:10px;margin-top:20px}
.actions a,.actions button{flex:1;padding:12px;border-radius:12px;border:none;font-family:inherit;font-weight:900;font-size:14px;cursor:pointer;text-decoration:none;text-align:center}
.btn-back{background:rgba(148,163,184,0.2);color:#fff}
.btn-close{background:rgba(239,68,68,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.4) !important}
</style>
{% endblock %}
{% block content %}
<div class="head">
  <a href="/support/" class="back-btn"><span class="arrow-icon">→</span></a>
  <h1>تیکت #{{ ticket.id }}</h1>
</div>

<div class="ticket-box">
  <div class="t-header">
    <div class="t-icon">{% if ticket.category == 'bug' %}🐛{% elif ticket.category == 'idea' %}💡{% elif ticket.category == 'payment' %}💳{% else %}📝{% endif %}</div>
    <div class="t-info">
      <div class="t-title">{{ ticket.subject }}</div>
      <div class="t-meta">{{ ticket.created_at|date:"Y/m/d H:i" }}</div>
    </div>
    <span class="t-badge badge-{{ ticket.status }}">{{ ticket.status_display }}</span>
  </div>

  <div class="t-body">{{ ticket.body }}</div>

  {% if ticket.admin_reply %}
    <div class="reply-box">
      <h3>💬 پاسخ پشتیبانی</h3>
      <div class="reply-body">{{ ticket.admin_reply }}</div>
      <div class="reply-time">📅 {{ ticket.replied_at|date:"Y/m/d H:i" }}</div>
    </div>
  {% elif ticket.status != "closed" %}
    <div class="no-reply">⏳ در انتظار پاسخ تیم پشتیبانی...</div>
  {% endif %}

  <div class="actions">
    <a href="/support/" class="btn-back">← بازگشت</a>
    {% if ticket.status != "closed" %}
      <form method="post" action="/support/{{ ticket.id }}/close/" style="display:contents;" onsubmit="return confirm('بستن این تیکت؟');">
        {% csrf_token %}
        <button type="submit" class="btn-close">✕ بستن</button>
      </form>
    {% endif %}
  </div>
</div>
{% endblock %}
''')
            print(f"  ✓ Rebuilt {t}")

# ============================================================
# STEP 4: REBUILD HOME with circular top-players + shop
# ============================================================
print("\n" + "="*70)
print("STEP 4: Home with circular top-players + shop")
print("="*70)

HOME_HTML = '''{% extends "base.html" %}
{% block title %}خانه{% endblock %}

{% block extra_css %}
<style>
  .bg-pattern { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
  .bg-pattern::before, .bg-pattern::after { content: ""; position: absolute; inset: -50%; background-image: radial-gradient(circle, rgba(244,197,66,0.35) 1px, transparent 1.5px), radial-gradient(circle, rgba(139,92,246,0.3) 1px, transparent 1.5px); background-size: 60px 60px, 90px 90px; background-position: 0 0, 30px 30px; animation: dotsFloat 30s linear infinite; opacity: 0.4; }
  .bg-pattern::after { animation-duration: 45s; animation-direction: reverse; }
  @keyframes dotsFloat { from { transform: translate(0, 0); } to { transform: translate(60px, 90px); } }
  .fly-dot { position: fixed; width: 4px; height: 4px; border-radius: 50%; background: #f4c542; box-shadow: 0 0 8px #f4c542; opacity: 0.6; z-index: 0; pointer-events: none; animation: flyUp linear infinite; }
  @keyframes flyUp { from { transform: translateY(100vh) scale(0.3); opacity: 0; } 20% { opacity: 0.7; } to { transform: translateY(-50px) scale(1); opacity: 0; } }

  /* Top row */
  .top-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 16px; position: relative; z-index: 3; min-height: 80px; }
  .btn-settings { width: 52px; height: 52px; border-radius: 16px; background: linear-gradient(135deg, var(--card), #0f0f1e); border: 2px solid rgba(148,163,184,0.4); display: flex; align-items: center; justify-content: center; text-decoration: none; font-size: 24px; flex-shrink: 0; transition: all 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
  .btn-settings:hover { border-color: var(--gold); transform: rotate(45deg) scale(1.08); }
  .profile-wrap { display: flex; justify-content: flex-end; flex: 1; min-width: 0; }
  .profile-oval { display: flex; align-items: center; gap: 0; padding: 6px; height: 68px; width: 68px; border-radius: 34px; background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.35), transparent 60%), linear-gradient(135deg, var(--card), #0f0f1e); border: 2.5px solid rgba(244,197,66,0.6); cursor: pointer; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); overflow: hidden; box-shadow: 0 0 25px rgba(244,197,66,0.3); flex-shrink: 0; }
  .profile-oval:hover { border-color: #fde68a; box-shadow: 0 0 40px rgba(244,197,66,0.5); }
  .profile-oval.expanded { width: 260px; padding: 12px 16px; gap: 12px; }
  .po-av { width: 52px; height: 52px; border-radius: 50%; background: linear-gradient(135deg, #2a2a4a, #1a1a2e); display: flex; align-items: center; justify-content: center; font-size: 26px; border: 2px solid #f4c542; box-shadow: 0 0 15px rgba(244,197,66,0.5); overflow: hidden; background-size: cover; background-position: center; flex-shrink: 0; transition: all 0.3s; }
  .profile-oval.expanded .po-av { width: 56px; height: 56px; font-size: 28px; }
  .po-details { flex: 1; min-width: 0; max-width: 0; opacity: 0; overflow: hidden; transition: all 0.4s; text-align: right; white-space: nowrap; }
  .profile-oval.expanded .po-details { max-width: 200px; opacity: 1; }
  .po-name { font-size: 15px; font-weight: 900; color: #fde68a; margin-bottom: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .po-meta { display: flex; gap: 6px; align-items: center; font-size: 10px; color: #94a3b8; flex-wrap: wrap; }
  .po-meta .badge { background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; padding: 1px 6px; border-radius: 6px; font-family: monospace; font-weight: 900; font-size: 9px; }

  /* ============ CIRCULAR TOP BUTTONS ============ */
  .circle-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-bottom: 20px;
    position: relative;
    z-index: 2;
  }
  .circle-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 16px 12px;
    border-radius: 20px;
    text-decoration: none;
    color: #fff;
    border: 2px solid;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    font-family: inherit;
    background: transparent;
    position: relative;
    overflow: hidden;
    min-height: 130px;
  }
  .circle-item:hover { transform: translateY(-4px); }
  .circle-item:active { transform: scale(0.97); }
  .circle-item .ci-icon {
    width: 70px;
    height: 70px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 34px;
    flex-shrink: 0;
    transition: transform 0.3s;
    position: relative;
  }
  .circle-item:hover .ci-icon { transform: scale(1.1); }
  .circle-item .ci-title {
    font-size: 14px;
    font-weight: 900;
    margin-top: 4px;
  }
  .circle-item .ci-desc {
    font-size: 10px;
    opacity: 0.7;
  }

  /* Top players */
  .circle-top {
    background: radial-gradient(circle at 50% 0%, rgba(244,197,66,0.35), transparent 70%),
                linear-gradient(135deg, #2a1a0e, #1a0f1a);
    border-color: rgba(244,197,66,0.6);
    box-shadow: 0 8px 25px rgba(244,197,66,0.2);
  }
  .circle-top:hover { border-color: #fde68a; box-shadow: 0 15px 40px rgba(244,197,66,0.5); }
  .circle-top .ci-icon {
    background: radial-gradient(circle, rgba(244,197,66,0.4), rgba(234,179,8,0.15));
    border: 2.5px solid rgba(244,197,66,0.7);
    box-shadow: 0 0 25px rgba(244,197,66,0.6);
    animation: pulse-gold 2.5s infinite;
  }
  @keyframes pulse-gold { 0%,100% { box-shadow: 0 0 25px rgba(244,197,66,0.6); } 50% { box-shadow: 0 0 40px rgba(244,197,66,0.9); } }
  .circle-top .ci-title { color: #fde68a; }

  /* Shop */
  .circle-shop {
    background: radial-gradient(circle at 50% 0%, rgba(100,116,139,0.3), transparent 70%),
                linear-gradient(135deg, #1a1a2e, #0f0f1e);
    border-color: rgba(100,116,139,0.4);
    opacity: 0.7;
    cursor: not-allowed;
  }
  .circle-shop .ci-icon {
    background: radial-gradient(circle, rgba(100,116,139,0.3), rgba(51,65,85,0.15));
    border: 2.5px solid rgba(100,116,139,0.5);
  }
  .circle-shop .ci-title { color: #cbd5e1; }
  .soon-badge {
    position: absolute;
    top: 8px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #eab308, #ca8a04);
    color: #1a1a1a;
    font-size: 9px;
    font-weight: 900;
    padding: 2px 8px;
    border-radius: 6px;
  }

  /* 3 squares */
  .section-label { font-size: 11px; color: var(--muted); font-weight: 900; letter-spacing: 2px; margin: 4px 4px 12px; display: flex; align-items: center; gap: 8px; position: relative; z-index: 2; }
  .section-label::after { content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, rgba(148,163,184,0.2), transparent); }

  .sq-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; position: relative; z-index: 2; }
  .sq-tile { aspect-ratio: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; padding: 12px 8px; border-radius: 20px; text-decoration: none; color: #fff; position: relative; overflow: hidden; border: 2px solid; transition: all 0.3s; cursor: pointer; font-family: inherit; background: transparent; }
  .sq-tile:hover { transform: translateY(-4px) scale(1.04); }
  .sq-tile::after { content: ""; position: absolute; top: 0; left: -100%; width: 60%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent); transform: skewX(-20deg); animation: shine 4s infinite; z-index: 2; pointer-events: none; }
  @keyframes shine { 0% { left: -100%; } 50%,100% { left: 200%; } }
  .sq-icon { font-size: 38px; line-height: 1; animation: float 3s ease-in-out infinite; }
  .sq-tile:nth-child(1) .sq-icon { animation-delay: 0s; }
  .sq-tile:nth-child(2) .sq-icon { animation-delay: 0.4s; }
  .sq-tile:nth-child(3) .sq-icon { animation-delay: 0.8s; }
  @keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
  .sq-title { font-size: 12px; font-weight: 900; }
  .sq-sub { font-size: 9px; opacity: 0.75; }

  .sq-notif { background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.4), transparent 60%), linear-gradient(135deg, #1a0f2e, #0f0f1e); border-color: rgba(139,92,246,0.6); }
  .sq-notif:hover { border-color: rgba(167,139,250,0.95); box-shadow: 0 18px 45px rgba(139,92,246,0.45); }
  .sq-notif .sq-title { color: #c4b5fd; }
  .sq-games { background: radial-gradient(circle at 100% 0%, rgba(236,72,153,0.4), transparent 60%), linear-gradient(135deg, #1a0f2e, #120824); border-color: rgba(236,72,153,0.6); }
  .sq-games:hover { border-color: rgba(236,72,153,0.95); box-shadow: 0 18px 45px rgba(236,72,153,0.45); }
  .sq-games .sq-title { color: #f9a8d4; }
  .sq-challenge { background: radial-gradient(circle at 100% 0%, rgba(239,68,68,0.4), transparent 60%), linear-gradient(135deg, #2a0a0a, #1a0606); border-color: rgba(239,68,68,0.6); }
  .sq-challenge:hover { border-color: rgba(248,113,113,0.95); box-shadow: 0 18px 45px rgba(239,68,68,0.45); }
  .sq-challenge .sq-title { color: #fca5a5; }

  .sq-badge { position: absolute; top: 8px; right: 8px; background: #ef4444; color: #fff; font-size: 10px; font-weight: 900; padding: 2px 8px; border-radius: 999px; z-index: 3; animation: pulseBadge 2s infinite; }
  @keyframes pulseBadge { 0%,100% { transform: scale(1); } 50% { transform: scale(1.18); } }

  /* Support */
  .support-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 18px;
    border-radius: 18px;
    background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.4), transparent 60%),
                linear-gradient(135deg, #0a1e2a, #05141a);
    border: 2px solid rgba(6,182,212,0.6);
    color: #fff;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 10px 30px rgba(6,182,212,0.2);
    position: relative;
    z-index: 2;
    margin-top: 8px;
  }
  .support-btn:hover { transform: translateY(-3px); border-color: rgba(34,211,238,0.95); box-shadow: 0 15px 40px rgba(6,182,212,0.45); }
  .support-btn .si { font-size: 28px; }
  .support-btn .sb { flex: 1; text-align: right; }
  .support-btn .st { font-size: 16px; font-weight: 900; color: #a5f3fc; margin-bottom: 3px; }
  .support-btn .sd { font-size: 11px; color: #94a3b8; }
  .support-btn .sa { font-size: 20px; color: #67e8f9; }

  .guest-warning { background: linear-gradient(135deg, rgba(234,179,8,0.15), rgba(249,115,22,0.08)); border: 1.5px solid rgba(234,179,8,0.35); border-radius: 14px; padding: 12px 14px; margin-bottom: 14px; display: flex; align-items: center; gap: 12px; position: relative; z-index: 2; }
  .guest-warning .gw-icon { font-size: 26px; flex-shrink: 0; }
  .guest-warning .gw-body { flex: 1; }
  .guest-warning .gw-title { font-size: 12px; font-weight: 900; color: #fde68a; margin-bottom: 2px; }
  .guest-warning .gw-desc { font-size: 10px; color: #fbbf24; line-height: 1.5; }
  .guest-warning .gw-logout { background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4); padding: 7px 12px; border-radius: 10px; font-size: 11px; font-weight: 900; text-decoration: none; }
</style>
{% endblock %}

{% block content %}
  <div class="bg-pattern"></div>
  <div class="fly-dot" style="left: 15%; animation-duration: 12s;"></div>
  <div class="fly-dot" style="left: 40%; animation-duration: 15s; animation-delay: 2s; background: #8b5cf6; box-shadow: 0 0 8px #8b5cf6;"></div>
  <div class="fly-dot" style="left: 65%; animation-duration: 18s; animation-delay: 4s;"></div>
  <div class="fly-dot" style="left: 85%; animation-duration: 14s; animation-delay: 1s; background: #06b6d4; box-shadow: 0 0 8px #06b6d4;"></div>

  <div class="top-row">
    <a href="/accounts/settings/" class="btn-settings" title="تنظیمات">⚙️</a>
    <div class="profile-wrap">
      <div class="profile-oval" id="profileOval" onclick="toggleProfile()">
        {% if user.avatar_type == "image" and user.avatar_id %}
          <div class="po-av" style="background-image: url('/static/avatars/images/{{ user.avatar_id|stringformat:"03d" }}.jpg');"></div>
        {% else %}
          <div class="po-av">{{ avatar_emoji }}</div>
        {% endif %}
        <div class="po-details">
          <div class="po-name">{{ user.alias }}</div>
          <div class="po-meta">
            <span class="badge">Lv {{ level|default:1 }}</span>
            <span>🪙 {{ user.coins|default:0 }}</span>
            <span>💎 {{ user.gems|default:0 }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Circular: top players + shop -->
  <div class="circle-grid">
    <a href="/game/top-players/" class="circle-item circle-top">
      <div class="ci-icon">⭐</div>
      <div class="ci-title">بازیکنان برتر</div>
      <div class="ci-desc">جدول رتبه‌بندی</div>
    </a>
    <div class="circle-item circle-shop">
      <span class="soon-badge">به زودی</span>
      <div class="ci-icon">🛒</div>
      <div class="ci-title">فروشگاه</div>
      <div class="ci-desc">خرید آیتم‌ها</div>
    </div>
  </div>

  {% if user.is_guest %}
    <div class="guest-warning">
      <span class="gw-icon">🎲</span>
      <div class="gw-body">
        <div class="gw-title">حساب مهمان</div>
        <div class="gw-desc">برای ذخیره دائمی، ثبت‌نام کن</div>
      </div>
      <a href="/accounts/register/" class="gw-logout">ثبت‌نام</a>
    </div>
  {% endif %}

  <div class="section-label">📋 منو اصلی</div>

  <div class="sq-grid">
    <a href="/social/notifications/" class="sq-tile sq-notif">
      {% if unread_notifications %}<span class="sq-badge">{{ unread_notifications }}</span>{% endif %}
      <div class="sq-icon">🔔</div>
      <div class="sq-title">اعلان‌ها</div>
      <div class="sq-sub">{% if unread_notifications %}{{ unread_notifications }} جدید{% else %}پیام‌ها{% endif %}</div>
    </a>
    <a href="/game/rooms/" class="sq-tile sq-games">
      <div class="sq-icon">🎮</div>
      <div class="sq-title">بازی‌ها</div>
      <div class="sq-sub">۷ حالت</div>
    </a>
    <a href="/game/challenge/" class="sq-tile sq-challenge">
      <div class="sq-icon">🏆</div>
      <div class="sq-title">چالش</div>
      <div class="sq-sub">تورنمنت</div>
    </a>
  </div>

  <div class="section-label">💬 ارتباط با ما</div>
  <a href="/support/" class="support-btn">
    <span class="si">💬</span>
    <div class="sb">
      <div class="st">پشتیبانی</div>
      <div class="sd">سوال داری؟ با ما در تماس باش</div>
    </div>
    <span class="sa">←</span>
  </a>

{% endblock %}

{% block extra_js %}
<script>
  function toggleProfile() {
    document.getElementById('profileOval').classList.toggle('expanded');
    if (window.vibrate) window.vibrate(8);
  }
</script>
{% endblock %}
'''
write("game/templates/game/menu.html", HOME_HTML)

# ============================================================
# STEP 5: Final check + test
# ============================================================
print("\n" + "="*70)
print("STEP 5: Final check + test")
print("="*70)

r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True, timeout=30)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:600] if r.stderr else r.stdout[:600]}")

# Retest
print("\nRe-testing all pages:")
User.objects.filter(username="__diag500__").delete()
u = User.objects.create_user(
    username="__diag500__", password="x"*10, alias="دیباگ",
    is_active=True, has_chosen_avatar=True, has_completed_registration=True,
)
c = Client()
c.force_login(u)
c.session["beta_unlocked"] = True
c.session.save()

for url, name in urls:
    try:
        r = c.get(url, follow=False)
        if r.status_code == 200:
            print(f"  ✓ {url:25s} ({name:15s}) → 200 OK")
        else:
            print(f"  ⚠ {url:25s} ({name:15s}) → {r.status_code}")
    except Exception as e:
        print(f"  ❌ {url:25s} ({name:15s}) → {type(e).__name__}")

u.delete()

print("\n" + "="*60)
print("✅ تمام")
print("="*60)
print("""
حالا سرور رو ران کن:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)

خانه جدید:
  ✓ ⚙️ تنظیمات (چپ بالا)
  ✓ پروفایل دایره‌ای (راست بالا) — کلیک → بیضی
  ✓ ⭐ بازیکنان برتر — دایره‌ای بزرگ
  ✓ 🛒 فروشگاه — دایره‌ای بزرگ (به زودی)
  ✓ 🔔 اعلان / 🎮 بازی‌ها / 🏆 چالش — ۳ مربع
  ✓ 💬 پشتیبانی — مستطیل پایین
""")
