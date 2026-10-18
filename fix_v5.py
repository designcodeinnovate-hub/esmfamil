#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, subprocess, sys, re

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
# 1) accounts/models.py - coins + gems
# ============================================================
print("\n[1/12] accounts/models.py")
p = os.path.join(ROOT, "accounts", "models.py")
src = read(p)
if "coins = models.IntegerField" in src:
    print("  SKIP")
else:
    old = "    last_seen = models.DateTimeField(default=timezone.now)"
    new = old + "\n    coins = models.IntegerField(default=0)\n    gems = models.IntegerField(default=0)"
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: coins + gems added")
    else:
        print("  WARN: last_seen not found")

# ============================================================
# 2) game/models.py - Player.team, team_ready, stopped_in_round
# ============================================================
print("\n[2/12] game/models.py")
p = os.path.join(ROOT, "game", "models.py")
src = read(p)
if "team = models.CharField(max_length=1" in src:
    print("  SKIP")
else:
    old = '''    score = models.IntegerField(default=0)
    is_ready = models.BooleanField(default=False)'''
    new = '''    score = models.IntegerField(default=0)
    is_ready = models.BooleanField(default=False)
    team = models.CharField(max_length=1, blank=True, default="")
    team_ready = models.BooleanField(default=False)
    stopped_round = models.PositiveIntegerField(default=0)'''
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: team fields added")
    else:
        print("  WARN: Player fields block not found")

# ============================================================
# 3) rooms.html - remove challenge, move puzzle to bottom
# ============================================================
print("\n[3/12] rooms.html")
p = os.path.join(ROOT, "game", "templates", "game", "rooms.html")
src = read(p)

# Remove challenge card
challenge_blocks = [
'''  <a href="/game/challenge/" class="big-card challenge">
    <div class="bc-icon">⚔️</div>
    <div class="bc-body">
      <div class="bc-title">چالش</div>
      <div class="bc-desc">تورنمنت هفتگی، مسابقه روزانه و ساعتی</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>

''',
]
for block in challenge_blocks:
    if block in src:
        src = src.replace(block, "", 1)
        print("  FIXED: challenge removed")
        break

# Move puzzle to bottom (after speed)
puzzle_block = '''  <div class="big-card puzzle soon" onclick="alert('🎯 بازی معما به زودی فعال می‌شود!')">
    <span class="soon-badge">به زودی</span>
    <div class="bc-icon">🎯</div>
    <div class="bc-body">
      <div class="bc-title">بازی معما</div>
      <div class="bc-desc">حدس کلمه از روی سرنخ</div>
    </div>
    <div class="bc-arrow">←</div>
  </div>

'''
speed_block = '''  <a href="/game/quick/bot/?mode=speed" class="big-card speed">
    <div class="bc-icon">⏱️</div>
    <div class="bc-body">
      <div class="bc-title">بازی سرعتی</div>
      <div class="bc-desc">مستقیم با حرف رندوم، فقط ۳۰ ثانیه!</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>'''

if puzzle_block in src and speed_block in src:
    # Remove puzzle
    src = src.replace(puzzle_block, "", 1)
    # Update speed desc
    new_speed = speed_block.replace("فقط ۳۰ ثانیه", "فقط ۲۰ ثانیه")
    # Add puzzle after speed
    src = src.replace(speed_block, new_speed + "\n\n" + puzzle_block.rstrip(), 1)
    print("  FIXED: puzzle moved to bottom + speed 20s")
else:
    print("  WARN: puzzle or speed block not found")

backup(p); write(p, src)

# ============================================================
# 4) game/views.py - speed 20s + team views
# ============================================================
print("\n[4/12] game/views.py")
p = os.path.join(ROOT, "game", "views.py")
src = read(p)

# 4a) Speed 30 -> 20 in direct mode
if "duration=30" in src:
    src = src.replace("duration=30", "duration=20")
    print("  FIXED: speed direct -> 20s")

if "base_time = 30" in src:
    src = src.replace("base_time = 30", "base_time = 20")
    print("  FIXED: speed base_time -> 20s")

# 4b) Add team views
if "def team_start(request):" in src:
    print("  SKIP: team views exist")
