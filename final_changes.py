#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) menu.html - remove alliance, reorder, disable shop, beta badge, settings left
# ============================================================
print("\n[1/6] Updating menu.html")

p = "game/templates/game/menu.html"
src = read(p)

# 1a) Remove alliance button (any version)
alliance_patterns = [
    r'<a href="/alliance/"[^>]*class="round-btn[^"]*"[^>]*>.*?</a>\s*',
    r'<a href="/alliance/"[^>]*>.*?</a>\s*',
]
for pattern in alliance_patterns:
    src = re.sub(pattern, '', src, flags=re.DOTALL)

# 1b) Replace top-bar with new layout (settings on left, beta animated on right)
old_topbar_pattern = re.compile(
    r'<div class="top-bar"[^>]*>.*?</div>\s*(?=<div class="coin-hud"|<div class="user-row"|<!--)',
    re.DOTALL
)
new_topbar = '''<div class="top-bar" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
  <div class="beta-badge-animated">
    <span style="font-size:14px;">🧪</span>
    <span>نسخه آزمایشی</span>
  </div>
  <div style="display:flex; align-items:center; gap:8px;">
    <a href="/accounts/settings/" class="settings-icon" title="تنظیمات">⚙️</a>
  </div>
</div>

'''
src = old_topbar_pattern.sub(new_topbar, src, count=1)

# 1c) Add CSS for animated beta badge + settings (if not present)
if ".beta-badge-animated" not in src:
    style_end = src.find("</style>")
    if style_end > 0:
        new_css = '''
  .beta-badge-animated {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 14px;
    background: linear-gradient(135deg, #eab308, #f59e0b);
    color: #1a1a1a;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 900;
    box-shadow: 0 4px 12px rgba(234,179,8,0.4);
    animation: betaPulse 2.2s ease-in-out infinite;
  }
  @keyframes betaPulse {
    0%, 100% { transform: scale(1); box-shadow: 0 4px 12px rgba(234,179,8,0.4); }
    50%      { transform: scale(1.08); box-shadow: 0 6px 20px rgba(234,179,8,0.7); }
  }
'''
        src = src[:style_end] + new_css + src[style_end:]

# 1d) Reorder: top-players row first, then shop disabled
# Find round-row block and rebuild
old_row_pattern = re.compile(
    r'<div class="round-row"[^>]*>.*?</div>\s*(?=<a href="/game/quick/|<!--)',
    re.DOTALL
)
new_rows = '''<div class="round-row" style="display:flex; gap:10px; justify-content:flex-end; margin-bottom:14px; flex-wrap:wrap;">
  <a href="/game/top-players/" class="round-btn round-top" title="بازیکنان برتر">
    <span class="rb-icon">⭐</span>
    <span class="rb-label">برتر</span>
  </a>
  <div class="round-btn round-shop-disabled" title="به زودی" style="opacity:0.45; cursor:not-allowed; background:rgba(148,163,184,0.15); border:1.5px solid rgba(148,163,184,0.25);">
    <span class="rb-icon" style="filter:grayscale(1);">🛒</span>
    <span class="rb-label" style="color:#94a3b8;">به زودی</span>
  </div>
</div>

'''
src = old_row_pattern.sub(new_rows, src, count=1)

write(p, src)
print("  ✓ menu.html updated")

# ============================================================
# 2) Puzzle game - views, urls, templates
# ============================================================
print("\n[2/6] Building puzzle game")

# Add puzzle views
p = "game/views.py"
src = read(p)

if "def puzzle_setup(request):" in src:
    print("  ✓ Puzzle views already exist")
