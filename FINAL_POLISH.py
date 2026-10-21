#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess, random as _r

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def read(p):
    try:
        with open(p, "r", encoding="utf-8") as f: return f.read()
    except: return ""
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) PUZZLE WORDS database
# ============================================================
print("\n[1/6] puzzle_words.py")
WORDS = [
    # حیوانات
    "خرگوش","گربه","پلنگ","شیر","ببر","فیل","زرافه","میمون","دلفین","مار","عقاب","شاهین","طوطی","پرستو","گنجشک","ققنوس","اسب","شتر","گوسفند","بز",
    "خرس","گرگ","روباه","آهو","گوزن","کرگدن","کرکس","جغد","بلبل","پروانه","زنبور","مورچه","عقرب","مارمولک","لاک‌پشت","قورباغه","کوسه","نهنگ","وال","فک","اختاپوس","میگو","خرچنگ","کبوتر","جیرجیرک","سوسک","خفاش","دارکوب","سنجاب","راسو","بزغاله","بره","کبک","قو","لک‌لک",
    # طبیعت
    "خورشید","ماه","ستاره","آسمان","ابر","باران","برف","رعد","آبشار","دریا","اقیانوس","رودخانه","دریاچه","جنگل","کوه","تپه","صحرا","بیابان","چشمه","چمن","گل","شاخه","ریشه","برگ","دانه","باد","طوفان","گردباد","مه","شبنم","یخ","سیل","زلزله","آتشفشان",
    # رنگ‌ها
    "قرمز","آبی","زرد","سبز","صورتی","بنفش","نارنجی","قهوه‌ای","مشکی","سفید","خاکستری","طلایی","نقره‌ای",
    # اشیا
    "کتاب","قلم","دفتر","میز","صندلی","تخت","پنجره","در","دیوار","سقف","پرده","فرش","بالش","آینه","ساعت","کلید","قفل","چراغ","لامپ","پنکه","بخاری","یخچال","تلویزیون","تلفن","رایانه","گوشی","هدفون","میکروفن",
    "چاقو","قاشق","چنگال","بشقاب","لیوان","فنجان","کتری","قوری","دیگ","ماهیتابه","سطل","جارو","تی","سبد","کیف","چمدان","کفش","جوراب","شلوار","پیراهن","کت","کلاه","دستکش","شال","روسری","عینک","ساعت‌مچی","دستبند","گردنبند","انگشتر",
    "توپ","بازی","عروسک","بادبادک","اسکیت","دوچرخه","توپ‌پا","راکت","شطرنج","تخته","مهره","کارت","تاس","پازل","معما",
    # غذاها
    "نان","برنج","مرغ","گوشت","ماهی","تخم‌مرغ","پنیر","کره","شیر","ماست","دوغ","عسل","مربا","شکر","نمک","فلفل","زردچوبه","دارچین","زعفران","چای","قهوه","آب","شربت","آبمیوه","سوپ","آش","پلو","کباب","خورش","سالاد","سیب‌زمینی","پیاز","سیر","گوجه","خیار","کاهو","هویج","کدو","بادمجان","فلفل‌دلمه",
    # میوه‌ها
    "سیب","موز","پرتقال","انگور","هلو","زردآلو","گیلاس","آلبالو","توت","تمشک","انار","انجیر","خرما","انبه","آناناس","کیوی","نارگیل","لیمو","نارنگی","طالبی","هندوانه","خربزه",
    # بدن
    "سر","چشم","گوش","بینی","دهان","لب","دندان","زبان","گردن","شانه","دست","انگشت","ناخن","سینه","قلب","شکم","پا","زانو","آرنج","مژه","ابرو","گونه","چانه","پیشانی","مو",
    # مکان‌ها
    "خانه","مدرسه","مسجد","بازار","فروشگاه","بیمارستان","پارک","خیابان","کوچه","میدان","پل","ایستگاه","فرودگاه","رستوران","کتابخانه","موزه","تئاتر","سینما","بانک","اداره","کارخانه","مزرعه","باغ","استخر","ساحل","جزیره",
    # احساسات
    "شادی","غم","خنده","گریه","عشق","نفرت","امید","ترس","خشم","آرامش","هیجان","حسادت","مهربانی","دوستی",
    # حرفه‌ها
    "پزشک","معلم","مهندس","راننده","خلبان","آشپز","نجار","بنا","خیاط","آرایشگر","نقاش","نویسنده","خواننده","بازیگر","کارگر","کشاورز","نگهبان","پلیس","سرباز","قاضی",
    # کارها
    "خواب","بیداری","راه‌رفتن","دویدن","پریدن","نشستن","بلندشدن","خوردن","نوشیدن","خواندن","نوشتن","گوش‌دادن","دیدن","فکرکردن","حرف‌زدن","خندیدن","گریه‌کردن","رقصیدن","آوازخواندن",
]
# حذف تکراری
WORDS = list(dict.fromkeys(WORDS))
print(f"  Total words: {len(WORDS)}")

write("game/puzzle_words.py", f'''# -*- coding: utf-8 -*-
"""بازی معما — کلمات ۴ تا ۸ حرفی"""

PUZZLE_WORDS = {WORDS!r}

# Filter only 4-8 char words
def get_puzzle_words():
    return [w for w in PUZZLE_WORDS if 4 <= len(w) <= 8]
''')

# ============================================================
# 2) PUZZLE VIEWS - rebuild
# ============================================================
print("\n[2/6] puzzle views rebuild")
p = "game/views.py"
src = read(p)

# Remove old puzzle views
import re
old = re.search(r'# =+\s*\n# Puzzle Game.*?(?=\n# =+\s*\n# 0-100|\n# =+\s*\n# Guess|\Z)', src, re.DOTALL)
if old:
    src = src[:old.start()] + src[old.end():]

