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
    bak = p + ".bak7"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) match_wait.html - super search screen
# ============================================================
print("\n[1/3] match_wait.html")
p = os.path.join(ROOT, "game", "templates", "game", "match_wait.html")

MATCH_WAIT = '''{% extends "base.html" %}
{% block title %}جستجوی حریف{% endblock %}

{% block extra_css %}
<style>
  .wait-wrap {
    text-align: center;
    padding: 40px 20px 30px;
    background:
      radial-gradient(circle at 50% 0%, rgba(59,130,246,0.35), transparent 55%),
      radial-gradient(circle at 50% 100%, rgba(139,92,246,0.2), transparent 55%),
      linear-gradient(135deg, #0a1428, #0a0f1e, #0f0f1e);
    border: 2px solid rgba(59,130,246,0.5);
    border-radius: 28px;
    margin-top: 20px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(59,130,246,0.3);
  }
  .wait-wrap::before {
    content: "";
    position: absolute;
    inset: -50%;
    background: conic-gradient(
      from 0deg,
      transparent 0deg,
      rgba(96,165,250,0.1) 90deg,
      transparent 180deg,
      rgba(139,92,246,0.1) 270deg,
      transparent 360deg
    );
    animation: waitRotate 10s linear infinite;
    z-index: 0;
    pointer-events: none;
  }
  @keyframes waitRotate { to { transform: rotate(360deg); } }

  .wait-wrap > * { position: relative; z-index: 1; }

  /* Radar spinner */
  .radar {
    width: 140px; height: 140px;
    margin: 0 auto 26px;
    position: relative;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(59,130,246,0.15), transparent 70%);
  }
  .radar::before,
  .radar::after {
    content: "";
    position: absolute;
    border-radius: 50%;
    border: 2px solid rgba(96,165,250,0.4);
    animation: radarPing 2.5s ease-out infinite;
  }
  .radar::before { inset: 30px; }
  .radar::after  { inset: 30px; animation-delay: 1.25s; }
  @keyframes radarPing {
    0%   { transform: scale(0.5); opacity: 1; }
    100% { transform: scale(2.2); opacity: 0; }
  }
  .radar-sweep {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background: conic-gradient(
      from 0deg,
      transparent 0deg,
      rgba(96,165,250,0.6) 60deg,
      transparent 90deg
    );
    animation: sweep 2s linear infinite;
    mask: radial-gradient(circle, black 40%, transparent 75%);
    -webkit-mask: radial-gradient(circle, black 40%, transparent 75%);
  }
  @keyframes sweep { to { transform: rotate(360deg); } }
  .radar-center {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    font-size: 48px;
    filter: drop-shadow(0 0 15px rgba(96,165,250,0.8));
    animation: centerPulse 1.5s ease-in-out infinite;
  }
  @keyframes centerPulse {
    0%,100% { transform: translate(-50%,-50%) scale(1); }
    50%     { transform: translate(-50%,-50%) scale(1.15); }
  }

  .wait-title {
    font-size: 22px; font-weight: 900; margin-bottom: 8px;
    background: linear-gradient(135deg, #bfdbfe, #60a5fa, #3b82f6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .wait-sub {
    color: var(--muted); font-size: 13px; line-height: 1.7;
    margin-bottom: 22px;
  }

  .players-count {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 10px 20px; border-radius: 999px;
    background: linear-gradient(135deg, rgba(59,130,246,0.25), rgba(139,92,246,0.15));
    border: 1.5px solid rgba(96,165,250,0.5);
    color: #bfdbfe; font-size: 14px; font-weight: bold;
    margin-bottom: 26px;
    box-shadow: 0 6px 20px rgba(59,130,246,0.25);
  }
  .players-count .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #4ade80; box-shadow: 0 0 10px #4ade80;
    animation: dotPulse 1.2s ease-in-out infinite;
  }
  @keyframes dotPulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
  .players-count b { color: #fff; font-family: monospace; font-size: 16px; }

  .wait-tips {
    background: rgba(255,255,255,0.04);
    border: 1px dashed rgba(96,165,250,0.3);
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 22px;
    text-align: right;
  }
  .wait-tips .tip-title {
    font-size: 11px; color: #93c5fd; font-weight: bold;
    margin-bottom: 8px; letter-spacing: 0.5px;
  }
  .wait-tips ul {
    list-style: none; padding: 0; margin: 0;
  }
  .wait-tips li {
    font-size: 12px; color: #cbd5e1;
    padding: 3px 0; line-height: 1.6;
  }
  .wait-tips li::before { content: "✦ "; color: #60a5fa; margin-left: 4px; }

  .cancel-btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 13px 32px; border-radius: 14px;
    background: rgba(239,68,68,0.15); color: #fca5a5;
    border: 1.5px solid rgba(239,68,68,0.4);
    text-decoration: none; font-weight: bold; font-size: 14px;
    transition: all 0.2s;
  }
  .cancel-btn:hover {
    background: rgba(239,68,68,0.3);
    border-color: #ef4444;
    color: #fff;
    transform: translateY(-2px);
  }
</style>
{% endblock %}

{% block content %}
  <div class="wait-wrap">
    <div class="radar">
      <div class="radar-sweep"></div>
      <div class="radar-center">🎯</div>
    </div>

    <div class="wait-title">در حال جستجوی حریف...</div>
    <div class="wait-sub">کمی صبر کن، به‌محض پیدا شدن<br>حریف، خودکار به بازی می‌ری.</div>

    <div class="players-count">
      <span class="dot"></span>
      <span>در صف:</span>
      <b id="countBox">...</b>
      <span>نفر</span>
    </div>

    <div class="wait-tips">
      <div class="tip-title">💡 نکته</div>
      <ul>
        <li>بازی سریع شروع می‌شه، آماده باش</li>
        <li>می‌تونی هم‌زمان با دوستات هم بازی کنی</li>
        <li>اگه خسته شدی، لغو کن</li>
      </ul>
    </div>

    <a href="/game/match/cancel/" class="cancel-btn">✕ لغو جستجو</a>
  </div>
{% endblock %}

{% block extra_js %}
<script>
  let checks = 0;
  const interval = setInterval(checkStatus, 2000);

  function checkStatus() {
    checks++;
    if (checks > 60) {
      clearInterval(interval);
      alert('حریفی پیدا نشد. دوباره تلاش کن.');
      window.location.href = '/game/rooms/';
      return;
    }
    fetch('/game/match/status/')
      .then(r => r.json())
      .then(data => {
        if (data.status === 'matched') {
          clearInterval(interval);
          window.location.href = data.url;
        } else if (data.status === 'cancelled') {
          clearInterval(interval);
          window.location.href = '/game/rooms/';
        } else if (data.count !== undefined) {
          const box = document.getElementById('countBox');
          if (box) box.textContent = data.count;
        }
      })
      .catch(e => console.log(e));
  }
</script>
{% endblock %}
'''
backup(p); write(p, MATCH_WAIT)