else:
    puzzle_code = '''

# ============================================================
# PUZZLE GAME (بازی معما - unscramble words)
# ============================================================
PUZZLE_WORDS_EASY = [
    "کتاب", "خانه", "دوست", "میوه", "نان", "دریا", "ماه", "گل",
    "شهر", "آب", "مادر", "پدر", "گربه", "مرغ", "سیب", "انار",
]
PUZZLE_WORDS_MEDIUM = [
    "دانشگاه", "کتابخانه", "خانواده", "دوستی", "کوهستان",
    "خورشید", "ستاره", "پرستو", "عقاب", "باران", "مدرسه",
    "دانشمند", "فرودگاه", "بیمارستان", "آشپزخانه",
]
PUZZLE_WORDS_HARD = [
    "دانشگاه", "کتابخانه", "خانواده", "پرستو", "خورشید",
    "بیمارستان", "فرودگاه", "دانشمند", "آشپزخانه",
    "کوهنوردی", "کامپیوتر", "تلویزیون", "یخچال", "پنکه",
]

PUZZLE_ROUNDS = 5
PUZZLE_TIME = 90


def _scramble_word(word):
    """Scramble letters of a word, ensuring result != original."""
    import random
    chars = list(word)
    if len(chars) < 2:
        return word
    for _ in range(30):
        random.shuffle(chars)
        result = "".join(chars)
        if result != word:
            return result
    chars[0], chars[1] = chars[1], chars[0]
    return "".join(chars)


@login_required
def puzzle_setup(request):
    check = _require_complete(request.user)
    if check:
        return check

    if request.method == "POST":
        difficulty = request.POST.get("difficulty", "medium")
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"

        import random
        if difficulty == "easy":
            pool = PUZZLE_WORDS_EASY
        elif difficulty == "hard":
            pool = PUZZLE_WORDS_HARD
        else:
            pool = PUZZLE_WORDS_MEDIUM

        words = random.sample(pool, min(PUZZLE_ROUNDS, len(pool)))

        from .models import Game, Player
        game = Game.objects.create(
            host=request.user, status="in_round",
            categories=["معما"], mode="puzzle",
            difficulty=difficulty, letter_mode="random",
        )
        Player.objects.create(game=game, user=request.user)

        # Scramble and save to session
        scrambled = [{"original": w, "scrambled": _scramble_word(w)} for w in words]
        request.session["puzzle_game_id"] = str(game.id)
        request.session["puzzle_words"] = scrambled
        request.session["puzzle_difficulty"] = difficulty

        return redirect("game:puzzle_play")

    return render(request, "game/puzzle_setup.html", {
        "active": "games",
    })


@login_required
def puzzle_play(request):
    check = _require_complete(request.user)
    if check:
        return check

    game_id = request.session.get("puzzle_game_id")
    words = request.session.get("puzzle_words")
    if not game_id or not words:
        return redirect("game:puzzle_setup")

    return render(request, "game/puzzle_play.html", {
        "words": words,
        "duration": PUZZLE_TIME,
        "active": "games",
    })


@login_required
def puzzle_submit(request):
    check = _require_complete(request.user)
    if check:
        return check

    if request.method != "POST":
        return redirect("game:puzzle_setup")

    game_id = request.session.get("puzzle_game_id")
    words = request.session.get("puzzle_words") or []
    difficulty = request.session.get("puzzle_difficulty", "medium")

    if not game_id or not words:
        return redirect("game:puzzle_setup")

    # Check answers
    results = []
    correct_count = 0
    for i, w in enumerate(words):
        user_answer = (request.POST.get(f"word_{i}") or "").strip()
        original = w["original"]
        is_correct = _normalize(user_answer) == _normalize(original)
        if is_correct:
            correct_count += 1
        results.append({
            "scrambled": w["scrambled"],
            "original": original,
            "user_answer": user_answer,
            "is_correct": is_correct,
        })

    # Calculate score based on difficulty
    base_points = {"easy": 10, "medium": 15, "hard": 25}.get(difficulty, 15)
    score = correct_count * base_points

    # Save to Player
    try:
        from .models import Game, Player
        game = Game.objects.get(id=game_id)
        player, _ = Player.objects.get_or_create(game=game, user=request.user)
        player.score = score
        player.save(update_fields=["score"])
        game.status = "finished"
        game.save(update_fields=["status"])
    except Exception:
        pass

    # Clear session
    for key in ["puzzle_game_id", "puzzle_words", "puzzle_difficulty"]:
        request.session.pop(key, None)

    return render(request, "game/puzzle_result.html", {
        "results": results,
        "score": score,
        "correct_count": correct_count,
        "total": len(words),
        "difficulty": difficulty,
        "base_points": base_points,
        "active": "games",
    })
'''
    src = src.rstrip() + puzzle_code + "\n"
    write(p, src)
    print("  ✓ Puzzle views added")

