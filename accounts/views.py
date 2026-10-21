from django.contrib import messages
# -*- coding: utf-8 -*-
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Sum
from django.shortcuts import redirect, render

from .avatars import AVATAR_CATEGORIES, IMAGE_AVATARS, get_avatar_display, get_emoji

User = get_user_model()


# ============================================================
# Helper
# ============================================================
def _next_after_login(user):
    if not user.has_chosen_avatar:
        return redirect("accounts:avatar_select")
    if not user.has_completed_registration:
        return redirect("accounts:complete_registration")
    return redirect("game:home")


# ============================================================
# Landing
# ============================================================
def landing(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)
    return render(request, "accounts/landing.html")


# ============================================================
# Register
# ============================================================
def register_view(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)

    error = None
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip().lower()
        password = request.POST.get("password") or ""
        password2 = request.POST.get("password2") or ""

        if not username:
            error = "شناسه کاربری را وارد کن."
        elif len(username) < 3:
            error = "شناسه باید حداقل ۳ حرف باشد."
        elif len(username) > 32:
            error = "شناسه نمی‌تواند بیشتر از ۳۲ حرف باشد."
        elif not all(c.isalnum() or c == "_" for c in username):
            error = "شناسه فقط حروف انگلیسی، اعداد و _."
        elif User.objects.filter(username=username).exists():
            error = "این شناسه قبلاً استفاده شده."
        elif len(password) < 6:
            error = "رمز باید حداقل ۶ حرف باشد."
        elif password != password2:
            error = "دو رمز یکسان نیستند."
        else:
            user = User.objects.create_user(
                username=username, password=password,
                alias=username, is_active=True, coins=100,
            )
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("accounts:complete_registration")

    return render(request, "accounts/register.html", {"error": error})


# ============================================================
# Login
# ============================================================
def login_view(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)

    error = None
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip().lower()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return _next_after_login(user)
        error = "شناسه یا رمز اشتباه است."

    return render(request, "accounts/login.html", {"error": error})


# ============================================================
# Complete registration (avatar + alias)
# ============================================================
@login_required
def complete_registration(request):
    user = request.user
    if user.has_completed_registration:
        return redirect("game:home")

    unlocked_ids = set(
        UserUnlockedAvatar.objects.filter(user=user, avatar_type="image")
        .values_list("avatar_id", flat=True)
    )
    image_list = []
    for img in IMAGE_AVATARS:
        image_list.append({
            "id": img["id"],
            "url": img["url"],
            "unlocked": img["id"] in unlocked_ids,
            "price": 0 if img["id"] in unlocked_ids else 50,
        })

    error = None
    if request.method == "POST":
        action = request.POST.get("action", "finish")

        if action == "unlock":
            try:
                aid = int(request.POST.get("avatar_id", 0))
            except (ValueError, TypeError):
                aid = 0
            if 1 <= aid <= 44:
                if UserUnlockedAvatar.objects.filter(user=user, avatar_type="image", avatar_id=aid).exists():
                    messages.info(request, "قبلاً باز شده.")
                elif (user.coins or 0) >= 50:
                    user.coins -= 50
                    user.save(update_fields=["coins"])
                    UserUnlockedAvatar.objects.create(user=user, avatar_type="image", avatar_id=aid)
                    messages.success(request, "🎉 آواتار باز شد! -50 سکه")
                else:
                    messages.error(request, "سکه کافی نداری (نیاز: 50).")
            return redirect("accounts:complete_registration")

        alias = (request.POST.get("alias") or "").strip()[:32]
        avatar_type = request.POST.get("avatar_type", "emoji")
        if avatar_type not in ("emoji", "image"):
            avatar_type = "emoji"
        try:
            avatar_id = int(request.POST.get("avatar_id", ""))
        except (ValueError, TypeError):
            avatar_id = -1
        max_id = 99 if avatar_type == "emoji" else 44

        if not alias:
            error = "نام نمایشی را وارد کن."
        elif len(alias) < 2:
            error = "نام باید حداقل ۲ حرف باشد."
        elif not (0 <= avatar_id <= max_id):
            error = "یک آواتار انتخاب کن."
        elif avatar_type == "image" and not UserUnlockedAvatar.objects.filter(
            user=user, avatar_type="image", avatar_id=avatar_id
        ).exists():
            error = "این آواتار قفله. اول بازش کن یا ایموجی انتخاب کن."
        else:
            user.alias = alias
            user.avatar_id = avatar_id
            user.avatar_type = avatar_type
            user.has_chosen_avatar = True
            user.has_completed_registration = True
            user.save(update_fields=[
                "alias", "avatar_id", "avatar_type",
                "has_chosen_avatar", "has_completed_registration",
            ])
            return redirect("game:home")

    return render(request, "accounts/complete_registration.html", {
        "categories": AVATAR_CATEGORIES,
        "image_avatars": image_list,
        "error": error,
        "user_coins": user.coins or 0,
    })



