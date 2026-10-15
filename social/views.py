from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.avatars import get_emoji
from .models import Friendship

User = get_user_model()


def _avatar_of(user):
    return get_emoji(user.avatar_id)


@login_required
def friends_home(request):
    """صفحه اصلی دوستان: لیست دوستان + درخواست‌های دریافتی + ارسالی."""
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    # دوستان تایید شده
    accepted = Friendship.objects.filter(
        Q(from_user=request.user, status="accepted") |
        Q(to_user=request.user, status="accepted")
    ).select_related("from_user", "to_user")

    friends = []
    for f in accepted:
        other = f.to_user if f.from_user_id == request.user.id else f.from_user
        friends.append({
            "user": other,
            "avatar": _avatar_of(other),
            "friendship_id": f.id,
        })

    # درخواست‌های دریافتی (pending)
    incoming = Friendship.objects.filter(
        to_user=request.user, status="pending"
    ).select_related("from_user")
    incoming_list = [
        {"req": f, "from": f.from_user, "avatar": _avatar_of(f.from_user)}
        for f in incoming
    ]

    # درخواست‌های ارسالی (pending)
    outgoing = Friendship.objects.filter(
        from_user=request.user, status="pending"
    ).select_related("to_user")
    outgoing_list = [
        {"req": f, "to": f.to_user, "avatar": _avatar_of(f.to_user)}
        for f in outgoing
    ]

    return render(request, "social/friends.html", {
        "friends": friends,
        "incoming": incoming_list,
        "outgoing": outgoing_list,
    })


@login_required
def search_user(request):
    """جستجوی کاربر با شناسه عددی یا نام نمایشی."""
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    query = (request.GET.get("q") or "").strip()
    results = []
    error = None

    if query:
        if query.isdigit():
            users = User.objects.filter(public_id=int(query)).exclude(id=request.user.id)
        else:
            users = User.objects.filter(alias__icontains=query).exclude(id=request.user.id)

        for u in users[:20]:
            # وضعیت دوستی
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
                elif fs.status == "rejected":
                    state = "none"

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

    # اگر قبلاً درخواستی وجود دارد
    existing = Friendship.objects.filter(
        Q(from_user=request.user, to_user=to_user) |
        Q(from_user=to_user, to_user=request.user)
    ).first()

    if existing:
        if existing.status == "accepted":
            messages.info(request, "قبلاً با این کاربر دوست هستی.")
        elif existing.status == "pending":
            messages.info(request, "درخواست در انتظار است.")
        else:
            # اگر رد شده بود، دوباره ارسال کن
            existing.status = "pending"
            existing.from_user = request.user
            existing.to_user = to_user
            existing.save()
            messages.success(request, "درخواست دوستی ارسال شد.")
    else:
        Friendship.objects.create(from_user=request.user, to_user=to_user)
        messages.success(request, "درخواست دوستی ارسال شد.")

    return redirect(request.META.get("HTTP_REFERER") or "social:friends_home")


@login_required
def accept_request(request, req_id):
    if request.method != "POST":
        return redirect("social:friends_home")
    req = get_object_or_404(Friendship, id=req_id, to_user=request.user, status="pending")
    req.status = "accepted"
    req.save()
    messages.success(request, f"{req.from_user.alias} به دوستانت اضافه شد.")
    return redirect("social:friends_home")


@login_required
def reject_request(request, req_id):
    if request.method != "POST":
        return redirect("social:friends_home")
    req = get_object_or_404(Friendship, id=req_id, to_user=request.user, status="pending")
    req.status = "rejected"
    req.save()
    messages.info(request, "درخواست رد شد.")
    return redirect("social:friends_home")


@login_required
def remove_friend(request, user_id):
    if request.method != "POST":
        return redirect("social:friends_home")
    other = get_object_or_404(User, id=user_id)
    Friendship.objects.filter(
        Q(from_user=request.user, to_user=other, status="accepted") |
        Q(from_user=other, to_user=request.user, status="accepted")
    ).delete()
    messages.info(request, "از لیست دوستان حذف شد.")
    return redirect("social:friends_home")


@login_required
def chat_view(request, user_id):
    """صفحه چت (فعلاً placeholder، بعداً پیام‌ها اضافه می‌شود)."""
    other = get_object_or_404(User, id=user_id)
    return render(request, "social/chat.html", {
        "other": other,
        "other_avatar": _avatar_of(other),
        "my_avatar": _avatar_of(request.user),
    })
