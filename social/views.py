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

    User.objects.filter(id=request.user.id).update(last_seen=now)

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

    incoming = Friendship.objects.filter(to_user=request.user, status="pending").select_related("from_user")
    incoming_list = [{"req": f, "from": f.from_user, "avatar": _avatar_of(f.from_user)} for f in incoming]

    outgoing = Friendship.objects.filter(from_user=request.user, status="pending").select_related("to_user")
    outgoing_list = [{"req": f, "to": f.to_user, "avatar": _avatar_of(f.to_user)} for f in outgoing]

    pending_invites = GameInvite.objects.filter(to_user=request.user, status="pending").select_related("from_user", "game")

    from alliance.models import Alliance, AllianceMember, AllianceMessage
    my_alliance = None
    membership = AllianceMember.objects.filter(user=request.user).select_related("alliance").first()
    if membership:
        a = membership.alliance
        last_msg = AllianceMessage.objects.filter(alliance=a).select_related("sender").order_by("-sent_at").first()
        my_alliance = {
            "id": a.id,
            "name": a.name,
            "emblem": a.emblem,
            "member_count": a.member_count(),
            "max_members": a.max_members,
            "role": membership.role,
            "role_display": membership.get_role_display(),
            "last_message": last_msg.body if last_msg else "",
            "last_message_sender": last_msg.sender.alias if last_msg else "",
        }

    all_alliances = []
    if not my_alliance:
        for a in Alliance.objects.all().order_by("-created_at")[:30]:
            count = a.member_count()
            if count < a.max_members:
                all_alliances.append({
                    "id": a.id,
                    "name": a.name,
                    "emblem": a.emblem,
                            "member_count": count,
                    "max_members": a.max_members,
                    "leader_avatar": _avatar_of(a.leader),
                })

    return render(request, "social/friends.html", {
        "friends": friends,
        "incoming": incoming_list,
        "outgoing": outgoing_list,
        "pending_invites": pending_invites,
        "my_alliance": my_alliance,
        "all_alliances": all_alliances,
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

@login_required
def notifications_view(request):
    from .models import Notification, NotificationRead

    all_notifs = list(
        Notification.objects.filter(user=request.user)
        .select_related("sender")
        .order_by("-created_at")
    )
    unread = sum(1 for n in all_notifs if not n.is_read)

    # Record reads for broadcast notifications
    broadcast_notifs = [n for n in all_notifs if n.type == "admin_broadcast" and not n.is_read]
    for n in broadcast_notifs:
        try:
            NotificationRead.objects.get_or_create(notification=n, user=request.user)
        except Exception:
            pass

    # Mark all as read
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    return render(request, "social/notifications.html", {
        "notifications": all_notifs,
        "unread_total": unread,
        "active": "home",
    })

# ============================================================
# Direct Chat API — for the 1-on-1 chat page
# ============================================================
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from .models import DirectChat, DirectMessage


def _are_friends(user_a, user_b):
    """True if both sides have an accepted friendship."""
    if user_a.id == user_b.id:
        return False
    return Friendship.objects.filter(
        (Q(from_user=user_a, to_user=user_b, status="accepted")) |
        (Q(from_user=user_b, to_user=user_a, status="accepted"))
    ).exists()


def _get_chat_between(user_a, user_b):
    """Get (or create) the canonical chat between two users."""
    if user_a.id > user_b.id:
        user_a, user_b = user_b, user_a
    chat, _ = DirectChat.objects.get_or_create(user1=user_a, user2=user_b)
    return chat


@login_required
@require_POST
def chat_send(request, user_id):
    """POST body: 'body'
    Returns { ok: True, message: {...} } on success.
    """
    other = get_object_or_404(User, id=user_id)

    if other.id == request.user.id:
        return JsonResponse({"error": "cannot_message_self"}, status=400)

    if not _are_friends(request.user, other):
        return JsonResponse({"error": "not_friends"}, status=403)

    body = (request.POST.get("body") or "").strip()[:2000]
    if not body:
        return JsonResponse({"error": "empty"}, status=400)

    chat = _get_chat_between(request.user, other)

    # Un-delete the chat for both sides (new message revives it)
    chat.user1_deleted_at = None
    chat.user2_deleted_at = None
    chat.last_message_at = timezone.now()
    chat.save(update_fields=["user1_deleted_at", "user2_deleted_at", "last_message_at"])

    # Also reset any previously-deleted messages' visibility for the sender's new view
    msg = DirectMessage.objects.create(
        chat=chat,
        sender=request.user,
        body=body,
    )

    return JsonResponse({
        "ok": True,
        "chat_id": chat.id,
        "message": {
            "id": msg.id,
            "body": msg.body,
            "is_mine": True,
            "sent_at": msg.sent_at.isoformat(),
            "is_read": False,
        }
    })


@login_required
@require_GET
def chat_messages(request, user_id):
    """Returns all visible messages between me and `user_id`.
    Also marks incoming messages as read.
    """
    other = get_object_or_404(User, id=user_id)

    if not _are_friends(request.user, other):
        return JsonResponse({"error": "not_friends"}, status=403)

    chat = DirectChat.objects.filter(
        (Q(user1=request.user, user2=other)) |
        (Q(user1=other, user2=request.user))
    ).first()

    if not chat:
        return JsonResponse({
            "chat_id": None,
            "messages": [],
            "other": {
                "id": other.id,
                "alias": other.alias,
                "username": other.username,
                "avatar_type": getattr(other, "avatar_type", "emoji"),
                "avatar_id": other.avatar_id,
            }
        })

    # Mark incoming as read
    DirectMessage.objects.filter(
        chat=chat, is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    # Load visible messages
    msgs = list(chat.messages.all().order_by("sent_at"))
    data = []
    for m in msgs:
        if not m.visible_to(request.user):
            continue
        data.append({
            "id": m.id,
            "body": m.body,
            "is_mine": m.sender_id == request.user.id,
            "sent_at": m.sent_at.isoformat(),
            "is_read": m.is_read,
        })

    return JsonResponse({
        "chat_id": chat.id,
        "messages": data,
        "other": {
            "id": other.id,
            "alias": other.alias,
            "username": other.username,
            "avatar_type": getattr(other, "avatar_type", "emoji"),
            "avatar_id": other.avatar_id,
        }
    })


@login_required
@require_POST
def chat_clear(request, user_id):
    """Soft-delete the entire conversation for the current user only."""
    other = get_object_or_404(User, id=user_id)

    if not _are_friends(request.user, other):
        return JsonResponse({"error": "not_friends"}, status=403)

    chat = DirectChat.objects.filter(
        (Q(user1=request.user, user2=other)) |
        (Q(user1=other, user2=request.user))
    ).first()

    if not chat:
        return JsonResponse({"ok": True})

    now = timezone.now()

    # Soft-delete all messages FROM me for me
    DirectMessage.objects.filter(
        chat=chat, sender=request.user
    ).update(deleted_by_sender=True)

    # Soft-delete all messages TO me for me
    DirectMessage.objects.filter(chat=chat).exclude(
        sender=request.user
    ).update(deleted_by_receiver=True)

    # Mark conversation as cleared for me
    if chat.user1_id == request.user.id:
        chat.user1_deleted_at = now
    else:
        chat.user2_deleted_at = now
    chat.save(update_fields=["user1_deleted_at", "user2_deleted_at"])

    return JsonResponse({"ok": True})