else:
    team_views = '''

# ============================================================
# بازی تیمی ۴ نفره (2 vs 2)
# ============================================================
import random as _random

TEAM_DURATION = 90
TEAM_ROUNDS = 3


@login_required
def team_start(request):
    check = _require_complete(request.user)
    if check:
        return check
    from .models import MatchQueue
    MatchQueue.objects.filter(user=request.user).delete()
    MatchQueue.objects.create(user=request.user)
    return redirect("game:team_wait")


@login_required
def team_wait(request):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import MatchQueue, Game, Player, Round

    my_q = MatchQueue.objects.filter(user=request.user).first()
    if not my_q:
        return redirect("game:rooms")

    # گروه‌بندی ۴ نفره: اگه ۴ نفر تو صف هستن، همه رو با هم بفرست
    total = MatchQueue.objects.count()
    if total >= 4:
        entries = list(MatchQueue.objects.order_by("joined_at")[:4])
        if any(e.user_id == request.user.id for e in entries):
            users = [e.user for e in entries]
            MatchQueue.objects.filter(user__in=users).delete()

            g = Game.objects.create(
                host=request.user, status="waiting",
                categories=DEFAULT_CATEGORIES[:8], mode="team",
                difficulty="medium", letter_mode="random",
                room_name="بازی تیمی",
            )
            for u in users:
                Player.objects.create(game=g, user=u)

            return redirect("game:team_select", room_code=g.code)

    return render(request, "game/team_wait.html", {"active": "games"})


@login_required
def team_cancel(request):
    from .models import MatchQueue
    MatchQueue.objects.filter(user=request.user).delete()
    return redirect("game:rooms")


@login_required
def team_status(request):
    from .models import MatchQueue, Game
    from django.http import JsonResponse
    if not MatchQueue.objects.filter(user=request.user).exists():
        # user left queue, check if in a team game
        g = Game.objects.filter(players__user=request.user, mode="team").order_by("-created_at").first()
        if g and g.status != "finished":
            return JsonResponse({"status": "matched", "url": f"/game/team/select/{g.code}/"})
        return JsonResponse({"status": "cancelled"})
    return JsonResponse({"status": "waiting", "count": MatchQueue.objects.count()})


@login_required
def team_select(request, room_code):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import Game, Player, Round

    g = Game.objects.filter(code=room_code, mode="team").first()
    if not g:
        return redirect("game:rooms")

    my_p = Player.objects.filter(game=g, user=request.user).first()
    if not my_p:
        return redirect("game:rooms")

    # اگه بازی شروع شده، برو به play
    if g.status == "in_round":
        return redirect("game:team_play", room_code=g.code)

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "choose_team":
            team = request.POST.get("team", "")
            if team in ("A", "B"):
                count = Player.objects.filter(game=g, team=team).exclude(user=request.user).count()
                if count < 2:
                    my_p.team = team
                    my_p.save(update_fields=["team"])

        elif action == "start":
            if g.host_id == request.user.id:
                all_players = Player.objects.filter(game=g)
                if all_players.count() == 4 and all_players.exclude(team="").count() == 4:
                    team_a = all_players.filter(team="A").count()
                    team_b = all_players.filter(team="B").count()
                    if team_a == 2 and team_b == 2:
                        letter = _random.choice(list("ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"))
                        Round.objects.filter(game=g).delete()
                        Round.objects.create(game=g, number=1, letter=letter, duration=TEAM_DURATION)
                        g.status = "in_round"
                        g.save(update_fields=["status"])
                        return redirect("game:team_play", room_code=g.code)

        return redirect("game:team_select", room_code=g.code)

    players_data = []
    for pl in Player.objects.filter(game=g).select_related("user"):
        players_data.append({
            "id": pl.id,
            "user": pl.user,
            "avatar": get_emoji(pl.user.avatar_id),
            "team": pl.team,
            "is_host": pl.user_id == g.host_id,
            "is_me": pl.user_id == request.user.id,
        })

    team_a = [p for p in players_data if p["team"] == "A"]
    team_b = [p for p in players_data if p["team"] == "B"]
    unassigned = [p for p in players_data if not p["team"]]

    can_start = (
        g.host_id == request.user.id
        and len(team_a) == 2
        and len(team_b) == 2
    )

    return render(request, "game/team_select.html", {
        "game": g,
        "team_a": team_a,
        "team_b": team_b,
        "unassigned": unassigned,
        "my_team": my_p.team,
        "can_start": can_start,
        "active": "games",
    })


@login_required
def team_play(request, room_code):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import Game, Player, Round, Answer
    from django.utils import timezone

    g = Game.objects.filter(code=room_code, mode="team").first()
    if not g:
        return redirect("game:rooms")

    my_p = Player.objects.filter(game=g, user=request.user).first()
    if not my_p:
        return redirect("game:rooms")

    if g.status == "finished":
        return redirect("game:team_result", room_code=g.code)

    round_obj = g.rounds.order_by("-number").first()
    if not round_obj:
        return redirect("game:team_select", room_code=g.code)

    # اگه تایم تموم شده یا هر دو تیم استوپ کردن → round end
    elapsed = (timezone.now() - round_obj.started_at).total_seconds()
    time_up = elapsed >= round_obj.duration

    stop_a = Player.objects.filter(game=g, team="A", stopped_round=round_obj.number).count()
    stop_b = Player.objects.filter(game=g, team="B", stopped_round=round_obj.number).count()
    both_stopped = stop_a >= 2 and stop_b >= 2

    if (time_up or both_stopped) and not round_obj.stopped_at:
        round_obj.stopped_at = timezone.now()
        round_obj.save(update_fields=["stopped_at"])
        return redirect("game:team_round_end", room_code=g.code)

    if round_obj.stopped_at:
        return redirect("game:team_round_end", room_code=g.code)

    if request.method == "POST":
        # ثبت پاسخ‌ها
        for cat in g.categories:
            raw = (request.POST.get(f"cat_{cat}") or "").strip()[:64]
            norm = _normalize(raw)
            score = 0
            if norm and norm[0] == round_obj.letter:
                if cat in ("اسم", "فامیل"):
                    score = 10
                else:
                    from .bot_data import is_valid_word
                    score = 10 if is_valid_word(norm, cat, round_obj.letter) else 0

            Answer.objects.update_or_create(
                round=round_obj, user=request.user, category=cat,
                defaults={"value": raw, "normalized": norm, "score": score},
            )

        my_p.stopped_round = round_obj.number
        my_p.save(update_fields=["stopped_round"])
        return redirect("game:team_play", room_code=g.code)

    my_stopped = my_p.stopped_round == round_obj.number
    teammate = Player.objects.filter(game=g, team=my_p.team).exclude(user=request.user).first()
    teammate_stopped = teammate and teammate.stopped_round == round_obj.number

    team_a_players = Player.objects.filter(game=g, team="A").select_related("user")
    team_b_players = Player.objects.filter(game=g, team="B").select_related("user")

    return render(request, "game/team_play.html", {
        "game": g,
        "round": round_obj,
        "categories": g.categories,
        "duration": round_obj.duration,
        "my_p": my_p,
        "my_stopped": my_stopped,
        "teammate_stopped": teammate_stopped,
        "team_a_players": team_a_players,
        "team_b_players": team_b_players,
        "elapsed": int(elapsed),
        "active": "games",
    })


@login_required
def team_status_ajax(request, room_code):
    from .models import Game, Player, Round
    from django.utils import timezone
    from django.http import JsonResponse

    g = Game.objects.filter(code=room_code, mode="team").first()
    if not g:
        return JsonResponse({"status": "error"})

    round_obj = g.rounds.order_by("-number").last()
    if not round_obj:
        return JsonResponse({"status": "no_round"})

    elapsed = (timezone.now() - round_obj.started_at).total_seconds()
    time_up = elapsed >= round_obj.duration
    stop_a = Player.objects.filter(game=g, team="A", stopped_round=round_obj.number).count()
    stop_b = Player.objects.filter(game=g, team="B", stopped_round=round_obj.number).count()
    both_stopped = stop_a >= 2 and stop_b >= 2

    if round_obj.stopped_at or time_up or both_stopped:
        return JsonResponse({"status": "round_end", "url": f"/game/team/round-end/{g.code}/"})

    my_p = Player.objects.filter(game=g, user=request.user).first()
    teammate = Player.objects.filter(game=g, team=my_p.team).exclude(user=request.user).first() if my_p else None

    return JsonResponse({
        "status": "playing",
        "my_stopped": my_p and my_p.stopped_round == round_obj.number,
        "teammate_stopped": teammate and teammate.stopped_round == round_obj.number,
        "stop_a": stop_a,
        "stop_b": stop_b,
        "elapsed": int(elapsed),
    })


@login_required
def team_round_end(request, room_code):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import Game, Player, Round, Answer

    g = Game.objects.filter(code=room_code, mode="team").first()
    if not g:
        return redirect("game:rooms")

    round_obj = g.rounds.order_by("-number").last()
    if not round_obj:
        return redirect("game:team_select", room_code=g.code)

    # محاسبه امتیاز این راند
    answers = Answer.objects.filter(round=round_obj)
    team_scores = {"A": 0, "B": 0}
    for a in answers:
        p_obj = Player.objects.filter(game=g, user=a.user).first()
        if p_obj and p_obj.team in ("A", "B"):
            team_scores[p_obj.team] += a.score

    # ذخیره به Player.score
    for pl in Player.objects.filter(game=g):
        prev_total = Answer.objects.filter(
            user=pl.user, round__game=g,
        ).aggregate(s=models.Sum("score"))["s"] or 0
        pl.score = prev_total
        pl.save(update_fields=["score"])

    # آیا راند بعدی هست؟
    has_next = round_obj.number < TEAM_ROUNDS

    if request.method == "POST" and request.POST.get("action") == "next_ready":
        my_p = Player.objects.filter(game=g, user=request.user).first()
        if my_p:
            my_p.team_ready = True
            my_p.save(update_fields=["team_ready"])

        # چک کن همه آماده‌ن
        ready_count = Player.objects.filter(game=g, team_ready=True).count()
        if ready_count >= 4 and has_next:
            letter = _random.choice(list("ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"))
            Round.objects.create(game=g, number=round_obj.number + 1, letter=letter, duration=TEAM_DURATION)
            Player.objects.filter(game=g).update(team_ready=False, stopped_round=0)
            return redirect("game:team_play", room_code=g.code)
        elif ready_count >= 4 and not has_next:
            g.status = "finished"
            g.save(update_fields=["status"])
            # جایزه
            winner_team = None
            if team_scores["A"] > team_scores["B"]:
                winner_team = "A"
            elif team_scores["B"] > team_scores["A"]:
                winner_team = "B"

            if winner_team:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                winners = Player.objects.filter(game=g, team=winner_team).values_list("user_id", flat=True)
                for uid in winners:
                    u = User.objects.filter(id=uid).first()
                    if u:
                        u.coins = (u.coins or 0) + 50
                        u.gems = (u.gems or 0) + 5
                        u.save(update_fields=["coins", "gems"])
            return redirect("game:team_result", room_code=g.code)

        return redirect("game:team_round_end", room_code=g.code)

    # جمع بندی راند
    round_data = []
    for pl in Player.objects.filter(game=g).select_related("user"):
        ans = Answer.objects.filter(round=round_obj, user=pl.user)
        pl_round_score = ans.aggregate(s=models.Sum("score"))["s"] or 0
        round_data.append({
            "user": pl.user,
            "avatar": get_emoji(pl.user.avatar_id),
            "team": pl.team,
            "round_score": pl_round_score,
            "total_score": pl.score,
        })

    my_p = Player.objects.filter(game=g, user=request.user).first()
    team_ready = my_p.team_ready if my_p else False

    return render(request, "game/team_round_end.html", {
        "game": g,
        "round": round_obj,
        "team_scores": team_scores,
        "round_data": round_data,
        "has_next": has_next,
        "team_ready": team_ready,
        "active": "games",
    })


@login_required
def team_result(request, room_code):
    from .models import Game, Player, Round, Answer

    g = Game.objects.filter(code=room_code, mode="team").first()
    if not g:
        return redirect("game:rooms")

    total_a = 0
    total_b = 0
    for pl in Player.objects.filter(game=g):
        total = Answer.objects.filter(user=pl.user, round__game=g).aggregate(s=models.Sum("score"))["s"] or 0
        if pl.team == "A":
            total_a += total
        elif pl.team == "B":
            total_b += total

    winner = "A" if total_a > total_b else ("B" if total_b > total_a else "tie")

    return render(request, "game/team_result.html", {
        "game": g,
        "total_a": total_a,
        "total_b": total_b,
        "winner": winner,
        "active": "games",
    })
'''
    src = src.rstrip() + "\n" + team_views + "\n"
    backup(p); write(p, src)
    print("  FIXED: team views added")

