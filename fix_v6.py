#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, subprocess, sys

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
# 1) base.html - bottom nav: remove خانه + دوستان
# ============================================================
print("\n[1/7] base.html - bottom nav")
p = os.path.join(ROOT, "templates", "base.html")
src = read(p)

old_nav_marker = "خانه</span>"
if old_nav_marker not in src:
    print("  SKIP: خانه already removed")
else:
    # Replace the entire bottom-nav block
    import re
    pat = re.compile(r'<nav class="bottom-nav">.*?</nav>', re.DOTALL)
    m = pat.search(src)
    if m:
        new_nav = '''<nav class="bottom-nav">
  <a href="/game/" class="nav-link {% if active == 'home' or active == 'games' %}active{% endif %}">
    <span class="nav-icon">🎮</span>
    <span>بازی‌ها</span>
  </a>
  <a href="/game/rooms/manage/" class="nav-link {% if active == 'rooms' %}active{% endif %}">
    <span class="nav-icon">🚪</span>
    <span>اتاق‌ها</span>
  </a>
  <a href="/accounts/profile/" class="nav-link {% if active == 'profile' %}active{% endif %}">
    <span class="nav-icon">👤</span>
    <span>پروفایل</span>
  </a>
</nav>'''
        src = src[:m.start()] + new_nav + src[m.end():]
        backup(p); write(p, src)
        print("  FIXED: nav has 3 items now")
    else:
        print("  WARN: bottom-nav block not found")

# ============================================================
# 2) menu.html - friends icon + coin HUD redesign
# ============================================================
print("\n[2/7] menu.html - top bar + coin HUD")
p = os.path.join(ROOT, "game", "templates", "game", "menu.html")
src = read(p)

# 2a) Replace top-bar to add friends icon
old_top = '''  <div class="top-bar">
    <div class="version-badge">
      <span>🧪</span>
      <span>نسخه آزمایشی</span>
    </div>
    <a href="/accounts/settings/" class="settings-icon" title="تنظیمات">⚙️</a>
  </div>'''
new_top = '''  <div class="top-bar">
    <div class="version-badge">
      <span>🧪</span>
      <span>نسخه آزمایشی</span>
    </div>
    <div style="display:flex; gap:8px;">
      <a href="/social/" class="settings-icon" title="دوستان">👥</a>
      <a href="/accounts/settings/" class="settings-icon" title="تنظیمات">⚙️</a>
    </div>
  </div>'''
if old_top in src:
    src = src.replace(old_top, new_top, 1)
    print("  FIXED: friends icon added to top-bar")
else:
    print("  WARN: top-bar not found")

# 2b) Replace coin HUD HTML
old_hud = '''  <div class="coin-hud">
    <div class="hud-chip hud-coins"><span>🪙</span><span class="num">{{ user.coins|default:0 }}</span><span style="font-size:11px;opacity:0.7;">سکه</span></div>
    <div class="hud-chip hud-gems"><span>💎</span><span class="num">{{ user.gems|default:0 }}</span><span style="font-size:11px;opacity:0.7;">جم</span></div>
  </div>'''
new_hud = '''  <div class="coin-hud">
    <div class="hud-chip hud-coins">
      <div class="hud-circle">🪙</div>
      <span class="hud-num">{{ user.coins|default:0 }}</span>
      <span class="hud-lbl">سکه</span>
    </div>
    <div class="hud-chip hud-gems">
      <div class="hud-circle">💎</div>
      <span class="hud-num">{{ user.gems|default:0 }}</span>
      <span class="hud-lbl">جم</span>
    </div>
  </div>'''
if old_hud in src:
    src = src.replace(old_hud, new_hud, 1)
    print("  FIXED: coin HUD HTML replaced")
else:
    print("  WARN: coin HUD HTML not found")

# 2c) Replace coin HUD CSS
old_css = '''  .coin-hud {
    display: flex; gap: 8px; margin-bottom: 14px;
  }
  .hud-chip {
    display: flex; align-items: center; gap: 6px;
    padding: 8px 14px; border-radius: 12px;
    font-size: 13px; font-weight: bold;
    font-family: monospace;
    flex: 1; justify-content: center;
  }
  .hud-coins { background: linear-gradient(135deg, rgba(234,179,8,0.2), rgba(244,197,66,0.1)); border: 1px solid rgba(234,179,8,0.4); color: #fde68a; }
  .hud-gems { background: linear-gradient(135deg, rgba(139,92,246,0.2), rgba(6,182,212,0.1)); border: 1px solid rgba(139,92,246,0.4); color: #c4b5fd; }
  .hud-chip .num { font-size: 15px; color: #fff; font-weight: 900; }'''