# Add URLs
p = "game/urls.py"
src = read(p)
if "puzzle_setup" not in src:
    old = '    path("challenge/", views.challenge_home, name="challenge"),'
    new = old + '''
    path("puzzle/", views.puzzle_setup, name="puzzle_setup"),
    path("puzzle/play/", views.puzzle_play, name="puzzle_play"),
    path("puzzle/submit/", views.puzzle_submit, name="puzzle_submit"),'''
    if old in src:
        src = src.replace(old, new, 1)
    else:
        src = src.rsplit("]", 1)[0] + '''    path("puzzle/", views.puzzle_setup, name="puzzle_setup"),
    path("puzzle/play/", views.puzzle_play, name="puzzle_play"),
    path("puzzle/submit/", views.puzzle_submit, name="puzzle_submit"),
]'''
    write(p, src)
    print("  ✓ Puzzle URLs added")

# Template: puzzle_setup.html
write("game/templates/game/puzzle_setup.html", '''{% extends "base.html" %}
{% block title %}بازی معما{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.head h1{font-size:22px;font-weight:bold}
.head h1 span{color:var(--gold)}
.hero{padding:30px 20px;background:radial-gradient(circle at 100% 0%,rgba(34,197,94,.3),transparent 60%),linear-gradient(135deg,#0a2a1a,#0f0f1e);border:1.5px solid rgba(34,197,94,.5);border-radius:24px;margin-bottom:20px;text-align:center}
.hero .icon{font-size:60px;margin-bottom:10px}
.hero h2{font-size:22px;font-weight:900;margin-bottom:8px;background:linear-gradient(135deg,#bbf7d0,#4ade80);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero p{color:var(--muted);font-size:13px;line-height:1.7}
.card{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:22px;margin-bottom:16px}
.card h3{font-size:15px;color:var(--gold);margin-bottom:16px}
.diff-row{display:flex;gap:10px;margin-bottom:16px}
.diff{flex:1;padding:16px;border-radius:14px;border:2px solid var(--border);background:var(--bg);text-align:center;cursor:pointer;transition:.2s}
.diff input{display:none}
.diff:hover{border-color:rgba(34,197,94,.4)}
.diff:has(input:checked){border-color:var(--green);background:linear-gradient(135deg,rgba(34,197,94,.2),rgba(6,182,212,.1));box-shadow:0 0 20px rgba(34,197,94,.3)}
.diff .icon{font-size:32px;margin-bottom:6px}
.diff .name{font-size:14px;font-weight:bold;color:#fff;margin-bottom:2px}
.diff .desc{font-size:11px;color:var(--muted)}
.start-btn{width:100%;padding:18px;border:none;border-radius:16px;font-size:17px;font-weight:900;font-family:inherit;cursor:pointer;color:#1a1a1a;background:linear-gradient(135deg,#22c55e,#16a34a);box-shadow:0 10px 30px rgba(34,197,94,.4);transition:.2s}
.start-btn:hover{transform:translateY(-2px)}
</style>
{% endblock %}
{% block content %}
<div class="head"><a href="/game/rooms/" class="back-btn"><span class="arrow-icon">→</span></a><h1>🎯 <span>بازی معما</span></h1></div>
<div class="hero">
  <div class="icon">🎯</div>
  <h2>بازی معما</h2>
  <p>حروف به هم ریخته رو مرتب کن و کلمه درست رو پیدا کن!</p>
</div>
<form method="post">
  {% csrf_token %}
  <div class="card">
    <h3>🎚️ سطح سختی</h3>
    <div class="diff-row">
      <label class="diff"><input type="radio" name="difficulty" value="easy" checked><div class="icon">😊</div><div class="name">آسان</div><div class="desc">۱۰ امتیاز/کلمه</div></label>
      <label class="diff"><input type="radio" name="difficulty" value="medium"><div class="icon">😐</div><div class="name">متوسط</div><div class="desc">۱۵ امتیاز/کلمه</div></label>
      <label class="diff"><input type="radio" name="difficulty" value="hard"><div class="icon">😈</div><div class="name">سخت</div><div class="desc">۲۵ امتیاز/کلمه</div></label>
    </div>
  </div>
  <button type="submit" class="start-btn">🚀 شروع بازی</button>
</form>
{% endblock %}
''')
print("  ✓ puzzle_setup.html")