NEW_PUZZLE = '''

# ============================================================
# Puzzle Game — arrange the scrambled word
# ============================================================
@login_required
def puzzle_home(request):
    check = _require_complete(request.user)
    if check:
        return check

    # New game request
    if request.method == "POST" and request.POST.get("action") == "new":
        _start_puzzle(request)
        return redirect("game:puzzle")

    # Start if no puzzle
    if "puzzle_items" not in request.session or request.session.get("puzzle_finished"):
        _start_puzzle(request)
        return redirect("game:puzzle")

    items = request.session.get("puzzle_items", [])
    tries = request.session.get("puzzle_guessed", {})
    total = len(items)

    # compute elapsed
    import time
    start_ts = request.session.get("puzzle_start_ts", 0)
    total_time = request.session.get("puzzle_total_time", 60)
    elapsed = int(time.time() - start_ts) if start_ts else 0
    remaining = max(0, total_time - elapsed)
    time_up = remaining <= 0

    return render(request, "game/puzzle.html", {
        "items": items,
        "total": total,
        "guessed": tries,
        "total_time": total_time,
        "remaining": remaining,
        "time_up": time_up,
        "finished": False,
        "active": "games",
    })


def _shuffle_letters(word):
    letters = list(word)
    for _ in range(20):
        _rand.shuffle(letters)
        if "".join(letters) != word:
            break
    return " ".join(letters)


def _start_puzzle(request):
    from .puzzle_words import get_puzzle_words
    pool = get_puzzle_words()
    if not pool:
        pool = ["کتاب", "درخت", "خورشید"]

    # Pick 5 random words (avoid duplicates)
    picks = _rand.sample(pool, min(5, len(pool)))

    items = []
    total_time = 0
    for i, w in enumerate(picks):
        # Time based on word length: 4-letter = 20s, 5 = 25s, ...
        seconds = len(w) * 5
        total_time += seconds
        items.append({
            "idx": i,
            "word": w,  # not sent to template directly
            "scrambled": _shuffle_letters(w),
            "length": len(w),
            "seconds": seconds,
        })

    import time
    request.session["puzzle_items"] = items
    request.session["puzzle_guessed"] = {}
    request.session["puzzle_start_ts"] = int(time.time())
    request.session["puzzle_total_time"] = total_time
    request.session["puzzle_finished"] = False
    request.session["puzzle_score"] = 0


@login_required
def puzzle_submit(request):
    check = _require_complete(request.user)
    if check:
        return check

    if request.method != "POST":
        return redirect("game:puzzle")

    if request.POST.get("action") == "new":
        _start_puzzle(request)
        return redirect("game:puzzle")

    items = request.session.get("puzzle_items", [])
    if not items:
        return redirect("game:puzzle")

    # Read all answers
    guessed = {}
    correct_count = 0
    for it in items:
        ans = (request.POST.get(f"ans_{it['idx']}") or "").strip()
        ans = ans.replace("ي", "ی").replace("ك", "ک").replace(" ", "").replace("\\u200c", "")
        target = it["word"].replace("ي", "ی").replace("ك", "ک").replace(" ", "").replace("\\u200c", "")
        is_correct = (ans == target)
        if is_correct:
            correct_count += 1
        guessed[it["idx"]] = {
            "answer": ans,
            "correct": is_correct,
        }

    request.session["puzzle_guessed"] = guessed
    request.session["puzzle_finished"] = True
    request.session["puzzle_score"] = correct_count * 10

    messages.success(request, f"🎯 {correct_count} از {len(items)} کلمه درست!")
    return redirect("game:puzzle")


@login_required
def puzzle_status(request):
    """Return JSON with remaining time."""
    from django.http import JsonResponse
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth"})
    import time
    start_ts = request.session.get("puzzle_start_ts", 0)
    total_time = request.session.get("puzzle_total_time", 60)
    if not start_ts:
        return JsonResponse({"remaining": total_time, "time_up": False})
    elapsed = int(time.time() - start_ts)
    remaining = max(0, total_time - elapsed)
    return JsonResponse({"remaining": remaining, "time_up": remaining <= 0})


# ============================================================
# Memory Game — match emoji pairs
# ============================================================
_MEMORY_EMOJIS = ["🐶","🐱","🦁","🐯","🐻","🐼","🐨","🐸","🦊","🐵","🦄","🐲"]

@login_required
def memory_home(request):
    check = _require_complete(request.user)
    if check:
        return check

    if request.method == "POST" and request.POST.get("action") == "new":
        _start_memory(request)
        return redirect("game:memory")

    if "memory_cards" not in request.session or request.session.get("memory_finished"):
        _start_memory(request)
        return redirect("game:memory")

    cards = request.session.get("memory_cards", [])
    return render(request, "game/memory.html", {
        "cards": cards,
        "total_pairs": len(cards) // 2,
        "active": "games",
    })


def _start_memory(request):
    import time
    # 4x4 = 16 cards = 8 pairs
    pair_count = 8
    emojis = _rand.sample(_MEMORY_EMOJIS, min(pair_count, len(_MEMORY_EMOJIS)))
    # duplicate
    cards_raw = emojis * 2
    _rand.shuffle(cards_raw)
    cards = []
    for i, em in enumerate(cards_raw):
        cards.append({
            "id": i,
            "emoji": em,
            "flipped": False,
            "matched": False,
        })
    request.session["memory_cards"] = cards
    request.session["memory_flipped"] = []
    request.session["memory_matched"] = 0
    request.session["memory_moves"] = 0
    request.session["memory_start_ts"] = int(time.time())
    request.session["memory_finished"] = False


@login_required
def memory_status(request):
    """AJAX endpoint to check game state."""
    from django.http import JsonResponse
    import time
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth"})
    cards = request.session.get("memory_cards", [])
    matched = request.session.get("memory_matched", 0)
    moves = request.session.get("memory_moves", 0)
    start = request.session.get("memory_start_ts", 0)
    elapsed = int(time.time() - start) if start else 0
    total_pairs = len(cards) // 2
    finished = matched >= total_pairs
    if finished:
        request.session["memory_finished"] = True
    return JsonResponse({
        "matched": matched,
        "total_pairs": total_pairs,
        "moves": moves,
        "elapsed": elapsed,
        "finished": finished,
    })
'''

