#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فیکس نهایی: پشتیبانی + معما + ۰ تا ۱۰۰ + خانه"""
import os, sys, re, subprocess

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
# 1) CLEAN accounts/models.py - remove ALL Support* classes
# ============================================================
print("\n[1/8] Cleaning accounts/models.py")
src = read("accounts/models.py")
original_len = len(src)

# Remove SupportTicket class
pattern = re.compile(r'\n\nclass SupportTicket\(models\.Model\):.*?(?=\n\nclass |\n\n# |\Z)', re.DOTALL)
src = pattern.sub('', src)

# Remove SupportMessage class
pattern = re.compile(r'\n\nclass SupportMessage\(models\.Model\):.*?(?=\n\nclass |\n\n# |\Z)', re.DOTALL)
src = pattern.sub('', src)

# Remove any remaining Support* references
if "SupportTicket" in src or "SupportMessage" in src:
    print("  ⚠ Still has Support* refs - forcing removal")
    lines = src.split("\n")
    result = []
    skip_until_class = False
    for line in lines:
        if line.startswith("class Support"):
            skip_until_class = True
            continue
        if skip_until_class:
            # Stop skipping at next class or non-indented
            if line.startswith("class ") or (line and not line.startswith(" ") and not line.startswith("#") and not line.startswith("@")):
                skip_until_class = False
                result.append(line)
            continue
        result.append(line)
    src = "\n".join(result)

if len(src) != original_len:
    write("accounts/models.py", src)
    print(f"  ✓ Removed {original_len - len(src)} chars")
else:
    print("  ✓ Already clean")

# ============================================================
# 2) FIX support/models.py - ensure related_name is unique
# ============================================================
print("\n[2/8] Fixing support/models.py")
if not os.path.exists("support/models.py"):
    write("support/models.py", '''# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models


class SupportTicket(models.Model):
    STATUS = [
        ("open", "باز"),
        ("in_progress", "در حال بررسی"),
        ("answered", "پاسخ داده شده"),
        ("closed", "بسته شده"),
    ]
    PRIORITY = [
        ("low", "کم"),
        ("normal", "معمولی"),
        ("high", "فوری"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="my_support_tickets",
    )
    subject = models.CharField(max_length=100)
    body = models.TextField(max_length=2000)
    category = models.CharField(max_length=20, default="general")
    status = models.CharField(max_length=15, choices=STATUS, default="open")
    priority = models.CharField(max_length=10, choices=PRIORITY, default="normal")
    admin_reply = models.TextField(blank=True, default="")
    replied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"#{self.id} - {self.subject[:30]}"

    def status_display(self):
        return dict(self.STATUS).get(self.status, self.status)
''')
    print("  ✓ Created fresh support/models.py")
else:
    s = read("support/models.py")
    if 'related_name="my_support_tickets"' not in s:
        s = s.replace('related_name="support_tickets"', 'related_name="my_support_tickets"')
        s = s.replace('related_name="user_support_tickets"', 'related_name="my_support_tickets"')
        write("support/models.py", s)
        print("  ✓ Fixed related_name")
    else:
        print("  ✓ Already fixed")

# ============================================================
# 3) Ensure support app files exist
# ============================================================
print("\n[3/8] Ensuring support app files")
if not os.path.exists("support/__init__.py"):
    write("support/__init__.py", "")
if not os.path.exists("support/apps.py"):
    write("support/apps.py", '''from django.apps import AppConfig


class SupportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "support"
''')
if not os.path.exists("support/migrations"):
    os.makedirs("support/migrations", exist_ok=True)
    write("support/migrations/__init__.py", "")