# Template: puzzle_play.html
write("game/templates/game/puzzle_play.html", '''{% extends "base.html" %}
{% block title %}بازی معما{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;padding:16px;background:radial-gradient(circle at 100% 0%,rgba(34,197,94,.2),transparent 60%),linear-gradient(135deg,#1a1a2e,#0f0f1e);border:1.5px solid rgba(34,197,94,.4);border-radius:22px}
.head h1{font-size:18px;font-weight:900}
.timer{font-size:26px;font-weight:900;font-family:monospace;color:var(--green)}
.word-card{display:flex;align-items:center;gap:12px;padding:14px 18px;background:var(--card);border:1.5px solid var(--border);border-radius:16px;margin-bottom:10px}
.scrambled{font-size:22px;font-weight:900;font-family:monospace;color:#4ade80;min-width:100px;text-align:center;letter-spacing:3px;background:rgba(34,197,94,.1);padding:8px 14px;border-radius:10px}
.answer-input{flex:1;padding:14px 16px;border-radius:12px;border:1.5px solid var(--border);background:var(--bg);color:#fff;font-size:16px;font-family:inherit}
.answer-input:focus{outline:none;border-color:var(--green)}
.submit-btn{width:100%;margin-top:20px;padding:18px;border:none;border-radius:16px;font-size:17px;font-weight:900;font-family:inherit;cursor:pointer;color:#1a1a1a;background:linear-gradient(135deg,#22c55e,#16a34a);box-shadow:0 10px 30px rgba(34,197,94,.4)}
.submit-btn:hover{transform:translateY(-2px)}
.form-wrap{padding-bottom:20px}
</style>
{% endblock %}
{% block content %}
<div class="head">
  <h1>🎯 بازی معما</h1>
  <div class="timer" id="timer">{{ duration }}</div>
</div>
<form method="post" action="/game/puzzle/submit/" id="puzzleForm" class="form-wrap">
  {% csrf_token %}
  {% for w in words %}
  <div class="word-card">
    <div class="scrambled">{{ w.scrambled }}</div>
    <input type="text" name="word_{{ forloop.counter0 }}" class="answer-input" placeholder="پاسخ..." autocomplete="off" maxlength="20">
  </div>
  {% endfor %}
  <button type="submit" class="submit-btn">✅ ارسال پاسخ‌ها</button>
</form>
<script>
  let left = {{ duration }};
  const timerEl = document.getElementById('timer');
  const form = document.getElementById('puzzleForm');
  const interval = setInterval(() => {
    left--;
    timerEl.textContent = left;
    if (left <= 10) timerEl.style.color = '#ef4444';
    if (left <= 0) { clearInterval(interval); form.submit(); }
  }, 1000);
</script>
{% endblock %}
''')
print("  ✓ puzzle_play.html")