src = src.rstrip() + "\n\n" + NEW_PUZZLE + "\n"
write(p, src)
print("  ✓ puzzle + memory views added")

# ============================================================
# 3) URLs
# ============================================================
print("\n[3/6] game/urls.py")
p = "game/urls.py"
src = read(p)

# Remove old puzzle routes
src = re.sub(r'\s*path\("puzzle/[^"]*"[^\n]*\n', '\n', src)

# Add new routes
if 'path("puzzle/", views.puzzle_home' not in src:
    anchor = '    path("challenge/", views.challenge_home, name="challenge"),'
    new_routes = '''
    path("puzzle/", views.puzzle_home, name="puzzle"),
    path("puzzle/submit/", views.puzzle_submit, name="puzzle_submit"),
    path("puzzle/status/", views.puzzle_status, name="puzzle_status"),
    path("memory/", views.memory_home, name="memory"),
    path("memory/status/", views.memory_status, name="memory_status"),'''
    if anchor in src:
        src = src.replace(anchor, anchor + new_routes, 1)
        write(p, src)
        print("  ✓ puzzle + memory routes added")
    else:
        print("  ⚠ challenge route not found — adding at end")
        src = src.rsplit("]", 1)[0] + new_routes + "\n]"
        write(p, src)

# ============================================================
# 4) Puzzle template
# ============================================================
print("\n[4/6] puzzle.html")
write("game/templates/game/puzzle.html", '''{% extends "base.html" %}
{% block title %}بازی معما{% endblock %}
{% block extra_css %}
<style>
  .head { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; justify-content: space-between; }
  .head-left { display: flex; align-items: center; gap: 12px; }
  .head h1 { font-size: 22px; font-weight: 900; background: linear-gradient(135deg, #4ade80, #16a34a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .timer-badge {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: #fff;
    padding: 8px 18px;
    border-radius: 999px;
    font-size: 16px;
    font-weight: 900;
    font-family: monospace;
    box-shadow: 0 8px 25px rgba(239,68,68,0.4);
  }
  .timer-badge.safe {
    background: linear-gradient(135deg, #22c55e, #16a34a);
    box-shadow: 0 8px 25px rgba(34,197,94,0.4);
  }
  .timer-badge.warn {
    background: linear-gradient(135deg, #eab308, #ca8a04);
    box-shadow: 0 8px 25px rgba(234,179,8,0.4);
    animation: pulse 1s infinite;
  }
  @keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.05); } }

  .intro {
    background: radial-gradient(circle at 100% 0%, rgba(34,197,94,0.25), transparent 60%),
                linear-gradient(135deg, #0a2a1a, #0f0f1e);
    border: 2px solid rgba(34,197,94,0.5);
    border-radius: 20px;
    padding: 18px 20px;
    margin-bottom: 18px;
    text-align: center;
  }
  .intro h2 { font-size: 17px; color: #bbf7d0; margin-bottom: 4px; font-weight: 900; }
  .intro p { font-size: 12px; color: #94a3b8; line-height: 1.6; }

  .word-item {
    background: var(--card);
    border: 1.5px solid rgba(34,197,94,0.3);
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 12px;
    transition: 0.2s;
    position: relative;
    overflow: hidden;
  }
  .word-item.correct { border-color: rgba(34,197,94,0.7); background: rgba(34,197,94,0.08); }
  .word-item.wrong { border-color: rgba(239,68,68,0.7); background: rgba(239,68,68,0.08); }
  .word-item.finished { cursor: not-allowed; }
  
  .word-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
  }
  .word-num {
    font-size: 11px;
    color: #94a3b8;
    font-weight: 900;
    font-family: monospace;
  }
  .word-sec {
    font-size: 10px;
    color: #4ade80;
    padding: 2px 8px;
    background: rgba(34,197,94,0.15);
    border-radius: 6px;
    font-family: monospace;
    font-weight: 900;
  }
  
  .scrambled {
    display: flex;
    gap: 6px;
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 12px;
  }
  .letter-tile {
    width: 42px;
    height: 42px;
    border-radius: 10px;
    background: linear-gradient(135deg, rgba(34,197,94,0.25), rgba(6,182,212,0.15));
    border: 1.5px solid rgba(34,197,94,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    font-weight: 900;
    color: #bbf7d0;
    box-shadow: 0 4px 12px rgba(34,197,94,0.2);
    font-family: Tahoma, sans-serif;
  }
  
  .answer-input {
    width: 100%;
    padding: 14px 16px;
    border-radius: 12px;
    border: 2px solid rgba(34,197,94,0.4);
    background: rgba(15,23,42,0.8);
    color: #fff;
    font-size: 20px;
    font-family: inherit;
    text-align: center;
    font-weight: 900;
    letter-spacing: 4px;
    box-sizing: border-box;
  }
  .answer-input:focus {
    outline: none;
    border-color: #4ade80;
    box-shadow: 0 0 20px rgba(34,197,94,0.3);
  }
  .answer-input:disabled { opacity: 0.6; }
  
  .result-msg {
    margin-top: 8px;
    font-size: 12px;
    text-align: center;
    font-weight: 900;
  }
  .result-msg.correct { color: #4ade80; }
  .result-msg.wrong { color: #f87171; }

  .btn-submit {
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 14px;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: #fff;
    font-size: 17px;
    font-weight: 900;
    font-family: inherit;
    cursor: pointer;
    box-shadow: 0 10px 30px rgba(34,197,94,0.4);
    margin-top: 12px;
    transition: 0.2s;
  }
  .btn-submit:hover { transform: translateY(-2px); }

  .btn-new {
    display: block;
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 14px;
    background: linear-gradient(135deg, #f4c542, #eab308);
    color: #1a1a1a;
    font-size: 16px;
    font-weight: 900;
    font-family: inherit;
    cursor: pointer;
    text-decoration: none;
    text-align: center;
    box-shadow: 0 10px 30px rgba(244,197,66,0.4);
    margin-top: 12px;
  }

  .finished-panel {
    text-align: center;
    padding: 30px 20px;
    border-radius: 22px;
    background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.25), transparent 60%),
                linear-gradient(135deg, #2a1a0e, #0f0f1e);
    border: 2px solid rgba(244,197,66,0.5);
    margin-bottom: 16px;
  }
  .finished-panel .big-icon { font-size: 70px; margin-bottom: 12px; }
  .finished-panel h2 {
    font-size: 22px; font-weight: 900;
    background: linear-gradient(135deg, #fde68a, #f4c542);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 10px;
  }
  .finished-panel .score-line {
    font-size: 15px; color: #fff; font-family: monospace; margin-bottom: 14px;
  }
  .finished-panel .score-line b { color: #fde68a; }
</style>
{% endblock %}
{% block content %}

  <div class="head">
    <div class="head-left">
      <a href="/game/rooms/" class="back-btn"><span class="arrow-icon">→</span></a>
      <h1>🎯 بازی معما</h1>
    </div>
    {% if not finished %}
      <div class="timer-badge {% if remaining > total_time / 2 %}safe{% elif remaining > 15 %}warn{% endif %}" id="timerBadge">
        ⏱ <span id="timerNum">{{ remaining }}</span>ث
      </div>
    {% endif %}
  </div>

  {% if finished %}
    <div class="finished-panel">
      <div class="big-icon">🏆</div>
      <h2>نتیجه بازی</h2>
      <div class="score-line">
        امتیاز: <b>{{ score|default:0 }}</b> از {{ total|default:0 }}
      </div>
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
        <div class="word-item" data-idx="{{ it.idx }}">
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
<script>
  {% if not finished %}
  let remaining = {{ remaining }};
  let total = {{ total_time }};
  const timerEl = document.getElementById('timerNum');
  const badge = document.getElementById('timerBadge');

  function updateTimer() {
    if (remaining <= 0) return;
    remaining--;
    if (timerEl) timerEl.textContent = remaining;
    if (badge) {
      badge.classList.remove('safe', 'warn');
      if (remaining > total / 2) badge.classList.add('safe');
      else if (remaining > 15) badge.classList.add('warn');
    }
    if (remaining <= 0) {
      document.getElementById('puzzleForm').submit();
    } else {
      setTimeout(updateTimer, 1000);
    }
  }
  setTimeout(updateTimer, 1000);
  {% endif %}
</script>
{% endblock %}
''')