new_css = '''  .coin-hud {
    display: flex; gap: 8px; margin-bottom: 14px;
    justify-content: flex-start;
  }
  .hud-chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px 5px 5px;
    border-radius: 999px;
    font-size: 12px; font-weight: bold;
    font-family: monospace;
  }
  .hud-coins {
    background: linear-gradient(135deg, rgba(234,179,8,0.15), rgba(244,197,66,0.06));
    border: 1.5px solid rgba(234,179,8,0.5);
    color: #fde68a;
  }
  .hud-gems {
    background: linear-gradient(135deg, rgba(139,92,246,0.15), rgba(6,182,212,0.06));
    border: 1.5px solid rgba(139,92,246,0.5);
    color: #c4b5fd;
  }
  .hud-circle {
    width: 26px; height: 26px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; flex-shrink: 0;
  }
  .hud-coins .hud-circle {
    background: linear-gradient(135deg, #f4c542, #ca8a04);
    box-shadow: 0 0 10px rgba(244,197,66,0.6);
  }
  .hud-gems .hud-circle {
    background: linear-gradient(135deg, #8b5cf6, #6b4eff);
    box-shadow: 0 0 10px rgba(139,92,246,0.6);
  }
  .hud-num { font-size: 13px; color: #fff; font-weight: 900; font-family: monospace; }
  .hud-lbl { font-size: 10px; opacity: 0.7; }'''

if old_css in src:
    src = src.replace(old_css, new_css, 1)
    print("  FIXED: coin HUD CSS replaced")
else:
    print("  WARN: coin HUD CSS not found")

# 2d) Replace bot card with "همه بازی‌ها"
old_bot = '''  <!-- بازی با بات -->
  <a href="/game/quick/" class="bot-btn">
    <div class="bb-icon">⚡</div>
    <div class="bb-body">
      <div class="bb-title">بازی با بات</div>
      <div class="bb-desc">سه سطح سختی — همین الان بازی کن</div>
    </div>
    <div class="bb-arrow">←</div>
  </a>'''
new_bot = '''  <!-- همه بازی‌ها -->
  <a href="/game/rooms/" class="bot-btn">
    <div class="bb-icon">🎮</div>
    <div class="bb-body">
      <div class="bb-title">همه بازی‌ها</div>
      <div class="bb-desc">بات، پلیر، گروهی، سرعتی و...</div>
    </div>
    <div class="bb-arrow">←</div>
  </a>'''
if old_bot in src:
    src = src.replace(old_bot, new_bot, 1)
    print("  FIXED: bot card -> همه بازی‌ها")
elif 'همه بازی‌ها' in src:
    print("  SKIP: card already replaced")
else:
    print("  WARN: bot card not found")

backup(p); write(p, src)

# ============================================================
# 3) rooms.html - group game link -> /game/team/start/
# ============================================================
print("\n[3/7] rooms.html - group game card")
p = os.path.join(ROOT, "game", "templates", "game", "rooms.html")
src = read(p)

old_group = '''  <a href="/game/rooms/manage/" class="big-card group">
    <div class="bc-icon">🚪</div>
    <div class="bc-body">
      <div class="bc-title">بازی گروهی</div>
      <div class="bc-desc">اتاق بساز یا به دوستانت بپیوند</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>'''
new_group = '''  <a href="/game/team/start/" class="big-card group">
    <div class="bc-icon">👥</div>
    <div class="bc-body">
      <div class="bc-title">بازی گروهی</div>
      <div class="bc-desc">۴ نفره · دو تیم ۲ نفره · ۳ راند</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>'''
if old_group in src:
    src = src.replace(old_group, new_group, 1)
    backup(p); write(p, src)
    print("  FIXED: group card -> team game")
elif '/game/team/start/' in src:
    print("  SKIP: already team link")
else:
    print("  WARN: group card not found")

# ============================================================
# 4) game/models.py - MatchQueue.mode
# ============================================================
print("\n[4/7] game/models.py - MatchQueue.mode")
p = os.path.join(ROOT, "game", "models.py")
src = read(p)

if "mode = models.CharField(max_length=8, default=\"1v1\")" in src:
    print("  SKIP: mode exists")
else:
    old = '''class MatchQueue(models.Model):
    """صف انتظار برای بازی رندم."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="match_queue",
    )
    difficulty = models.CharField(max_length=8, default="medium")'''
    new = '''class MatchQueue(models.Model):
    """صف انتظار برای بازی رندم."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="match_queue",
    )
    mode = models.CharField(max_length=8, default="1v1")
    difficulty = models.CharField(max_length=8, default="medium")'''
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: mode field added")
    else:
        print("  WARN: MatchQueue class not found")