# ============================================================
# 5) game/urls.py - team routes
# ============================================================
print("\n[5/12] game/urls.py")
p = os.path.join(ROOT, "game", "urls.py")
src = read(p)

if "team/start/" in src:
    print("  SKIP")
else:
    old = '    path("match/status/", views.match_status, name="match_status"),'
    new = old + '''
    path("team/start/", views.team_start, name="team_start"),
    path("team/wait/", views.team_wait, name="team_wait"),
    path("team/cancel/", views.team_cancel, name="team_cancel"),
    path("team/status/", views.team_status, name="team_status"),
    path("team/select/<str:room_code>/", views.team_select, name="team_select"),
    path("team/play/<str:room_code>/", views.team_play, name="team_play"),
    path("team/play-status/<str:room_code>/", views.team_status_ajax, name="team_status_ajax"),
    path("team/round-end/<str:room_code>/", views.team_round_end, name="team_round_end"),
    path("team/result/<str:room_code>/", views.team_result, name="team_result"),'''
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: routes added")
    else:
        print("  WARN: match/status not found")

# ============================================================
# 6) menu.html - coins/gems HUD
# ============================================================
print("\n[6/12] menu.html")
p = os.path.join(ROOT, "game", "templates", "game", "menu.html")
src = read(p)

# Add CSS for HUD
if "coin-hud" not in src:
    css_end = src.find("{% endblock %}", src.find("{% block extra_css %}"))
    if css_end > 0:
        css_add = '''
  .coin-hud {
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
  .hud-chip .num { font-size: 15px; color: #fff; font-weight: 900; }
'''
        src = src[:css_end] + css_add + src[css_end:]