# ============================================================
# 2) team_wait.html - 4 slots with avatars
# ============================================================
print("\n[2/3] team_wait.html")
p = os.path.join(ROOT, "game", "templates", "game", "team_wait.html")

TEAM_WAIT = '''{% extends "base.html" %}
{% block title %}در انتظار بازیکنان{% endblock %}

{% block extra_css %}
<style>
  .wait-wrap {
    text-align: center;
    padding: 36px 20px 28px;
    background:
      radial-gradient(circle at 50% 0%, rgba(139,92,246,0.4), transparent 55%),
      radial-gradient(circle at 50% 100%, rgba(236,72,153,0.2), transparent 55%),
      linear-gradient(135deg, #1a0f2e, #170a24, #0f0f1e);
    border: 2px solid rgba(139,92,246,0.6);
    border-radius: 28px;
    margin-top: 16px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(139,92,246,0.3);
  }
  .wait-wrap::before {
    content: "";
    position: absolute;
    inset: -50%;
    background: conic-gradient(
      from 0deg,
      transparent 0deg,
      rgba(167,139,250,0.12) 90deg,
      transparent 180deg,
      rgba(236,72,153,0.12) 270deg,
      transparent 360deg
    );
    animation: teamRotate 10s linear infinite;
    z-index: 0;
    pointer-events: none;
  }
  @keyframes teamRotate { to { transform: rotate(360deg); } }
  .wait-wrap > * { position: relative; z-index: 1; }

  .team-title {
    font-size: 22px; font-weight: 900; margin-bottom: 6px;
    background: linear-gradient(135deg, #e9d5ff, #a78bfa, #ec4899);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .team-sub {
    color: var(--muted); font-size: 12.5px; line-height: 1.7;
    margin-bottom: 24px;
  }

  /* 4 slots grid */
  .slots {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 24px;
    padding: 0 8px;
  }
  .slot {
    position: relative;
    padding: 16px 12px;
    border-radius: 18px;
    border: 2px dashed rgba(167,139,250,0.35);
    background: rgba(15,23,42,0.4);
    min-height: 110px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    transition: all 0.3s;
  }
  .slot.filled {
    border-style: solid;
    border-color: rgba(74,222,128,0.6);
    background: linear-gradient(135deg, rgba(34,197,94,0.15), rgba(15,23,42,0.6));
    box-shadow: 0 8px 20px rgba(34,197,94,0.2);
    animation: slotFill 0.4s ease-out;
  }
  @keyframes slotFill {
    from { transform: scale(0.9); opacity: 0.7; }
    to   { transform: scale(1); opacity: 1; }
  }
  .slot.me {
    border-color: var(--gold) !important;
    background: linear-gradient(135deg, rgba(244,197,66,0.2), rgba(15,23,42,0.6)) !important;
    box-shadow: 0 8px 20px rgba(244,197,66,0.3) !important;
  }
  .slot-avatar {
    width: 48px; height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(139,92,246,0.4), rgba(6,182,212,0.2));
    display: flex; align-items: center; justify-content: center;
    font-size: 26px;
    margin-bottom: 6px;
    border: 2px solid rgba(255,255,255,0.15);
    background-size: cover; background-position: center;
  }
  .slot.filled .slot-avatar {
    border-color: #4ade80;
    box-shadow: 0 0 15px rgba(74,222,128,0.5);
  }
  .slot.me .slot-avatar {
    border-color: var(--gold);
    box-shadow: 0 0 15px rgba(244,197,66,0.6);
  }
  .slot-name {
    font-size: 12px;
    font-weight: bold;
    color: #fff;
    text-align: center;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100%;
  }
  .slot.me .slot-name { color: var(--gold); }
  .slot-empty {
    font-size: 32px;
    color: rgba(167,139,250,0.4);
    margin-bottom: 6px;
    animation: emptyPulse 1.5s ease-in-out infinite;
  }
  @keyframes emptyPulse {
    0%,100% { opacity: 0.4; }
    50%     { opacity: 0.9; }
  }
  .slot-empty-lbl {
    font-size: 10.5px;
    color: rgba(148,163,184,0.6);
  }

  .progress-box {
    margin-bottom: 20px;
  }
  .progress-text {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 18px; border-radius: 999px;
    background: linear-gradient(135deg, rgba(139,92,246,0.25), rgba(236,72,153,0.15));
    border: 1.5px solid rgba(167,139,250,0.5);
    color: #e9d5ff; font-size: 13px; font-weight: bold;
    margin-bottom: 10px;
  }
  .progress-text b { color: #fff; font-family: monospace; font-size: 16px; }
  .progress-bar {
    width: 90%; max-width: 300px;
    height: 8px;
    background: rgba(148,163,184,0.15);
    border-radius: 8px;
    overflow: hidden;
    margin: 0 auto;
  }
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #8b5cf6, #ec4899, #8b5cf6);
    background-size: 200% 100%;
    border-radius: 8px;
    transition: width 0.5s ease-out;
    box-shadow: 0 0 15px rgba(167,139,250,0.6);
    animation: progressShine 2s linear infinite;
  }
  @keyframes progressShine {
    0%   { background-position: 0% 50%; }
    100% { background-position: 200% 50%; }
  }

  .cancel-btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 13px 32px; border-radius: 14px;
    background: rgba(239,68,68,0.15); color: #fca5a5;
    border: 1.5px solid rgba(239,68,68,0.4);
    text-decoration: none; font-weight: bold; font-size: 14px;
    transition: all 0.2s;
  }
  .cancel-btn:hover {
    background: rgba(239,68,68,0.3);
    border-color: #ef4444;
    color: #fff;
    transform: translateY(-2px);
  }
</style>
{% endblock %}

{% block content %}
  <div class="wait-wrap">
    <div class="team-title">دنبال هم‌تیمی‌ها...</div>
    <div class="team-sub">برای بازی تیمی ۴ نفره لازمه<br>وقتی همه جمع شدن، تیم انتخاب می‌کنی</div>

    <div class="slots" id="slotsGrid">
      <div class="slot me" data-slot="0">
        <div class="slot-avatar">
          {% if user.avatar_type == "image" and user.avatar_id %}
            <div style="width:100%;height:100%;border-radius:50%;background-image:url('/static/avatars/images/{{ user.avatar_id|stringformat:"03d" }}.jpg');background-size:cover;"></div>
          {% else %}
            {{ user.avatar_emoji|default:"👤" }}
          {% endif %}
        </div>
        <div class="slot-name">{{ user.alias }} (شما)</div>
      </div>
      <div class="slot" data-slot="1">
        <div class="slot-empty">?</div>
        <div class="slot-empty-lbl">در انتظار...</div>
      </div>
      <div class="slot" data-slot="2">
        <div class="slot-empty">?</div>
        <div class="slot-empty-lbl">در انتظار...</div>
      </div>
      <div class="slot" data-slot="3">
        <div class="slot-empty">?</div>
        <div class="slot-empty-lbl">در انتظار...</div>
      </div>
    </div>

    <div class="progress-box">
      <div class="progress-text">
        <span>در صف:</span>
        <b id="countBox">...</b>
        <span>/ 4 نفر</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" id="progressFill" style="width: 25%;"></div>
      </div>
    </div>

    <a href="/game/team/cancel/" class="cancel-btn">✕ لغو</a>
  </div>
{% endblock %}

{% block extra_js %}
<script>
  let checks = 0;
  const interval = setInterval(() => {
    checks++;
    if (checks > 60) {
      clearInterval(interval);
      alert('کسی پیدا نشد. دوباره تلاش کن.');
      window.location.href = '/game/rooms/';
      return;
    }
    fetch('/game/team/status/')
      .then(r => r.json())
      .then(d => {
        if (d.status === 'matched') {
          clearInterval(interval);
          window.location.href = d.url;
        } else if (d.status === 'cancelled') {
          clearInterval(interval);
          window.location.href = '/game/rooms/';
        } else if (d.count !== undefined) {
          const count = Math.min(d.count, 4);
          document.getElementById('countBox').textContent = count;
          document.getElementById('progressFill').style.width = (count * 25) + '%';
          // Update slots
          for (let i = 1; i < count && i < 4; i++) {
            const slot = document.querySelector(`.slot[data-slot="${i}"]`);
            if (slot && !slot.classList.contains('filled')) {
              slot.classList.add('filled');
              slot.innerHTML = '<div class="slot-avatar">👤</div><div class="slot-name">بازیکن ' + (i + 1) + '</div>';
            }
          }
        }
      })
      .catch(e => console.log(e));
  }, 2000);
</script>
{% endblock %}
'''
backup(p); write(p, TEAM_WAIT)

# ============================================================
# 3) Verify + note about avatar_emoji in base context
# ============================================================
print("\n[3/3] Verification")
print("  match_wait.html: radar animation ✓" if "radar-sweep" in read(p) else "  match_wait.html: ✗")
print("  team_wait.html: 4 slots ✓" if 'data-slot="3"' in read(p) else "  team_wait.html: ✗")

# Check if user.avatar_emoji works (custom User model might not have this attribute)
accounts_models = os.path.join(ROOT, "accounts", "models.py")
acc_src = read(accounts_models)
if "def avatar_emoji" in acc_src or "@property" in acc_src and "avatar_emoji" in acc_src:
    print("  user.avatar_emoji property exists ✓")
else:
    print("  ⚠ user.avatar_emoji property may not exist — check team_wait.html shows emoji")
    print("    If avatar shows empty, we'll add a context processor")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
What's new:
  📡 match_wait: radar sweep + ping animation + pulsing target + tips card
  👥 team_wait:  4 live slots grid + progress bar + count update
  ✨ Both use rotating conic gradient backgrounds matching super cards

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R

Test:
  - /game/match/ -> radar screen (blue)
  - /game/team/start/ -> 4 slots (purple/pink)
""")