if not os.path.exists("support/urls.py"):
    write("support/urls.py", '''from django.urls import path
from . import views

app_name = "support"

urlpatterns = [
    path("", views.support_home, name="home"),
    path("<int:ticket_id>/", views.ticket_detail, name="ticket"),
    path("<int:ticket_id>/close/", views.ticket_close, name="close"),
]
''')
if not os.path.exists("support/views.py"):
    write("support/views.py", '''# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import SupportTicket


@login_required
def support_home(request):
    if not getattr(request.user, "has_chosen_avatar", False):
        return redirect("accounts:avatar_select")

    if request.method == "POST":
        subject = (request.POST.get("subject") or "").strip()[:100]
        body = (request.POST.get("body") or "").strip()[:2000]
        category = request.POST.get("category", "general")

        if not subject or len(subject) < 3:
            messages.error(request, "موضوع باید حداقل ۳ حرف باشد.")
        elif not body or len(body) < 10:
            messages.error(request, "متن پیام باید حداقل ۱۰ حرف باشد.")
        else:
            ticket = SupportTicket.objects.create(
                user=request.user,
                subject=subject,
                body=body,
                category=category if category in ("general", "bug", "idea", "payment") else "general",
            )
            messages.success(request, f"✅ تیکت #{ticket.id} ثبت شد. به زودی پاسخ می‌دیم.")
            return redirect("support:home")

    my_tickets = SupportTicket.objects.filter(user=request.user)[:20]
    return render(request, "support/home.html", {
        "tickets": my_tickets,
        "active": "home",
    })


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    return render(request, "support/ticket.html", {
        "ticket": ticket,
        "active": "home",
    })


@login_required
def ticket_close(request, ticket_id):
    if request.method != "POST":
        return redirect("support:home")
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    if ticket.status != "closed":
        ticket.status = "closed"
        ticket.save(update_fields=["status"])
        messages.success(request, f"تیکت #{ticket.id} بسته شد.")
    return redirect("support:home")
''')
print("  ✓ Support app files ready")

# ============================================================
# 4) Ensure game/views.py has ALL required views
# ============================================================
print("\n[4/8] Fixing game/views.py")
views_src = read("game/views.py")

# Find existing functions
existing_fns = set(re.findall(r'^def ([a-zA-Z_][a-zA-Z0-9_]*)\(', views_src, re.MULTILINE))
print(f"  Existing: {len(existing_fns)} functions")

# ============================================================
# Ensure puzzle_words.py exists
# ============================================================
if not os.path.exists("game/puzzle_words.py"):
    print("  Creating puzzle_words.py...")
    words = ["کتاب","درخت","خورشید","آبشار","پروانه","خرگوش","پلنگ","دلفین","عقاب","طوطی",
             "گنجشک","اسب","شتر","خرس","گرگ","روباه","آهو","گوزن","جغد","بلبل",
             "زنبور","مورچه","عقرب","مارمولک","نهنگ","کوسه","کبوتر","سنجاب","آسمان","ابر",
             "باران","برف","رعد","دریا","اقیانوس","رودخانه","دریاچه","جنگل","کوه","تپه",
             "صحرا","بیابان","چشمه","چمن","گل","شاخه","ریشه","برگ","باد","طوفان",
             "مه","شبنم","یخ","آتشفشان","قرمز","آبی","زرد","سبز","صورتی","بنفش",
             "نارنجی","مشکی","سفید","طلایی","نقره‌ای","دفتر","میز","صندلی","تخت","پنجره",
             "دیوار","سقف","پرده","فرش","بالش","آینه","ساعت","کلید","قفل","چراغ",
             "لامپ","پنکه","یخچال","تلفن","گوشی","هدفون","چاقو","قاشق","چنگال","بشقاب",
             "لیوان","فنجان","کتری","قوری","دیگ","سطل","جارو","سبد","کیف","چمدان",
             "کفش","جوراب","شلوار","پیراهن","کلاه","دستکش","شال","روسری","عینک","دستبند",
             "گردنبند","انگشتر","توپ","عروسک","بادبادک","اسکیت","دوچرخه","راکت","شطرنج","تخته",
             "نان","برنج","مرغ","گوشت","ماهی","پنیر","کره","شیر","ماست","دوغ",
             "عسل","مربا","شکر","نمک","فلفل","زعفران","چای","قهوه","شربت","سوپ",
             "آش","پلو","کباب","خورش","سالاد","پیاز","سیر","گوجه","خیار","کاهو",
             "هویج","کدو","بادمجان","سیب","موز","پرتقال","انگور","هلو","زردآلو","گیلاس",
             "توت","انار","انجیر","خرما","انبه","آناناس","کیوی","نارگیل","لیمو","نارنگی",
             "طالبی","هندوانه","خربزه","چشم","گوش","بینی","دهان","دندان","زبان","گردن",
             "شانه","دست","انگشت","ناخن","قلب","شکم","زانو","آرنج","مو","خانه",
             "مدرسه","مسجد","بازار","فروشگاه","بیمارستان","پارک","خیابان","کوچه","میدان","پل",
             "فرودگاه","رستوران","کتابخانه","موزه","سینما","بانک","اداره","کارخانه","مزرعه","باغ",
             "ساحل","جزیره","شادی","غم","خنده","گریه","عشق","امید","ترس","خشم",
             "آرامش","هیجان","مهربانی","دوستی","پزشک","معلم","مهندس","راننده","خلبان","آشپز",
             "نجار","بنا","خیاط","نقاش","نویسنده","خواننده","بازیگر","کارگر","کشاورز","نگهبان",
             "پلیس","سرباز","قاضی","خواب","بیداری","دویدن","پریدن","نشستن","خوردن","نوشیدن",
             "خواندن","نوشتن","دیدن","فکرکردن","خندیدن","رقصیدن","آوازخواندن"]
    
    write("game/puzzle_words.py", f'''# -*- coding: utf-8 -*-
PUZZLE_WORDS = {words!r}

def get_puzzle_words():
    return [w for w in PUZZLE_WORDS if 4 <= len(w) <= 8]
''')