# Insert HUD after top-bar
if 'class="coin-hud"' not in src:
    old = '''    <a href="/accounts/settings/" class="settings-icon" title="تنظیمات">⚙️</a>
  </div>'''
    new = '''    <a href="/accounts/settings/" class="settings-icon" title="تنظیمات">⚙️</a>
  </div>

  <div class="coin-hud">
    <div class="hud-chip hud-coins"><span>🪙</span><span class="num">{{ user.coins|default:0 }}</span><span style="font-size:11px;opacity:0.7;">سکه</span></div>
    <div class="hud-chip hud-gems"><span>💎</span><span class="num">{{ user.gems|default:0 }}</span><span style="font-size:11px;opacity:0.7;">جم</span></div>
  </div>'''
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: coin/gem HUD added")
    else:
        print("  WARN: settings-icon anchor not found")

# ============================================================
# 7) base.html - smooth nav transitions
# ============================================================
print("\n[7/12] base.html")
p = os.path.join(ROOT, "templates", "base.html")
src = read(p)

if "page-transition" in src:
    print("  SKIP")
else:
    anchor = "    .container {\n      position: relative;"
    add = '''    .container {
      position: relative;
      animation: pageFadeIn 0.35s cubic-bezier(0.4, 0, 0.2, 1);'''
    if anchor in src:
        src = src.replace(anchor, add, 1)
    # Add keyframes
    kf_anchor = "    .bottom-nav {"
    kf_add = '''    @keyframes pageFadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .bottom-nav a { transition: color 0.2s, transform 0.15s; }
    .bottom-nav a .nav-icon { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
    .bottom-nav a.active .nav-icon { animation: navPulse 0.4s ease-out; }
    @keyframes navPulse {
      0%   { transform: scale(1) translateY(0); }
      50%  { transform: scale(1.2) translateY(-3px); }
      100% { transform: scale(1.12) translateY(-1px); }
    }
    .bottom-nav a:active { transform: scale(0.92); }
    .bottom-nav a.active::before {
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .bottom-nav {'''
    if kf_anchor in src:
        src = src.replace(kf_anchor, kf_add, 1)
    backup(p); write(p, src)
    print("  FIXED: smooth nav CSS added")

# ============================================================
# 8) bot_play.html - pretty graphics
# ============================================================
print("\n[8/12] bot_play.html")
p = os.path.join(ROOT, "game", "templates", "game", "bot_play.html")