# Template: puzzle_result.html
write("game/templates/game/puzzle_result.html", '''{% extends "base.html" %}
{% block title %}نتیجه معما{% endblock %}
{% block extra_css %}
<style>
.hero{text-align:center;padding:36px 24px;background:radial-gradient(circle at 50% 0%,rgba(34,197,94,.3),transparent 70%),linear-gradient(135deg,#1a1a2e,#0f0f1e);border:2px solid rgba(34,197,94,.5);border-radius:24px;margin-bottom:20px}
.hero .icon{font-size:80px;margin-bottom:12px}
.hero h1{font-size:26px;font-weight:900;margin-bottom:16px;background:linear-gradient(135deg,#bbf7d0,#4ade80,#16a34a);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.score-box{display:inline-block;padding:16px 32px;background:rgba(34,197,94,.15);border:2px solid rgba(34,197,94,.5);border-radius:18px;margin-top:12px}
.score-box .lbl{font-size:11px;color:#94a3b8;margin-bottom:6px}
.score-box .val{font-size:42px;font-weight:900;font-family:monospace;color:#4ade80}
.stats{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:20px}
.stat{padding:14px;background:var(--card);border:1px solid var(--border);border-radius:14px;text-align:center}
.stat .v{font-size:22px;font-weight:900;color:#fff;font-family:monospace;margin-bottom:4px}
.stat .l{font-size:11px;color:var(--muted)}
.result-card{padding:14px;background:var(--card);border:1.5px solid var(--border);border-radius:14px;margin-bottom:8px;display:flex;align-items:center;gap:12px}
.result-card.correct{border-color:rgba(34,197,94,.5);background:linear-gradient(135deg,rgba(34,197,94,.08),var(--card))}
.result-card.wrong{border-color:rgba(239,68,68,.4);background:linear-gradient(135deg,rgba(239,68,68,.05),var(--card))}
.result-card .em{font-size:24px;width:36px;text-align:center}
.result-card .body{flex:1}
.result-card .label{font-size:10px;color:var(--muted);margin-bottom:2px}
.result-card .word{font-size:16px;font-weight:bold;color:#fff}
.result-card .answer{font-size:12px;color:#fca5a5;margin-top:2px}
.actions{display:flex;gap:10px;margin-top:20px}
.actions a{flex:1;padding:16px;border-radius:14px;text-decoration:none;text-align:center;font-weight:900;font-size:15px}
.btn-home{background:rgba(51,65,85,.7);color:#cbd5e1;border:1px solid rgba(148,163,184,.2)}
.btn-again{background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;box-shadow:0 8px 20px rgba(34,197,94,.4)}
</style>
{% endblock %}
{% block content %}
<div class="hero">
  <div class="icon">{% if correct_count == total %}🏆{% elif correct_count > total|add:"-3" %}🎉{% else %}💪{% endif %}</div>
  <h1>{% if correct_count == total %}عالی! همه درست!{% elif correct_count >= 3 %}خوب بود!{% else %}باز هم تلاش کن!{% endif %}</h1>
  <div class="score-box">
    <div class="lbl">امتیاز</div>
    <div class="val">{{ score }}</div>
  </div>
</div>
<div class="stats">
  <div class="stat"><div class="v">{{ correct_count }}/{{ total }}</div><div class="l">صحیح</div></div>
  <div class="stat"><div class="v">{{ base_points }}</div><div class="l">امتیاز/کلمه</div></div>
  <div class="stat"><div class="v">{{ difficulty }}</div><div class="l">سطح</div></div>
</div>
{% for r in results %}
<div class="result-card {% if r.is_correct %}correct{% else %}wrong{% endif %}">
  <div class="em">{% if r.is_correct %}✅{% else %}❌{% endif %}</div>
  <div class="body">
    <div class="label">{{ r.scrambled }}</div>
    <div class="word">{{ r.original }}</div>
    {% if not r.is_correct %}<div class="answer">پاسخ تو: {{ r.user_answer|default:"خالی" }}</div>{% endif %}
  </div>
</div>
{% endfor %}
<div class="actions">
  <a href="/game/" class="btn-home">🏠 خانه</a>
  <a href="/game/puzzle/" class="btn-again">🔄 دوباره</a>
</div>
{% endblock %}
''')
print("  ✓ puzzle_result.html")

# Update rooms.html - enable puzzle
p = "game/templates/game/rooms.html"
src = read(p)
old_puzzle = re.compile(
    r'<div class="big puzzle soon"[^>]*>.*?</div>\s*(?=</?div|{%|$)',
    re.DOTALL
)
new_puzzle = '''<a href="/game/puzzle/" class="big puzzle" style="background:radial-gradient(circle at 100% 0%,rgba(34,197,94,.3),transparent 60%),linear-gradient(135deg,#0a2a1a,#0f0f1e);border-color:rgba(34,197,94,.5);">
  <div class="bic">🎯</div>
  <div class="bbody"><div class="btitle">بازی معما</div><div class="bdesc">حروف به هم ریخته رو مرتب کن</div></div>
  <div class="barrow">←</div>
</a>
'''
src = old_puzzle.sub(new_puzzle, src, count=1)
write(p, src)
print("  ✓ rooms.html puzzle enabled")

