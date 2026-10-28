# -*- coding: utf-8 -*-
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, Sum

from accounts.avatars import get_emoji
from .models import (
    Alliance, AllianceMember, AllianceMessage,
    AllianceGameInvite, AllianceGameInterest,
)


def _av(user):
    try:
        return get_emoji(user.avatar_id)
    except Exception:
        return "👤"

def _av_obj(user):
    """Returns {'is_image': bool, 'value': emoji_or_url}"""
    try:
        from accounts.avatars import get_avatar_display, get_emoji
        atype, aval = get_avatar_display(user)
        if atype == "image" and aval:
            return {"is_image": True, "value": aval}
        return {"is_image": False, "value": get_emoji(user.avatar_id)}
    except Exception:
        return {"is_image": False, "value": "👤"}



@login_required
def alliance_home(request):
    if not getattr(request.user, "has_chosen_avatar", False):
        return redirect("accounts:avatar_select")

    mem = AllianceMember.objects.filter(user=request.user).select_related("alliance").first()
    if mem:
        return redirect("alliance:detail", alliance_id=mem.alliance.id)

    q = (request.GET.get("q") or "").strip()
    qs = Alliance.objects.all().order_by("-created_at")
    if q:
        qs = qs.filter(Q(name__icontains=q))

    data = []
    for a in qs[:50]:
        n = a.member_count()
        data.append({
            "obj": a, "count": n,
            "is_full": n >= a.max_members,
            "leader_avatar": _av(a.leader),
        })

    return render(request, "alliance/home.html", {
        "alliances": data, "query": q, "active": "friends",
    })


@login_required
def create_alliance(request):
    if not getattr(request.user, "has_chosen_avatar", False):
        return redirect("accounts:avatar_select")

    if AllianceMember.objects.filter(user=request.user).exists():
        messages.info(request, "شما الان عضو یک اتحاد هستید.")
        return redirect("alliance:home")

    error = None
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()[:40]
        desc = (request.POST.get("description") or "").strip()[:500]
        emblem = (request.POST.get("emblem") or "🛡️").strip()[:4]
        try:
            mx = int(request.POST.get("max_members") or 50)
        except (ValueError, TypeError):
            mx = 50
        mx = max(5, min(100, mx))

        if not name:
            error = "نام اتحاد را وارد کن."
        elif len(name) < 3:
            error = "نام باید حداقل ۳ حرف باشد."
        elif Alliance.objects.filter(name=name).exists():
            error = "این نام قبلاً گرفته شده."
        else:
            a = Alliance.objects.create(
                name=name, description=desc,
                emblem=emblem or "🛡️", leader=request.user,
                max_members=mx,
            )
            AllianceMember.objects.create(alliance=a, user=request.user, role="leader")
            messages.success(request, f"اتحاد «{name}» ساخته شد!")
            return redirect("alliance:detail", alliance_id=a.id)

    emojis = [
        "🛡️", "⚔️", "🏰", "🐉", "🦅", "🐺",
        "🔥", "⚡", "👑", "💎", "🌟", "🦁",
        "🏆", "🎯", "🎮", "🎨", "🎭", "🎪",
        "🌙", "☀️", "🌈", "⭐", "💫", "✨",
        "🚀", "🎸", "🎬", "🎲", "🐯", "🐻",
        "🦊", "🐼", "🦄", "🍀", "🌊", "🏔️",
    ]
    return render(request, "alliance/create.html", {
        "error": error, "emojis": emojis, "active": "friends",
    })


@login_required
def join_alliance(request, alliance_id):
    if not getattr(request.user, "has_chosen_avatar", False):
        return redirect("accounts:avatar_select")

    if AllianceMember.objects.filter(user=request.user).exists():
        messages.info(request, "شما الان عضو یک اتحاد هستید.")
        return redirect("alliance:home")

    a = get_object_or_404(Alliance, id=alliance_id)
    if request.method != "POST":
        return redirect("alliance:home")

    if a.member_count() >= a.max_members:
        messages.error(request, "این اتحاد پر شده است.")
        return redirect("alliance:home")

    AllianceMember.objects.create(alliance=a, user=request.user, role="member")
    messages.success(request, f"به اتحاد «{a.name}» پیوستی!")
    return redirect("alliance:detail", alliance_id=a.id)