BOT_PLAY_HTML = '''{% extends "base.html" %}
{% block title %}در حال بازی{% endblock %}

{% block extra_css %}
<style>
  .game-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 16px;
    background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.2), transparent 60%),
                linear-gradient(135deg, #1a1a2e, #0f0f1e);
    border: 1.5px solid rgba(244,197,66,0.4); border-radius: 22px;
    box-shadow: 0 10px 30px rgba(244,197,66,0.15); }

  .letter-box {
    width: 84px; height: 84px; border-radius: 50%;
    background: radial-gradient(circle, rgba(244,197,66,0.35), rgba(244,197,66,0.05));
    display: flex; align-items: center; justify-content: center;
    font-size: 48px; font-weight: 900; color: var(--gold);
    text-shadow: 0 0 30px rgba(244,197,66,0.9), 0 0 60px rgba(244,197,66,0.5);
    border: 3px solid rgba(244,197,66,0.6);
    animation: letterPulse 2s ease-in-out infinite;
  }
  @keyframes letterPulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(244,197,66,0.7); }
    50%     { box-shadow: 0 0 0 12px rgba(244,197,66,0); }
  }

  .timer-wrapper { position: relative; width: 84px; height: 84px; }
  .timer-svg { transform: rotate(-90deg); width: 84px; height: 84px; }
  .timer-circle-bg { fill: none; stroke: rgba(255,255,255,0.1); stroke-width: 6; }
  .timer-circle-progress { fill: none; stroke: #22c55e; stroke-width: 6; stroke-linecap: round;
    stroke-dasharray: 232; stroke-dashoffset: 0;
    transition: stroke-dashoffset 1s linear, stroke 0.3s; filter: drop-shadow(0 0 6px currentColor); }
  .timer-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
    font-size: 22px; font-weight: 900; font-family: monospace; color: #fff;
    text-shadow: 0 0 10px rgba(255,255,255,0.4); }

  .answers-grid { display: flex; flex-direction: column; gap: 10px; padding-bottom: 90px; }
  .answer-row {
    display: flex; align-items: center; gap: 10px;
    background: linear-gradient(135deg, rgba(30,41,59,0.7), rgba(15,23,42,0.5));
    padding: 8px 14px; border-radius: 14px;
    border: 1.5px solid rgba(148,163,184,0.15);
    transition: 0.2s;
  }
  .answer-row:focus-within {
    border-color: var(--gold);
    box-shadow: 0 0 20px rgba(244,197,66,0.2);
    transform: translateY(-1px);
  }
  .answer-row .label {
    width: 82px; color: var(--gold); font-size: 13px; font-weight: bold;
    padding: 6px 0;
  }
  .answer-row input {
    flex: 1; background: transparent; border: none;
    color: #fff; font-size: 16px; padding: 8px 4px;
    font-family: inherit; font-weight: 500;
  }
  .answer-row input:focus { outline: none; }
  .answer-row input::placeholder { color: rgba(148,163,184,0.4); }

  .stop-wrapper { position: fixed; left: 16px; right: 16px; max-width: 520px; margin: 0 auto; z-index: 50;
    bottom: 80px; bottom: calc(72px + env(safe-area-inset-bottom, 0px) + 8px); }
  button.stop { width: 100%; padding: 16px; border: none; border-radius: 16px;
    font-size: 17px; font-weight: 900; font-family: inherit; cursor: pointer;
    color: #fff; background: linear-gradient(135deg, #ef4444, #b91c1c);
    box-shadow: 0 10px 30px rgba(239,68,68,0.5);
    transition: 0.2s; }
  button.stop:hover { transform: translateY(-2px); }
</style>
{% endblock %}

{% block content %}
  <div class="game-header">
    <div class="letter-box">{{ round.letter }}</div>
    <div class="timer-wrapper">
      <svg class="timer-svg"><circle class="timer-circle-bg" cx="42" cy="42" r="37"></circle><circle class="timer-circle-progress" id="timerProgress" cx="42" cy="42" r="37"></circle></svg>
      <div class="timer-text" id="timerText">{{ duration }}</div>
    </div>
  </div>

  <form method="post" action="/game/quick/bot/submit/{{ game.id }}/" id="form">
    {% csrf_token %}
    <div class="answers-grid">
      {% for c in categories %}
        <div class="answer-row">
          <div class="label">{{ c }}</div>
          <input type="text" name="cat_{{ c }}" autocomplete="off" maxlength="64" placeholder="با {{ round.letter }} شروع شود...">
        </div>
      {% endfor %}
    </div>
    <div class="stop-wrapper">
      <button type="submit" class="stop">✋ استپ!</button>
    </div>
  </form>

<script>
  let total = {{ duration }};
  let left = total;
  const textEl = document.getElementById('timerText');
  const circle = document.getElementById('timerProgress');
  const form = document.getElementById('form');
  const circumference = 2 * Math.PI * 37;
  circle.style.strokeDasharray = circumference;

  const timer = setInterval(() => {
    left--;
    textEl.textContent = left;
    circle.style.strokeDashoffset = circumference - (left / total) * circumference;
    if (left <= 5) { circle.style.stroke = '#ef4444'; textEl.style.color = '#ef4444'; }
    else if (left <= total / 2) { circle.style.stroke = '#eab308'; textEl.style.color = '#eab308'; }
    if (left <= 0) { clearInterval(timer); form.submit(); }
  }, 1000);
</script>
{% endblock %}
'''
backup(p); write(p, BOT_PLAY_HTML)

# ============================================================
# 9) team_wait.html
# ============================================================
print("\n[9/12] team_wait.html")
p = os.path.join(ROOT, "game", "templates", "game", "team_wait.html")
TEAM_WAIT = '''{% extends "base.html" %}
{% block title %}در انتظار بازیکنان{% endblock %}
{% block extra_css %}
<style>
  .wait-box { text-align: center; padding: 50px 20px; background: var(--card); border: 1px solid var(--border); border-radius: 24px; margin-top: 30px; }
  .spinner { width: 90px; height: 90px; margin: 0 auto 24px; border: 5px solid rgba(139,92,246,0.2); border-top-color: var(--purple); border-radius: 50%; animation: spin 1.2s linear infinite; position: relative; }
  .spinner::after { content: "👥"; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 30px; }
  @keyframes spin { to { transform: rotate(360deg); } }
  h1 { font-size: 22px; margin-bottom: 8px; background: linear-gradient(135deg, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  p.sub { color: var(--muted); font-size: 13px; line-height: 1.7; margin-bottom: 18px; }
  .count { display: inline-block; background: rgba(139,92,246,0.15); color: #c4b5fd; padding: 10px 22px; border-radius: 14px; font-size: 15px; font-weight: bold; margin-bottom: 22px; border: 1px solid rgba(139,92,246,0.3); }
  .cancel-btn { display: inline-block; padding: 12px 28px; border-radius: 14px; background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.35); text-decoration: none; font-weight: bold; font-size: 14px; }
</style>
{% endblock %}
{% block content %}
  <div class="wait-box">
    <div class="spinner"></div>
    <h1>دنبال بازیکنان می‌گردیم...</h1>
    <p class="sub">برای بازی تیمی ۴ نفره لازمه.<br>وقتی همه پیدا شدن، انتخاب تیم می‌کنی.</p>
    <div class="count" id="countBox">در انتظار...</div>
    <br><a href="/game/team/cancel/" class="cancel-btn">✕ لغو</a>
  </div>
{% endblock %}
{% block extra_js %}
<script>
  let checks = 0;
  const interval = setInterval(() => {
    checks++;
    if (checks > 60) { clearInterval(interval); alert('کسی پیدا نشد.'); window.location.href='/game/rooms/'; return; }
    fetch('/game/team/status/').then(r=>r.json()).then(d => {
      if (d.status === 'matched') { clearInterval(interval); window.location.href = d.url; }
      else if (d.status === 'cancelled') { clearInterval(interval); window.location.href = '/game/rooms/'; }
      else if (d.count) document.getElementById('countBox').textContent = d.count + ' / 4 نفر در صف';
    }).catch(()=>{});
  }, 2000);
</script>
{% endblock %}
'''
backup(p); write(p, TEAM_WAIT)