# ============================================================
# 5) Memory template
# ============================================================
print("\n[5/6] memory.html")
write("game/templates/game/memory.html", '''{% extends "base.html" %}
{% block title %}بازی حافظه{% endblock %}
{% block extra_css %}
<style>
  .head { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; justify-content: space-between; }
  .head-left { display: flex; align-items: center; gap: 12px; }
  .head h1 { font-size: 22px; font-weight: 900; background: linear-gradient(135deg, #a78bfa, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }

  .stats-bar {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
  }
  .stat-chip {
    flex: 1;
    background: linear-gradient(135deg, rgba(139,92,246,0.15), rgba(6,182,212,0.1));
    border: 1.5px solid rgba(139,92,246,0.4);
    border-radius: 12px;
    padding: 10px;
    text-align: center;
  }
  .stat-chip .lbl { font-size: 10px; color: #94a3b8; margin-bottom: 2px; }
  .stat-chip .val { font-size: 16px; font-weight: 900; color: #c4b5fd; font-family: monospace; }

  .intro {
    background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.25), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #0f0f1e);
    border: 2px solid rgba(139,92,246,0.5);
    border-radius: 20px;
    padding: 16px 20px;
    margin-bottom: 18px;
    text-align: center;
  }
  .intro h2 { font-size: 16px; color: #e9d5ff; margin-bottom: 4px; font-weight: 900; }
  .intro p { font-size: 12px; color: #94a3b8; line-height: 1.6; }

  .grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-bottom: 20px;
  }

  .card {
    aspect-ratio: 1;
    position: relative;
    perspective: 600px;
    cursor: pointer;
  }
  .card-inner {
    position: relative;
    width: 100%;
    height: 100%;
    transition: transform 0.5s;
    transform-style: preserve-3d;
  }
  .card.flipped .card-inner,
  .card.matched .card-inner {
    transform: rotateY(180deg);
  }
  .card-face {
    position: absolute;
    inset: 0;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
  }
  .card-back {
    background: linear-gradient(135deg, rgba(139,92,246,0.4), rgba(6,182,212,0.3));
    border: 2px solid rgba(139,92,246,0.6);
    font-size: 32px;
    color: rgba(255,255,255,0.3);
    box-shadow: 0 4px 12px rgba(139,92,246,0.3);
    transition: all 0.2s;
  }
  .card:hover .card-back {
    border-color: rgba(167,139,250,0.95);
    box-shadow: 0 8px 20px rgba(139,92,246,0.5);
    transform: scale(1.04);
  }
  .card-front {
    background: linear-gradient(135deg, rgba(244,197,66,0.35), rgba(139,92,246,0.25));
    border: 2px solid rgba(244,197,66,0.6);
    font-size: 36px;
    transform: rotateY(180deg);
    box-shadow: 0 4px 15px rgba(244,197,66,0.4);
  }
  .card.matched .card-front {
    background: linear-gradient(135deg, rgba(34,197,94,0.35), rgba(6,182,212,0.25));
    border-color: rgba(34,197,94,0.7);
    box-shadow: 0 0 20px rgba(34,197,94,0.6);
    animation: matchGlow 0.5s;
  }
  @keyframes matchGlow {
    0% { transform: rotateY(180deg) scale(1); }
    50% { transform: rotateY(180deg) scale(1.15); }
    100% { transform: rotateY(180deg) scale(1); }
  }

  .btn-new {
    display: block;
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 14px;
    background: linear-gradient(135deg, #f4c542, #eab308);
    color: #1a1a1a;
    font-size: 16px;
    font-weight: 900;
    font-family: inherit;
    cursor: pointer;
    text-decoration: none;
    text-align: center;
    box-shadow: 0 10px 30px rgba(244,197,66,0.4);
    margin-top: 8px;
  }

  .win-panel {
    text-align: center;
    padding: 30px 20px;
    border-radius: 22px;
    background: radial-gradient(circle at 100% 0%, rgba(34,197,94,0.25), transparent 60%),
                linear-gradient(135deg, #0a2a1a, #0f0f1e);
    border: 2px solid rgba(34,197,94,0.5);
    margin-bottom: 16px;
    display: none;
  }
  .win-panel.show { display: block; animation: popIn 0.5s; }
  @keyframes popIn { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
  .win-panel .big-icon { font-size: 70px; margin-bottom: 12px; }
  .win-panel h2 {
    font-size: 24px; font-weight: 900;
    background: linear-gradient(135deg, #4ade80, #16a34a);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 10px;
  }
  .win-panel .stats {
    display: flex; gap: 10px; justify-content: center; margin-bottom: 16px;
  }
  .win-panel .stats > div {
    padding: 10px 16px;
    background: rgba(15,23,42,0.6);
    border-radius: 12px;
    border: 1px solid rgba(34,197,94,0.3);
  }
  .win-panel .stats .l { font-size: 10px; color: #94a3b8; margin-bottom: 2px; }
  .win-panel .stats .v { font-size: 18px; font-weight: 900; color: #4ade80; font-family: monospace; }
</style>
{% endblock %}
{% block content %}

  <div class="head">
    <div class="head-left">
      <a href="/game/rooms/" class="back-btn"><span class="arrow-icon">→</span></a>
      <h1>🧠 بازی حافظه</h1>
    </div>
  </div>

  <div class="stats-bar">
    <div class="stat-chip">
      <div class="lbl">جفت پیداشده</div>
      <div class="val" id="matchedCount">0 / {{ total_pairs }}</div>
    </div>
    <div class="stat-chip">
      <div class="lbl">حرکت</div>
      <div class="val" id="movesCount">0</div>
    </div>
    <div class="stat-chip">
      <div class="lbl">زمان</div>
      <div class="val" id="timeCount">0:00</div>
    </div>
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

  <div class="win-panel" id="winPanel">
    <div class="big-icon">🎉</div>
    <h2>آفرین! بردی</h2>
    <div class="stats">
      <div><div class="l">حرکت</div><div class="v" id="winMoves">0</div></div>
      <div><div class="l">زمان</div><div class="v" id="winTime">0:00</div></div>
    </div>
    <form method="post">
      {% csrf_token %}
      <input type="hidden" name="action" value="new">
      <button type="submit" class="btn-new">🔄 بازی جدید</button>
    </form>
  </div>

{% endblock %}
{% block extra_js %}
<script>
  let firstCard = null;
  let secondCard = null;
  let lock = false;
  let matched = 0;
  let moves = 0;
  let totalPairs = {{ total_pairs }};
  let startTime = Date.now();

  function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m + ":" + String(s).padStart(2, "0");
  }

  function updateTime() {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    document.getElementById('timeCount').textContent = formatTime(elapsed);
  }
  setInterval(updateTime, 1000);

  function flipCard(card) {
    if (lock || card.classList.contains('flipped') || card.classList.contains('matched')) return;

    card.classList.add('flipped');

    if (!firstCard) {
      firstCard = card;
      return;
    }

    secondCard = card;
    lock = true;
    moves++;
    document.getElementById('movesCount').textContent = moves;

    const em1 = firstCard.dataset.emoji;
    const em2 = secondCard.dataset.emoji;

    if (em1 === em2) {
      setTimeout(() => {
        firstCard.classList.add('matched');
        secondCard.classList.add('matched');
        matched++;
        document.getElementById('matchedCount').textContent = matched + " / " + totalPairs;
        reset();
        if (matched >= totalPairs) {
          win();
        }
      }, 500);
    } else {
      setTimeout(() => {
        firstCard.classList.remove('flipped');
        secondCard.classList.remove('flipped');
        reset();
      }, 800);
    }
  }

  function reset() {
    firstCard = null;
    secondCard = null;
    lock = false;
  }

  function win() {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    document.getElementById('winMoves').textContent = moves;
    document.getElementById('winTime').textContent = formatTime(elapsed);
    document.getElementById('winPanel').classList.add('show');
  }
</script>
{% endblock %}
''')

