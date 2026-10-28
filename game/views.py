from django.contrib import messages
import random as _rand
from django.db import models
from django.db.models import Q
import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from datetime import timedelta
from django.utils import timezone

from accounts.avatars import get_emoji, get_avatar_html

from . import bot as bot_logic
from .bot_data import LETTER_DIFFICULTY

from .models import (
    DEFAULT_CATEGORIES, Answer, BotAnswer, Game, Player, Round,
)

def _avatar(user):
    from accounts.avatars import get_avatar_display
    _, val = get_avatar_display(user)
    return val

def _normalize(text):
    if not text:
        return ""
    t = text.strip().replace("\u200c", "").replace(" ", "")
    return t.replace("ي", "ی").replace("ك", "ک")



# ============================================================
# Helpers (Phase 0 cleanup)
# ============================================================

def _require_complete(user):
    if not user.is_authenticated:
        return redirect("landing")
    if not user.has_completed_registration or not user.has_chosen_avatar:
        return redirect("accounts:complete_registration")
    return None



# ============================================================
# CHAIN GAME — helpers (Phase 0 cleanup)
# ============================================================
import time as _time

_CHAIN_CATEGORIES = ["اسم", "فامیل", "میوه", "رنگ", "شهر", "کشور", "حیوان", "اشیاء", "غذا", "شغل"]
_CHAIN_SECONDS = 10
_CHAIN_LETTERS = list("اآبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی")


def _chain_norm(text):
    if not text:
        return ""
    return text.strip().replace("ي", "ی").replace("ك", "ک").replace("\u200c", "").replace(" ", "")


def _chain_last_letter(word):
    if not word:
        return ""
    return word.strip()[-1]


def _chain_starting_word(category):
    from .bot_data import words_for
    good_starts = []
    for letter in _CHAIN_LETTERS:
        for w in words_for(category, letter):
            last_l = w[-1]
            if len(words_for(category, last_l)) >= 2:
                good_starts.append(w)
    if good_starts:
        return _rand.choice(good_starts)
    for letter in _CHAIN_LETTERS:
        ws = words_for(category, letter)
        if ws:
            return _rand.choice(ws)
    return "علی"


def _chain_init(request, category, difficulty):
    start_word = _chain_starting_word(category)
    request.session["chain_game"] = {
        "category": category,
        "difficulty": difficulty,
        "last_word": start_word,
        "last_letter": _chain_last_letter(start_word),
        "history": [{"who": "start", "word": start_word}],
        "used_words": [start_word],
        "turn": "player",
        "player_score": 0,
        "bot_score": 0,
        "turn_deadline": int(_time.time()) + _CHAIN_SECONDS,
        "game_over": False,
        "winner": None,
    }



# ============================================================
# LEVEL / XP helpers
# ============================================================
def _xp_for_level(level):
    """XP لازم برای رسیدن به لول N.
    لول ۱ = ۰، لول ۲ = ۱۰۰، لول ۳ = ۳۰۰، لول ۴ = ۶۰۰، لول ۵ = ۱۰۰۰...
    فرمول: 50 * N * (N - 1)
    """
    if level <= 1:
        return 0
    return 50 * level * (level - 1)


def _level_from_xp(xp):
    """از XP → لول (بزرگ‌ترین N که 50*N*(N-1) <= xp)."""
    if xp < 0:
        xp = 0
    level = 1
    while _xp_for_level(level + 1) <= xp:
        level += 1
        if level > 999:
            break
    return level


def _level_progress(xp):
    """(لول فعلی، XP توی این لول، XP لازم برای لول بعد)."""
    lvl = _level_from_xp(xp)
    cur_threshold = _xp_for_level(lvl)
    next_threshold = _xp_for_level(lvl + 1)
    span = next_threshold - cur_threshold
    done = xp - cur_threshold
    return lvl, done, span


def _add_xp(user, amount):
    """XP اضافه می‌کنه + برمی‌گردونه (level_before, level_after)."""
    level_before = _level_from_xp(user.xp or 0)
    user.xp = (user.xp or 0) + max(0, int(amount))
    user.save(update_fields=["xp"])
    level_after = _level_from_xp(user.xp or 0)
    return level_before, level_after