# ============================================================
# 5) game/views.py - queue separation + round end logic
# ============================================================
print("\n[5/7] game/views.py")
p = os.path.join(ROOT, "game", "views.py")
src = read(p)
changed = False

# 5a) match_start: mode="1v1"
old = '''    # حذف از صف قبلی
    MatchQueue.objects.filter(user=request.user).delete()

    # اضافه به صف جدید
    MatchQueue.objects.create(user=request.user)'''
new = '''    # حذف از صف قبلی
    MatchQueue.objects.filter(user=request.user).delete()

    # اضافه به صف جدید
    MatchQueue.objects.create(user=request.user, mode="1v1")'''
if old in src:
    src = src.replace(old, new, 1); changed = True
    print("  FIXED: match_start mode=1v1")

# 5b) match_wait: filter 1v1
old = '''    my_queue = MatchQueue.objects.filter(user=request.user).first()
    if not my_queue:
        return redirect("game:rooms")

    # کسی هست که از من زودتر اومده؟
    opponent_queue = MatchQueue.objects.filter(
        joined_at__lt=my_queue.joined_at
    ).exclude(user=request.user).first()'''
new = '''    my_queue = MatchQueue.objects.filter(user=request.user, mode="1v1").first()
    if not my_queue:
        return redirect("game:rooms")

    # کسی هست که از من زودتر اومده؟
    opponent_queue = MatchQueue.objects.filter(
        mode="1v1",
        joined_at__lt=my_queue.joined_at
    ).exclude(user=request.user).first()'''
if old in src:
    src = src.replace(old, new, 1); changed = True
    print("  FIXED: match_wait filter 1v1")

# 5c) match_status: filter 1v1
old = '''    my_queue = MatchQueue.objects.filter(user=request.user).first()
    if not my_queue:
        return JsonResponse({"status": "cancelled"})'''
new = '''    my_queue = MatchQueue.objects.filter(user=request.user, mode="1v1").first()
    if not my_queue:
        return JsonResponse({"status": "cancelled"})'''
if old in src:
    src = src.replace(old, new, 1); changed = True
    print("  FIXED: match_status filter 1v1")

# 5d) team_start: mode="team"
old = '''    from .models import MatchQueue
    MatchQueue.objects.filter(user=request.user).delete()
    MatchQueue.objects.create(user=request.user)
    return redirect("game:team_wait")'''
new = '''    from .models import MatchQueue
    MatchQueue.objects.filter(user=request.user).delete()
    MatchQueue.objects.create(user=request.user, mode="team")
    return redirect("game:team_wait")'''
if old in src:
    src = src.replace(old, new, 1); changed = True
    print("  FIXED: team_start mode=team")

# 5e) team_wait: filter team
old = '''    my_q = MatchQueue.objects.filter(user=request.user).first()
    if not my_q:
        return redirect("game:rooms")

    # گروه‌بندی ۴ نفره: اگه ۴ نفر تو صف هستن، همه رو با هم بفرست
    total = MatchQueue.objects.count()
    if total >= 4:
        entries = list(MatchQueue.objects.order_by("joined_at")[:4])'''
new = '''    my_q = MatchQueue.objects.filter(user=request.user, mode="team").first()
    if not my_q:
        return redirect("game:rooms")

    # گروه‌بندی ۴ نفره: اگه ۴ نفر تو صف هستن، همه رو با هم بفرست
    total = MatchQueue.objects.filter(mode="team").count()
    if total >= 4:
        entries = list(MatchQueue.objects.filter(mode="team").order_by("joined_at")[:4])'''
if old in src:
    src = src.replace(old, new, 1); changed = True
    print("  FIXED: team_wait filter team")

# 5f) team_status: filter team
old = '''    if not MatchQueue.objects.filter(user=request.user).exists():
        # user left queue, check if in a team game'''
new = '''    if not MatchQueue.objects.filter(user=request.user, mode="team").exists():
        # user left queue, check if in a team game'''
if old in src:
    src = src.replace(old, new, 1); changed = True
    print("  FIXED: team_status filter team")

# 5g) team_play round end: OR instead of AND
old = '''    stop_a = Player.objects.filter(game=g, team="A", stopped_round=round_obj.number).count()
    stop_b = Player.objects.filter(game=g, team="B", stopped_round=round_obj.number).count()
    both_stopped = stop_a >= 2 and stop_b >= 2

    if (time_up or both_stopped) and not round_obj.stopped_at:'''