# ============================================================
# 10) team_select.html
# ============================================================
print("\n[10/12] team_select.html")
p = os.path.join(ROOT, "game", "templates", "game", "team_select.html")
TEAM_SELECT = '''{% extends "base.html" %}
{% block title %}انتخاب تیم{% endblock %}
{% block extra_css %}
<style>
  .head { text-align: center; margin-bottom: 20px; }
  .head h1 { font-size: 22px; font-weight: 900; background: linear-gradient(135deg, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 6px; }
  .head p { color: var(--muted); font-size: 13px; }
  .teams-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
  .team-col { padding: 16px; border-radius: 18px; min-height: 180px; }
  .team-a { background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(15,23,42,0.6)); border: 2px solid rgba(59,130,246,0.4); }
  .team-b { background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(15,23,42,0.6)); border: 2px solid rgba(239,68,68,0.4); }
  .team-col h3 { font-size: 15px; margin-bottom: 12px; text-align: center; }
  .team-a h3 { color: #93c5fd; }
  .team-b h3 { color: #fca5a5; }
  .team-slot { padding: 10px; border-radius: 12px; background: rgba(15,23,42,0.6); margin-bottom: 8px; text-align: center; font-size: 13px; border: 1px dashed rgba(148,163,184,0.2); }
  .team-slot.filled { border-style: solid; background: rgba(15,23,42,0.9); }
  .team-slot .name { font-weight: bold; color: #fff; margin-top: 4px; }
  .team-slot .av { font-size: 24px; }
  .join-btn { width: 100%; padding: 10px; border-radius: 12px; border: none; font-family: inherit; font-weight: bold; font-size: 13px; cursor: pointer; }
  .join-a { background: linear-gradient(135deg, #3b82f6, #2563eb); color: #fff; }
  .join-b { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; }
  .start-btn { width: 100%; padding: 16px; border-radius: 16px; border: none; font-family: inherit; font-weight: 900; font-size: 16px; cursor: pointer; color: #1a1a1a; background: linear-gradient(135deg, #f4c542, #eab308); box-shadow: 0 10px 30px rgba(244,197,66,0.4); }
  .start-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
{% endblock %}
{% block content %}
  <div class="head">
    <h1>⚔️ انتخاب تیم</h1>
    <p>۴ بازیکن پیدا شدن! تیم خودت رو انتخاب کن.</p>
  </div>

  <div class="teams-grid">
    <div class="team-col team-a">
      <h3>🔵 تیم آبی ({{ team_a|length }}/2)</h3>
      {% for p in team_a %}
        <div class="team-slot filled"><div class="av">{{ p.avatar }}</div><div class="name">{{ p.user.alias }}{% if p.is_me %} (شما){% endif %}</div></div>
      {% endfor %}
      {% for i in "12" %}
        {% if team_a|length < forloop.counter %}
          <div class="team-slot">خالی</div>
        {% endif %}
      {% endfor %}
      {% if my_team != "A" and team_a|length < 2 %}
        <form method="post">{% csrf_token %}<input type="hidden" name="action" value="choose_team"><input type="hidden" name="team" value="A"><button type="submit" class="join-btn join-a">پیوستن</button></form>
      {% endif %}
    </div>

    <div class="team-col team-b">
      <h3>🔴 تیم قرمز ({{ team_b|length }}/2)</h3>
      {% for p in team_b %}
        <div class="team-slot filled"><div class="av">{{ p.avatar }}</div><div class="name">{{ p.user.alias }}{% if p.is_me %} (شما){% endif %}</div></div>
      {% endfor %}
      {% for i in "12" %}
        {% if team_b|length < forloop.counter %}
          <div class="team-slot">خالی</div>
        {% endif %}
      {% endfor %}
      {% if my_team != "B" and team_b|length < 2 %}
        <form method="post">{% csrf_token %}<input type="hidden" name="action" value="choose_team"><input type="hidden" name="team" value="B"><button type="submit" class="join-btn join-b">پیوستن</button></form>
      {% endif %}
    </div>
  </div>

  {% if can_start %}
    <form method="post">{% csrf_token %}<input type="hidden" name="action" value="start"><button type="submit" class="start-btn">🚀 شروع بازی</button></form>
  {% else %}
    <button class="start-btn" disabled>منتظر انتخاب همه بازیکنان...</button>
  {% endif %}

  <script>setTimeout(()=>window.location.reload(), 3000);</script>
{% endblock %}
'''
backup(p); write(p, TEAM_SELECT)