# ============================================================
# Add missing views
# ============================================================
NEW_VIEWS = []

if "puzzle_home" not in existing_fns:
    NEW_VIEWS.append('''

# ============================================================
# Puzzle Game
# ============================================================
@login_required
def puzzle_home(request):
    check = _require_complete(request.user)
    if check:
        return check
    from game.puzzle_words import get_puzzle_words
    import time, random as _r

    if request.method == "POST" and request.POST.get("action") == "new":
        request.session.pop("puzzle_items", None)
        request.session["puzzle_finished"] = True
        return redirect("game:puzzle")

    if "puzzle_items" not in request.session or request.session.get("puzzle_finished"):
        pool = get_puzzle_words()
        picks = _r.sample(pool, min(5, len(pool)))
        items = []
        total_time = 0
        for i, w in enumerate(picks):
            sec = len(w) * 5
            total_time += sec
            letters = list(w)
            for _ in range(30):
                _r.shuffle(letters)
                if "".join(letters) != w:
                    break
            items.append({
                "idx": i,
                "word": w,
                "scrambled": " ".join(letters),
                "length": len(w),
                "seconds": sec,
            })
        request.session["puzzle_items"] = items
        request.session["puzzle_start_ts"] = int(time.time())
        request.session["puzzle_total_time"] = total_time
        request.session["puzzle_finished"] = False
        request.session["puzzle_score"] = 0

    items = request.session.get("puzzle_items", [])
    start_ts = request.session.get("puzzle_start_ts", 0)
    total_time = request.session.get("puzzle_total_time", 60)
    elapsed = int(time.time() - start_ts) if start_ts else 0
    remaining = max(0, total_time - elapsed)

    if remaining <= 0 and not request.session.get("puzzle_finished"):
        request.session["puzzle_finished"] = True

    if request.session.get("puzzle_finished"):
        return render(request, "game/puzzle.html", {
            "finished": True,
            "score": request.session.get("puzzle_score", 0),
            "total": len(items),
            "active": "games",
        })

    return render(request, "game/puzzle.html", {
        "items": items,
        "total": len(items),
        "remaining": remaining,
        "total_time": total_time,
        "finished": False,
        "active": "games",
    })


@login_required
def puzzle_submit(request):
    check = _require_complete(request.user)
    if check:
        return check
    if request.method != "POST":
        return redirect("game:puzzle")
    if request.POST.get("action") == "new":
        request.session.pop("puzzle_items", None)
        return redirect("game:puzzle")

    items = request.session.get("puzzle_items", [])
    correct = 0
    for it in items:
        ans = (request.POST.get(f"ans_{it['idx']}") or "").strip()
        ans = ans.replace("ي","ی").replace("ك","ک").replace(" ","").replace("\u200c","")
        target = it["word"].replace("ي","ی").replace("ك","ک").replace(" ","").replace("\u200c","")
        if ans == target:
            correct += 1
    request.session["puzzle_score"] = correct * 10
    request.session["puzzle_finished"] = True
    messages.success(request, f"🎯 {correct} از {len(items)} درست!")
    return redirect("game:puzzle")
''')
    print("  + puzzle_home, puzzle_submit added")

if "puzzle_status" not in existing_fns:
    NEW_VIEWS.append('''

@login_required
def puzzle_status(request):
    from django.http import JsonResponse
    import time
    start_ts = request.session.get("puzzle_start_ts", 0)
    total_time = request.session.get("puzzle_total_time", 60)
    if not start_ts:
        return JsonResponse({"remaining": total_time, "time_up": False})
    remaining = max(0, total_time - int(time.time() - start_ts))
    return JsonResponse({"remaining": remaining, "time_up": remaining <= 0})
''')
    print("  + puzzle_status added")

