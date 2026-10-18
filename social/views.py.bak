from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta
import random

from accounts.avatars import get_emoji
from game.models import Game, Player
from .models import Friendship, Notification, GameInvite

User = get_user_model()

def _avatar_of(user):
    return get_emoji(user.avatar_id)

@login_required
def friends_home(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    now = timezone.now()
    online_threshold = now - timedelta(minutes=5)
    
    # آپدیت وضعیت آنلاین بودن کاربر فعلی
    User.objects.filter(id=request.user.id).update(last_seen=now)

    # دوستان تایید شده
    accepted = Friendship.objects.filter(
        Q(from_user=request.user, status="accepted") |
        Q(to_user=request.user, status="accepted")
    ).select_related("from_user", "to_user")

    friends = []
    for f in accepted:
        other = f.to_user if f.from_user_id == request.user.id else f.from_user
        is_online = other.last_seen and other.last_seen >= online_threshold
        
        stats = Player.objects.filter(user=other).aggregate(
            total_score=Sum('score'), games=Count('id')
        )
        total_score = stats['total_score'] or 0
        games = stats['games'] or 0
        level = 1 + total_score // 100

        friends.append({
            "user": other,
            "avatar": _avatar_of(other),
            "friendship_id": f.id,
            "is_online": is_online,
            "level": level,
            "total_score": total_score,
            "games": games,
        })

    # درخواست‌های دریافتی
    incoming = Friendship.objects.filter(to_user=request.user, status="pending").select_related("from_user")
    incoming_list = [{"req": f, "from": f.from_user, "avatar": _avatar_of(f.from_user)} for f in incoming]

    # درخواست‌های ارسالی
    outgoing = Friendship.objects.filter(from_user=request.user, status="pending").select_related("to_user")
    outgoing_list = [{"req": f, "to": f.to_user, "avatar": _avatar_of(f.to_user)} for f in outgoing]

    # دعوت‌نامه‌های بازی در انتظار
    pending_invites = GameInvite.objects.filter(to_user=request.user, status="pending").select_related("from_user", "game")

    return render(request, "social/friends.html", {
        "friends": friends,
        "incoming": incoming_list,
        "outgoing": outgoing_list,
        "pending_invites": pending_invites,
        "active": "friends",
    })

@login_required
def search_user(request):
    query = (request.GET.get("q") or "").strip()
    results = []
    error = None

    if query:
        # جستجو با نام نمایشی یا نام کاربری
        users = User.objects.filter(
            Q(alias__icontains=query) | Q(username__icontains=query)
        ).exclude(id=request.user.id)

        for u in users[:20]:
            fs = Friendship.objects.filter(
                Q(from_user=request.user, to_user=u) |
                Q(from_user=u, to_user=request.user)
            ).first()

            state = "none"
            if fs:
                if fs.status == "accepted":
                    state = "friend"
                elif fs.status == "pending":
                    state = "pending_out" if fs.from_user_id == request.user.id else "pending_in"

            results.append({
                "user": u,
                "avatar": _avatar_of(u),
                "state": state,
            })

        if not results:
            error = "کاربری با این مشخصات پیدا نشد."

    return render(request, "social/search.html", {
        "query": query,
        "results": results,
        "error": error,
    })

@login_required
def send_request(request, user_id):
    if request.method != "POST":
        return redirect("social:friends_home")
    to_user = get_object_or_404(User, id=user_id)
    if to_user == request.user:
        return redirect("social:friends_home")

    existing = Friendship.objects.filter(
        Q(from_user=request.user, to_user=to_user) | Q(from_user=to_user, to_user=request.user)
    ).first()

    if existing:
        if existing.status == "rejected":
            existing.status = "pending"
            existing.from_user = request.user
            existing.to_user = to_user
            existing.save()
    else:
        Friendship.objects.create(from_user=request.user, to_user=to_user)

    return redirect(request.META.get("HTTP_REFERER") or "social:friends_home")

@login_required
def accept_request(request, req_id):
    if request.method != "POST":
        return redirect("social:friends_home")
    req = get_object_or_404(Friendship, id=req_id, to_user=request.user, status="pending")
    req.status = "accepted"
    req.save()
    return redirect("social:friends_home")

@login_required
def reject_request(request, req_id):
    if request.method != "POST":
        return redirect("social:friends_home")
    req = get_object_or_404(Friendship, id=req_id, to_user=request.user, status="pending")
    req.status = "rejected"
    req.save()
    return redirect("social:friends_home")

@login_required
def remove_friend(request, user_id):
    if request.method != "POST":
        return redirect("social:friends_home")
    other = get_object_or_404(User, id=user_id)
    Friendship.objects.filter(
        Q(from_user=request.user, to_user=other) | Q(from_user=other, to_user=request.user)
    ).delete()
    return redirect("social:friends_home")

@login_required
def chat_view(request, user_id):
    other = get_object_or_404(User, id=user_id)
    return render(request, "social/chat.html", {
        "other": other,
        "other_avatar": _avatar_of(other),
        "my_avatar": _avatar_of(request.user),
    })

# ============================================================
# سیستم دعوت به بازی
# ============================================================

@login_required
def send_game_invite(request, user_id):
    if request.method == "POST":
        to_user = get_object_or_404(User, id=user_id)
        
        categories = request.POST.getlist("categories")
        if not categories: categories = ["اسم", "فامیل", "میوه"]
        letter_mode = request.POST.get("letter_mode", "random")
        letter = request.POST.get("letter", "").strip()
        if letter_mode == "random" or not letter:
            letter = random.choice(list("ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"))

        game = Game.objects.create(
            host=request.user,
            status="waiting",
            categories=categories,
            mode="invite",
        )
        Player.objects.create(game=game, user=request.user)

        inv = GameInvite.objects.create(
            from_user=request.user,
            to_user=to_user,
            game=game,
        )

        # چک آنلاین بودن
        is_online = to_user.last_seen and to_user.last_seen >= (timezone.now() - timedelta(minutes=5))

        Notification.objects.create(
            user=to_user,
            type="game_invite",
            title="دعوت به بازی",
            body=f"{request.user.alias} شما را به بازی دعوت کرد!",
            url="/social/"
        )

        return JsonResponse({"status": "ok", "is_online": is_online, "invite_id": inv.id})
    return JsonResponse({"status": "error"}, status=400)

@login_required
def check_invite_status(request, invite_id):
    inv = get_object_or_404(GameInvite, id=invite_id, from_user=request.user)
    if inv.status == "accepted":
        return JsonResponse({"status": "accepted", "url": f"/game/room/{inv.game.code}/"})
    elif inv.status == "rejected":
        return JsonResponse({"status": "rejected"})
    return JsonResponse({"status": "pending"})

@login_required
def accept_invite(request, invite_id):
    if request.method == "POST":
        inv = get_object_or_404(GameInvite, id=invite_id, to_user=request.user, status="pending")
        inv.status = "accepted"
        inv.save()
        Player.objects.get_or_create(game=inv.game, user=request.user)
        return JsonResponse({"status": "ok", "url": f"/game/room/{inv.game.code}/"})
    return JsonResponse({"status": "error"}, status=400)

@login_required
def reject_invite(request, invite_id):
    if request.method == "POST":
        inv = get_object_or_404(GameInvite, id=invite_id, to_user=request.user, status="pending")
        inv.status = "rejected"
        inv.save()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)