@login_required
def avatar_select(request):
    if request.user.is_guest:
        return render(request, "accounts/avatar_select.html", {
            "categories": AVATAR_CATEGORIES,
            "image_avatars": [],
            "is_guest": True,
            "locked_message": "🔒 تغییر آواتار در حالت مهمان قفل است.",
        })

    unlocked_ids = set(
        UserUnlockedAvatar.objects.filter(user=request.user, avatar_type="image")
        .values_list("avatar_id", flat=True)
    )

    image_list = []
    for img in IMAGE_AVATARS:
        image_list.append({
            "id": img["id"],
            "url": img["url"],
            "unlocked": img["id"] in unlocked_ids,
            "price": 0 if img["id"] in unlocked_ids else 50,
        })

    if request.method == "POST":
        action = request.POST.get("action", "select")

        if action == "unlock":
            try:
                aid = int(request.POST.get("avatar_id", 0))
            except (ValueError, TypeError):
                aid = 0
            if not (1 <= aid <= 44):
                messages.error(request, "آواتار نامعتبر.")
                return redirect("accounts:avatar_select")

            if UserUnlockedAvatar.objects.filter(user=request.user, avatar_type="image", avatar_id=aid).exists():
                messages.info(request, "قبلاً باز شده.")
                return redirect("accounts:avatar_select")

            PRICE = 50
            if (request.user.coins or 0) < PRICE:
                messages.error(request, f"سکه کافی نداری (نیاز: {PRICE}).")
                return redirect("accounts:avatar_select")

            request.user.coins -= PRICE
            request.user.save(update_fields=["coins"])
            UserUnlockedAvatar.objects.create(user=request.user, avatar_type="image", avatar_id=aid)
            messages.success(request, f"🎉 آواتار باز شد! -{PRICE} سکه")
            return redirect("accounts:avatar_select")

        # Normal selection
        avatar_type = request.POST.get("avatar_type", "emoji")
        if avatar_type not in ("emoji", "image"):
            avatar_type = "emoji"
        try:
            aid = int(request.POST.get("avatar_id", ""))
        except (ValueError, TypeError):
            aid = -1
        max_id = 99 if avatar_type == "emoji" else 44

        if not (0 <= aid <= max_id):
            messages.error(request, "آواتار نامعتبر.")
        elif avatar_type == "image" and not UserUnlockedAvatar.objects.filter(
            user=request.user, avatar_type="image", avatar_id=aid
        ).exists():
            messages.error(request, "این آواتار قفله. اول بازش کن.")
            return redirect("accounts:avatar_select")
        else:
            request.user.avatar_id = aid
            request.user.avatar_type = avatar_type
            request.user.has_chosen_avatar = True
            request.user.save(update_fields=["avatar_id", "avatar_type", "has_chosen_avatar"])
            messages.success(request, "آواتار تغییر کرد.")
            return redirect("accounts:profile")

    return render(request, "accounts/avatar_select.html", {
        "categories": AVATAR_CATEGORIES,
        "image_avatars": image_list,
        "current_avatar": request.user.avatar_id,
        "current_type": request.user.avatar_type,
        "is_guest": False,
        "user_coins": request.user.coins or 0,
        "active": "profile",
    })



def logout_view(request):
    logout(request)
    return redirect("landing")


# ============================================================
# Profile
# ============================================================
@login_required
def profile_view(request):
    from game.models import Player
    user = request.user
    message = None
    error = None

    if request.method == "POST" and user.is_guest:
        error = "🔒 این قابلیت در حالت مهمان قفل است."
    elif request.method == "POST":
        new_alias = (request.POST.get("alias") or "").strip()[:32]
        if new_alias and new_alias != user.alias:
            if len(new_alias) < 2:
                error = "نام باید حداقل ۲ حرف باشد."
            else:
                user.alias = new_alias
                user.save(update_fields=["alias"])
                message = "نام نمایشی تغییر کرد."

    my_players = Player.objects.filter(user=user)
    total_games = my_players.count()
    total_score = my_players.aggregate(t=Sum("score"))["t"] or 0
    best_score = my_players.aggregate(m=Max("score"))["m"] or 0
    avg_score = my_players.aggregate(a=Avg("score"))["a"] or 0
    avg_score = round(avg_score, 1)

    level = 1 + total_score // 100
    level_progress = total_score % 100

    atype, aval = get_avatar_display(user)

    return render(request, "accounts/profile.html", {
        "profile_user": user,
        "avatar_emoji": get_emoji(user.avatar_id),
        "avatar_type": atype,
        "avatar_value": aval,
        "message": message,
        "error": error,
        "is_guest": user.is_guest,
        "active": "profile",
        "level": level,
        "level_progress": level_progress,
        "level_progress_text": f"{level_progress} / 100 امتیاز تا لول بعد",
        "stats": {
            "total_games": total_games,
            "total_score": total_score,
            "best_score": best_score,
            "avg_score": avg_score,
        },
    })


# ============================================================
# Settings
# ============================================================
@login_required
def settings_view(request):
    return render(request, "accounts/settings.html", {"active": "profile"})


# ============================================================
# Shop (delegate to shop_views)
# ============================================================
@login_required
def shop_view(request):
    return redirect("accounts:shop")


# ============================================================
# Guest
# ============================================================
def guest_start(request):
    if request.user.is_authenticated:
        return redirect("game:home")

    import random, secrets
    for _ in range(30):
        num = random.randint(10_000_000, 99_999_999)
        username = f"user_{num}"
        if not User.objects.filter(username=username).exists():
            break

    password = secrets.token_urlsafe(24)
    user = User.objects.create_user(
        username=username, password=password, alias=username,
        avatar_id=None, has_chosen_avatar=True, has_completed_registration=True,
        is_active=True, is_guest=True,
    )
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("game:home")
