import secrets

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Avg, Max, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .avatars import AVATAR_CATEGORIES, get_emoji
from .emails import send_verification_email
from .models import EmailVerificationToken
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


# ---------- API ----------

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        send_verification_email(user)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = request.query_params.get("token", "")
        try:
            ev = EmailVerificationToken.objects.select_related("user").get(token=token)
        except EmailVerificationToken.DoesNotExist:
            return Response({"detail": "invalid token"}, status=400)
        if not ev.is_valid():
            return Response({"detail": "expired or used"}, status=400)

        ev.used_at = timezone.now()
        ev.save(update_fields=["used_at"])

        user = ev.user
        user.is_active = True
        user.email_verified_at = timezone.now()
        user.save(update_fields=["is_active", "email_verified_at"])
        return Response({"detail": "email verified"})


class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        User = get_user_model()
        email = (request.data.get("email") or "").lower()
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                send_verification_email(user)
        except User.DoesNotExist:
            pass
        return Response({"detail": "if the email exists, we sent a link"})


# ---------- Web (HTML) ----------

def _next_after_login(user):
    if not user.has_chosen_avatar:
        return redirect("accounts:avatar_select")
    return redirect("game:home")


def landing(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)
    return render(request, "accounts/landing.html")


# ---------- ثبت‌نام ----------

def register_view(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)

    errors = []
    email = alias = ""

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        alias = (request.POST.get("alias") or "").strip()[:32]
        password = request.POST.get("password") or ""
        password2 = request.POST.get("password2") or ""

        User = get_user_model()

        # ایمیل
        if not email:
            errors.append("ایمیل الزامی است.")
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append("ایمیل معتبر نیست.")

        # نام
        if not alias:
            errors.append("نام نمایشی الزامی است.")
        elif User.objects.filter(alias__iexact=alias).exists():
            errors.append("این نام قبلاً استفاده شده.")

        # تکراری بودن ایمیل
        if email and User.objects.filter(email=email).exists():
            errors.append("این ایمیل قبلاً ثبت شده. با آن وارد شوید یا رمز را بازیابی کنید.")

        # رمز
        if len(password) < 8:
            errors.append("رمز عبور باید حداقل ۸ کاراکتر باشد.")
        elif password != password2:
            errors.append("رمزها با هم یکسان نیستند.")

        if not errors:
            user = User.objects.create_user(email=email, alias=alias, password=password)
            send_verification_email(user)
            token = EmailVerificationToken.objects.filter(user=user).latest("created_at").token
            return render(request, "accounts/register_done.html", {
                "email": email,
                "verify_token": token,
                "debug": settings.DEBUG,
            })

    return render(request, "accounts/register.html", {
        "errors": errors,
        "email": email,
        "alias": alias,
    })


def verify_email_web(request):
    """صفحه وب تأیید ایمیل. با کلیک روی لینک، کاربر فعال می‌شود."""
    token = request.GET.get("token", "")
    if not token:
        return render(request, "accounts/verify_done.html", {
            "ok": False,
            "message": "لینک نامعتبر است.",
        })

    try:
        ev = EmailVerificationToken.objects.select_related("user").get(token=token)
    except EmailVerificationToken.DoesNotExist:
        return render(request, "accounts/verify_done.html", {
            "ok": False,
            "message": "این لینک معتبر نیست.",
        })

    if not ev.is_valid():
        return render(request, "accounts/verify_done.html", {
            "ok": False,
            "message": "این لینک منقضی شده یا قبلاً استفاده شده.",
            "email": ev.user.email,
        })

    ev.used_at = timezone.now()
    ev.save(update_fields=["used_at"])

    user = ev.user
    user.is_active = True
    user.email_verified_at = timezone.now()
    user.save(update_fields=["is_active", "email_verified_at"])

    return render(request, "accounts/verify_done.html", {
        "ok": True,
        "message": "ایمیلت با موفقیت تأیید شد! حالا می‌تونی وارد بشی.",
    })


def email_login(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        # بررسی اینکه ایمیل وجود داره ولی فعال نیست
        User = get_user_model()
        maybe = User.objects.filter(email=email).first()
        if maybe and not maybe.is_active:
            # اجازه بده دوباره لینک بفرسته
            send_verification_email(maybe)
            token = EmailVerificationToken.objects.filter(user=maybe).latest("created_at").token
            return render(request, "accounts/email_login.html", {
                "error": "ایمیلت هنوز تأیید نشده. لینک تأیید دوباره ساخته شد.",
                "verify_token": token,
                "debug": settings.DEBUG,
            })

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return _next_after_login(user)

        return render(request, "accounts/email_login.html", {
            "error": "ایمیل یا رمز اشتباه است.",
        })

    return render(request, "accounts/email_login.html")


def guest_start(request):
    User = get_user_model()
    if request.user.is_authenticated:
        return redirect("accounts:guest_name")

    while True:
        n = secrets.randbelow(9000) + 1000
        alias = f"مهمان{n}"
        if not User.objects.filter(alias=alias).exists():
            break

    email = f"guest_{secrets.token_hex(6)}@guest.local"
    user = User.objects.create_user(
        email=email, alias=alias,
        password=secrets.token_urlsafe(16),
        is_active=True,
        email_verified_at=timezone.now(),
    )
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("accounts:guest_name")


@login_required
def guest_name(request):
    if request.method == "POST":
        new_alias = (request.POST.get("alias") or "").strip()[:32]
        if new_alias and new_alias != request.user.alias:
            User = get_user_model()
            if not User.objects.filter(alias__iexact=new_alias).exclude(pk=request.user.pk).exists():
                request.user.alias = new_alias
                request.user.save(update_fields=["alias"])
        return redirect("accounts:avatar_select")
    return render(request, "accounts/guest_name.html")


def logout_view(request):
    logout(request)
    return redirect("landing")


@login_required
def avatar_select(request):
    if request.method == "POST":
        raw = request.POST.get("avatar_id", "")
        try:
            aid = int(raw)
        except ValueError:
            aid = -1
        if 0 <= aid <= 99:
            request.user.avatar_id = aid
            request.user.has_chosen_avatar = True
            request.user.save(update_fields=["avatar_id", "has_chosen_avatar"])
            return redirect("game:home")
    return render(request, "accounts/avatar_select.html", {
        "categories": AVATAR_CATEGORIES,
        "current_avatar": request.user.avatar_id,
    })


@login_required
def profile_view(request):
    from game.models import Player

    user = request.user
    message = None
    error = None

    if request.method == "POST":
        new_alias = (request.POST.get("alias") or "").strip()[:32]
        if new_alias and new_alias != user.alias:
            User = get_user_model()
            if User.objects.filter(alias__iexact=new_alias).exclude(pk=user.pk).exists():
                error = "این نام قبلاً استفاده شده."
            else:
                user.alias = new_alias
                user.save(update_fields=["alias"])
                message = "نام با موفقیت تغییر کرد."
        elif not new_alias:
            error = "نام نمی‌تواند خالی باشد."

    my_players = Player.objects.filter(user=user)
    total_games = my_players.count()
    total_score = my_players.aggregate(t=Sum("score"))["t"] or 0
    best_score = my_players.aggregate(m=Max("score"))["m"] or 0
    avg_score = my_players.aggregate(a=Avg("score"))["a"] or 0
    avg_score = round(avg_score, 1)

    return render(request, "accounts/profile.html", {
        "profile_user": user,
        "avatar_emoji": get_emoji(user.avatar_id),
        "message": message,
        "error": error,
        "stats": {
            "total_games": total_games,
            "total_score": total_score,
            "best_score": best_score,
            "avg_score": avg_score,
        },
    })