@login_required
def join_by_code(request):
    """User enters alliance NAME to join (no invite code needed)."""
    if not getattr(request.user, "has_chosen_avatar", False):
        return redirect("accounts:avatar_select")

    if AllianceMember.objects.filter(user=request.user).exists():
        messages.info(request, "شما الان عضو یک اتحاد هستید.")
        return redirect("alliance:home")

    error = None
    suggested = []

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()[:40]
        if not name:
            error = "اسم اتحاد را وارد کن."
        else:
            # Exact match (case-insensitive)
            a = Alliance.objects.filter(name__iexact=name).first()

            # If not exact, try partial
            if not a:
                partial = Alliance.objects.filter(name__icontains=name).exclude(
                    members__user=request.user
                )
                if partial.count() == 1:
                    a = partial.first()
                else:
                    suggested = [
                        {
                            "id": x.id, "name": x.name, "emblem": x.emblem,
                            "member_count": x.member_count(),
                            "max_members": x.max_members,
                        }
                        for x in partial[:5] if x.member_count() < x.max_members
                    ]
                    if not suggested:
                        error = f"اتحادی با اسم «{name}» پیدا نشد."
                    else:
                        error = f"اتحاد دقیق «{name}» پیدا نشد. شاید منظورت این‌ها باشه:"

            if a:
                if a.member_count() >= a.max_members:
                    error = "این اتحاد پر است."
                else:
                    AllianceMember.objects.create(
                        alliance=a, user=request.user, role="member",
                    )
                    messages.success(request, f"به اتحاد «{a.name}» پیوستی!")
                    return redirect("alliance:detail", alliance_id=a.id)

    return render(request, "alliance/join.html", {
        "error": error,
        "suggested": suggested,
        "active": "friends",
    })