if "memory_home" not in existing_fns:
    NEW_VIEWS.append('''

# ============================================================
# Memory Game
# ============================================================
_MEMORY_EMOJIS = ["🐶","🐱","🦁","🐯","🐻","🐼","🐨","🐸","🦊","🐵","🦄","🐲"]

@login_required
def memory_home(request):
    check = _require_complete(request.user)
    if check:
        return check
    import random as _r

    if request.method == "POST" and request.POST.get("action") == "new":
        request.session.pop("memory_cards", None)

    if "memory_cards" not in request.session:
        emojis = _r.sample(_MEMORY_EMOJIS, 8)
        cards_raw = emojis * 2
        _r.shuffle(cards_raw)
        cards = [{"id": i, "emoji": em, "flipped": False, "matched": False} for i, em in enumerate(cards_raw)]
        request.session["memory_cards"] = cards
        request.session["memory_matched"] = 0
        request.session["memory_moves"] = 0

    cards = request.session.get("memory_cards", [])
    return render(request, "game/memory.html", {
        "cards": cards,
        "total_pairs": len(cards) // 2,
        "active": "games",
    })


@login_required
def memory_status(request):
    from django.http import JsonResponse
    cards = request.session.get("memory_cards", [])
    return JsonResponse({"total_pairs": len(cards) // 2})
''')
    print("  + memory_home, memory_status added")

if "guess_home" not in existing_fns:
    NEW_VIEWS.append('''

# ============================================================
# 0-100 Guess Game
# ============================================================
@login_required
def guess_home(request):
    check = _require_complete(request.user)
    if check:
        return check
    import random as _r

    if request.method == "POST" and request.POST.get("action") == "new":
        request.session.pop("guess_number", None)

    if "guess_number" not in request.session:
        request.session["guess_number"] = _r.randint(0, 100)
        request.session["guess_tries"] = 0
        request.session["guess_max"] = 7
        request.session["guess_finished"] = False
        request.session["guess_won"] = False
        request.session["guess_history"] = []

    return render(request, "game/guess.html", {
        "tries": request.session.get("guess_tries", 0),
        "max_tries": request.session.get("guess_max", 7),
        "finished": request.session.get("guess_finished", False),
        "won": request.session.get("guess_won", False),
        "number": request.session.get("guess_number") if request.session.get("guess_finished") else None,
        "history": request.session.get("guess_history", []),
        "active": "games",
    })


@login_required
def guess_attempt(request):
    check = _require_complete(request.user)
    if check:
        return check
    if request.method != "POST":
        return redirect("game:guess")

    try:
        guess = int(request.POST.get("guess", -1))
    except (ValueError, TypeError):
        return redirect("game:guess")

    if not (0 <= guess <= 100):
        messages.error(request, "عدد بین ۰ تا ۱۰۰ باشه.")
        return redirect("game:guess")

    number = request.session.get("guess_number", 50)
    tries = request.session.get("guess_tries", 0) + 1
    max_tries = request.session.get("guess_max", 7)
    history = request.session.get("guess_history", [])

    if guess == number:
        request.session["guess_won"] = True
        request.session["guess_finished"] = True
        request.session["guess_tries"] = tries
        history.append({"guess": guess, "result": "win"})
        messages.success(request, f"🎉 آفرین! عدد {number} بود. توی {tries} تلاش.")
    elif tries >= max_tries:
        request.session["guess_won"] = False
        request.session["guess_finished"] = True
        request.session["guess_tries"] = tries
        history.append({"guess": guess, "result": "low" if guess < number else "high"})
        messages.error(request, f"❌ باختی! عدد {number} بود.")
    else:
        request.session["guess_tries"] = tries
        result = "low" if guess < number else "high"
        history.append({"guess": guess, "result": result})
        if result == "low":
            messages.info(request, f"⬆️ بزرگ‌تره! ({max_tries - tries} تلاش دیگه)")
        else:
            messages.info(request, f"⬇️ کوچیک‌تره! ({max_tries - tries} تلاش دیگه)")

    request.session["guess_history"] = history
    return redirect("game:guess")
''')
    print("  + guess_home, guess_attempt added")

if NEW_VIEWS:
    views_src = views_src.rstrip() + "\n" + "\n".join(NEW_VIEWS) + "\n"
    write("game/views.py", views_src)

# Ensure imports
if "from django.contrib import messages" not in views_src:
    views_src = read("game/views.py")
    if "from django.contrib.auth.decorators import login_required" in views_src:
        views_src = views_src.replace(
            "from django.contrib.auth.decorators import login_required",
            "from django.contrib import messages\nfrom django.contrib.auth.decorators import login_required",
            1
        )
        write("game/views.py", views_src)
        print("  ✓ messages imported")