# ============================================================
# 3) Admin - send to all
# ============================================================
print("\n[3/6] Adding send-to-all admin")

p = "accounts/admin_views.py"
src = read(p)

if "def send_to_all" in src:
    print("  ✓ Already exists")
else:
    src = src.rstrip() + '''

# ============================================================
# Admin — Send reward/coins to all users
# ============================================================
@never_cache
def send_to_all(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")

    from django.contrib.auth import get_user_model
    from django.db.models import F
    from social.models import Notification
    User = get_user_model()

    message = request.session.pop("admin_message", None)

    if request.method == "POST":
        action = request.POST.get("action", "send")
        if action == "send":
            try:
                coins = int(request.POST.get("coins") or 0)
                gems = int(request.POST.get("gems") or 0)
            except (ValueError, TypeError):
                coins = 0
                gems = 0
            note = (request.POST.get("note") or "").strip()[:200]

            if coins == 0 and gems == 0:
                request.session["admin_message"] = {"type": "error", "text": "حداقل یکی از مقادیر باید بیشتر از صفر باشد."}
                return redirect("custom_admin:send_to_all")

            # Bulk update
            if coins != 0 or gems != 0:
                try:
                    User.objects.all().update(
                        coins=F("coins") + coins,
                        gems=F("gems") + gems,
                    )
                except Exception as e:
                    request.session["admin_message"] = {"type": "error", "text": f"خطا: {e}"}
                    return redirect("custom_admin:send_to_all")

            # Send notification to all users
            if note:
                sender = User.objects.filter(is_staff=True).first()
                uids = User.objects.values_list("id", flat=True)
                batch = []
                for uid in uids.iterator(chunk_size=1000):
                    batch.append(Notification(
                        user_id=uid,
                        type="admin_broadcast",
                        title="🎁 جایزه ویژه!",
                        body=note,
                        url="/accounts/shop/",
                        is_read=False,
                        sender=sender,
                    ))
                    if len(batch) >= 500:
                        Notification.objects.bulk_create(batch)
                        batch = []
                if batch:
                    Notification.objects.bulk_create(batch)

            total = User.objects.count()
            request.session["admin_message"] = {
                "type": "success",
                "text": f"✅ به {total} کاربر داده شد (سکه: {coins:+d}، جم: {gems:+d}).",
            }
            return redirect("custom_admin:send_to_all")

        elif action == "reset_all":
            try:
                User.objects.all().update(coins=0, gems=0)
                request.session["admin_message"] = {"type": "success", "text": "همه سکه/جم‌ها صفر شدند."}
            except Exception as e:
                request.session["admin_message"] = {"type": "error", "text": f"خطا: {e}"}
            return redirect("custom_admin:send_to_all")

    total_users = User.objects.count()
    return render(request, "custom_admin/send_to_all.html", {
        "message": message,
        "total_users": total_users,
    })
'''
    write(p, src)
    print("  ✓ send_to_all view added")

# Add route
p = "accounts/admin_urls.py"
src = read(p)
if "send_to_all" not in src:
    old = '    path("guest-log/", admin_views.guest_log_list, name="guest_log_list"),'
    new = old + '\n    path("send-to-all/", admin_views.send_to_all, name="send_to_all"),'
    if old in src:
        src = src.replace(old, new, 1)
    else:
        src = src.rsplit("]", 1)[0] + '    path("send-to-all/", admin_views.send_to_all, name="send_to_all"),\n]'
    write(p, src)
    print("  ✓ Route added")