@login_required
def alliance_detail(request, alliance_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    mem = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not mem:
        messages.info(request, "برای دیدن اتحاد باید عضو شوی.")
        return redirect("alliance:home")

    if request.method == "POST":
        # Permission check
        can_send = True
        if a.who_can_send == "leader" and mem.role != "leader":
            can_send = False
        elif a.who_can_send == "admins" and mem.role not in ("leader", "admin"):
            can_send = False

        if can_send:
            body = (request.POST.get("body") or "").strip()[:2000]
            if body:
                AllianceMessage.objects.create(alliance=a, sender=request.user, body=body)
        return redirect("alliance:detail", alliance_id=a.id)

    online_cutoff = timezone.now() - timedelta(minutes=5)
    rows = AllianceMember.objects.filter(alliance=a).select_related("user").order_by("role", "-joined_at")

    nickname_map = {}
    members = []
    for m in rows:
        u = m.user
        display = m.nickname or u.alias
        nickname_map[u.id] = display
        try:
            is_online = bool(u.last_seen and u.last_seen >= online_cutoff)
        except Exception:
            is_online = False
        try:
            agg = u.player_set.aggregate(t=Sum("score"))
            total = agg.get("t") or 0
        except Exception:
            total = 0
        members.append({
            "user": u,
            "avatar": _av_obj(u),
            "role": m.role,
            "role_display": m.get_role_display(),
            "joined_at": m.joined_at,
            "is_online": is_online,
            "level": 1 + total // 100,
            "is_me": u.id == request.user.id,
            "nickname": m.nickname,
            "display_name": display,
        })

    msgs_qs = AllianceMessage.objects.filter(alliance=a).select_related("sender").order_by("sent_at")[:300]
    chat_messages = []
    for m in msgs_qs:
        if m.sender is None:
            av = {"is_image": False, "value": "🤖"}
            sender_display = "سیستم"
        else:
            av = _av_obj(m.sender)
            sender_display = nickname_map.get(m.sender_id, m.sender.alias)
        chat_messages.append({
            "avatar": av,
            "sender_alias": sender_display,
            "body": m.body,
            "sent_at": m.sent_at,
            "is_me": (m.sender_id == request.user.id) if m.sender_id else False,
            "message_type": m.message_type,
        })

    # Online count
    online_count = sum(1 for m in members if m.get("is_online"))

    # Chat permission
    can_send = True
    send_blocked_reason = ""
    if a.who_can_send == "leader" and mem.role != "leader":
        can_send = False
        send_blocked_reason = "فقط رهبر می‌تونه پیام بفرسته"
    elif a.who_can_send == "admins" and mem.role not in ("leader", "admin"):
        can_send = False
        send_blocked_reason = "فقط رهبر و مدیران می‌تونن پیام بفرستن"

    # My display name
    my_display = mem.nickname or request.user.alias

    # Return URL (where "back" should go)
    referer = request.META.get("HTTP_REFERER", "")
    if "/alliance/" in referer and "/alliance/" not in request.path:
        back_url = "/alliance/"
    else:
        back_url = "/social/"

    return render(request, "alliance/detail.html", {
        "alliance": a,
        "members": members,
        "my_role": mem.role,
        "is_leader": mem.role == "leader",
        "chat_messages": chat_messages,
        "member_count": len(members),
        "active": "friends",
        "can_send": can_send,
        "send_blocked_reason": send_blocked_reason,
        "my_display": my_display,
        "my_nickname": mem.nickname,
        "back_url": back_url,
        "online_count": online_count,
    })

@login_required
def alliance_edit(request, alliance_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    mem = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not mem or mem.role != "leader":
        messages.error(request, "فقط رهبر می‌تونه ویرایش کنه.")
        return redirect("alliance:detail", alliance_id=a.id)

    error = None
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()[:40]
        desc = (request.POST.get("description") or "").strip()[:500]
        emblem = (request.POST.get("emblem") or a.emblem).strip()[:4]
        try:
            mx = int(request.POST.get("max_members") or a.max_members)
        except (ValueError, TypeError):
            mx = a.max_members
        mx = max(5, min(100, mx))

        if not name:
            error = "نام اتحاد را وارد کن."
        elif len(name) < 3:
            error = "نام باید حداقل ۳ حرف باشد."
        elif Alliance.objects.filter(name=name).exclude(id=a.id).exists():
            error = "این نام قبلاً گرفته شده."
        elif a.member_count() > mx:
            error = "ظرفیت جدید از اعضای فعلی کمتره."
        else:
            a.name, a.description = name, desc
            a.emblem, a.max_members = emblem or a.emblem, mx
            a.save()
            messages.success(request, "تغییرات ذخیره شد.")
            return redirect("alliance:detail", alliance_id=a.id)

    emojis = [
        "🛡️", "⚔️", "🏰", "🐉", "🦅", "🐺",
        "🔥", "⚡", "👑", "💎", "🌟", "🦁",
        "🏆", "🎯", "🎮", "🎨", "🎭", "🎪",
        "🌙", "☀️", "🌈", "⭐", "💫", "✨",
        "🚀", "🎸", "🎬", "🎲", "🐯", "🐻",
        "🦊", "🐼", "🦄", "🍀", "🌊", "🏔️",
    ]
    return render(request, "alliance/edit.html", {
        "alliance": a, "error": error, "emojis": emojis, "active": "friends",
    })


@login_required
def alliance_chat(request, alliance_id):
    # Merged into detail page - redirect for backwards compatibility
    return redirect("alliance:detail", alliance_id=alliance_id)

@login_required
def leave_alliance(request, alliance_id):
    if request.method != "POST":
        return redirect("alliance:home")
    a = get_object_or_404(Alliance, id=alliance_id)
    m = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not m:
        return redirect("alliance:home")
    if m.role == "leader":
        if a.member_count() <= 1:
            a.delete()
            messages.info(request, "اتحاد پاک شد.")
            return redirect("alliance:home")
        messages.error(request, "رهبر نمی‌تونه اتحاد رو ترک کنه.")
        return redirect("alliance:detail", alliance_id=a.id)
    m.delete()
    messages.info(request, "از اتحاد خارج شدی.")
    return redirect("alliance:home")


@login_required
def kick_member(request, alliance_id, user_id):
    if request.method != "POST":
        return redirect("alliance:home")
    a = get_object_or_404(Alliance, id=alliance_id)
    me = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not me or me.role not in ("leader", "admin"):
        messages.error(request, "دسترسی نداری.")
        return redirect("alliance:detail", alliance_id=a.id)
    target = AllianceMember.objects.filter(alliance=a, user_id=user_id).first()
    if not target:
        return redirect("alliance:detail", alliance_id=a.id)
    if target.role == "leader":
        messages.error(request, "نمی‌تونی رهبر رو اخراج کنی.")
        return redirect("alliance:detail", alliance_id=a.id)
    if target.role == "admin" and me.role != "leader":
        messages.error(request, "فقط رهبر می‌تونه مدیر رو اخراج کنه.")
        return redirect("alliance:detail", alliance_id=a.id)
    alias = target.nickname or target.user.alias
    target.delete()
    messages.success(request, f"{alias} اخراج شد.")
    return redirect("alliance:detail", alliance_id=a.id)

@login_required
@require_POST
def game_invite_create(request, alliance_id):
    alliance = get_object_or_404(Alliance, id=alliance_id)

    if not _is_member(request.user, alliance):
        return JsonResponse({"error": "not_member"}, status=403)
    if not _can_create_invite(request.user, alliance):
        return JsonResponse({"error": "no_permission"}, status=403)

    game_type = (request.POST.get("game_type") or "1v1").strip()
    valid_types = [c[0] for c in AllianceGameInvite.GAME_TYPE_CHOICES]
    if game_type not in valid_types:
        return JsonResponse({"error": "invalid_type"}, status=400)

    try:
        min_p = int(request.POST.get("min_players") or 2)
        max_p = int(request.POST.get("max_players") or 8)
        expires_min = int(request.POST.get("expires_minutes") or 15)
    except (ValueError, TypeError):
        return JsonResponse({"error": "invalid_numbers"}, status=400)

    min_p = max(2, min(20, min_p))
    max_p = max(min_p, min(20, max_p))
    expires_min = max(5, min(60, expires_min))

    # Post a chat message for context
    type_display = dict(AllianceGameInvite.GAME_TYPE_CHOICES)[game_type]
    msg = AllianceMessage.objects.create(
        alliance=alliance,
        sender=request.user,
        body=f"🎮 دعوت به بازی «{type_display}» — میزبان: {request.user.alias}",
    )

    invite = AllianceGameInvite.objects.create(
        alliance=alliance,
        host=request.user,
        game_type=game_type,
        chat_message=msg,
        min_players=min_p,
        max_players=max_p,
        expires_at=timezone.now() + timedelta(minutes=expires_min),
    )

    return JsonResponse({
        "ok": True,
        "invite_id": invite.id,
        "message_id": msg.id,
    })


@login_required
@require_POST
def game_invite_interested(request, invite_id):
    invite = get_object_or_404(AllianceGameInvite, id=invite_id)

    if not _is_member(request.user, invite.alliance):
        return JsonResponse({"error": "not_member"}, status=403)
    if invite.status != "open":
        return JsonResponse({"error": "not_open"}, status=400)
    if invite.host_id == request.user.id:
        return JsonResponse({"error": "host_cant_join"}, status=400)

    obj, created = AllianceGameInterest.objects.get_or_create(
        invite=invite, user=request.user,
    )

    if obj.is_kicked:
        return JsonResponse({"error": "kicked"}, status=403)

    if not created:
        # Toggle OFF
        obj.delete()
        return JsonResponse({
            "ok": True,
            "interested": False,
            "count": invite.interested_count(),
        })

    return JsonResponse({
        "ok": True,
        "interested": True,
        "count": invite.interested_count(),
    })


@login_required
@require_POST
def game_invite_kick(request, invite_id):
    invite = get_object_or_404(AllianceGameInvite, id=invite_id)

    if invite.host_id != request.user.id:
        return JsonResponse({"error": "not_host"}, status=403)
    if invite.status != "open":
        return JsonResponse({"error": "already_started"}, status=400)

    target_id = request.POST.get("user_id")
    if not target_id:
        return JsonResponse({"error": "no_user_id"}, status=400)

    interest = AllianceGameInterest.objects.filter(
        invite=invite, user_id=target_id
    ).first()
    if not interest:
        return JsonResponse({"error": "not_interested"}, status=404)

    interest.is_kicked = True
    interest.save(update_fields=["is_kicked"])
    return JsonResponse({"ok": True, "count": invite.interested_count()})


@login_required
@require_POST
def game_invite_start(request, invite_id):
    invite = get_object_or_404(AllianceGameInvite, id=invite_id)

    if invite.host_id != request.user.id:
        return JsonResponse({"error": "not_host"}, status=403)
    if invite.status != "open":
        return JsonResponse({"error": "already_started"}, status=400)

    active_interests = invite.interests.filter(is_kicked=False)
    total_players = 1 + active_interests.count()  # host + interested

    if total_players < invite.min_players:
        return JsonResponse({
            "error": "not_enough_players",
            "have": total_players,
            "need": invite.min_players,
        }, status=400)

    # Create the actual Game
    mode_map = {
        "1v1": "group",
        "team": "team",
        "puzzle": "puzzle",
        "memory": "memory",
        "chain": "chain",
        "speed": "group",
    }
    categories = ["اسم", "فامیل", "میوه", "رنگ", "شهر", "کشور", "حیوان", "غذا"]
    if invite.game_type in ("puzzle", "memory", "chain"):
        categories = ["معما"]

    game = Game.objects.create(
        host=request.user,
        status="waiting",
        categories=categories,
        mode=mode_map.get(invite.game_type, "group"),
        room_name=f"بازی {invite.alliance.name}",
        max_players=min(total_players, invite.max_players),
    )
    Player.objects.create(game=game, user=request.user)
    for i in active_interests:
        Player.objects.get_or_create(game=game, user=i.user)

    invite.game = game
    invite.status = "started"
    invite.save(update_fields=["game", "status"])

    # Post chat message
    AllianceMessage.objects.create(
        alliance=invite.alliance,
        sender=request.user,
        body=f"✅ بازی شروع شد — کد اتاق: {game.code}",
        message_type="system",
    )

    return JsonResponse({
        "ok": True,
        "game_id": str(game.id),
        "game_code": game.code,
        "url": f"/game/room/{game.code}/",
    })



# ============================================================
# Member Management
# ============================================================
@login_required
@require_POST
def member_promote(request, alliance_id, user_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    me = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not me or me.role != "leader":
        messages.error(request, "فقط رهبر می‌تونه مدیر تعیین کنه.")
        return redirect("alliance:detail", alliance_id=a.id)
    target = AllianceMember.objects.filter(alliance=a, user_id=user_id).first()
    if target and target.role == "member":
        target.role = "admin"
        target.save(update_fields=["role"])
        messages.success(request, f"{target.nickname or target.user.alias} به مدیر ارتقا یافت.")
    return redirect("alliance:detail", alliance_id=a.id)


@login_required
@require_POST
def member_demote(request, alliance_id, user_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    me = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not me or me.role != "leader":
        messages.error(request, "فقط رهبر می‌تونه مدیر رو عزل کنه.")
        return redirect("alliance:detail", alliance_id=a.id)
    target = AllianceMember.objects.filter(alliance=a, user_id=user_id).first()
    if target and target.role == "admin":
        target.role = "member"
        target.save(update_fields=["role"])
        messages.success(request, f"{target.nickname or target.user.alias} از مدیریت حذف شد.")
    return redirect("alliance:detail", alliance_id=a.id)


@login_required
@require_POST
def member_set_nickname(request, alliance_id, user_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    me = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not me:
        return redirect("alliance:home")
    target = AllianceMember.objects.filter(alliance=a, user_id=user_id).first()
    if not target:
        return redirect("alliance:detail", alliance_id=a.id)
    can_edit = (request.user.id == target.user_id) or (me.role in ("leader", "admin"))
    if not can_edit:
        messages.error(request, "اجازه نداری.")
        return redirect("alliance:detail", alliance_id=a.id)
    if target.role == "leader" and me.role != "leader":
        messages.error(request, "نمی‌تونی اسم رهبر رو تغییر بدی.")
        return redirect("alliance:detail", alliance_id=a.id)
    nickname = (request.POST.get("nickname") or "").strip()[:32]
    target.nickname = nickname
    target.save(update_fields=["nickname"])
    if nickname:
        messages.success(request, f"اسم به «{nickname}» تغییر کرد.")
    else:
        messages.success(request, "اسم اختصاصی حذف شد.")
    return redirect("alliance:detail", alliance_id=a.id)


@login_required
@require_POST
def transfer_leadership(request, alliance_id, user_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    me = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not me or me.role != "leader":
        messages.error(request, "فقط رهبر می‌تونه رهبری رو منتقل کنه.")
        return redirect("alliance:detail", alliance_id=a.id)
    target = AllianceMember.objects.filter(alliance=a, user_id=user_id).first()
    if not target or target.user_id == request.user.id:
        return redirect("alliance:detail", alliance_id=a.id)
    me.role = "admin"
    me.save(update_fields=["role"])
    target.role = "leader"
    target.save(update_fields=["role"])
    a.leader = target.user
    a.save(update_fields=["leader"])
    messages.success(request, f"رهبری به {target.nickname or target.user.alias} منتقل شد.")
    return redirect("alliance:detail", alliance_id=a.id)


@login_required
@require_POST
def alliance_delete(request, alliance_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    me = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not me or me.role != "leader":
        messages.error(request, "فقط رهبر می‌تونه اتحاد رو حذف کنه.")
        return redirect("alliance:detail", alliance_id=a.id)
    a.delete()
    messages.success(request, "اتحاد حذف شد.")
    return redirect("alliance:home")


# Alliance Game Invite — API endpoints