# ============================================================
# 6) Home page rebuild — dots bg + circles + oval profile + support bottom
# ============================================================
print("\n[6/6] Home page rebuild")
write("game/templates/game/menu.html", '''{% extends "base.html" %}
{% block title %}خانه{% endblock %}

{% block extra_css %}
<style>
  /* ============ ANIMATED DOTS BACKGROUND ============ */
  .bg-pattern {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: 0;
    pointer-events: none;
    overflow: hidden;
    opacity: 0.4;
  }
  .bg-pattern::before,
  .bg-pattern::after {
    content: "";
    position: absolute;
    inset: -50%;
    background-image:
      radial-gradient(circle, rgba(244,197,66,0.35) 1px, transparent 1.5px),
      radial-gradient(circle, rgba(139,92,246,0.3) 1px, transparent 1.5px);
    background-size: 60px 60px, 90px 90px;
    background-position: 0 0, 30px 30px;
    animation: dotsFloat 30s linear infinite;
  }
  .bg-pattern::after {
    animation-duration: 45s;
    animation-direction: reverse;
    opacity: 0.5;
  }
  @keyframes dotsFloat {
    from { transform: translate(0, 0); }
    to { transform: translate(60px, 90px); }
  }
  
  /* Flying particles */
  .fly-dot {
    position: fixed;
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: #f4c542;
    box-shadow: 0 0 8px #f4c542;
    opacity: 0.6;
    z-index: 0;
    pointer-events: none;
    animation: flyUp linear infinite;
  }
  @keyframes flyUp {
    from { transform: translateY(100vh) scale(0.3); opacity: 0; }
    20% { opacity: 0.7; }
    80% { opacity: 0.5; }
    to { transform: translateY(-50px) scale(1); opacity: 0; }
  }

  /* ============ TOP CIRCLES (right) ============ */
  .top-circles {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-bottom: 14px;
    position: relative;
    z-index: 2;
  }
  .circle-btn {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1px;
    text-decoration: none;
    color: #fff;
    border: 2px solid;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    font-family: inherit;
    flex-shrink: 0;
  }
  .circle-btn:hover { transform: translateY(-3px) scale(1.08); }
  .circle-btn:active { transform: scale(0.95); }
  
  .circle-top {
    background: radial-gradient(circle at 30% 30%, rgba(244,197,66,0.4), rgba(234,179,8,0.15));
    border-color: rgba(244,197,66,0.7);
    box-shadow: 0 0 20px rgba(244,197,66,0.35);
  }
  .circle-top:hover { box-shadow: 0 0 35px rgba(244,197,66,0.8); border-color: #fde68a; }
  .circle-top .ci { font-size: 26px; filter: drop-shadow(0 0 8px rgba(244,197,66,0.9)); }
  .circle-top .cl { font-size: 9px; font-weight: 900; color: #fde68a; }
  
  .circle-challenge {
    background: radial-gradient(circle at 30% 30%, rgba(239,68,68,0.4), rgba(249,115,22,0.15));
    border-color: rgba(239,68,68,0.7);
    box-shadow: 0 0 20px rgba(239,68,68,0.35);
  }
  .circle-challenge:hover { box-shadow: 0 0 35px rgba(239,68,68,0.8); border-color: #fca5a5; }
  .circle-challenge .ci { font-size: 26px; filter: drop-shadow(0 0 8px rgba(239,68,68,0.9)); }
  .circle-challenge .cl { font-size: 9px; font-weight: 900; color: #fca5a5; }

  /* ============ PROFILE OVAL (circle → oval on click) ============ */
  .profile-oval {
    display: flex;
    align-items: center;
    gap: 0;
    padding: 6px;
    margin: 0 auto 18px;
    width: 68px;
    height: 68px;
    border-radius: 50%;
    background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.35), transparent 60%),
                radial-gradient(circle at 0% 100%, rgba(139,92,246,0.25), transparent 60%),
                linear-gradient(135deg, var(--card), #0f0f1e);
    border: 2.5px solid rgba(244,197,66,0.6);
    cursor: pointer;
    transition: all 0.45s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    position: relative;
    z-index: 2;
    box-shadow: 0 0 25px rgba(244,197,66,0.3);
  }
  .profile-oval:hover {
    border-color: #fde68a;
    box-shadow: 0 0 40px rgba(244,197,66,0.6);
  }
  .profile-oval.expanded {
    width: 100%;
    height: 96px;
    border-radius: 48px;
    padding: 14px 18px;
    gap: 14px;
    box-shadow: 0 15px 45px rgba(244,197,66,0.4);
  }
  
  .po-av {
    width: 52px; height: 52px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2a2a4a, #1a1a2e);
    display: flex; align-items: center; justify-content: center;
    font-size: 26px;
    border: 2px solid #f4c542;
    box-shadow: 0 0 15px rgba(244,197,66,0.5);
    overflow: hidden;
    background-size: cover;
    background-position: center;
    flex-shrink: 0;
    transition: all 0.4s;
  }
  .profile-oval.expanded .po-av {
    width: 64px;
    height: 64px;
    font-size: 32px;
    box-shadow: 0 0 25px rgba(244,197,66,0.8);
  }
  
  .po-details {
    flex: 1;
    min-width: 0;
    max-width: 0;
    opacity: 0;
    overflow: hidden;
    transition: all 0.4s;
    text-align: right;
    white-space: nowrap;
  }
  .profile-oval.expanded .po-details {
    max-width: 500px;
    opacity: 1;
  }
  .po-name {
    font-size: 18px;
    font-weight: 900;
    color: #fde68a;
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .po-meta {
    display: flex;
    gap: 8px;
    align-items: center;
    font-size: 12px;
    color: #94a3b8;
    flex-wrap: wrap;
  }
  .po-meta .badge {
    background: linear-gradient(135deg, #8b5cf6, #6b4eff);
    color: #fff;
    padding: 2px 8px;
    border-radius: 8px;
    font-family: monospace;
    font-weight: 900;
    font-size: 10px;
  }
  
  .po-chevron {
    color: var(--gold);
    font-size: 16px;
    transition: transform 0.4s;
    flex-shrink: 0;
  }
  .profile-oval.expanded .po-chevron {
    transform: rotate(180deg);
  }

  /* ============ SQUARE TILES ============ */
  .section-label {
    font-size: 11px;
    color: var(--muted);
    font-weight: 900;
    letter-spacing: 2px;
    margin: 18px 4px 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    text-transform: uppercase;
    position: relative;
    z-index: 2;
  }
  .section-label::after {
    content: "";
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(148,163,184,0.2), transparent);
  }
  
  .sq-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 16px;
    position: relative;
    z-index: 2;
  }
  .sq-tile {
    aspect-ratio: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 12px 8px;
    border-radius: 20px;
    text-decoration: none;
    color: #fff;
    position: relative;
    overflow: hidden;
    border: 2px solid;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    font-family: inherit;
    background: transparent;
  }
  .sq-tile:hover { transform: translateY(-4px) scale(1.04); }
  .sq-tile:active { transform: scale(0.97); }
  
  /* Shine sweep */
  .sq-tile::after {
    content: "";
    position: absolute;
    top: 0; left: -100%;
    width: 60%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
    transform: skewX(-20deg);
    animation: shine 4s infinite;
    z-index: 2;
    pointer-events: none;
  }
  @keyframes shine {
    0% { left: -100%; }
    50%,100% { left: 200%; }
  }
  
  .sq-icon {
    font-size: 40px;
    line-height: 1;
    filter: drop-shadow(0 4px 12px rgba(0,0,0,0.5));
    transition: transform 0.3s;
    animation: float 3s ease-in-out infinite;
  }
  .sq-tile:nth-child(1) .sq-icon { animation-delay: 0s; }
  .sq-tile:nth-child(2) .sq-icon { animation-delay: 0.4s; }
  .sq-tile:nth-child(3) .sq-icon { animation-delay: 0.8s; }
  @keyframes float {
    0%,100% { transform: translateY(0); }
    50% { transform: translateY(-4px); }
  }
  .sq-tile:hover .sq-icon { transform: scale(1.2) rotate(-8deg); animation: none; }
  .sq-title { font-size: 12px; font-weight: 900; letter-spacing: 0.2px; }
  .sq-sub { font-size: 9px; opacity: 0.75; }
  
  .sq-notif {
    background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.4), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #0f0f1e);
    border-color: rgba(139,92,246,0.6);
    box-shadow: 0 10px 30px rgba(139,92,246,0.2);
  }
  .sq-notif:hover { border-color: rgba(167,139,250,0.95); box-shadow: 0 18px 45px rgba(139,92,246,0.45); }
  .sq-notif .sq-title { color: #c4b5fd; }
  
  .sq-games {
    background: radial-gradient(circle at 100% 0%, rgba(236,72,153,0.4), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #120824);
    border-color: rgba(236,72,153,0.6);
    box-shadow: 0 10px 30px rgba(236,72,153,0.2);
  }
  .sq-games:hover { border-color: rgba(236,72,153,0.95); box-shadow: 0 18px 45px rgba(236,72,153,0.45); }
  .sq-games .sq-title { color: #f9a8d4; }
  
  .sq-shop {
    background: radial-gradient(circle at 100% 0%, rgba(100,116,139,0.3), transparent 60%),
                linear-gradient(135deg, #1a1a2e, #0f0f1e);
    border-color: rgba(100,116,139,0.4);
    opacity: 0.65;
    cursor: not-allowed;
  }
  .sq-shop:hover { transform: none; box-shadow: none; }
  .sq-shop .sq-title { color: #cbd5e1; }
  .sq-shop::after { animation: none; }
  .sq-badge {
    position: absolute;
    top: 8px; right: 8px;
    background: #ef4444; color: #fff;
    font-size: 10px; font-weight: 900;
    padding: 2px 8px;
    border-radius: 999px;
    box-shadow: 0 3px 10px rgba(239,68,68,0.6);
    animation: pulseBadge 2s infinite;
    z-index: 3;
  }
  @keyframes pulseBadge { 0%,100% { transform: scale(1); } 50% { transform: scale(1.18); } }

  /* ============ BOTTOM SUPPORT ============ */
  .bottom-sq {
    position: relative;
    z-index: 2;
    display: block;
    width: 100%;
    padding: 18px;
    background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.4), transparent 60%),
                linear-gradient(135deg, #0a1e2a, #0f0f1e);
    border: 2px solid rgba(6,182,212,0.6);
    border-radius: 20px;
    text-decoration: none;
    color: #fff;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 10px 30px rgba(6,182,212,0.2);
    font-family: inherit;
    margin-top: 8px;
    overflow: hidden;
  }
  .bottom-sq::after {
    content: "";
    position: absolute;
    top: 0; left: -100%;
    width: 60%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
    transform: skewX(-20deg);
    animation: shine 5s infinite;
    pointer-events: none;
  }
  .bottom-sq:hover { transform: translateY(-3px); box-shadow: 0 18px 45px rgba(6,182,212,0.45); border-color: rgba(34,211,238,0.95); }
  .bottom-sq-inner {
    display: flex;
    align-items: center;
    gap: 14px;
    position: relative;
    z-index: 2;
  }
  .bottom-sq .b-icon { font-size: 36px; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.5)); }
  .bottom-sq .b-body { flex: 1; text-align: right; }
  .bottom-sq .b-title { font-size: 16px; font-weight: 900; color: #a5f3fc; margin-bottom: 3px; }
  .bottom-sq .b-sub { font-size: 11px; color: #94a3b8; }
  .bottom-sq .b-arrow { font-size: 20px; color: #67e8f9; }

  /* ============ GUEST WARNING ============ */
  .guest-warning {
    background: linear-gradient(135deg, rgba(234,179,8,0.15), rgba(249,115,22,0.08));
    border: 1.5px solid rgba(234,179,8,0.35);
    border-radius: 14px;
    padding: 12px 14px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 12px;
    position: relative;
    z-index: 2;
  }
  .guest-warning .gw-icon { font-size: 26px; flex-shrink: 0; }
  .guest-warning .gw-body { flex: 1; }
  .guest-warning .gw-title { font-size: 12px; font-weight: 900; color: #fde68a; margin-bottom: 2px; }
  .guest-warning .gw-desc { font-size: 10px; color: #fbbf24; line-height: 1.5; }
  .guest-warning .gw-logout {
    background: rgba(239,68,68,0.2);
    color: #fca5a5;
    border: 1px solid rgba(239,68,68,0.4);
    padding: 7px 12px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 900;
    text-decoration: none;
  }
</style>
{% endblock %}

{% block content %}

  <!-- animated background -->
  <div class="bg-pattern"></div>
  
  <!-- flying particles -->
  <div class="fly-dot" style="left: 10%; animation-duration: 12s; animation-delay: 0s;"></div>
  <div class="fly-dot" style="left: 25%; animation-duration: 15s; animation-delay: 2s; background: #8b5cf6; box-shadow: 0 0 8px #8b5cf6;"></div>
  <div class="fly-dot" style="left: 45%; animation-duration: 18s; animation-delay: 4s;"></div>
  <div class="fly-dot" style="left: 60%; animation-duration: 14s; animation-delay: 1s; background: #06b6d4; box-shadow: 0 0 8px #06b6d4;"></div>
  <div class="fly-dot" style="left: 78%; animation-duration: 16s; animation-delay: 3s;"></div>
  <div class="fly-dot" style="left: 92%; animation-duration: 13s; animation-delay: 5s; background: #8b5cf6; box-shadow: 0 0 8px #8b5cf6;"></div>

  <!-- Top circles (right) -->
  <div class="top-circles">
    <a href="/game/top-players/" class="circle-btn circle-top" title="بازیکنان برتر">
      <div class="ci">⭐</div>
      <div class="cl">برتر</div>
    </a>
    <a href="/game/challenge/" class="circle-btn circle-challenge" title="چالش">
      <div class="ci">🏆</div>
      <div class="cl">چالش</div>
    </a>
  </div>

  <!-- Profile (circle → oval) -->
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
        <span>🎮 {{ stats.total_games|default:0 }}</span>
      </div>
    </div>
    <div class="po-chevron">▼</div>
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

  <!-- 3 middle squares -->
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

    <div class="sq-tile sq-shop">
      <div class="sq-icon">🛒</div>
      <div class="sq-title">فروشگاه</div>
      <div class="sq-sub">به زودی</div>
    </div>
  </div>

  <!-- Support button (bottom square) -->
  <div class="section-label">💬 ارتباط با ما</div>

  <button class="bottom-sq" onclick="openSupport()">
    <div class="bottom-sq-inner">
      <div class="b-icon">💬</div>
      <div class="b-body">
        <div class="b-title">پشتیبانی</div>
        <div class="b-sub">سوال داری؟ با ما در تماس باش</div>
      </div>
      <div class="b-arrow">←</div>
    </div>
  </button>

{% endblock %}

{% block extra_js %}
<script>
  function toggleProfile() {
    const oval = document.getElementById('profileOval');
    oval.classList.toggle('expanded');
    if (window.vibrate) window.vibrate(8);
    if (window.soundClick) window.soundClick();
  }
  
  function openSupport() {
    alert('📬 پشتیبانی:\\n\\n📧 support@esmfamil.com\\n💬 @esmfamil_support');
    if (window.soundClick) window.soundClick();
  }
</script>
{% endblock %}
''')