# ============================================================
# 5) Rebuild game/urls.py with only VALID routes
# ============================================================
print("\n[5/8] Rebuilding game/urls.py")
views_src = read("game/views.py")
existing_fns = set(re.findall(r'^def ([a-zA-Z_][a-zA-Z0-9_]*)\(', views_src, re.MULTILINE))
print(f"  Now have {len(existing_fns)} functions")

ROUTES = [
    ("", "home", "home"),
    ("rooms/", "rooms_list", "rooms"),
    ("rooms/manage/", "rooms_manage", "rooms_manage"),
    ("rooms/join/<str:room_code>/", "join_room", "join_room"),
    ("rooms/leave/<str:room_code>/", "leave_room", "leave_room"),
    ("room/<str:room_code>/", "room", "room"),
    ("friends/", "friends_page", "friends"),
    ("leaderboard/", "leaderboard_view", "leaderboard"),
    ("top-players/", "top_players_view", "top_players"),
    ("quick/", "quick_play", "quick_play"),
    ("quick/bot/", "bot_setup", "bot_setup"),
    ("quick/bot/play/<uuid:game_id>/", "bot_play", "bot_play"),
    ("quick/bot/submit/<uuid:game_id>/", "bot_submit", "bot_submit"),
    ("challenge/", "challenge_home", "challenge"),
    ("challenge/<int:tournament_id>/join/", "tournament_join", "tournament_join"),
    ("match/", "match_start", "match_start"),
    ("match/wait/", "match_wait", "match_wait"),
    ("match/cancel/", "match_cancel", "match_cancel"),
    ("match/status/", "match_status", "match_status"),
    ("team/start/", "team_start", "team_start"),
    ("team/wait/", "team_wait", "team_wait"),
    ("team/cancel/", "team_cancel", "team_cancel"),
    ("team/status/", "team_status", "team_status"),
    ("team/select/<str:room_code>/", "team_select", "team_select"),
    ("team/play/<str:room_code>/", "team_play", "team_play"),
    ("team/play-status/<str:room_code>/", "team_status_ajax", "team_status_ajax"),
    ("team/round-end/<str:room_code>/", "team_round_end", "team_round_end"),
    ("team/result/<str:room_code>/", "team_result", "team_result"),
    ("puzzle/", "puzzle_home", "puzzle"),
    ("puzzle/submit/", "puzzle_submit", "puzzle_submit"),
    ("puzzle/status/", "puzzle_status", "puzzle_status"),
    ("memory/", "memory_home", "memory"),
    ("memory/status/", "memory_status", "memory_status"),
    ("guess/", "guess_home", "guess"),
    ("guess/attempt/", "guess_attempt", "guess_attempt"),
]

valid = [r for r in ROUTES if r[1] in existing_fns]
missing = [r for r in ROUTES if r[1] not in existing_fns]

print(f"  Valid routes: {len(valid)}")
for r in missing:
    print(f"    ✗ Missing: {r[1]}")

url_patterns = "\n".join([f'    path("{r[0]}", views.{r[1]}, name="{r[2]}"),' for r in valid])

write("game/urls.py", f'''from django.urls import path
from . import views

app_name = "game"

urlpatterns = [
{url_patterns}
]
''')

# ============================================================
# 6) Ensure templates exist
# ============================================================
print("\n[6/8] Checking templates")
templates_needed = [
    "game/templates/game/puzzle.html",
    "game/templates/game/memory.html",
    "game/templates/game/guess.html",
    "support/templates/support/home.html",
    "support/templates/support/ticket.html",
]

for t in templates_needed:
    if os.path.exists(t) and os.path.getsize(t) > 100:
        print(f"  ✓ {t}")
    else:
        print(f"  ⚠ {t} MISSING or empty")

# ============================================================
# 7) REBUILD HOME with rectangular support + challenge
# ============================================================
print("\n[7/8] Rebuilding home page")