# ============================================================
# 11) team_play.html
# ============================================================
print("\n[11/12] team_play.html")
p = os.path.join(ROOT, "game", "templates", "game", "team_play.html")
TEAM_PLAY = '''{% extends "base.html" %}
{% block title %}بازی تیمی - راند {{ round.number }}{% endblock %}
{% block extra_css %}
<style>
  .team-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding: 14px; background: var(--card); border: 1px solid var(--border); border-radius: 18px; }
  .letter-big { width: 66px; height: 66px; border-radius: 50%; background: radial-gradient(circle, rgba(244,197,66,0.3), transparent); display: flex; align-items: center; justify-content: center; font-size: 34px; font-weight: 900; color: var(--gold); border: 3px solid rgba(244,197,66,0.5); animation: lp 2s infinite; }
  @keyframes lp { 0%,100% { box-shadow: 0 0 0 0 rgba(244,197,66,0.7); } 50% { box-shadow: 0 0 0 12px rgba(244,197,66,0); } }
  .round-info { flex: 1; }
  .round-info .lbl { font-size: 11px; color: var(--muted); margin-bottom: 3px; }
  .round-info .title { font-size: 16px; font-weight: bold; color: #fff; }
  .timer-big { font-size: 26px; font-weight: 900; font-family: monospace; color: var(--gold); }

  .teams-mini { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 14px; }
  .mini-team { padding: 10px; border-radius: 12px; text-align: center; font-size: 12px; }
  .mini-a { background: rgba(59,130,246,0.15); border: 1px solid rgba(59,130,246,0.4); color: #93c5fd; }
  .mini-b { background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.4); color: #fca5a5; }
  .mini-team .players { font-size: 11px; margin-top: 4px; opacity: 0.85; }

  .answer-row { display: flex; align-items: center; gap: 10px; background: linear-gradient(135deg, rgba(30,41,59,0.7), rgba(15,23,42,0.5)); padding: 8px 14px; border-radius: 14px; border: 1.5px solid rgba(148,163,184,0.15); margin-bottom: 8px; }
  .answer-row .label { width: 82px; color: var(--gold); font-size: 13px; font-weight: bold; }
  .answer-row input { flex: 1; background: transparent; border: none; color: #fff; font-size: 15px; padding: 6px 4px; font-family: inherit; }
  .answer-row input:focus { outline: none; }

  .submit-bar { position: fixed; left: 16px; right: 16px; max-width: 520px; margin: 0 auto; bottom: calc(72px + env(safe-area-inset-bottom, 0px) + 8px); z-index: 50; }
  .stop-btn { width: 100%; padding: 16px; border-radius: 16px; border: none; font-family: inherit; font-weight: 900; font-size: 17px; cursor: pointer; color: #fff; background: linear-gradient(135deg, #ef4444, #b91c1c); box-shadow: 0 10px 30px rgba(239,68,68,0.5); }

  .waiting-box { text-align: center; padding: 40px 20px; background: var(--card); border: 2px dashed rgba(139,92,246,0.4); border-radius: 20px; margin-top: 20px; }
  .waiting-box .icon { font-size: 60px; margin-bottom: 12px; }
  .waiting-box h2 { font-size: 18px; color: #c4b5fd; margin-bottom: 8px; }
  .waiting-box p { color: var(--muted); font-size: 13px; line-height: 1.7; }
  .answers-grid { padding-bottom: 90px; }
</style>
{% endblock %}
{% block content %}
  <div class="team-header">
    <div class="letter-big">{{ round.letter }}</div>
    <div class="round-info">
      <div class="lbl">راند {{ round.number }} از ۳</div>
      <div class="title">بازی تیمی</div>
    </div>
    <div class="timer-big" id="timer">{{ duration }}</div>
  </div>

  <div class="teams-mini">
    <div class="mini-team mini-a">
      <div>🔵 تیم آبی {% if my_p.team == "A" %}(شما){% endif %}</div>
      <div class="players">
        {% for p in team_a_players %}
          {{ p.user.alias }}{% if p.stopped_round == round.number %} ✓{% endif %}{% if not forloop.last %} · {% endif %}
        {% endfor %}
      </div>
    </div>
    <div class="mini-team mini-b">
      <div>🔴 تیم قرمز {% if my_p.team == "B" %}(شما){% endif %}</div>
      <div class="players">
        {% for p in team_b_players %}
          {{ p.user.alias }}{% if p.stopped_round == round.number %} ✓{% endif %}{% if not forloop.last %} · {% endif %}
        {% endfor %}
      </div>
    </div>
  </div>

  {% if my_stopped %}
    <div class="waiting-box">
      <div class="icon">{% if teammate_stopped %}✅{% else %}⏳{% endif %}</div>
      <h2>{% if teammate_stopped %}تیم شما آماده!{% else %}منتظر هم‌تیمی...{% endif %}</h2>
      <p>{% if teammate_stopped %}وقتی تیم مقابل هم استوپ کرد، امتیازها حساب می‌شن.{% else %}شما استوپ زدی، حالا منتظر هم‌تیمی هستیم.{% endif %}</p>
    </div>
  {% else %}
    <form method="post" id="form">
      {% csrf_token %}
      <div class="answers-grid">
        {% for c in categories %}
          <div class="answer-row">
            <div class="label">{{ c }}</div>
            <input type="text" name="cat_{{ c }}" autocomplete="off" maxlength="64" placeholder="با {{ round.letter }} شروع شود...">
          </div>
        {% endfor %}
      </div>
      <div class="submit-bar">
        <button type="submit" class="stop-btn">✋ استوپ!</button>
      </div>
    </form>
  {% endif %}

<script>
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
</script>
{% endblock %}
'''
backup(p); write(p, TEAM_PLAY)

# ============================================================
# 12) team_round_end.html + team_result.html
# ============================================================
print("\n[12/12] team_round_end + team_result")
p = os.path.join(ROOT, "game", "templates", "game", "team_round_end.html")
ROUND_END = '''{% extends "base.html" %}
{% block title %}نتیجه راند {{ round.number }}{% endblock %}
{% block extra_css %}
<style>
  .score-hero { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
  .team-score { padding: 24px 16px; border-radius: 20px; text-align: center; }
  .team-score.a { background: radial-gradient(circle at 50% 0%, rgba(59,130,246,0.3), transparent 70%), linear-gradient(135deg, #0a1a2a, #0f0f1e); border: 2px solid rgba(59,130,246,0.5); }
  .team-score.b { background: radial-gradient(circle at 50% 0%, rgba(239,68,68,0.3), transparent 70%), linear-gradient(135deg, #2a0a0a, #0f0f1e); border: 2px solid rgba(239,68,68,0.5); }
  .team-score .lbl { font-size: 12px; color: var(--muted); margin-bottom: 6px; }
  .team-score.a .lbl { color: #93c5fd; }
  .team-score.b .lbl { color: #fca5a5; }
  .team-score .num { font-size: 44px; font-weight: 900; font-family: monospace; }
  .team-score.a .num { color: #60a5fa; }
  .team-score.b .num { color: #f87171; }
  .player-result { display: flex; align-items: center; gap: 12px; padding: 12px 14px; background: var(--card); border-radius: 14px; border: 1px solid var(--border); margin-bottom: 8px; }
  .player-result .av { font-size: 24px; }
  .player-result .info { flex: 1; }
  .player-result .name { font-size: 14px; font-weight: bold; color: #fff; }
  .player-result .team-tag { font-size: 10px; padding: 2px 8px; border-radius: 6px; margin-right: 6px; }
  .team-tag.a { background: rgba(59,130,246,0.2); color: #93c5fd; }
  .team-tag.b { background: rgba(239,68,68,0.2); color: #fca5a5; }
  .player-result .score { font-size: 18px; font-weight: bold; color: var(--gold); font-family: monospace; }
  .btn-next { width: 100%; margin-top: 20px; padding: 16px; border-radius: 16px; border: none; font-family: inherit; font-weight: 900; font-size: 16px; cursor: pointer; color: #1a1a1a; background: linear-gradient(135deg, #f4c542, #eab308); box-shadow: 0 10px 30px rgba(244,197,66,0.4); }
  .btn-next:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
{% endblock %}
{% block content %}
  <h1 style="text-align:center; margin-bottom:16px; font-size:20px;">نتیجه راند {{ round.number }}</h1>

  <div class="score-hero">
    <div class="team-score a"><div class="lbl">🔵 تیم آبی</div><div class="num">{{ team_scores.A }}</div></div>
    <div class="team-score b"><div class="lbl">🔴 تیم قرمز</div><div class="num">{{ team_scores.B }}</div></div>
  </div>

  {% for p in round_data %}
    <div class="player-result">
      <div class="av">{{ p.avatar }}</div>
      <div class="info">
        <div class="name">{{ p.user.alias }}
          <span class="team-tag {% if p.team == 'A' %}a{% else %}b{% endif %}">{% if p.team == 'A' %}آبی{% else %}قرمز{% endif %}</span>
        </div>
      </div>
      <div class="score">{{ p.round_score }}</div>
    </div>
  {% endfor %}

  <form method="post">
    {% csrf_token %}
    <input type="hidden" name="action" value="next_ready">
    {% if team_ready %}
      <button class="btn-next" disabled>✅ آماده‌ای، منتظر بقیه...</button>
    {% else %}
      <button type="submit" class="btn-next">{% if has_next %}▶️ راند بعدی{% else %}🏁 دیدن نتیجه نهایی{% endif %}</button>
    {% endif %}
  </form>

  <script>setTimeout(()=>window.location.reload(), 3000);</script>
{% endblock %}
'''
backup(p); write(p, ROUND_END)

