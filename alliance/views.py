from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.avatars import get_emoji
from .models import Alliance, AllianceMember, AllianceMessage


def _avatar(user):
    return get_emoji(user.avatar_id)


@login_required
def alliance_home(request):
    """صفحه اتحاد: اگر کاربر عضو است، به پروفایل اتحاد، وگرنه به ساخت/ورود."""
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    my_membership = AllianceMember.objects.filter(user=request.user).select_related("alliance").first()
    if my_membership:
        return redirect("alliance:detail", alliance_id=my_membership.alliance.id)

    # لیست اتحادهای عمومی (برای مرور)
    alliances = Alliance.objects.all().order_by("-created_at")[:20]
    alliances_data = []
    for a in alliances:
        alliances_data.append({
            "obj": a,
            "count": a.member_count(),
            "leader_avatar": _avatar(a.leader),
        })

    return render(request, "alliance/home.html", {
        "alliances": alliances_data,
    })


@login_required
def create_alliance(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    if AllianceMember.objects.filter(user=request.user).exists():
        messages.info(request, "شما الان عضو یک اتحاد هستید.")
        return redirect("alliance:home")

    error = None

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()[:40]
        tag = (request.POST.get("tag") or "").strip().upper()[:8]
        description = (request.POST.get("description") or "").strip()[:200]
        emblem = (request.POST.get("emblem") or "🛡️").strip()[:4]

        if not name:
            error = "نام اتحاد را وارد کن."
        elif len(name) < 3:
            error = "نام اتحاد باید حداقل ۳ حرف باشد."
        elif Alliance.objects.filter(name=name).exists():
            error = "این نام قبلاً گرفته شده."
        else:
            a = Alliance.objects.create(
                name=name, tag=tag, description=description,
                emblem=emblem or "🛡️", leader=request.user,
            )
            AllianceMember.objects.create(alliance=a, user=request.user, role="leader")
            messages.success(request, f"اتحاد «{name}» ساخته شد!")
            return redirect("alliance:detail", alliance_id=a.id)

    emojis = ["🛡️", "⚔️", "🏰", "🐉", "🦅", "🐺", "🔥", "⚡", "👑", "💎", "🌟", "🦁"]
    return render(request, "alliance/create.html", {
        "error": error,
        "emojis": emojis,
    })


@login_required
def join_by_code(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    if AllianceMember.objects.filter(user=request.user).exists():
        messages.info(request, "شما الان عضو یک اتحاد هستید.")
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

    return render(request, "alliance/join.html", {"error": error})


@login_required
def alliance_detail(request, alliance_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    my_membership = AllianceMember.objects.filter(alliance=a, user=request.user).first()

    if not my_membership:
        messages.info(request, "برای دیدن اتحاد باید عضو شوی.")
        return redirect("alliance:home")

    members = AllianceMember.objects.filter(alliance=a).select_related("user").order_by("role", "-joined_at")
    members_data = []
    for m in members:
        members_data.append({
            "user": m.user,
            "avatar": _avatar(m.user),
            "role": m.role,
            "role_display": m.get_role_display(),
            "joined_at": m.joined_at,
        })

    recent_messages = AllianceMessage.objects.filter(alliance=a).select_related("sender").order_by("-sent_at")[:5]
    recent_messages = list(reversed(recent_messages))

    return render(request, "alliance/detail.html", {
        "alliance": a,
        "members": members_data,
        "my_role": my_membership.role,
        "is_leader": my_membership.role == "leader",
        "recent_messages": recent_messages,
        "member_count": len(members_data),
    })


@login_required
def alliance_chat(request, alliance_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    my_membership = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not my_membership:
        return redirect("alliance:home")

    if request.method == "POST":
        body = (request.POST.get("body") or "").strip()[:500]
        if body:
            AllianceMessage.objects.create(alliance=a, sender=request.user, body=body)
        return redirect("alliance:chat", alliance_id=a.id)

    all_messages = AllianceMessage.objects.filter(alliance=a).select_related("sender").order_by("sent_at")[:200]
    messages_data = []
    for m in all_messages:
        messages_data.append({
            "sender": m.sender,
            "avatar": _avatar(m.sender),
            "body": m.body,
            "sent_at": m.sent_at,
            "is_me": m.sender_id == request.user.id,
        })

    return render(request, "alliance/chat.html", {
        "alliance": a,
        "messages": messages_data,
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
        # اگر رهبر تنها عضو است، اتحاد پاک شود
        if a.member_count() <= 1:
            a.delete()
            messages.info(request, "اتحاد پاک شد.")
            return redirect("alliance:home")
        else:
            messages.error(request, "رهبر نمی‌تواند اتحاد را ترک کند. ابتدا رهبری را منتقل کن.")
            return redirect("alliance:detail", alliance_id=a.id)

    m.delete()
    messages.info(request, "از اتحاد خارج شدی.")
    return redirect("alliance:home")


@login_required
def kick_member(request, alliance_id, user_id):
    if request.method != "POST":
        return redirect("alliance:home")

    a = get_object_or_404(Alliance, id=alliance_id)
    my_m = AllianceMember.objects.filter(alliance=a, user=request.user).first()

    if not my_m or my_m.role != "leader":
        messages.error(request, "دسترسی نداری.")
        return redirect("alliance:detail", alliance_id=a.id)

    target = AllianceMember.objects.filter(alliance=a, user_id=user_id).first()
    if target and target.role != "leader":
        target.delete()
        messages.success(request, "عضو حذف شد.")

    return redirect("alliance:detail", alliance_id=a.id)