HOME_HTML = '''{% extends "base.html" %}
{% block title %}خانه{% endblock %}

{% block extra_css %}
<style>
  /* ============ ANIMATED BACKGROUND ============ */
  .bg-pattern { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
  .bg-pattern::before, .bg-pattern::after {
    content: ""; position: absolute; inset: -50%;
    background-image:
      radial-gradient(circle, rgba(244,197,66,0.35) 1px, transparent 1.5px),
      radial-gradient(circle, rgba(139,92,246,0.3) 1px, transparent 1.5px);
    background-size: 60px 60px, 90px 90px;
    background-position: 0 0, 30px 30px;
    animation: dotsFloat 30s linear infinite;
    opacity: 0.4;
  }
  .bg-pattern::after { animation-duration: 45s; animation-direction: reverse; }
  @keyframes dotsFloat { from { transform: translate(0, 0); } to { transform: translate(60px, 90px); } }
  .fly-dot {
    position: fixed; width: 4px; height: 4px; border-radius: 50%;
    background: #f4c542; box-shadow: 0 0 8px #f4c542;
    opacity: 0.6; z-index: 0; pointer-events: none; animation: flyUp linear infinite;
  }
  @keyframes flyUp {
    from { transform: translateY(100vh) scale(0.3); opacity: 0; }
    20% { opacity: 0.7; }
    to { transform: translateY(-50px) scale(1); opacity: 0; }
  }

  /* ============ TOP ROW ============ */
  .top-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 16px; position: relative; z-index: 3; min-height: 80px; }
  .btn-settings { width: 52px; height: 52px; border-radius: 16px; background: linear-gradient(135deg, var(--card), #0f0f1e); border: 2px solid rgba(148,163,184,0.4); display: flex; align-items: center; justify-content: center; text-decoration: none; font-size: 24px; flex-shrink: 0; transition: all 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
  .btn-settings:hover { border-color: var(--gold); transform: rotate(45deg) scale(1.08); box-shadow: 0 8px 20px rgba(244,197,66,0.3); }
  .profile-wrap { display: flex; justify-content: flex-end; flex: 1; min-width: 0; }
  .profile-oval { display: flex; align-items: center; gap: 0; padding: 6px; height: 68px; width: 68px; border-radius: 34px; background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.35), transparent 60%), linear-gradient(135deg, var(--card), #0f0f1e); border: 2.5px solid rgba(244,197,66,0.6); cursor: pointer; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); overflow: hidden; position: relative; box-shadow: 0 0 25px rgba(244,197,66,0.3); flex-shrink: 0; }
  .profile-oval:hover { border-color: #fde68a; box-shadow: 0 0 40px rgba(244,197,66,0.5); }
  .profile-oval.expanded { width: 260px; padding: 12px 16px; gap: 12px; }
  .po-av { width: 52px; height: 52px; border-radius: 50%; background: linear-gradient(135deg, #2a2a4a, #1a1a2e); display: flex; align-items: center; justify-content: center; font-size: 26px; border: 2px solid #f4c542; box-shadow: 0 0 15px rgba(244,197,66,0.5); overflow: hidden; background-size: cover; background-position: center; flex-shrink: 0; transition: all 0.3s; }
  .profile-oval.expanded .po-av { width: 56px; height: 56px; font-size: 28px; }
  .po-details { flex: 1; min-width: 0; max-width: 0; opacity: 0; overflow: hidden; transition: all 0.4s; text-align: right; white-space: nowrap; }
  .profile-oval.expanded .po-details { max-width: 200px; opacity: 1; }
  .po-name { font-size: 15px; font-weight: 900; color: #fde68a; margin-bottom: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .po-meta { display: flex; gap: 6px; align-items: center; font-size: 10px; color: #94a3b8; flex-wrap: wrap; }
  .po-meta .badge { background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; padding: 1px 6px; border-radius: 6px; font-family: monospace; font-weight: 900; font-size: 9px; }

  /* ============ RECTANGULAR BUTTONS (right column) ============ */
  .right-column { display: flex; flex-direction: column; align-items: stretch; gap: 10px; margin-bottom: 16px; position: relative; z-index: 2; }
  .rect-btn {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 14px 18px;
    border-radius: 16px;
    text-decoration: none;
    color: #fff;
    border: 2px solid;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    font-family: inherit;
    box-shadow: 0 6px 18px rgba(0,0,0,0.3);
    position: relative;
    overflow: hidden;
  }
  .rect-btn::after {
    content: "";
    position: absolute;
    top: 0; left: -100%;
    width: 60%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
    transform: skewX(-20deg);
    animation: shine 4s infinite;
    pointer-events: none;
  }
  @keyframes shine { 0% { left: -100%; } 50%,100% { left: 200%; } }
  .rect-btn:hover { transform: translateY(-3px); }
  .rect-btn:active { transform: scale(0.98); }
  .rect-btn .icon-wrap { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; }
  .rect-btn .body { flex: 1; text-align: right; }
  .rect-btn .title { font-size: 16px; font-weight: 900; margin-bottom: 3px; }
  .rect-btn .desc { font-size: 11px; opacity: 0.8; }
  .rect-btn .arrow { font-size: 20px; opacity: 0.7; }

  /* Top players — gold */
  .rect-top { background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.3), transparent 60%), linear-gradient(135deg, #2a1a0e, #1a0f1a); border-color: rgba(244,197,66,0.6); }
  .rect-top:hover { border-color: #fde68a; box-shadow: 0 12px 30px rgba(244,197,66,0.4); }
  .rect-top .icon-wrap { background: radial-gradient(circle, rgba(244,197,66,0.4), rgba(234,179,8,0.15)); box-shadow: 0 0 12px rgba(244,197,66,0.6); }
  .rect-top .title { color: #fde68a; }

  /* Challenge — red */
  .rect-challenge { background: radial-gradient(circle at 100% 0%, rgba(239,68,68,0.3), transparent 60%), linear-gradient(135deg, #2a0a0a, #1a0606); border-color: rgba(239,68,68,0.6); }
  .rect-challenge:hover { border-color: #fca5a5; box-shadow: 0 12px 30px rgba(239,68,68,0.4); }
  .rect-challenge .icon-wrap { background: radial-gradient(circle, rgba(239,68,68,0.4), rgba(249,115,22,0.15)); box-shadow: 0 0 12px rgba(239,68,68,0.6); }
  .rect-challenge .title { color: #fca5a5; }

  /* Support — cyan */
  .rect-support { background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.3), transparent 60%), linear-gradient(135deg, #0a1e2a, #05141a); border-color: rgba(6,182,212,0.6); }
  .rect-support:hover { border-color: #a5f3fc; box-shadow: 0 12px 30px rgba(6,182,212,0.4); }
  .rect-support .icon-wrap { background: radial-gradient(circle, rgba(6,182,212,0.4), rgba(59,130,246,0.15)); box-shadow: 0 0 12px rgba(6,182,212,0.6); }
  .rect-support .title { color: #a5f3fc; }

  /* ============ 3 SQUARES ============ */
  .section-label { font-size: 11px; color: var(--muted); font-weight: 900; letter-spacing: 2px; margin: 4px 4px 12px; display: flex; align-items: center; gap: 8px; position: relative; z-index: 2; }
  .section-label::after { content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, rgba(148,163,184,0.2), transparent); }

  .sq-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; position: relative; z-index: 2; }
  .sq-tile { aspect-ratio: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; padding: 12px 8px; border-radius: 20px; text-decoration: none; color: #fff; position: relative; overflow: hidden; border: 2px solid; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer; font-family: inherit; background: transparent; }
  .sq-tile:hover { transform: translateY(-4px) scale(1.04); }
  .sq-tile::after { content: ""; position: absolute; top: 0; left: -100%; width: 60%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent); transform: skewX(-20deg); animation: shine 4s infinite; z-index: 2; pointer-events: none; }
  .sq-icon { font-size: 38px; line-height: 1; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.5)); animation: float 3s ease-in-out infinite; }
  .sq-tile:nth-child(1) .sq-icon { animation-delay: 0s; }
  .sq-tile:nth-child(2) .sq-icon { animation-delay: 0.4s; }
  .sq-tile:nth-child(3) .sq-icon { animation-delay: 0.8s; }
  @keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
  .sq-tile:hover .sq-icon { transform: scale(1.2) rotate(-8deg); animation: none; }
  .sq-title { font-size: 12px; font-weight: 900; }
  .sq-sub { font-size: 9px; opacity: 0.75; }

  .sq-notif { background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.4), transparent 60%), linear-gradient(135deg, #1a0f2e, #0f0f1e); border-color: rgba(139,92,246,0.6); }
  .sq-notif:hover { border-color: rgba(167,139,250,0.95); box-shadow: 0 18px 45px rgba(139,92,246,0.45); }
  .sq-notif .sq-title { color: #c4b5fd; }
  .sq-games { background: radial-gradient(circle at 100% 0%, rgba(236,72,153,0.4), transparent 60%), linear-gradient(135deg, #1a0f2e, #120824); border-color: rgba(236,72,153,0.6); }
  .sq-games:hover { border-color: rgba(236,72,153,0.95); box-shadow: 0 18px 45px rgba(236,72,153,0.45); }
  .sq-games .sq-title { color: #f9a8d4; }
  .sq-shop { background: radial-gradient(circle at 100% 0%, rgba(100,116,139,0.3), transparent 60%), linear-gradient(135deg, #1a1a2e, #0f0f1e); border-color: rgba(100,116,139,0.4); opacity: 0.65; cursor: not-allowed; }
  .sq-shop:hover { transform: none; box-shadow: none; }
  .sq-shop .sq-title { color: #cbd5e1; }
  .sq-shop::after { animation: none; }

  .sq-badge { position: absolute; top: 8px; right: 8px; background: #ef4444; color: #fff; font-size: 10px; font-weight: 900; padding: 2px 8px; border-radius: 999px; box-shadow: 0 3px 10px rgba(239,68,68,0.6); animation: pulseBadge 2s infinite; z-index: 3; }
  @keyframes pulseBadge { 0%,100% { transform: scale(1); } 50% { transform: scale(1.18); } }

  /* Guest */
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

  <!-- Top row -->
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

  <!-- Right column: top players + challenge (rectangular) -->
  <div class="right-column">
    <a href="/game/top-players/" class="rect-btn rect-top">
      <div class="icon-wrap">⭐</div>
      <div class="body">
        <div class="title">بازیکنان برتر</div>
        <div class="desc">جدول رتبه‌بندی</div>
      </div>
      <div class="arrow">←</div>
    </a>
    <a href="/game/challenge/" class="rect-btn rect-challenge">
      <div class="icon-wrap">🏆</div>
      <div class="body">
        <div class="title">چالش</div>
        <div class="desc">تورنمنت و مسابقات</div>
      </div>
      <div class="arrow">←</div>
    </a>
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

  <!-- 3 squares -->
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

  <!-- Support (rectangular, bottom) -->
  <div class="section-label">💬 ارتباط با ما</div>
  <a href="/support/" class="rect-btn rect-support">
    <div class="icon-wrap">💬</div>
    <div class="body">
      <div class="title">پشتیبانی</div>
      <div class="desc">سوال داری؟ با ما در تماس باش</div>
    </div>
    <div class="arrow">←</div>
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
# 8) Migrations + check + TEST
# ============================================================
print("\n[8/8] Migrate + check + test")

# Delete any conflicting fake migrations
for f in os.listdir("accounts/migrations"):
    if "remove_supportticket" in f:
        os.remove(f"accounts/migrations/{f}")
        print(f"  Removed {f}")

# Migrate
print("\n  $ makemigrations")
r = subprocess.run([sys.executable, "manage.py", "makemigrations", "--noinput"],
                   capture_output=True, text=True, timeout=60)
if r.returncode == 0:
    if r.stdout.strip():
        print(f"    {r.stdout.strip()[:300]}")
else:
    print(f"    ⚠ {r.stderr.strip()[:400] if r.stderr else 'unknown'}")

print("\n  $ migrate")
r = subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"],
                   capture_output=True, text=True, timeout=60)
if r.returncode == 0:
    print("    ✓ Migrated")
else:
    print(f"    ⚠ {r.stderr.strip()[:400] if r.stderr else 'unknown'}")

# Check
print("\n  $ check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True, timeout=30)
if r.returncode == 0:
    print("    ✓ Django check PASSED")
else:
    print(f"    ⚠ {r.stderr[:600] if r.stderr else r.stdout[:600]}")

# Test
print("\n  Testing pages...")
TEST_CODE = '''
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
import django
django.setup()
from django.test import Client
from accounts.models import User