# ============================================================
# Update rooms.html to remove challenge
# ============================================================
print("\n[6b/6] rooms.html — remove challenge")
p = "game/templates/game/rooms.html"
src = read(p)

# Remove challenge block
pattern = re.compile(
    r'<a href="/game/challenge/"[^>]*class="big challenge"[^>]*>.*?</a>',
    re.DOTALL
)
src = pattern.sub('', src)

# Add puzzle and memory if not there
if '/game/puzzle/' not in src:
    insert = '''
  <a href="/game/puzzle/" class="big puzzle">
    <div class="badge-new">🆕 جدید</div>
    <div class="bic">🎯</div>
    <div class="bbody">
      <div class="btitle">بازی معما</div>
      <div class="bdesc">حروف رو مرتب کن، کلمه رو بساز</div>
      <div class="btags">
        <span class="btag">🧩 ۵ کلمه</span>
        <span class="btag">⏱ زمان محدود</span>
      </div>
    </div>
    <div class="barrow">←</div>
  </a>
  
  <a href="/game/memory/" class="big memory" style="background: linear-gradient(135deg, #1a0f2e, #0f0f1e); border-color: rgba(167,139,250,0.6); box-shadow: 0 15px 40px rgba(139,92,246,0.25);">
    <div class="badge-new">🆕 جدید</div>
    <div class="bic">🧠</div>
    <div class="bbody">
      <div class="btitle" style="color: #c4b5fd;">بازی حافظه</div>
      <div class="bdesc">کارت‌ها رو بچرخون، جفت‌ها رو پیدا کن</div>
      <div class="btags">
        <span class="btag">🧠 ۸ جفت</span>
        <span class="btag">🎯 سرعت + حافظه</span>
      </div>
    </div>
    <div class="barrow">←</div>
  </a>
'''
    # Find last </a> and insert before section end
    last_a = src.rfind("</a>")
    if last_a > 0:
        # Find the closing of that <a> element
        end_pos = last_a + 4
        src = src[:end_pos] + insert + src[end_pos:]

