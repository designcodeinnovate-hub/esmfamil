# -*- coding: utf-8 -*-
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q, Sum

from accounts.avatars import get_emoji
from .models import Alliance, AllianceMember, AllianceMessage


def _av(user):
    try:
        return get_emoji(user.avatar_id)
    except Exception:
        return "👤"


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
        qs = qs.filter(Q(name__icontains=q) | Q(tag__icontains=q))

    data = []
    for a in qs[:50]:
        n = a.member_count()
        data.append({
            "obj": a, "count": n,
            "is_full": n >= a.max_members,
            "has_password": bool(a.password),
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
        tag = (request.POST.get("tag") or "").strip().upper()[:8]
        desc = (request.POST.get("description") or "").strip()[:200]
        emblem = (request.POST.get("emblem") or "🛡️").strip()[:4]
        password = (request.POST.get("password") or "").strip()[:32]
        try:
            mx = int(request.POST.get("max_members") or 30)
        except (ValueError, TypeError):
            mx = 30
        mx = max(5, min(50, mx))

        if not name:
            error = "نام اتحاد را وارد کن."
        elif len(name) < 3:
            error = "نام باید حداقل ۳ حرف باشد."
        elif Alliance.objects.filter(name=name).exists():
            error = "این نام قبلاً گرفته شده."
        else:
            a = Alliance.objects.create(
                name=name, tag=tag, description=desc,
                emblem=emblem or "🛡️", leader=request.user,
                max_members=mx, password=password,
            )
            AllianceMember.objects.create(alliance=a, user=request.user, role="leader")
            messages.success(request, f"اتحاد «{name}» ساخته شد!")
            return redirect("alliance:detail", alliance_id=a.id)

    emojis = ["🛡️", "⚔️", "🏰", "🐉", "🦅", "🐺", "🔥", "⚡", "👑", "💎", "🌟", "🦁"]
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

    if a.password:
        entered = (request.POST.get("password") or "").strip()
        if entered != a.password:
            messages.error(request, "رمز اتحاد اشتباه است.")
            return redirect("alliance:home")

    if a.member_count() >= a.max_members:
        messages.error(request, "این اتحاد پر شده است.")
        return redirect("alliance:home")

    AllianceMember.objects.create(alliance=a, user=request.user, role="member")
    messages.success(request, f"به اتحاد «{a.name}» پیوستی!")
    return redirect("alliance:detail", alliance_id=a.id)


@login_required
def join_by_code(request):
    if not getattr(request.user, "has_chosen_avatar", False):
        return redirect("accounts:avatar_select")

    if AllianceMember.objects.filter(user=request.user).exists():
        return redirect("alliance:home")

    error = None
    if request.method == "POST":
        code = (request.POST.get("code") or "").strip().upper()
        a = Alliance.objects.filter(invite_code=code).first()
        if not a:
            error = "کد دعوت نامعتبر است."
        elif a.member_count() >= a.max_members:
            error = "این اتحاد پر است."
        else:
            AllianceMember.objects.create(alliance=a, user=request.user, role="member")
            messages.success(request, f"به اتحاد «{a.name}» پیوستی!")
            return redirect("alliance:detail", alliance_id=a.id)

    return render(request, "alliance/join.html", {"error": error, "active": "friends"})


@login_required
def alliance_detail(request, alliance_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    mem = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not mem:
        messages.info(request, "برای دیدن اتحاد باید عضو شوی.")
        return redirect("alliance:home")

    online_cutoff = timezone.now() - timedelta(minutes=5)
    rows = AllianceMember.objects.filter(alliance=a).select_related("user").order_by("role", "-joined_at")

    members = []
    for m in rows:
        u = m.user
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
            "user": u, "avatar": _av(u), "role": m.role,
            "role_display": m.get_role_display(), "joined_at": m.joined_at,
            "is_online": is_online, "level": 1 + total // 100,
        })

    recent = list(reversed(
        AllianceMessage.objects.filter(alliance=a).select_related("sender").order_by("-sent_at")[:5]
    ))

    return render(request, "alliance/detail.html", {
        "alliance": a, "members": members,
        "my_role": mem.role, "is_leader": mem.role == "leader",
        "recent_messages": recent, "member_count": len(members),
        "active": "friends",
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
        tag = (request.POST.get("tag") or "").strip().upper()[:8]
        desc = (request.POST.get("description") or "").strip()[:200]
        emblem = (request.POST.get("emblem") or a.emblem).strip()[:4]
        password = (request.POST.get("password") or "").strip()[:32]
        try:
            mx = int(request.POST.get("max_members") or a.max_members)
        except (ValueError, TypeError):
            mx = a.max_members
        mx = max(5, min(50, mx))

        if not name:
            error = "نام اتحاد را وارد کن."
        elif len(name) < 3:
            error = "نام باید حداقل ۳ حرف باشد."
        elif Alliance.objects.filter(name=name).exclude(id=a.id).exists():
            error = "این نام قبلاً گرفته شده."
        elif a.member_count() > mx:
            error = "ظرفیت جدید از اعضای فعلی کمتره."
        else:
            a.name, a.tag, a.description = name, tag, desc
            a.emblem, a.password, a.max_members = emblem or a.emblem, password, mx
            a.save()
            messages.success(request, "تغییرات ذخیره شد.")
            return redirect("alliance:detail", alliance_id=a.id)

    emojis = ["🛡️", "⚔️", "🏰", "🐉", "🦅", "🐺", "🔥", "⚡", "👑", "💎", "🌟", "🦁"]
    return render(request, "alliance/edit.html", {
        "alliance": a, "error": error, "emojis": emojis, "active": "friends",
    })


@login_required
def alliance_chat(request, alliance_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    mem = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not mem:
        return redirect("alliance:home")

    if request.method == "POST":
        body = (request.POST.get("body") or "").strip()[:500]
        if body:
            AllianceMessage.objects.create(alliance=a, sender=request.user, body=body)
        return redirect("alliance:chat", alliance_id=a.id)

    msgs = AllianceMessage.objects.filter(alliance=a).select_related("sender").order_by("sent_at")[:200]
    data = [{
        "sender": m.sender, "avatar": _av(m.sender), "body": m.body,
        "sent_at": m.sent_at, "is_me": m.sender_id == request.user.id,
    } for m in msgs]

    return render(request, "alliance/chat.html", {
        "alliance": a, "messages": data, "active": "friends",
    })


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
    if not me or me.role != "leader":
        messages.error(request, "دسترسی نداری.")
        return redirect("alliance:detail", alliance_id=a.id)
    target = AllianceMember.objects.filter(alliance=a, user_id=user_id).first()
    if target and target.role != "leader":
        target.delete()
        messages.success(request, "عضو حذف شد.")
    return redirect("alliance:detail", alliance_id=a.id)