User.objects.filter(username="__final__").delete()
u = User.objects.create_user(
    username="__final__", password="x"*10, alias="فینال",
    is_active=True, has_chosen_avatar=True, has_completed_registration=True,
)

c = Client()
c.force_login(u)
c.session["beta_unlocked"] = True
c.session.save()

tests = [
    ("/game/", "خانه"),
    ("/support/", "پشتیبانی"),
    ("/game/puzzle/", "معما"),
    ("/game/guess/", "۰ تا ۱۰۰"),
    ("/game/memory/", "حافظه"),
    ("/game/rooms/", "بازی‌ها"),
]

for url, name in tests:
    try:
        r = c.get(url, follow=False)
        mark = "OK" if r.status_code == 200 else f"-> {r.status_code}"
        print(f"  {url:25s} {name:15s} {mark}")
    except Exception as e:
        print(f"  {url:25s} {name:15s} ERR: {type(e).__name__}")

u.delete()
'''

r = subprocess.run([sys.executable, "-c", TEST_CODE],
                   capture_output=True, text=True, timeout=60,
                   env={**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings"})
print(r.stdout)
if r.stderr and ("Traceback" in r.stderr or "Error" in r.stderr):
    print(f"  ERR: {r.stderr[:400]}")

print("\n" + "="*60)
print("✅ تموم")
print("="*60)
print("""
حالا سرور رو ران کن:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver

تست:
  http://127.0.0.1:8000/game/          ← خانه (پشتیبانی و چالش مستطیل)
  http://127.0.0.1:8000/support/       ← پشتیبانی
  http://127.0.0.1:8000/game/puzzle/   ← معما
  http://127.0.0.1:8000/game/guess/    ← ۰ تا ۱۰۰
""")