write(p, src)
print("  ✓ challenge removed, puzzle + memory added")

# ============================================================
# Final check
# ============================================================
print("\n[check] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ PASSED")
else:
    print(f"  ⚠ {r.stderr[:500]}")

r = subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Migrate OK")

print("\n" + "="*60)
print("✅ همه چیز آماده")
print("="*60)
print("""
چه چیزایی:

  🏠 خانه:
     ✓ پس‌زمینه نقطه‌ای متحرک (بدون خط چرخشی)
     ✓ ذرات طلایی/بنفش شناور
     ✓ ۲ دایره بالا-راست: ⭐ برتر + 🏆 چالش
     ✓ پروفایل: دایره → کلیک → بیضی می‌شه (با Lv + سکه + جم + بازی)
     ✓ ۳ مربع: 🔔 اعلان‌ها + 🎮 بازی‌ها + 🛒 فروشگاه (غیرفعال)
     ✓ 💬 پشتیبانی پایین (مربع بزرگ)

  🎯 بازی معما (جدید - کلمه‌سازی):
     ✓ ۲۰۰+ کلمه فارسی (۴-۸ حرف)
     ✓ ۵ کلمه تصادفی در هر بازی
     ✓ حروف به‌هم‌ریخته، باید مرتب کنی
     ✓ زمان بر اساس طول کلمه (۴ حرف=۲۰s، ۵ حرف=۲۵s)
     ✓ تایمر کلی جمع همه زمان‌ها

  🧠 بازی حافظه (جدید - ایده خودم):
     ✓ ۱۶ کارت (۸ جفت ایموجی)
     ✓ 3D flip animation
     ✓ شمارش حرکت + زمان
     ✓ تشخیص برد

  🎮 بازی‌ها (rooms.html):
     ✓ چالش حذف شد (به خانه منتقل)
     ✓ بازی معما (جدید)
     ✓ بازی حافظه (جدید)
     ✓ ۷ حالت کل

حالا:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R

تست:
  http://127.0.0.1:8000/game/         ← خانه جدید
  http://127.0.0.1:8000/game/rooms/   ← ۷ بازی
  http://127.0.0.1:8000/game/puzzle/  ← معما
  http://127.0.0.1:8000/game/memory/  ← حافظه
  http://127.0.0.1:8000/game/challenge/ ← چالش (از خانه)
""")