@login_required
def home(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")
    from social.notifications import unread_count
    from django.db.models import Sum, Count

    # Get player stats
    from .models import Player
    my_players = Player.objects.filter(user=request.user)
    total_games = my_players.count()
    total_score = my_players.aggregate(t=Sum("score"))["t"] or 0
    level = 1 + total_score // 100
    level_progress = total_score % 100

    from .models import DailyRewardClaim
    daily_status = DailyRewardClaim.get_status(request.user)
    next_reward_amount = 0
    if daily_status["can_claim"]:
        idx = daily_status["next_day"] - 1
        if 0 <= idx < len(DailyRewardClaim.REWARDS):
            next_reward_amount = DailyRewardClaim.REWARDS[idx]
    daily_status["next_reward_amount"] = next_reward_amount

    return render(request, "game/menu.html", {
        "avatar_emoji": _avatar(request.user),
        "active": "home",
        "unread_notifications": unread_count(request.user),
        "level": level,
        "level_progress": level_progress,
        "stats": {
            "total_games": total_games,
            "total_score": total_score,
        },
        "daily_status": daily_status,
    })

@login_required
def rooms_list(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")
    my_rooms = Game.objects.filter(players__user=request.user).order_by("-created_at")[:5]
    return render(request, "game/rooms.html", {
        "categories": DEFAULT_CATEGORIES,
        "my_rooms": my_rooms,
        "active": "games",
    })

@login_required
def friends_page(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")
    return render(request, "game/coming_soon.html", {
        "icon": "👥",
        "title": "دوستان",
        "message": "این بخش به‌زودی فعال می‌شه.",
    })

@login_required
def quick_play(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")
    return redirect("game:bot_setup")

@login_required
def bot_setup(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    mode = request.GET.get("mode", "normal")
    is_speed = (mode == "speed")
    is_challenge = (mode == "challenge")

    # Direct speed mode - no setup, start immediately
    if is_speed and request.method == "GET":
        difficulty = "medium"
        selected = DEFAULT_CATEGORIES[:8]
        letter = bot_logic.bot_pick_letter(difficulty)
        game = Game.objects.create(
            host=request.user, status="in_round",
            categories=selected, mode="bot",
            difficulty=difficulty, letter_mode="random",
        )
        Player.objects.create(game=game, user=request.user)
        Round.objects.create(game=game, number=1, letter=letter, duration=20)
        return redirect("game:bot_play", game_id=game.id)

    if request.method == "POST":
        difficulty = request.POST.get("difficulty", "medium")
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"

        letter_mode = request.POST.get("letter_mode", "random")
        if letter_mode not in ("random", "player"):
            letter_mode = "random"

        selected = [c for c in request.POST.getlist("categories") if c in DEFAULT_CATEGORIES]
        if not selected:
            selected = DEFAULT_CATEGORIES

        if letter_mode == "player":
            letter = (request.POST.get("letter") or "").strip()[:2]
            if not letter:
                letter = bot_logic.bot_pick_letter(difficulty)
        else:
            if is_challenge:
                letter = random.choice(list("ثضظژذغ"))
            else:
                letter = bot_logic.bot_pick_letter(difficulty)

        if is_speed:
            base_time = 20
        else:
            base_time = {"easy": 150, "medium": 120, "hard": 90}[difficulty]
        letter_hardness = LETTER_DIFFICULTY.get(letter, 1)
        duration = base_time + (letter_hardness - 1) * 20

        game = Game.objects.create(
            host=request.user,
            status="in_round",
            categories=selected,
            mode="bot",
            difficulty=difficulty,
            letter_mode=letter_mode,
        )
        Player.objects.create(game=game, user=request.user)
        Round.objects.create(
            game=game,
            number=1,
            letter=letter,
            duration=duration,
        )
        return redirect("game:bot_play", game_id=game.id)

    # دسته‌های غیرمعمول که پیش‌فرض غیرفعالن
    unusual_cats = ["فیلم", "برند", "ورزش", "ابزار", "لباس", "کتاب", "مکان", "گیاه", "بیماری"]
    
    # خوندن تنظیمات کاربر
    user_settings = request.user.settings_json or {}
    # اگه کاربر تنظیمات ذخیره نکرده باشه، اینا پیش‌فرض غیرفعال میشن
    if "excluded_categories" not in user_settings:
        excluded = unusual_cats
    else:
        excluded = user_settings.get("excluded_categories", [])

    main_cats = ["اسم", "فامیل", "میوه", "رنگ", "شهر", "کشور", "ماشین", "حیوان", "اشیا", "غذا", "شغل", "اعضای بدن"]
    
    active_main = [c for c in main_cats if c not in excluded]
    active_extra = [c for c in unusual_cats if c not in excluded]

    return render(request, "game/bot_setup.html", {
        "active_main": active_main,
        "active_extra": active_extra,
        "excluded_categories": excluded,
    })

@login_required
def bot_play(request, game_id):
    game = Game.objects.filter(id=game_id, host=request.user, mode="bot").first()
    if not game:
        return redirect("game:home")
    round_obj = game.rounds.order_by("-number").first()
    if not round_obj:
        return redirect("game:home")
    return render(request, "game/bot_play.html", {
        "game": game,
        "round": round_obj,
        "categories": game.categories,
        "duration": round_obj.duration,
    })

@login_required
def bot_submit(request, game_id):
    game = Game.objects.filter(id=game_id, host=request.user, mode="bot").first()
    if not game:
        return redirect("game:home")
    round_obj = game.rounds.order_by("-number").first()
    if not round_obj or round_obj.stopped_at:
        return redirect("game:home")

    round_obj.stopped_at = timezone.now()
    round_obj.stopper = request.user
    round_obj.save(update_fields=["stopped_at", "stopper"])

    from .bot_data import is_valid_word

    player_answers = []
    for cat in game.categories:
        raw = (request.POST.get(f"cat_{cat}") or "").strip()[:64]
        norm = _normalize(raw)
        score = 0
        reason = ""
        
        if not raw:
            reason = "خالی"
        elif not norm or norm[0] != round_obj.letter:
            reason = "پاسخ اشتباه"
        elif cat in ("اسم", "فامیل"):
            # برای اسم و فامیل فقط حرف اول کافیه
            score = 10
            reason = "صحیح"
        elif not is_valid_word(norm, cat, round_obj.letter):
            reason = "پاسخ اشتباه"
        else:
            score = 10
            reason = "صحیح"
        
        Answer.objects.update_or_create(
            round=round_obj, user=request.user, category=cat,
            defaults={"value": raw, "normalized": norm, "score": score},
        )
        player_answers.append({
            "category": cat,
            "value": raw or "—",
            "normalized": norm,
            "score": score,
            "reason": reason,
        })

    bot_raw, _ = bot_logic.bot_answers_for_round(
        game.categories, round_obj.letter, game.difficulty, round_obj.duration
    )
    bot_answers = []
    for cat in game.categories:
        w = bot_raw.get(cat, "")
        norm = _normalize(w)
        score = 10 if (norm and norm[0] == round_obj.letter) else 0
        BotAnswer.objects.update_or_create(
            round=round_obj, category=cat,
            defaults={"value": w, "normalized": norm, "score": score},
        )
        bot_answers.append({
            "category": cat,
            "value": w or "—",
            "normalized": norm,
            "score": score,
        })

    for i, cat in enumerate(game.categories):
        p_norm = player_answers[i]["normalized"]
        b_norm = bot_answers[i]["normalized"]
        if p_norm and b_norm and p_norm == b_norm:
            player_answers[i]["score"] = 5
            bot_answers[i]["score"] = 5

    player_total = sum(a["score"] for a in player_answers)
    bot_total = sum(a["score"] for a in bot_answers)

    if player_total > bot_total:
        winner = "player"
    elif bot_total > player_total:
        winner = "bot"
    else:
        winner = "tie"

    p = game.players.get(user=request.user)
    p.score += player_total
    p.save(update_fields=["score"])

    return render(request, "game/bot_result.html", {
        "game": game,
        "round": round_obj,
        "categories": game.categories,
        "player_answers": player_answers,
        "bot_answers": bot_answers,
        "player_total": player_total,
        "bot_total": bot_total,
        "winner": winner,
    })

@login_required
def leaderboard_view(request):
    check = _require_complete(request.user)
    if check:
        return check

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start.replace(day=1)

    def _top(period_start, limit=10):
        rows = (
            Player.objects
            .filter(game__created_at__gte=period_start)
            .values("user_id")
            .annotate(total=Sum("score"), games=Count("id"))
            .order_by("-total")[:limit]
        )
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_ids = [r["user_id"] for r in rows]
        users_map = {u.id: u for u in User.objects.filter(id__in=user_ids)}

        result = []
        for idx, r in enumerate(rows, start=1):
            u = users_map.get(r["user_id"])
            if not u:
                continue
            result.append({
                "rank": idx,
                "user": u,
                "avatar": get_avatar_html(u),
                "alias": u.alias,
                "total": r["total"] or 0,
                "games": r["games"],
            })
        return result

    daily = _top(today_start)
    weekly = _top(week_start)
    monthly = _top(month_start)

    # رتبه شخصی
    def _my_rank(period_start):
        my_total = (
            Player.objects
            .filter(user=request.user, game__created_at__gte=period_start)
            .aggregate(t=Sum("score"))["t"] or 0
        )
        if my_total == 0:
            return {"total": 0, "rank": "—", "games": 0}

        my_games = Player.objects.filter(
            user=request.user, game__created_at__gte=period_start
        ).count()

        # چند نفر امتیاز بیشتری دارن؟
        better = (
            Player.objects
            .filter(game__created_at__gte=period_start)
            .values("user_id")
            .annotate(t=Sum("score"))
            .filter(t__gt=my_total)
            .count()
        )
        return {"total": my_total, "rank": better + 1, "games": my_games}

    my_daily = _my_rank(today_start)
    my_weekly = _my_rank(week_start)
    my_monthly = _my_rank(month_start)

    return render(request, "game/leaderboard.html", {
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "my_daily": my_daily,
        "my_weekly": my_weekly,
        "my_monthly": my_monthly,
        "my_avatar": _avatar(request.user),
        "my_alias": request.user.alias,
        "active": "leaderboard",
    })

@login_required
def top_players_view(request):
    """بازیکنان برتر همه دوران."""
    from django.contrib.auth import get_user_model
    from django.db.models import Count, Sum

    User = get_user_model()
    top = (
        Player.objects
        .values("user_id")
        .annotate(total=Sum("score"), games=Count("id"))
        .order_by("-total")[:30]
    )

    ids = [t["user_id"] for t in top]
    users = {u.id: u for u in User.objects.filter(id__in=ids)}

    result = []
    for i, t in enumerate(top, 1):
        u = users.get(t["user_id"])
        if not u:
            continue
        result.append({
            "rank": i,
            "user": u,
            "avatar": get_avatar_html(u),
            "avatar_type": getattr(u, "avatar_type", "emoji"),
            "avatar_id": u.avatar_id,
            "alias": u.alias,
            "total": t["total"] or 0,
            "games": t["games"],
            "level": 1 + (t["total"] or 0) // 100,
        })

    return render(request, "game/top_players.html", {
        "players": result,
        "active": "leaderboard",
    })

# ============================================================
# Matchmaking — بازی با پلیر رندم
# ============================================================

@login_required
def rooms_manage(request):
    check = _require_complete(request.user)
    if check:
        return check

    query = (request.GET.get("q") or "").strip()
    active_rooms = Game.objects.filter(status="waiting", mode="group").order_by("-created_at")

    if query:
        active_rooms = active_rooms.filter(
            Q(room_name__icontains=query) | Q(host__alias__icontains=query)
        )

    rooms_data = []
    for r in active_rooms:
        count = r.players.count()
        is_member = r.players.filter(user=request.user).exists()
        rooms_data.append({
            "obj": r,
            "count": count,
            "is_full": count >= r.max_players,
            "has_password": bool(r.password),
            "is_member": is_member,
            "host_avatar": get_emoji(r.host.avatar_id),
            "game_type": r.intended_game_type or "—",
        })

    if request.method == "POST":
        room_name = (request.POST.get("room_name") or "").strip()[:50] or "اتاق بازی"
        password = (request.POST.get("password") or "").strip()[:32]
        try:
            max_players = int(request.POST.get("max_players") or 8)
        except (ValueError, TypeError):
            max_players = 8
        max_players = max(2, min(15, max_players))

        game_type = request.POST.get("game_type", "player")
        valid_types = ["player", "team", "challenge", "speed", "bot", "puzzle"]
        if game_type not in valid_types:
            game_type = "player"

        selected = [c for c in request.POST.getlist("categories") if c in DEFAULT_CATEGORIES]
        if not selected:
            selected = DEFAULT_CATEGORIES[:8]

        game = Game.objects.create(
            host=request.user, status="waiting",
            categories=selected, mode="group", password=password,
            room_name=room_name, max_players=max_players,
            intended_game_type=game_type,
        )
        Player.objects.create(game=game, user=request.user)
        return redirect("game:room", room_code=game.code)

    return render(request, "game/rooms_manage.html", {
        "categories": DEFAULT_CATEGORIES,
        "rooms": rooms_data,
        "query": query,
        "active": "rooms",
        "game_types": [
            ("player", "⚔️ با پلیر (۱v۱)"),
            ("challenge", "🔥 چالشی"),
            ("speed", "⏱️ سرعتی"),
            ("puzzle", "🎯 معما"),
            ("bot", "🤖 با بات"),
        ],
    })

@login_required
def join_room(request, room_code):
    check = _require_complete(request.user)
    if check:
        return check

    room_obj = Game.objects.filter(code=room_code).first()
    if not room_obj:
        return redirect("game:rooms_manage")

    is_member = room_obj.players.filter(user=request.user).exists()
    if not is_member and room_obj.players.count() >= room_obj.max_players:
        return render(request, "game/rooms_manage.html", {
            "categories": DEFAULT_CATEGORIES,
            "rooms": [],
            "error": "ظرفیت این اتاق پر شده است.",
            "query": "",
            "active": "rooms",
        })

    if request.method == "POST":
        password = (request.POST.get("password") or "").strip()
        if room_obj.password and room_obj.password != password:
            return render(request, "game/room_password.html", {
                "room": room_obj,
                "error": "رمز عبور اشتباه است.",
                "active": "rooms",
            })
        Player.objects.get_or_create(game=room_obj, user=request.user)
        return redirect("game:room", room_code=room_obj.code)

    if room_obj.password and not is_member:
        return render(request, "game/room_password.html", {
            "room": room_obj,
            "active": "rooms",
        })

    Player.objects.get_or_create(game=room_obj, user=request.user)
    return redirect("game:room", room_code=room_obj.code)

@login_required
def room(request, room_code):
    check = _require_complete(request.user)
    if check:
        return check

    room_obj = Game.objects.filter(code=room_code).first()
    if not room_obj:
        return redirect("game:rooms_manage")

    Player.objects.get_or_create(game=room_obj, user=request.user)

    players = []
    my_is_ready = False
    for p in room_obj.players.select_related("user"):
        if p.user_id == request.user.id:
            my_is_ready = p.is_ready
        players.append({
            "user_id": p.user.id,
            "alias": p.user.alias,
            "avatar": get_avatar_html(p.user),
            "avatar_type": getattr(p.user, "avatar_type", "emoji"),
            "avatar_id": p.user.avatar_id,
            "is_ready": p.is_ready,
            "score": p.score,
            "is_host": p.user_id == room_obj.host_id,
        })

    is_host = room_obj.host_id == request.user.id

    return render(request, "game/room.html", {
        "room": room_obj,
        "categories": room_obj.categories,
        "players": players,
        "is_host": is_host,
        "my_is_ready": my_is_ready,
        "host": room_obj.host,
        "host_avatar": get_emoji(room_obj.host.avatar_id),
        "active": "rooms",
    })

@login_required
def leave_room(request, room_code):
    check = _require_complete(request.user)
    if check:
        return check

    if request.method != "POST":
        return redirect("game:room", room_code=room_code)

    room_obj = Game.objects.filter(code=room_code).first()
    if not room_obj:
        return redirect("game:rooms_manage")

    is_host = room_obj.host_id == request.user.id

    if is_host:
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"game_{room_obj.id}",
                {"type": "ev.room_closed"}
            )
        except Exception:
            pass
        room_obj.players.all().delete()
        room_obj.delete()
    else:
        room_obj.players.filter(user=request.user).delete()

    return redirect("game:rooms_manage")

import random as _random

@login_required
def challenge_home(request):
    check = _require_complete(request.user)
    if check:
        return check

    from django.utils import timezone
    try:
        from .models import Tournament, TournamentEntry
    except ImportError:
        return render(request, "game/challenge.html", {
            "weekly": [], "daily": [], "hourly": [], "active": "games",
        })

    now = timezone.now()
    Tournament.objects.filter(end_at__lt=now, status__in=["scheduled", "active"]).update(status="finished")

    def _list(t_type):
        qs = Tournament.objects.filter(tournament_type=t_type).order_by("-start_at")[:10]
        out = []
        for x in qs:
            is_joined = TournamentEntry.objects.filter(tournament=x, user=request.user).exists()
            out.append({
                "id": x.id,
                "name": x.name,
                "icon": x.icon,
                "description": x.description,
                "tournament_type": x.tournament_type,
                "status": x.status,
                "get_status_display": x.get_status_display(),
                "start_at": x.start_at,
                "end_at": x.end_at,
                "start_at_ts": int(x.start_at.timestamp()),
                "end_at_ts": int(x.end_at.timestamp()),
                "entry_count": x.entry_count(),
                "max_players": x.max_players,
                "prize_coins": x.prize_coins,
                "prize_gems": x.prize_gems,
                "entry_fee_coins": x.entry_fee_coins,
                "is_live": x.is_live,
                "is_finished": x.is_finished,
                "is_upcoming": x.is_upcoming,
                "is_joined": is_joined,
            })
        return out

    return render(request, "game/challenge.html", {
        "weekly": _list("weekly"),
        "daily": _list("daily"),
        "hourly": _list("hourly"),
        "active": "games",
    })

@login_required
def tournament_join(request, tournament_id):
    check = _require_complete(request.user)
    if check:
        return check

    from django.utils import timezone
    from .models import Tournament, TournamentEntry
    from django.contrib import messages

    t = Tournament.objects.filter(id=tournament_id).first()
    if not t:
        messages.error(request, "تورنمنت پیدا نشد.")
        return redirect("game:challenge")

    if not t.is_live:
        messages.error(request, "این تورنمنت در حال برگزاری نیست.")
        return redirect("game:challenge")

    if t.entry_count() >= t.max_players:
        messages.error(request, "ظرفیت پر شده.")
        return redirect("game:challenge")

    if TournamentEntry.objects.filter(tournament=t, user=request.user).exists():
        messages.info(request, "قبلاً ثبت‌نام کردی.")
        return redirect("game:challenge")

    if t.entry_fee_coins and (request.user.coins or 0) < t.entry_fee_coins:
        messages.error(request, f"سکه کافی نداری (نیاز: {t.entry_fee_coins}).")
        return redirect("game:challenge")

    if t.entry_fee_gems and (request.user.gems or 0) < t.entry_fee_gems:
        messages.error(request, f"جم کافی نداری (نیاز: {t.entry_fee_gems}).")
        return redirect("game:challenge")

    if t.entry_fee_coins:
        request.user.coins -= t.entry_fee_coins
    if t.entry_fee_gems:
        request.user.gems -= t.entry_fee_gems
    if t.entry_fee_coins or t.entry_fee_gems:
        request.user.save(update_fields=["coins", "gems"])

    TournamentEntry.objects.create(tournament=t, user=request.user)
    messages.success(request, f"در تورنمنت «{t.name}» ثبت‌نام کردی!")
    return redirect("game:challenge")

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

# ============================================================
# PUZZLE GAME
# ============================================================

# ============================================================
# MEMORY GAME
# ============================================================

# ============================================================
# GUESS GAME (0-100)
# ============================================================

# ============================================================
# PUZZLE GAME
# ============================================================
@login_required
def puzzle_home(request):
    check = _require_complete(request.user)
    if check:
        return check
    from game.puzzle_words import get_puzzle_words
    import time

    if request.method == "POST" and request.POST.get("action") == "new":
        request.session.pop("puzzle_items", None)

    if "puzzle_items" not in request.session or request.session.get("puzzle_finished"):
        pool = get_puzzle_words()
        picks = _rand.sample(pool, min(5, len(pool)))
        items = []
        total_time = 0
        for i, w in enumerate(picks):
            sec = len(w) * 5
            total_time += sec
            letters = list(w)
            for _ in range(30):
                _rand.shuffle(letters)
                if "".join(letters) != w:
                    break
            items.append({"idx": i, "word": w, "scrambled": " ".join(letters), "length": len(w), "seconds": sec})
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
        return render(request, "game/puzzle.html", {"finished": True, "score": request.session.get("puzzle_score", 0), "total": len(items), "active": "games"})

    return render(request, "game/puzzle.html", {"items": items, "total": len(items), "remaining": remaining, "total_time": total_time, "finished": False, "active": "games"})

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
        ans = (request.POST.get(f"ans_{it['idx']}") or "").strip().replace("ي","ی").replace("ك","ک").replace(" ","").replace("\u200c","")
        target = it["word"].replace("ي","ی").replace("ك","ک").replace(" ","").replace("\u200c","")
        if ans == target:
            correct += 1
    request.session["puzzle_score"] = correct * 10
    request.session["puzzle_finished"] = True
    messages.success(request, f"🎯 {correct} از {len(items)} درست!")
    return redirect("game:puzzle")

# ============================================================
# MEMORY GAME
# ============================================================
_MEMORY_EMOJIS = ["🐶","🐱","🦁","🐯","🐻","🐼","🐨","🐸","🦊","🐵","🦄","🐲","🐔","🐧","🦋","🐝","🐞","🦉","🦅","🐢","🐙","🦀","🦈","🐬","🐘","🦒","🦓","🦔","🐰","🐹"]

@login_required
def memory_home(request):
    check = _require_complete(request.user)
    if check:
        return check

    difficulty = request.GET.get("diff", "")
    if difficulty not in ("easy", "medium", "hard"):
        # Show difficulty selection
        return render(request, "game/memory_select.html", {"active": "games"})

    if difficulty == "easy":
        pairs = 6
    elif difficulty == "medium":
        pairs = 10
    else:
        pairs = 15

    if request.method == "POST" and request.POST.get("action") == "new":
        request.session.pop("memory_cards", None)

    expected = pairs * 2
    cards = request.session.get("memory_cards", [])
    if not cards or len(cards) != expected:
        emojis = _rand.sample(_MEMORY_EMOJIS, pairs)
        cards_raw = emojis * 2
        _rand.shuffle(cards_raw)
        cards = [{"id": i, "emoji": em, "flipped": False, "matched": False}
                 for i, em in enumerate(cards_raw)]
        request.session["memory_cards"] = cards

    return render(request, "game/memory.html", {
        "cards": cards, "total_pairs": pairs,
        "difficulty": difficulty, "active": "games",
    })

@login_required
def memory_select(request):
    check = _require_complete(request.user)
    if check:
        return check
    return render(request, "game/memory_select.html", {"active": "games"})

@login_required
def chain_setup(request):
    check = _require_complete(request.user)
    if check:
        return check
    if request.method == "POST":
        category = request.POST.get("category", "اسم")
        difficulty = request.POST.get("difficulty", "medium")
        if category not in _CHAIN_CATEGORIES:
            category = "اسم"
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"
        _chain_init(request, category, difficulty)
        return redirect("game:chain_play")
    return render(request, "game/chain_setup.html", {
        "categories": _CHAIN_CATEGORIES,
        "active": "games",
    })

@login_required
def chain_play(request):
    check = _require_complete(request.user)
    if check:
        return check

    game = request.session.get("chain_game")
    if not game:
        return redirect("game:chain_setup")

    if game.get("game_over"):
        return render(request, "game/chain.html", {
            "game": game, "remaining": 0, "game_over": True, "active": "games",
        })

    now = int(_time.time())

    # Bot's turn
    if game["turn"] == "bot":
        from .bot_data import words_for
        required_letter = game["last_letter"]
        category = game["category"]
        difficulty = game["difficulty"]

        candidates = words_for(category, required_letter)
        used_norm = set(_chain_norm(w) for w in game["used_words"])
        candidates = [w for w in candidates if _chain_norm(w) not in used_norm]

        fail_rate = {"easy": 0.35, "medium": 0.15, "hard": 0.05}.get(difficulty, 0.15)
        if not candidates or _rand.random() < fail_rate:
            game["game_over"] = True
            game["winner"] = "player"
            game["history"].append({"who": "bot", "word": "❌"})
        else:
            answer = _rand.choice(candidates)
            game["bot_score"] += 10
            game["last_word"] = answer
            game["last_letter"] = _chain_last_letter(answer)
            game["history"].append({"who": "bot", "word": answer})
            game["used_words"].append(answer)
            game["turn"] = "player"
            game["turn_deadline"] = int(_time.time()) + _CHAIN_SECONDS
        request.session["chain_game"] = game
        return redirect("game:chain_play")

    # Player's turn
    if now > game["turn_deadline"] + 3:
        game["game_over"] = True
        game["winner"] = "bot"
        request.session["chain_game"] = game
        messages.error(request, "⏰ زمان تمام شد! بات برد.")
        return redirect("game:chain_play")

    if request.method == "POST":
        answer = (request.POST.get("answer") or "").strip()
        if not answer:
            game["game_over"] = True
            game["winner"] = "bot"
            request.session["chain_game"] = game
            messages.error(request, "⏰ زمان تمام شد! بات برد.")
            return redirect("game:chain_play")

        if now > game["turn_deadline"] + 5:
            game["game_over"] = True
            game["winner"] = "bot"
            request.session["chain_game"] = game
            messages.error(request, "⏰ دیر رسید! بات برد.")
            return redirect("game:chain_play")

        norm = _chain_norm(answer)
        required = _chain_norm(game["last_letter"])
        if not norm or norm[0] != required:
            messages.error(request, f"پاسخ باید با «{game['last_letter']}» شروع بشه.")
            return redirect("game:chain_play")

        used_norm = set(_chain_norm(w) for w in game["used_words"])
        if norm in used_norm:
            messages.error(request, "این کلمه قبلاً استفاده شده.")
            return redirect("game:chain_play")

        game["player_score"] += 10
        game["last_word"] = answer
        game["last_letter"] = _chain_last_letter(answer)
        game["history"].append({"who": "player", "word": answer})
        game["used_words"].append(answer)
        game["turn"] = "bot"
        request.session["chain_game"] = game
        messages.success(request, f"✅ «{answer}» ثبت شد.")
        return redirect("game:chain_play")

    remaining = max(0, game["turn_deadline"] - now)
    return render(request, "game/chain.html", {
        "game": game, "remaining": remaining, "game_over": False, "active": "games",
    })

@login_required
def chain_reset(request):
    check = _require_complete(request.user)
    if check:
        return check
    request.session.pop("chain_game", None)
    return redirect("game:chain_setup")

# ============================================================
# CHAIN LIVE — با بازیکن واقعی
# ============================================================
import time as _time2

_CHAIN_LIVE_SECONDS = 15

def _chain_live_norm(text):
    if not text:
        return ""
    return text.strip().replace("ي", "ی").replace("ك", "ک").replace("\u200c", "").replace(" ", "")

def _chain_live_valid(word, category, letter):
    """Check if word exists in bot_data for this category and starts with letter."""
    from .bot_data import words_for
    if not word or not letter:
        return False
    w = _chain_live_norm(word)
    l = _chain_live_norm(letter)
    if not w or not l:
        return False
    if w[0] != l:
        return False
    candidates = words_for(category, letter)
    norm_candidates = [_chain_live_norm(c) for c in candidates]
    return w in norm_candidates

@login_required
def chain_live_start(request):
    check = _require_complete(request.user)
    if check:
        return check
    from .models import MatchQueue, Game, Player, Round
    MatchQueue.objects.filter(user=request.user).delete()
    MatchQueue.objects.create(user=request.user, mode="chain")
    return redirect("game:chain_live_wait")

@login_required
def chain_live_wait(request):
    check = _require_complete(request.user)
    if check:
        return check
    from .models import MatchQueue, Game, Player
    import random

    my_q = MatchQueue.objects.filter(user=request.user, mode="chain").first()
    if not my_q:
        return redirect("game:chain_live_start")

    opponent_q = MatchQueue.objects.filter(
        mode="chain", joined_at__lt=my_q.joined_at
    ).exclude(user=request.user).first()

    if opponent_q:
        opponent = opponent_q.user
        MatchQueue.objects.filter(user__in=[request.user, opponent]).delete()

        category = _rand.choice(_CHAIN_CATEGORIES)
        # Pick starting word with valid follow-up
        from .bot_data import words_for
        good_words = []
        for letter in _CHAIN_LETTERS:
            for w in words_for(category, letter):
                last_l = w[-1]
                if len(words_for(category, last_l)) >= 2:
                    good_words.append(w)
        if not good_words:
            for letter in _CHAIN_LETTERS:
                ws = words_for(category, letter)
                if ws:
                    good_words.extend(ws[:3])
        start_word = _rand.choice(good_words) if good_words else "علی"

        game = Game.objects.create(
            host=request.user, status="in_round",
            categories=[category], mode="chain",
            difficulty="medium", letter_mode="random",
        )
        Player.objects.create(game=game, user=request.user)
        Player.objects.create(game=game, user=opponent)

        request.session["chain_live"] = {
            "game_id": str(game.id),
            "category": category,
            "last_word": start_word,
            "last_letter": start_word[-1],
            "used": [start_word],
            "turn_user_id": request.user.id,
            "turn_deadline": int(_time2.time()) + _CHAIN_LIVE_SECONDS,
            "history": [{"who": "start", "word": start_word}],
            "finished": False,
            "winner_user_id": None,
        }
        return redirect("game:chain_live_play", room_code=game.code)

    return render(request, "game/chain_live_wait.html", {"active": "games"})

@login_required
def chain_live_cancel(request):
    from .models import MatchQueue
    MatchQueue.objects.filter(user=request.user).delete()
    return redirect("game:rooms")

@login_required
def chain_live_status(request):
    from .models import MatchQueue, Game
    from django.http import JsonResponse
    my_q = MatchQueue.objects.filter(user=request.user, mode="chain").first()
    if not my_q:
        g = Game.objects.filter(players__user=request.user, mode="chain").order_by("-created_at").first()
        if g and g.status != "finished":
            return JsonResponse({"status": "matched", "url": f"/game/chain-live/{g.code}/"})
        return JsonResponse({"status": "cancelled"})
    return JsonResponse({"status": "waiting", "count": MatchQueue.objects.filter(mode="chain").count()})

@login_required
def chain_live_play(request, room_code):
    check = _require_complete(request.user)
    if check:
        return check
    from .models import Game, Player

    game = Game.objects.filter(code=room_code, mode="chain").first()
    if not game:
        return redirect("game:rooms")

    my_p = Player.objects.filter(game=game, user=request.user).first()
    if not my_p:
        return redirect("game:rooms")

    state = request.session.get("chain_live")
    if not state or state.get("game_id") != str(game.id):
        return redirect("game:rooms")

    if request.method == "POST" and not state.get("finished"):
        action = request.POST.get("action", "answer")
        if action == "answer":
            if state["turn_user_id"] != request.user.id:
                messages.error(request, "نوبت شما نیست!")
                return redirect("game:chain_live_play", room_code=game.code)

            answer = (request.POST.get("answer") or "").strip()
            category = state["category"]
            required = state["last_letter"]

            if _time2.time() > state["turn_deadline"] + 3:
                state["finished"] = True
                state["winner_user_id"] = None
                messages.error(request, "⏰ زمان تمام شد!")
            elif not answer:
                state["finished"] = True
                state["winner_user_id"] = None
                messages.error(request, "زمان تمام شد!")
            elif _chain_live_norm(answer)[:1] != _chain_live_norm(required):
                messages.error(request, f"پاسخ باید با «{required}» شروع بشه.")
                return redirect("game:chain_live_play", room_code=game.code)
            elif _chain_live_norm(answer) in [_chain_live_norm(w) for w in state["used"]]:
                messages.error(request, "این کلمه قبلا استفاده شده.")
                return redirect("game:chain_live_play", room_code=game.code)
            elif not _chain_live_valid(answer, category, required):
                messages.error(request, "❌ همچین کلمه‌ای وجود ندارد!")
                return redirect("game:chain_live_play", room_code=game.code)
            else:
                state["last_word"] = answer
                state["last_letter"] = answer[-1]
                state["used"].append(answer)
                state["history"].append({"who": request.user.id, "word": answer})
                other = Player.objects.filter(game=game).exclude(user=request.user).first()
                state["turn_user_id"] = other.user.id if other else request.user.id
                state["turn_deadline"] = int(_time2.time()) + _CHAIN_LIVE_SECONDS
                messages.success(request, f"✅ «{answer}» ثبت شد.")
                request.session["chain_live"] = state
                return redirect("game:chain_live_play", room_code=game.code)

        elif action == "forfeit":
            state["finished"] = True
            state["winner_user_id"] = None
            messages.info(request, "بازی را رها کردی.")
            request.session["chain_live"] = state
            return redirect("game:chain_live_play", room_code=game.code)

        request.session["chain_live"] = state

    remaining = max(0, state["turn_deadline"] - int(_time2.time()))
    players = Player.objects.filter(game=game).select_related("user")
    is_my_turn = state["turn_user_id"] == request.user.id
    return render(request, "game/chain_live.html", {
        "game": game,
        "state": state,
        "players": players,
        "is_my_turn": is_my_turn,
        "remaining": remaining,
        "finished": state.get("finished", False),
        "active": "games",
    })

# ============================================================
# DAILY REWARD
# ============================================================

# ============================================================
# DAILY REWARD (7-day streak)
# ============================================================
@login_required
def daily_reward(request):
    check = _require_complete(request.user)
    if check:
        return check
    from .models import DailyRewardClaim

    if request.method == "POST":
        ok, msg, amount = DailyRewardClaim.claim(request.user)
        if ok:
            messages.success(request, msg)
        else:
            messages.warning(request, msg)
        return redirect("game:daily_reward")

    status = DailyRewardClaim.get_status(request.user)
    next_amount = 0
    if status["can_claim"]:
        idx = status["next_day"] - 1
        if 0 <= idx < len(DailyRewardClaim.REWARDS):
            next_amount = DailyRewardClaim.REWARDS[idx]
    return render(request, "game/daily_reward.html", {
        "status": status,
        "rewards": DailyRewardClaim.REWARDS,
        "next_amount": next_amount,
        "active": "home",
    })


# ============================================================
# ONLINE — Matchmaking + بازی آنلاین
# ============================================================
import random as _online_random
import time as _online_time
from django.utils import timezone as _online_tz

_REWARD_WIN = 100
_REWARD_LOSS = 10
_REWARD_TIE = 50

_ONLINE_DURATION = 90  # ثانیه برای راند اسم فامیل


def _build_1v1_payload():
    """محتوای مشترک یه بازی ۱v۱ اسم فامیل."""
    cats = ["اسم", "فامیل", "میوه", "رنگ", "شهر", "کشور", "ماشین", "حیوان", "اشیاء", "غذا"]
    letter = _online_random.choice(list("ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"))
    return {
        "categories": cats,
        "letter": letter,
        "duration": _ONLINE_DURATION,
        "started_at": _online_tz.now().timestamp(),
    }


@login_required
def match_start(request):
    """ورود به صف انتظار برای اسم فامیل آنلاین."""
    check = _require_complete(request.user)
    if check:
        return check

    from .models import MatchQueue, OnlineGame, OnlinePlayer

    # اگه این کاربر تو یه بازی فعال هست، برگردونش
    active = (
        OnlinePlayer.objects
        .filter(user=request.user, game__mode="1v1", game__status__in=["waiting", "playing"])
        .select_related("game")
        .order_by("-game__created_at")
        .first()
    )
    if active:
        return redirect("game:online_1v1", game_id=str(active.game.id))

    # حذف از صف قبلی (هر مودی)
    MatchQueue.objects.filter(user=request.user).delete()
    MatchQueue.objects.create(user=request.user, mode="1v1")

    return redirect("game:match_wait")


@login_required
def match_wait(request):
    """صفحه انتظار — وقتی دو نفر هستن، بازی ساخته می‌شه."""
    check = _require_complete(request.user)
    if check:
        return check

    from .models import MatchQueue, OnlineGame, OnlinePlayer

    # کاربر باید تو صف باشه
    my_queue = MatchQueue.objects.filter(user=request.user, mode="1v1").first()
    if not my_queue:
        # شاید تو بازی فعال هست
        active = (
            OnlinePlayer.objects
            .filter(user=request.user, game__mode="1v1", game__status__in=["waiting", "playing"])
            .select_related("game")
            .order_by("-game__created_at")
            .first()
        )
        if active:
            return redirect("game:online_1v1", game_id=str(active.game.id))
        return redirect("game:rooms")

    # حریف؟
    opponent_q = (
        MatchQueue.objects
        .filter(mode="1v1", joined_at__lt=my_queue.joined_at)
        .exclude(user=request.user)
        .order_by("joined_at")
        .first()
    )

    if opponent_q:
        opponent = opponent_q.user
        # پاک کردن هر دو از صف
        MatchQueue.objects.filter(user__in=[request.user, opponent]).delete()

        # ساخت OnlineGame
        game = OnlineGame.objects.create(
            mode="1v1",
            status="playing",
            payload=_build_1v1_payload(),
        )
        OnlinePlayer.objects.create(game=game, user=request.user)
        OnlinePlayer.objects.create(game=game, user=opponent)

        # اعلان به هر دو
        try:
            from social.notifications import notify
            notify(request.user, "game_invite", "بازی پیدا شد!",
                   f"حریف: {opponent.alias}", f"/game/online/{game.id}/")
            notify(opponent, "game_invite", "بازی پیدا شد!",
                   f"حریف: {request.user.alias}", f"/game/online/{game.id}/")
        except Exception:
            pass

        return redirect("game:online_1v1", game_id=str(game.id))

    return render(request, "game/match_wait.html", {
        "active": "games",
        "queue_count": MatchQueue.objects.filter(mode="1v1").count(),
    })


@login_required
def match_cancel(request):
    from .models import MatchQueue
    MatchQueue.objects.filter(user=request.user).delete()
    return redirect("game:rooms")


@login_required
def match_status(request):
    """AJAX polling وضعیت صف/بازی."""
    from django.http import JsonResponse
    from .models import MatchQueue, OnlineGame, OnlinePlayer

    active = (
        OnlinePlayer.objects
        .filter(user=request.user, game__mode="1v1", game__status__in=["waiting", "playing"])
        .select_related("game")
        .order_by("-game__created_at")
        .first()
    )
    if active:
        return JsonResponse({
            "status": "matched",
            "url": f"/game/online/{active.game.id}/",
        })

    my_queue = MatchQueue.objects.filter(user=request.user, mode="1v1").first()
    if not my_queue:
        return JsonResponse({"status": "cancelled"})

    return JsonResponse({
        "status": "waiting",
        "count": MatchQueue.objects.filter(mode="1v1").count(),
    })


# ------------------------------------------------------------
# صفحه بازی آنلاین ۱v۱
# ------------------------------------------------------------
@login_required
def online_1v1(request, game_id):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import OnlineGame, OnlinePlayer, Answer, Round, Game, Player

    try:
        game = OnlineGame.objects.get(id=game_id, mode="1v1")
    except OnlineGame.DoesNotExist:
        return redirect("game:rooms")

    me = OnlinePlayer.objects.filter(game=game, user=request.user).first()
    if not me:
        return redirect("game:rooms")

    other = OnlinePlayer.objects.filter(game=game).exclude(user=request.user).select_related("user").first()
    payload = game.payload or {}
    cats = payload.get("categories", [])
    letter = payload.get("letter", "")
    duration = payload.get("duration", _ONLINE_DURATION)
    started_at = payload.get("started_at", 0)

    now_ts = _online_tz.now().timestamp()
    elapsed = max(0, int(now_ts - started_at))
    remaining = max(0, int(duration - elapsed))
    time_up = remaining <= 0

    # ---------- POST: ثبت پاسخ و استپ ----------
    if request.method == "POST" and game.status == "playing" and not me.finished_at:
        # ثبت پاسخ‌ها
        from .bot_data import is_valid_word
        total_score = 0
        for cat in cats:
            raw = (request.POST.get(f"cat_{cat}") or "").strip()[:64]
            norm = _normalize(raw)
            score = 0
            if raw and norm and norm[0] == letter:
                if cat in ("اسم", "فامیل"):
                    score = 10
                elif is_valid_word(norm, cat, letter):
                    score = 10
            total_score += score
        me.score = total_score
        me.finished_at = _online_tz.now()
        me.save(update_fields=["score", "finished_at"])

        # پایان بازی؟
        all_finished = not OnlinePlayer.objects.filter(game=game, finished_at__isnull=True).exists()
        if all_finished:
            _finish_online_game(game)
        return redirect("game:online_1v1", game_id=str(game.id))

    # ---------- چک زمان ----------
    if game.status == "playing":
        finished_count = OnlinePlayer.objects.filter(game=game, finished_at__isnull=False).count()
        if time_up and finished_count < 2:
            # هر کی استپ نزده = ۰ امتیاز، تمام
            for op in OnlinePlayer.objects.filter(game=game, finished_at__isnull=True):
                op.finished_at = _online_tz.now()
                op.save(update_fields=["finished_at"])
            _finish_online_game(game)
            game.refresh_from_db()

    return render(request, "game/online_1v1.html", {
        "game": game,
        "me": me,
        "other": other,
        "categories": cats,
        "letter": letter,
        "duration": duration,
        "remaining": remaining,
        "time_up": time_up,
        "active": "games",
    })


def _finish_online_game(game):
    """تعیین برنده + جایزه."""
    from .models import OnlinePlayer
    from django.contrib.auth import get_user_model

    if game.status == "finished":
        return

    players = list(OnlinePlayer.objects.filter(game=game).select_related("user"))
    if len(players) < 2:
        game.status = "finished"
        game.finished_at = _online_tz.now()
        game.save(update_fields=["status", "finished_at"])
        return

    a, b = players[0], players[1]

    if a.score > b.score:
        winner, loser = a, b
        game.winner_user_id = winner.user_id
    elif b.score > a.score:
        winner, loser = b, a
        game.winner_user_id = winner.user_id
    else:
        # مساوی بر اساس امتیاز → سریع‌تر استپ زده برنده
        if a.finished_at and b.finished_at:
            if a.finished_at < b.finished_at:
                game.winner_user_id = a.user_id
            elif b.finished_at < a.finished_at:
                game.winner_user_id = b.user_id
            else:
                game.winner_user_id = None
        else:
            game.winner_user_id = None

    # جایزه
    if game.winner_user_id is None:
        for p in players:
            p.user.coins = (p.user.coins or 0) + _REWARD_TIE
            p.user.save(update_fields=["coins"])
    else:
        for p in players:
            if p.user_id == game.winner_user_id:
                p.user.coins = (p.user.coins or 0) + _REWARD_WIN
                title, body = "🏆 بردی!", f"+{_REWARD_WIN} سکه"
            else:
                p.user.coins = (p.user.coins or 0) + _REWARD_LOSS
                title, body = "😢 باختی", f"+{_REWARD_LOSS} سکه"
            p.user.save(update_fields=["coins"])
            try:
                from social.notifications import notify
                notify(p.user, "game_result", title, body, f"/game/online/{game.id}/")
            except Exception:
                pass

    # XP: 50 برد، 20 باخت، 35 مساوی
    for p in players:
        xp_amt = _REWARD_TIE if game.winner_user_id is None else (_REWARD_WIN if p.user_id == game.winner_user_id else _REWARD_LOSS)
        # مقدار XP از پاداش سکه‌ست، ولی جدا حساب می‌کنیم
        if game.winner_user_id is None:
            xp_gain = 35
        elif p.user_id == game.winner_user_id:
            xp_gain = 50
        else:
            xp_gain = 20
        _add_xp(p.user, xp_gain)

    game.status = "finished"
    game.finished_at = _online_tz.now()
    game.save(update_fields=["status", "finished_at", "winner_user_id"])

# ============================================================
# GUESS GAME — 0..100
# ============================================================
@login_required
def guess_home(request):
    check = _require_complete(request.user)
    if check:
        return check

    if request.method == "POST" and request.POST.get("action") == "new":
        _start_guess(request)
        return redirect("game:guess")

    if "guess_number" not in request.session:
        _start_guess(request)

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
        messages.error(request, "عدد باید بین ۰ تا ۱۰۰ باشه.")
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


# ============================================================
# ONLINE — معما
# ============================================================
_PUZZLE_ONLINE_DURATION = 90
_PUZZLE_WORDS_POOL = None


def _get_puzzle_pool():
    """بارگذاری lazy از game.puzzle_words."""
    global _PUZZLE_WORDS_POOL
    if _PUZZLE_WORDS_POOL is None:
        try:
            from .puzzle_words import PUZZLE_WORDS
            _PUZZLE_WORDS_POOL = [w for w in PUZZLE_WORDS if 4 <= len(w) <= 8]
        except Exception:
            _PUZZLE_WORDS_POOL = ["کتاب", "درخت", "خورشید", "آبشار", "پروانه"]
    return _PUZZLE_WORDS_POOL


def _shuffle_letters_online(word):
    letters = list(word)
    for _ in range(30):
        _online_random.shuffle(letters)
        if "".join(letters) != word:
            return " ".join(letters)
    return " ".join(letters)


def _build_puzzle_payload():
    """۵ کلمه تصادفی برای هر دو بازیکن."""
    pool = _get_puzzle_pool()
    picks = _online_random.sample(pool, min(5, len(pool)))
    items = [{"word": w, "scrambled": _shuffle_letters_online(w), "idx": i}
             for i, w in enumerate(picks)]
    return {
        "words": items,
        "duration": _PUZZLE_ONLINE_DURATION,
        "started_at": _online_tz.now().timestamp(),
    }


def _norm_fa(text):
    if not text:
        return ""
    return text.strip().replace("ي", "ی").replace("ك", "ک").replace("\u200c", "").replace(" ", "")


@login_required
def match_start_puzzle(request):
    """ورود به صف انتظار برای معما."""
    check = _require_complete(request.user)
    if check:
        return check

    from .models import MatchQueue, OnlineGame, OnlinePlayer

    active = (
        OnlinePlayer.objects
        .filter(user=request.user, game__mode="puzzle", game__status__in=["waiting", "playing"])
        .select_related("game").order_by("-game__created_at").first()
    )
    if active:
        return redirect("game:online_puzzle", game_id=str(active.game.id))

    MatchQueue.objects.filter(user=request.user).delete()
    MatchQueue.objects.create(user=request.user, mode="puzzle")
    return redirect("game:match_wait_puzzle")


@login_required
def match_wait_puzzle(request):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import MatchQueue, OnlineGame, OnlinePlayer

    my_queue = MatchQueue.objects.filter(user=request.user, mode="puzzle").first()
    if not my_queue:
        active = (
            OnlinePlayer.objects
            .filter(user=request.user, game__mode="puzzle", game__status__in=["waiting", "playing"])
            .select_related("game").order_by("-game__created_at").first()
        )
        if active:
            return redirect("game:online_puzzle", game_id=str(active.game.id))
        return redirect("game:rooms")

    # لول من
    my_level = _level_from_xp(request.user.xp or 0)

    # همه‌ی حریف‌های ممکن (بی‌نهایت صبر)
    candidates = (
        MatchQueue.objects
        .filter(mode="puzzle")
        .exclude(user=request.user)
        .select_related("user")
    )

    # بهترین حریف: کمترین اختلاف لول
    best = None
    best_diff = 999
    for q in candidates:
        opp_level = _level_from_xp(q.user.xp or 0)
        diff = abs(opp_level - my_level)
        if diff < best_diff:
            best_diff = diff
            best = q

    if best and best_diff <= 3:
        opponent = best.user
        MatchQueue.objects.filter(user__in=[request.user, opponent]).delete()

        game = OnlineGame.objects.create(
            mode="puzzle", status="playing",
            payload=_build_puzzle_payload(),
        )
        OnlinePlayer.objects.create(game=game, user=request.user)
        OnlinePlayer.objects.create(game=game, user=opponent)

        try:
            from social.notifications import notify
            notify(request.user, "game_invite", "بازی پیدا شد!",
                   f"حریف: {opponent.alias}", f"/game/online/puzzle/{game.id}/")
            notify(opponent, "game_invite", "بازی پیدا شد!",
                   f"حریف: {request.user.alias}", f"/game/online/puzzle/{game.id}/")
        except Exception:
            pass

        return redirect("game:online_puzzle", game_id=str(game.id))

    return render(request, "game/match_wait.html", {
        "active": "games",
        "queue_count": candidates.count(),
        "mode_name": "puzzle",
    })

@login_required
def match_cancel_puzzle(request):
    from .models import MatchQueue
    MatchQueue.objects.filter(user=request.user, mode="puzzle").delete()
    return redirect("game:rooms")


@login_required
def online_puzzle(request, game_id):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import OnlineGame, OnlinePlayer

    try:
        game = OnlineGame.objects.get(id=game_id, mode="puzzle")
    except OnlineGame.DoesNotExist:
        return redirect("game:rooms")

    me = OnlinePlayer.objects.filter(game=game, user=request.user).first()
    if not me:
        return redirect("game:rooms")

    other = (
        OnlinePlayer.objects
        .filter(game=game).exclude(user=request.user)
        .select_related("user").first()
    )

    payload = game.payload or {}
    words = payload.get("words", [])
    duration = payload.get("duration", _PUZZLE_ONLINE_DURATION)
    started_at = payload.get("started_at", 0)

    now_ts = _online_tz.now().timestamp()
    elapsed = max(0, int(now_ts - started_at))
    remaining = max(0, int(duration - elapsed))
    time_up = remaining <= 0

    # ---------- POST: ثبت پاسخ‌ها ----------
    if request.method == "POST" and game.status == "playing" and not me.finished_at:
        correct = 0
        for it in words:
            ans = (request.POST.get(f"ans_{it['idx']}") or "").strip()
            target = it["word"]
            if _norm_fa(ans) == _norm_fa(target) and ans:
                correct += 1
        me.score = correct
        me.finished_at = _online_tz.now()
        me.save(update_fields=["score", "finished_at"])

        all_done = not OnlinePlayer.objects.filter(game=game, finished_at__isnull=True).exists()
        if all_done:
            _finish_online_game(game)
        return redirect("game:online_puzzle", game_id=str(game.id))

    # ---------- چک پایان زمان ----------
    if game.status == "playing":
        finished_count = OnlinePlayer.objects.filter(game=game, finished_at__isnull=False).count()
        if time_up and finished_count < 2:
            for op in OnlinePlayer.objects.filter(game=game, finished_at__isnull=True):
                op.finished_at = _online_tz.now()
                op.save(update_fields=["finished_at"])
            _finish_online_game(game)
            game.refresh_from_db()

    return render(request, "game/online_puzzle.html", {
        "game": game,
        "me": me,
        "other": other,
        "words": words,
        "duration": duration,
        "remaining": remaining,
        "time_up": time_up,
        "active": "games",
    })


# ============================================================
# ONLINE — حافظه
# ============================================================
_MEMORY_ONLINE_DURATION = 90
_MEMORY_EMOJIS_ONLINE = ["🐶","🐱","🦁","🐯","🐻","🐼","🐨","🐸","🦊","🐵","🦄","🐲"]


def _build_memory_payload():
    emojis = _online_random.sample(_MEMORY_EMOJIS_ONLINE, 8)
    cards_raw = emojis * 2
    _online_random.shuffle(cards_raw)
    cards = [{"id": i, "emoji": em} for i, em in enumerate(cards_raw)]
    return {
        "cards": cards,
        "total_pairs": 8,
        "duration": _MEMORY_ONLINE_DURATION,
        "started_at": _online_tz.now().timestamp(),
    }


@login_required
def match_start_memory(request):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import MatchQueue, OnlineGame, OnlinePlayer

    active = (
        OnlinePlayer.objects
        .filter(user=request.user, game__mode="memory", game__status__in=["waiting", "playing"])
        .select_related("game").order_by("-game__created_at").first()
    )
    if active:
        return redirect("game:online_memory", game_id=str(active.game.id))

    MatchQueue.objects.filter(user=request.user).delete()
    MatchQueue.objects.create(user=request.user, mode="memory")
    return redirect("game:match_wait_memory")


@login_required
def match_wait_memory(request):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import MatchQueue, OnlineGame, OnlinePlayer

    my_queue = MatchQueue.objects.filter(user=request.user, mode="memory").first()
    if not my_queue:
        active = (
            OnlinePlayer.objects
            .filter(user=request.user, game__mode="memory", game__status__in=["waiting", "playing"])
            .select_related("game").order_by("-game__created_at").first()
        )
        if active:
            return redirect("game:online_memory", game_id=str(active.game.id))
        return redirect("game:rooms")

    # لول من
    my_level = _level_from_xp(request.user.xp or 0)

    # همه‌ی حریف‌های ممکن (بی‌نهایت صبر)
    candidates = (
        MatchQueue.objects
        .filter(mode="memory")
        .exclude(user=request.user)
        .select_related("user")
    )

    # بهترین حریف: کمترین اختلاف لول
    best = None
    best_diff = 999
    for q in candidates:
        opp_level = _level_from_xp(q.user.xp or 0)
        diff = abs(opp_level - my_level)
        if diff < best_diff:
            best_diff = diff
            best = q

    if best and best_diff <= 3:
        opponent = best.user
        MatchQueue.objects.filter(user__in=[request.user, opponent]).delete()

        game = OnlineGame.objects.create(
            mode="memory", status="playing",
            payload=_build_memory_payload(),
        )
        OnlinePlayer.objects.create(game=game, user=request.user)
        OnlinePlayer.objects.create(game=game, user=opponent)

        try:
            from social.notifications import notify
            notify(request.user, "game_invite", "بازی پیدا شد!",
                   f"حریف: {opponent.alias}", f"/game/online/memory/{game.id}/")
            notify(opponent, "game_invite", "بازی پیدا شد!",
                   f"حریف: {request.user.alias}", f"/game/online/memory/{game.id}/")
        except Exception:
            pass

        return redirect("game:online_memory", game_id=str(game.id))

    return render(request, "game/match_wait.html", {
        "active": "games",
        "queue_count": candidates.count(),
        "mode_name": "memory",
    })

@login_required
def match_cancel_memory(request):
    from .models import MatchQueue
    MatchQueue.objects.filter(user=request.user, mode="memory").delete()
    return redirect("game:rooms")


@login_required
def online_memory(request, game_id):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import OnlineGame, OnlinePlayer

    try:
        game = OnlineGame.objects.get(id=game_id, mode="memory")
    except OnlineGame.DoesNotExist:
        return redirect("game:rooms")

    me = OnlinePlayer.objects.filter(game=game, user=request.user).first()
    if not me:
        return redirect("game:rooms")

    other = (
        OnlinePlayer.objects
        .filter(game=game).exclude(user=request.user)
        .select_related("user").first()
    )

    payload = game.payload or {}
    cards = payload.get("cards", [])
    total_pairs = payload.get("total_pairs", 8)
    duration = payload.get("duration", _MEMORY_ONLINE_DURATION)
    started_at = payload.get("started_at", 0)

    now_ts = _online_tz.now().timestamp()
    elapsed = max(0, int(now_ts - started_at))
    remaining = max(0, int(duration - elapsed))
    time_up = remaining <= 0

    # ---------- POST: ثبت نتیجه ----------
    if request.method == "POST" and game.status == "playing" and not me.finished_at:
        try:
            found_pairs = int(request.POST.get("found_pairs", 0))
        except (ValueError, TypeError):
            found_pairs = 0
        found_pairs = max(0, min(found_pairs, total_pairs))

        me.score = found_pairs
        me.finished_at = _online_tz.now()
        me.save(update_fields=["score", "finished_at"])

        all_done = not OnlinePlayer.objects.filter(game=game, finished_at__isnull=True).exists()
        if all_done:
            _finish_online_game(game)
        return redirect("game:online_memory", game_id=str(game.id))

    # ---------- چک پایان زمان ----------
    if game.status == "playing":
        finished_count = OnlinePlayer.objects.filter(game=game, finished_at__isnull=False).count()
        if time_up and finished_count < 2:
            for op in OnlinePlayer.objects.filter(game=game, finished_at__isnull=True):
                op.finished_at = _online_tz.now()
                op.save(update_fields=["finished_at"])
            _finish_online_game(game)
            game.refresh_from_db()

    return render(request, "game/online_memory.html", {
        "game": game,
        "me": me,
        "other": other,
        "cards": cards,
        "total_pairs": total_pairs,
        "duration": duration,
        "remaining": remaining,
        "time_up": time_up,
        "active": "games",
    })


# ============================================================
# ONLINE — زنجیره کلمات
# ============================================================
_CHAIN_ONLINE_DURATION = 180   # کل زمان بازی (۳ دقیقه)
_CHAIN_ONLINE_TURN = 15        # مهلت هر نوبت


def _build_chain_payload():
    category = _online_random.choice(_CHAIN_CATEGORIES)
    start_word = _chain_starting_word(category)
    first_user_id_holder = {"user_id": None}  # بعداً پر می‌شه
    return {
        "category": category,
        "start_word": start_word,
        "used_words": [start_word],
        "current_word": start_word,
        "current_letter": _chain_last_letter(start_word),
        "turn_user_id": None,  # تو match_wait پر می‌شه
        "turn_deadline": int(_online_tz.now().timestamp()) + _CHAIN_ONLINE_TURN,
        "game_deadline": int(_online_tz.now().timestamp()) + _CHAIN_ONLINE_DURATION,
        "history": [{"who": "start", "word": start_word}],
        "loser_user_id": None,
    }


@login_required
def match_start_chain(request):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import MatchQueue, OnlineGame, OnlinePlayer

    active = (
        OnlinePlayer.objects
        .filter(user=request.user, game__mode="chain", game__status__in=["waiting", "playing"])
        .select_related("game").order_by("-game__created_at").first()
    )
    if active:
        return redirect("game:online_chain", game_id=str(active.game.id))

    MatchQueue.objects.filter(user=request.user).delete()
    MatchQueue.objects.create(user=request.user, mode="chain")
    return redirect("game:match_wait_chain")


@login_required
def match_wait_chain(request):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import MatchQueue, OnlineGame, OnlinePlayer

    my_queue = MatchQueue.objects.filter(user=request.user, mode="chain").first()
    if not my_queue:
        active = (
            OnlinePlayer.objects
            .filter(user=request.user, game__mode="chain", game__status__in=["waiting", "playing"])
            .select_related("game").order_by("-game__created_at").first()
        )
        if active:
            return redirect("game:online_chain", game_id=str(active.game.id))
        return redirect("game:rooms")

    # لول من
    my_level = _level_from_xp(request.user.xp or 0)

    # همه‌ی حریف‌های ممکن (بی‌نهایت صبر)
    candidates = (
        MatchQueue.objects
        .filter(mode="chain")
        .exclude(user=request.user)
        .select_related("user")
    )

    # بهترین حریف: کمترین اختلاف لول
    best = None
    best_diff = 999
    for q in candidates:
        opp_level = _level_from_xp(q.user.xp or 0)
        diff = abs(opp_level - my_level)
        if diff < best_diff:
            best_diff = diff
            best = q

    if best and best_diff <= 3:
        opponent = best.user
        MatchQueue.objects.filter(user__in=[request.user, opponent]).delete()

        game = OnlineGame.objects.create(
            mode="chain", status="playing",
            payload=_build_chain_payload(),
        )
        OnlinePlayer.objects.create(game=game, user=request.user)
        OnlinePlayer.objects.create(game=game, user=opponent)

        try:
            from social.notifications import notify
            notify(request.user, "game_invite", "بازی پیدا شد!",
                   f"حریف: {opponent.alias}", f"/game/online/chain/{game.id}/")
            notify(opponent, "game_invite", "بازی پیدا شد!",
                   f"حریف: {request.user.alias}", f"/game/online/chain/{game.id}/")
        except Exception:
            pass

        return redirect("game:online_chain", game_id=str(game.id))

    return render(request, "game/match_wait.html", {
        "active": "games",
        "queue_count": candidates.count(),
        "mode_name": "chain",
    })

@login_required
def match_cancel_chain(request):
    from .models import MatchQueue
    MatchQueue.objects.filter(user=request.user, mode="chain").delete()
    return redirect("game:rooms")


@login_required
def online_chain(request, game_id):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import OnlineGame, OnlinePlayer

    try:
        game = OnlineGame.objects.get(id=game_id, mode="chain")
    except OnlineGame.DoesNotExist:
        return redirect("game:rooms")

    me = OnlinePlayer.objects.filter(game=game, user=request.user).first()
    if not me:
        return redirect("game:rooms")

    other = (
        OnlinePlayer.objects
        .filter(game=game).exclude(user=request.user)
        .select_related("user").first()
    )

    payload = game.payload or {}
    turn_user_id = payload.get("turn_user_id")
    turn_deadline = payload.get("turn_deadline", 0)
    game_deadline = payload.get("game_deadline", 0)

    now_ts = int(_online_tz.now().timestamp())

    # ---------- POST: ثبت پاسخ بازیکن ----------
    if request.method == "POST" and game.status == "playing":
        if turn_user_id != request.user.id:
            messages.error(request, "نوبت شما نیست!")
            return redirect("game:online_chain", game_id=str(game.id))

        if now_ts > turn_deadline + 2:
            # دیر رسید → باخت
            payload["loser_user_id"] = request.user.id
            game.payload = payload
            _finish_online_game_chain(game, loser_user_id=request.user.id)
            game.refresh_from_db()
            return redirect("game:online_chain", game_id=str(game.id))

        answer = (request.POST.get("answer") or "").strip()
        required = payload.get("current_letter", "")
        category = payload.get("category", "اسم")

        if not answer:
            messages.error(request, "پاسخ خالی نمی‌تونه باشه!")
            return redirect("game:online_chain", game_id=str(game.id))

        norm = _chain_norm(answer)
        used_norm = set(_chain_norm(w) for w in payload.get("used_words", []))

        if not norm or norm[0] != _chain_norm(required):
            messages.error(request, f"پاسخ باید با «{required}» شروع بشه!")
            return redirect("game:online_chain", game_id=str(game.id))

        if norm in used_norm:
            messages.error(request, "این کلمه قبلاً استفاده شده!")
            return redirect("game:online_chain", game_id=str(game.id))

        # اعتبارسنجی کلمه (از دیتابیس بات)
        from .bot_data import is_valid_word
        if not is_valid_word(norm, category, required):
            messages.error(request, f"❌ «{answer}» تو دسته «{category}» با «{required}» پیدا نشد!")
            return redirect("game:online_chain", game_id=str(game.id))

        # ثبت موفق
        payload["used_words"].append(answer)
        payload["current_word"] = answer
        payload["current_letter"] = _chain_last_letter(answer)
        payload["history"].append({"who": request.user.id, "word": answer})
        payload["turn_user_id"] = other.user_id
        payload["turn_deadline"] = int(_online_tz.now().timestamp()) + _CHAIN_ONLINE_TURN
        game.payload = payload
        game.save(update_fields=["payload"])

        # امتیاز: ۱ کلمه درست
        me.score += 1
        me.save(update_fields=["score"])

        messages.success(request, f"✅ «{answer}» ثبت شد!")
        return redirect("game:online_chain", game_id=str(game.id))

    # ---------- چک زمان: نوبت گذشته ----------
    if game.status == "playing":
        # مهلت کل تموم شده؟
        if now_ts > game_deadline:
            # هر کی نوبتشه، می‌بازه (یا مساوی اگه هر دو نوبت برابر داشتن)
            # ساده: هر کی الان نوبتشه، باخت
            loser = turn_user_id
            _finish_online_game_chain(game, loser_user_id=loser)
            game.refresh_from_db()
        # مهلت نوبت تموم شده؟
        elif now_ts > turn_deadline + 3 and turn_user_id:
            _finish_online_game_chain(game, loser_user_id=turn_user_id)
            game.refresh_from_db()

    payload = game.payload or {}

    return render(request, "game/online_chain.html", {
        "game": game,
        "me": me,
        "other": other,
        "payload": payload,
        "category": payload.get("category", "—"),
        "current_word": payload.get("current_word", "—"),
        "current_letter": payload.get("current_letter", "—"),
        "history": payload.get("history", []),
        "is_my_turn": payload.get("turn_user_id") == request.user.id,
        "turn_deadline": payload.get("turn_deadline", 0),
        "game_deadline": payload.get("game_deadline", 0),
        "now_ts": now_ts,
        "active": "games",
    })


def _finish_online_game_chain(game, loser_user_id):
    """تعیین برنده + جایزه."""
    from .models import OnlinePlayer

    if game.status == "finished":
        return

    players = list(OnlinePlayer.objects.filter(game=game).select_related("user"))
    if len(players) < 2:
        game.status = "finished"
        game.finished_at = _online_tz.now()
        game.save(update_fields=["status", "finished_at"])
        return

    winner = next((p for p in players if p.user_id != loser_user_id), None)
    if not winner:
        game.winner_user_id = None
    else:
        game.winner_user_id = winner.user_id

    # جایزه
    for p in players:
        if game.winner_user_id is None:
            p.user.coins = (p.user.coins or 0) + _REWARD_TIE
            p.user.save(update_fields=["coins"])
        elif p.user_id == game.winner_user_id:
            p.user.coins = (p.user.coins or 0) + _REWARD_WIN
            p.user.save(update_fields=["coins"])
            try:
                from social.notifications import notify
                notify(p.user, "game_result", "🏆 بردی!", f"+{_REWARD_WIN} سکه",
                       f"/game/online/chain/{game.id}/")
            except Exception:
                pass
        else:
            p.user.coins = (p.user.coins or 0) + _REWARD_LOSS
            p.user.save(update_fields=["coins"])
            try:
                from social.notifications import notify
                notify(p.user, "game_result", "😢 باختی", f"+{_REWARD_LOSS} سکه",
                       f"/game/online/chain/{game.id}/")
            except Exception:
                pass

    for p in players:
        if game.winner_user_id is None:
            xp_gain = 35
        elif p.user_id == game.winner_user_id:
            xp_gain = 50
        else:
            xp_gain = 20
        _add_xp(p.user, xp_gain)

    game.status = "finished"
    game.finished_at = _online_tz.now()
    game.save(update_fields=["status", "finished_at", "winner_user_id"])


@login_required
def online_chain_status(request, game_id):
    """AJAX polling وضعیت بازی."""
    from django.http import JsonResponse
    from .models import OnlineGame

    try:
        game = OnlineGame.objects.get(id=game_id, mode="chain")
    except OnlineGame.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)

    payload = game.payload or {}
    now_ts = int(_online_tz.now().timestamp())

    return JsonResponse({
        "status": game.status,
        "winner_user_id": game.winner_user_id,
        "turn_user_id": payload.get("turn_user_id"),
        "turn_deadline": payload.get("turn_deadline", 0),
        "game_deadline": payload.get("game_deadline", 0),
        "current_word": payload.get("current_word"),
        "current_letter": payload.get("current_letter"),
        "history_count": len(payload.get("history", [])),
        "now_ts": now_ts,
    })


# ============================================================
# ONLINE — سرعتی (۲۰ ثانیه، ۱ راند)
# ============================================================
_SPEED_ONLINE_DURATION = 20


def _build_speed_payload():
    cats = ["اسم", "فامیل", "میوه", "رنگ", "شهر", "حیوان"]
    letter = _online_random.choice(list("ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"))
    return {
        "categories": cats,
        "letter": letter,
        "duration": _SPEED_ONLINE_DURATION,
        "started_at": _online_tz.now().timestamp(),
    }


@login_required
def match_start_speed(request):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import MatchQueue, OnlineGame, OnlinePlayer

    active = (
        OnlinePlayer.objects
        .filter(user=request.user, game__mode="1v1", game__status__in=["waiting", "playing"])
        .select_related("game").order_by("-game__created_at").first()
    )
    # برای سرعتی از همون mode="1v1" استفاده می‌کنیم ولی payload رو متفاوت می‌سازیم
    # بهتر: mode="speed" جدا
    active = (
        OnlinePlayer.objects
        .filter(user=request.user, game__mode="speed", game__status__in=["waiting", "playing"])
        .select_related("game").order_by("-game__created_at").first()
    )
    if active:
        return redirect("game:online_speed", game_id=str(active.game.id))

    MatchQueue.objects.filter(user=request.user).delete()
    MatchQueue.objects.create(user=request.user, mode="speed")
    return redirect("game:match_wait_speed")


@login_required
def match_wait_speed(request):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import MatchQueue, OnlineGame, OnlinePlayer

    my_queue = MatchQueue.objects.filter(user=request.user, mode="speed").first()
    if not my_queue:
        active = (
            OnlinePlayer.objects
            .filter(user=request.user, game__mode="speed", game__status__in=["waiting", "playing"])
            .select_related("game").order_by("-game__created_at").first()
        )
        if active:
            return redirect("game:online_speed", game_id=str(active.game.id))
        return redirect("game:rooms")

    # لول من
    my_level = _level_from_xp(request.user.xp or 0)

    # همه‌ی حریف‌های ممکن (بی‌نهایت صبر)
    candidates = (
        MatchQueue.objects
        .filter(mode="speed")
        .exclude(user=request.user)
        .select_related("user")
    )

    # بهترین حریف: کمترین اختلاف لول
    best = None
    best_diff = 999
    for q in candidates:
        opp_level = _level_from_xp(q.user.xp or 0)
        diff = abs(opp_level - my_level)
        if diff < best_diff:
            best_diff = diff
            best = q

    if best and best_diff <= 3:
        opponent = best.user
        MatchQueue.objects.filter(user__in=[request.user, opponent]).delete()

        game = OnlineGame.objects.create(
            mode="speed", status="playing",
            payload=_build_speed_payload(),
        )
        OnlinePlayer.objects.create(game=game, user=request.user)
        OnlinePlayer.objects.create(game=game, user=opponent)

        try:
            from social.notifications import notify
            notify(request.user, "game_invite", "بازی پیدا شد!",
                   f"حریف: {opponent.alias}", f"/game/online/speed/{game.id}/")
            notify(opponent, "game_invite", "بازی پیدا شد!",
                   f"حریف: {request.user.alias}", f"/game/online/speed/{game.id}/")
        except Exception:
            pass

        return redirect("game:online_speed", game_id=str(game.id))

    return render(request, "game/match_wait.html", {
        "active": "games",
        "queue_count": candidates.count(),
        "mode_name": "speed",
    })

@login_required
def match_cancel_speed(request):
    from .models import MatchQueue
    MatchQueue.objects.filter(user=request.user, mode="speed").delete()
    return redirect("game:rooms")


@login_required
def online_speed(request, game_id):
    check = _require_complete(request.user)
    if check:
        return check

    from .models import OnlineGame, OnlinePlayer

    try:
        game = OnlineGame.objects.get(id=game_id, mode="speed")
    except OnlineGame.DoesNotExist:
        return redirect("game:rooms")

    me = OnlinePlayer.objects.filter(game=game, user=request.user).first()
    if not me:
        return redirect("game:rooms")

    other = (
        OnlinePlayer.objects
        .filter(game=game).exclude(user=request.user)
        .select_related("user").first()
    )

    payload = game.payload or {}
    cats = payload.get("categories", [])
    letter = payload.get("letter", "")
    duration = payload.get("duration", _SPEED_ONLINE_DURATION)
    started_at = payload.get("started_at", 0)

    now_ts = _online_tz.now().timestamp()
    elapsed = max(0, int(now_ts - started_at))
    remaining = max(0, int(duration - elapsed))
    time_up = remaining <= 0

    # ---------- POST: ثبت پاسخ ----------
    if request.method == "POST" and game.status == "playing" and not me.finished_at:
        from .bot_data import is_valid_word
        total_score = 0
        for cat in cats:
            raw = (request.POST.get(f"cat_{cat}") or "").strip()[:64]
            norm = _normalize(raw)
            score = 0
            if raw and norm and norm[0] == letter:
                if cat in ("اسم", "فامیل"):
                    score = 10
                elif is_valid_word(norm, cat, letter):
                    score = 10
            total_score += score
        me.score = total_score
        me.finished_at = _online_tz.now()
        me.save(update_fields=["score", "finished_at"])

        all_done = not OnlinePlayer.objects.filter(game=game, finished_at__isnull=True).exists()
        if all_done:
            _finish_online_game(game)
        return redirect("game:online_speed", game_id=str(game.id))

    # ---------- چک زمان ----------
    if game.status == "playing":
        finished_count = OnlinePlayer.objects.filter(game=game, finished_at__isnull=False).count()
        if time_up and finished_count < 2:
            for op in OnlinePlayer.objects.filter(game=game, finished_at__isnull=True):
                op.finished_at = _online_tz.now()
                op.save(update_fields=["finished_at"])
            _finish_online_game(game)
            game.refresh_from_db()

    return render(request, "game/online_speed.html", {
        "game": game,
        "me": me,
        "other": other,
        "categories": cats,
        "letter": letter,
        "duration": duration,
        "remaining": remaining,
        "time_up": time_up,
        "active": "games",
    })