p = os.path.join(ROOT, "game", "templates", "game", "team_result.html")
RESULT = '''{% extends "base.html" %}
{% block title %}نتیجه نهایی{% endblock %}
{% block extra_css %}
<style>
  .verdict { text-align: center; padding: 40px 20px; background: radial-gradient(circle at 50% 0%, rgba(244,197,66,0.2), transparent 70%), linear-gradient(135deg, #1a1a2e, #0f0f1e); border: 2px solid rgba(244,197,66,0.4); border-radius: 24px; margin-bottom: 20px; }
  .verdict .icon { font-size: 80px; margin-bottom: 12px; }
  .verdict h1 { font-size: 26px; font-weight: 900; background: linear-gradient(135deg, #fde68a, #f4c542, #ca8a04); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 16px; }
  .final-scores { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }
  .fs { padding: 20px 16px; border-radius: 16px; text-align: center; }
  .fs.a { background: rgba(59,130,246,0.15); border: 1px solid rgba(59,130,246,0.4); }
  .fs.b { background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.4); }
  .fs .lbl { font-size: 12px; margin-bottom: 4px; }
  .fs.a .lbl { color: #93c5fd; }
  .fs.b .lbl { color: #fca5a5; }
  .fs .num { font-size: 32px; font-weight: 900; font-family: monospace; color: #fff; }
  .rewards { text-align: center; padding: 16px; background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.3); border-radius: 16px; margin-bottom: 20px; color: #86efac; font-size: 14px; }
  .btn-home { display: block; width: 100%; padding: 16px; border-radius: 16px; text-align: center; text-decoration: none; color: #1a1a1a; font-weight: 900; font-size: 16px; background: linear-gradient(135deg, #f4c542, #eab308); box-shadow: 0 10px 30px rgba(244,197,66,0.4); }
</style>
{% endblock %}
{% block content %}
  <div class="verdict">
    <div class="icon">{% if winner == "tie" %}🤝{% else %}🏆{% endif %}</div>
    <h1>{% if winner == "tie" %}مساوی شد!{% else %}تیم {% if winner == "A" %}آبی{% else %}قرمز{% endif %} برنده شد!{% endif %}</h1>
    <div class="final-scores">
      <div class="fs a"><div class="lbl">🔵 آبی</div><div class="num">{{ total_a }}</div></div>
      <div class="fs b"><div class="lbl">🔴 قرمز</div><div class="num">{{ total_b }}</div></div>
    </div>
  </div>

  {% if winner != "tie" %}
    <div class="rewards">🎁 اعضای تیم برنده: +۵۰ سکه و +۵ جم</div>
  {% endif %}

  <a href="/game/" class="btn-home">🏠 بازگشت به خانه</a>
{% endblock %}
'''
backup(p); write(p, RESULT)

# ============================================================
# MIGRATIONS
# ============================================================
print("\n[Migrations] Running...")
for cmd in [
    [sys.executable, "manage.py", "makemigrations", "accounts", "game"],
    [sys.executable, "manage.py", "migrate"],
]:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd[1:])}")
    if r.stdout.strip(): print("   ", r.stdout.strip().replace("\n", "\n    ")[:500])
    if r.returncode != 0 and r.stderr.strip():
        print("   STDERR:", r.stderr.strip()[:500])

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Summary:
  1.  User.coins + User.gems (migration)
  2.  Player.team + team_ready + stopped_round (migration)
  3.  rooms.html: challenge removed, puzzle moved to bottom, speed 20s
  4.  Speed direct 30s -> 20s
  5.  menu.html: coin/gem HUD added
  6.  base.html: smooth nav fade + pulse
  7.  bot_play.html: pretty redesign
  8.  Team game 4-player: queue -> team select -> 3 rounds -> rewards
  9.  New templates: team_wait, team_select, team_play, team_round_end, team_result
  10. New routes under /game/team/*

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R

Test team game:
  - Click "بازی گروهی" in /game/rooms/
  - Opens 4 players needed (open 3 browsers/incognito)
  - Wait for all 4, then teams select
  - 2 per team, host starts
  - 3 rounds, winner team gets coins+gems
""")
