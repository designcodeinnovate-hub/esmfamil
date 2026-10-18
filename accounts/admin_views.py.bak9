"""پنل ادمین سفارشی — فقط برای مدیر سیستم."""
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache


# ⚠️ فقط از اینجا قابل تغییر است — نه از دیتابیس
ADMIN_USERNAME = "admin74"
ADMIN_PASSWORD = "Amir2255ds"


def _check_auth(request):
    """آیا این نشست لاگین ادمین است؟"""
    return request.session.get("custom_admin_logged_in") is True


@never_cache
def admin_login(request):
    """صفحه ورود ادمین."""
    if _check_auth(request):
        return redirect("custom_admin:dashboard")

    error = None

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            request.session["custom_admin_logged_in"] = True
            request.session.set_expiry(60 * 60 * 8)
            return redirect("custom_admin:dashboard")
        else:
            error = "نام کاربری یا رمز عبور اشتباه است."

    return render(request, "custom_admin/login.html", {"error": error})


@never_cache
def admin_logout(request):
    request.session.pop("custom_admin_logged_in", None)
    return redirect("custom_admin:login")


@never_cache
def dashboard(request):
    """داشبورد ادمین: لیست کاربران."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    User = get_user_model()
    from game.models import Player

    search = (request.GET.get("q") or "").strip()

    users_qs = User.objects.all().order_by("-date_joined")

    if search:
        from django.db.models import Q
        users_qs = users_qs.filter(
            Q(username__icontains=search) |
            Q(alias__icontains=search) |
            Q(public_id__icontains=search)
        )

    players_stats = (
        Player.objects
        .values("user_id")
        .annotate(total_score=Sum("score"), games=Count("id"))
    )
    stats_map = {s["user_id"]: s for s in players_stats}

    users_data = []
    for u in users_qs[:500]:
        st = stats_map.get(u.id, {})
        total = st.get("total_score", 0) or 0
        level = 1 + total // 100

        # الگوریتم هش پسورد
        algo = "—"
        if u.password:
            parts = u.password.split("$")
            if parts:
                algo = parts[0]  # argon2 / pbkdf2 / bcrypt

        users_data.append({
            "id": u.id,
            "username": u.username,
            "alias": u.alias,
            "public_id": u.public_id,
            "avatar": u.avatar_id,
            "avatar_type": getattr(u, "avatar_type", "emoji"),
            "level": level,
            "total_score": total,
            "games": st.get("games", 0),
            "is_active": u.is_active,
            "is_staff": u.is_staff,
            "is_guest": getattr(u, "is_guest", False),
            "has_completed": u.has_completed_registration,
            "phone": u.phone or "—",
            "date_joined": u.date_joined,
            "last_login": u.last_login,
            "password_algo": algo,
        })

    total_users = User.objects.count()
    total_players = Player.objects.count()
    total_scores = Player.objects.aggregate(t=Sum("score"))["t"] or 0

    return render(request, "custom_admin/dashboard.html", {
        "users": users_data,
        "search": search,
        "stats": {
            "total_users": total_users,
            "total_games": total_players,
            "total_scores": total_scores,
        },
    })


@never_cache
def user_detail(request, user_id):
    """جزئیات یک کاربر."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("custom_admin:dashboard")

    from game.models import Player
    players = Player.objects.filter(user=u).select_related("game").order_by("-id")[:20]

    games_data = []
    for p in players:
        games_data.append({
            "game_id": p.game.id,
            "mode": p.game.mode,
            "score": p.score,
            "created_at": p.game.created_at,
            "status": p.game.status,
        })

    message = request.session.pop("admin_message", None)

    return render(request, "custom_admin/user_detail.html", {
        "u": u,
        "games": games_data,
        "message": message,
    })


@never_cache
def user_toggle_active(request, user_id):
    """فعال/غیرفعال کردن کاربر."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    if request.method != "POST":
        return redirect("custom_admin:dashboard")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
        u.is_active = not u.is_active
        u.save(update_fields=["is_active"])
    except User.DoesNotExist:
        pass

    return redirect("custom_admin:dashboard")


@never_cache
def user_delete(request, user_id):
    """حذف کاربر."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    if request.method != "POST":
        return redirect("custom_admin:dashboard")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
        u.delete()
    except User.DoesNotExist:
        pass

    return redirect("custom_admin:dashboard")


@never_cache
def user_reset_password(request, user_id):
    """تغییر پسورد کاربر توسط ادمین."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    if request.method != "POST":
        return redirect("custom_admin:dashboard")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("custom_admin:dashboard")

    new_password = (request.POST.get("new_password") or "").strip()

    if len(new_password) < 6:
        request.session["admin_message"] = {
            "type": "error",
            "text": "رمز جدید باید حداقل ۶ کاراکتر باشد."
        }
    else:
        u.set_password(new_password)
        u.save()
        request.session["admin_message"] = {
            "type": "success",
            "text": f"رمز کاربر {u.username} با موفقیت تغییر کرد."
        }

    return redirect("custom_admin:user_detail", user_id=u.id)


@never_cache
def user_change_alias(request, user_id):
    """تغییر نام نمایشی کاربر توسط ادمین."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    if request.method != "POST":
        return redirect("custom_admin:dashboard")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("custom_admin:dashboard")

    new_alias = (request.POST.get("new_alias") or "").strip()[:32]

    if len(new_alias) < 2:
        request.session["admin_message"] = {
            "type": "error",
            "text": "نام نمایشی باید حداقل ۲ کاراکتر باشد."
        }
    else:
        u.alias = new_alias
        u.save(update_fields=["alias"])
        request.session["admin_message"] = {
            "type": "success",
            "text": f"نام نمایشی به «{new_alias}» تغییر کرد."
        }

    return redirect("custom_admin:user_detail", user_id=u.id)
