import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.avatars import get_emoji

from . import bot as bot_logic
from .bot_data import LETTER_DIFFICULTY
from .models import (
    DEFAULT_CATEGORIES, Answer, BotAnswer, Game, Player, Round,
)


def _avatar(user):
    return get_emoji(user.avatar_id)


def _normalize(text):
    if not text:
        return ""
    t = text.strip().replace("\u200c", "").replace(" ", "")
    return t.replace("ي", "ی").replace("ك", "ک")


@login_required
def home(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")
    return render(request, "game/menu.html", {
        "avatar_emoji": _avatar(request.user),
    })


@login_required
def rooms_list(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")
    my_rooms = Game.objects.filter(players__user=request.user).order_by("-created_at")[:5]
    return render(request, "game/rooms.html", {
        "categories": DEFAULT_CATEGORIES,
        "my_rooms": my_rooms,
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
            letter = bot_logic.bot_pick_letter(difficulty)

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

    return render(request, "game/bot_setup.html", {
        "categories": DEFAULT_CATEGORIES,
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

    player_answers = []
    for cat in game.categories:
        raw = (request.POST.get(f"cat_{cat}") or "").strip()[:64]
        norm = _normalize(raw)
        score = 10 if (norm and norm[0] == round_obj.letter) else 0
        Answer.objects.update_or_create(
            round=round_obj, user=request.user, category=cat,
            defaults={"value": raw, "normalized": norm, "score": score},
        )
        player_answers.append({
            "category": cat,
            "value": raw or "—",
            "normalized": norm,
            "score": score,
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
def create_room(request):
    if request.method != "POST":
        return redirect("game:rooms")
    selected = [c for c in request.POST.getlist("categories") if c in DEFAULT_CATEGORIES]
    if not selected:
        selected = DEFAULT_CATEGORIES
    password = (request.POST.get("password") or "").strip()[:32]
    room = Game.objects.create(
        host=request.user, status="waiting",
        categories=selected, mode="group", password=password,
    )
    Player.objects.create(game=room, user=request.user)
    return redirect("game:room", room_code=room.code)


@login_required
def join_room(request):
    if request.method != "POST":
        return redirect("game:rooms")
    code = (request.POST.get("code") or "").strip()
    password = (request.POST.get("password") or "").strip()
    room = Game.objects.filter(code=code).first()
    if room is None:
        return redirect("game:rooms")
    if room.password and room.password != password:
        return redirect("game:rooms")
    Player.objects.get_or_create(game=room, user=request.user)
    return redirect("game:room", room_code=room.code)


@login_required
def room(request, room_code):
    room = Game.objects.filter(code=room_code).first()
    if room is None:
        return redirect("game:home")
    players = []
    for p in room.players.select_related("user"):
        players.append({
            "user_id": p.user.id,
            "alias": p.user.alias,
            "avatar": get_emoji(p.user.avatar_id),
            "is_ready": p.is_ready,
            "score": p.score,
        })
    return render(request, "game/room.html", {
        "room": room,
        "categories": room.categories,
        "players": players,
    })