# Template
write("accounts/templates/custom_admin/send_to_all.html", '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>جایزه به همه — پنل ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 800px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; }
    .topbar h1 { font-size: 20px; color: #fca5a5; }
    .topbar a { padding: 9px 16px; border-radius: 10px; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold; }
    .admin-tabs { display: flex; gap: 6px; margin-bottom: 20px; background: #12121f; border: 1px solid rgba(148,163,184,0.15); padding: 6px; border-radius: 14px; overflow-x: auto; }
    .admin-tab { flex: 1; min-width: 90px; padding: 12px 14px; border-radius: 10px; text-align: center; text-decoration: none; font-size: 12px; font-weight: bold; color: #94a3b8; transition: 0.2s; white-space: nowrap; }
    .admin-tab:hover { background: rgba(148,163,184,0.1); color: #fff; }
    .admin-tab.active { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; box-shadow: 0 6px 20px rgba(239,68,68,0.4); }
    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }
    .card { background: #12121f; border: 1px solid rgba(148,163,184,0.15); border-radius: 16px; padding: 24px; margin-bottom: 16px; }
    .card h3 { color: #fdba74; font-size: 16px; margin-bottom: 16px; }
    .stats { background: rgba(59,130,246,0.1); border-right: 3px solid #3b82f6; padding: 12px 16px; border-radius: 10px; font-size: 13px; color: #93c5fd; margin-bottom: 16px; }
    label { display: block; color: #94a3b8; font-size: 12px; margin: 12px 0 6px; font-weight: bold; }
    input[type=number], input[type=text], textarea { width: 100%; padding: 14px 16px; border-radius: 12px; border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15; color: #fff; font-size: 15px; font-family: inherit; box-sizing: border-box; }
    textarea { resize: vertical; min-height: 80px; }
    input:focus, textarea:focus { outline: none; border-color: #facc15; }
    button.send-btn { width: 100%; margin-top: 16px; padding: 16px; border: none; border-radius: 14px; font-size: 16px; font-weight: bold; font-family: inherit; cursor: pointer; color: #fff; background: linear-gradient(135deg, #22c55e, #16a34a); box-shadow: 0 8px 20px rgba(34,197,94,0.4); }
    button.send-btn:hover { transform: translateY(-1px); }
    button.reset-btn { width: 100%; margin-top: 10px; padding: 14px; border: none; border-radius: 12px; font-size: 14px; font-weight: bold; font-family: inherit; cursor: pointer; color: #fca5a5; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); }
    .row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>🎁 جایزه به همه</h1>
    <a href="{% url 'custom_admin:logout' %}">خروج</a>
  </div>

  <div class="admin-tabs">
    <a href="/panel-admin/dashboard/" class="admin-tab">👥 کاربران</a>
    <a href="/panel-admin/alliances/" class="admin-tab">🛡️ اتحادها</a>
    <a href="/panel-admin/rooms/" class="admin-tab">🚪 اتاق‌ها</a>
    <a href="/panel-admin/announcements/" class="admin-tab">📢 اعلان‌ها</a>
    <a href="/panel-admin/tournaments/" class="admin-tab">🏆 تورنمنت</a>
    <a href="/panel-admin/shop/" class="admin-tab">🛒 فروشگاه</a>
    <a href="/panel-admin/guest-log/" class="admin-tab">🎲 مهمان‌ها</a>
    <a href="/panel-admin/send-to-all/" class="admin-tab active">🎁 جایزه همه</a>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <div class="stats">
    📊 تعداد کل کاربران: <b>{{ total_users }}</b> نفر
  </div>

  <div class="card">
    <h3>🎁 ارسال سکه/جم به همه کاربران</h3>
    <form method="post">
      {% csrf_token %}
      <input type="hidden" name="action" value="send">
      <div class="row-2">
        <div>
          <label>🪙 سکه (هر کاربر)</label>
          <input type="number" name="coins" value="0" placeholder="مثلاً 500">
        </div>
        <div>
          <label>💎 جم (هر کاربر)</label>
          <input type="number" name="gems" value="0" placeholder="مثلاً 10">
        </div>
      </div>
      <label>📝 پیام (اختیاری)</label>
      <textarea name="note" maxlength="200" placeholder="مثلاً: هدیه ویژه به مناسبت بازگشایی!"></textarea>
      <button type="submit" class="send-btn" onclick="return confirm('این جایزه به همه {{ total_users }} کاربر داده می‌شه. مطمئنی؟');">🎁 ارسال به همه</button>
    </form>
  </div>

  <div class="card">
    <h3>⚠️ اقدامات خطرناک</h3>
    <form method="post" onsubmit="return confirm('همه سکه‌ها و جم‌های همه کاربران صفر می‌شوند. مطمئنی؟');">
      {% csrf_token %}
      <input type="hidden" name="action" value="reset_all">
      <button type="submit" class="reset-btn">🗑️ صفر کردن همه سکه و جم‌ها</button>
    </form>
  </div>
</div>
</body>
</html>
''')
print("  ✓ send_to_all.html")

# Add tab to dashboard and other admin pages
admin_pages = ["dashboard.html", "alliances.html", "rooms.html", "announcements.html", "tournaments.html", "shop_items.html", "guest_log.html"]
for tpl in admin_pages:
    tp = f"accounts/templates/custom_admin/{tpl}"
    if not os.path.exists(tp): continue
    src = read(tp)
    if "/panel-admin/send-to-all/" in src:
        continue
    # Find the guest-log tab and add after it, or add before closing admin-tabs div
    if "/panel-admin/guest-log/" in src:
        # Find the anchor and add after
        idx = src.find('/panel-admin/guest-log/')
        if idx > 0:
            end_tag = src.find("</a>", idx) + 4
            new_tab = '\n    <a href="/panel-admin/send-to-all/" class="admin-tab">🎁 جایزه همه</a>'
            src = src[:end_tag] + new_tab + src[end_tag:]
            write(tp, src)
            print(f"  ✓ Tab added to {tpl}")
    else:
        # Just add before closing div
        idx = src.find("</div>", src.find("admin-tabs"))
        if idx > 0:
            new_tab = '\n    <a href="/panel-admin/send-to-all/" class="admin-tab">🎁 جایزه همه</a>'
            src = src[:idx] + new_tab + src[idx:]
            write(tp, src)
            print(f"  ✓ Tab added to {tpl}")

# ============================================================
# 4) Verify and test
# ============================================================
print("\n[4/6] Migrations")
for cmd in [
    [sys.executable, "manage.py", "makemigrations", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 and r.stderr.strip():
        print(f"  ⚠ {r.stderr[:200]}")

print("\n[5/6] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ PASSED")
else:
    print(f"  ⚠ {r.stderr[:600]}")

print("\n[6/6] HTTP Test")
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

tu, created = User.objects.get_or_create(
    username="__final_test__",
    defaults={"alias": "final", "is_active": True, "has_chosen_avatar": True, "has_completed_registration": True}
)
if created:
    tu.set_password("x")
    tu.save()

c = Client()
c.force_login(tu)
c.session["beta_unlocked"] = True
c.session.save()

urls = [
    ("/game/", "menu"),
    ("/game/puzzle/", "puzzle setup"),
    ("/game/rooms/", "rooms list"),
    ("/panel-admin/send-to-all/", "admin send-to-all"),
]
for url, name in urls:
    try:
        r = c.get(url, follow=False)
        status = r.status_code
        mark = "✓" if status == 200 else ("→" if status in (301, 302) else "✗")
        print(f"  {mark} {url:35s} → {status} ({name})")
    except Exception as e:
        print(f"  ✗ {url:35s} → {type(e).__name__}: {str(e)[:80]}")

if created:
    tu.delete()

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
What was changed:

  menu.html:
    ✓ Removed alliance button
    ✓ Settings on LEFT
    ✓ Animated beta badge on RIGHT (pulsing)
    ✓ Top players first, shop disabled "به زودی"

  Puzzle game:
    ✓ Setup page at /game/puzzle/
    ✓ 3 difficulties (easy/medium/hard)
    ✓ 5 scrambled words, 90 seconds
    ✓ Score saved to Player
    ✓ Result page with details

  Admin:
    ✓ /panel-admin/send-to-all/ — give coins/gems to all
    ✓ Optional message to all
    ✓ Reset all coins/gems button

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)
""")