new = '''    stop_a = Player.objects.filter(game=g, team="A", stopped_round=round_obj.number).count()
    stop_b = Player.objects.filter(game=g, team="B", stopped_round=round_obj.number).count()
    one_team_done = (stop_a >= 2) or (stop_b >= 2)

    if (time_up or one_team_done) and not round_obj.stopped_at:'''
if old in src:
    src = src.replace(old, new, 1); changed = True
    print("  FIXED: team_play round_end = OR")

# 5h) team_status_ajax: OR instead of AND
old = '''    stop_a = Player.objects.filter(game=g, team="A", stopped_round=round_obj.number).count()
    stop_b = Player.objects.filter(game=g, team="B", stopped_round=round_obj.number).count()
    both_stopped = stop_a >= 2 and stop_b >= 2

    if round_obj.stopped_at or time_up or both_stopped:'''
new = '''    stop_a = Player.objects.filter(game=g, team="A", stopped_round=round_obj.number).count()
    stop_b = Player.objects.filter(game=g, team="B", stopped_round=round_obj.number).count()
    one_team_done = (stop_a >= 2) or (stop_b >= 2)

    if round_obj.stopped_at or time_up or one_team_done:'''
if old in src:
    src = src.replace(old, new, 1); changed = True
    print("  FIXED: team_status_ajax round_end = OR")

if changed:
    backup(p); write(p, src)

# ============================================================
# 6) team_play.html - better polling
# ============================================================
print("\n[6/7] team_play.html - polling JS")
p = os.path.join(ROOT, "game", "templates", "game", "team_play.html")
src = read(p)

old_js = '''<script>
  let left = {{ duration }} - {{ elapsed }};
  if (left < 0) left = 0;
  const timerEl = document.getElementById('timer');
  const timer = setInterval(() => {
    left--;
    if (timerEl) timerEl.textContent = left;
    if (left <= 0) { clearInterval(timer); }
  }, 1000);

  setInterval(() => {
    fetch('/game/team/play-status/{{ game.code }}/').then(r=>r.json()).then(d => {
      if (d.status === 'round_end') { clearInterval(timer); window.location.href = d.url; }
      else if (d.status === 'playing') {
        if (d.my_stopped && !document.querySelector('.waiting-box')) window.location.reload();
      }
    }).catch(()=>{});
  }, 2500);
</script>'''

new_js = '''<script>
  let left = {{ duration }} - {{ elapsed }};
  if (left < 0) left = 0;
  const timerEl = document.getElementById('timer');
  const timer = setInterval(() => {
    left--;
    if (timerEl) timerEl.textContent = left;
    if (left <= 0) { clearInterval(timer); }
  }, 1000);

  let lastState = "{% if my_stopped %}1{% else %}0{% endif %}-{% if teammate_stopped %}1{% else %}0{% endif %}";
  setInterval(() => {
    fetch('/game/team/play-status/{{ game.code }}/').then(r=>r.json()).then(d => {
      if (d.status === 'round_end') { clearInterval(timer); window.location.href = d.url; return; }
      if (d.status === 'playing') {
        const st = (d.my_stopped ? 1 : 0) + "-" + (d.teammate_stopped ? 1 : 0);
        if (st !== lastState) { window.location.reload(); }
      }
    }).catch(()=>{});
  }, 2000);
</script>'''
if old_js in src:
    src = src.replace(old_js, new_js, 1)
    backup(p); write(p, src)
    print("  FIXED: polling JS")
else:
    print("  WARN: polling JS block not found")

# ============================================================
# 7) Migrations
# ============================================================
print("\n[7/7] Migrations")
for cmd in [
    [sys.executable, "manage.py", "makemigrations", "game"],
    [sys.executable, "manage.py", "migrate"],
]:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd[1:])}")
    if r.stdout.strip(): print("   ", r.stdout.strip().replace("\n", "\n    ")[:400])
    if r.returncode != 0 and r.stderr.strip():
        print("   ERR:", r.stderr.strip()[:300])

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Summary:
  1. Bottom nav: بازی‌ها | اتاق‌ها | پروفایل (خانه و دوستان حذف)
  2. menu.html: friends icon in top-bar + redesigned coin HUD (circle icons + pill borders)
  3. menu.html: bot card -> "همه بازی‌ها" -> /game/rooms/
  4. MatchQueue.mode: 1v1 vs team separation
  5. match_wait, team_wait, match_status, team_status: filter by mode
  6. team_play + team_status_ajax: round ends when EITHER team both stop
  7. team_play.html: better state tracking in polling
  8. rooms.html: "بازی گروهی" -> /game/team/start/

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R

Test:
  - Menu (بازی‌ها) shows coin/gem pills + friends icon
  - Tap "همه بازی‌ها" to see all modes
  - Team game: 4 players → teams → 3 rounds
""")
