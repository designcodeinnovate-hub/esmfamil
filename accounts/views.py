import secrets
import random

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .avatars import AVATAR_CATEGORIES, IMAGE_AVATARS, get_emoji, get_avatar_display
from .models import EmailVerificationToken
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

# ============================================================
#                       API Endpoints
# ============================================================
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

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
                pass
        except User.DoesNotExist:
            pass
        return Response({"detail": "if the email exists, we sent a link"})

# ============================================================
#                       Web (HTML)
# ============================================================
def _next_after_login(user):
    if not user.has_chosen_avatar:
        return redirect("accounts:avatar_select")
    if not user.has_completed_registration:
        return redirect("accounts:complete_registration")
    return redirect("game:home")

def landing(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)
    return render(request, "accounts/landing.html")

def register_view(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)
    error = None
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip().lower()
        password = request.POST.get("password") or ""
        password2 = request.POST.get("password2") or ""
        User = get_user_model()
        if not username:
            error = "شناسه کاربری را وارد کن."
        elif len(username) < 3:
            error = "شناسه کاربری باید حداقل ۳ کاراکتر باشد."
        elif len(username) > 32:
            error = "شناسه کاربری نمی‌تواند بیشتر از ۳۲ کاراکتر باشد."
        elif not all(c.isalnum() or c == "_" for c in username):
            error = "شناسه کاربری فقط می‌تواند شامل حروف انگلیسی، اعداد و _ باشد."
        elif User.objects.filter(username=username).exists():
            error = "این شناسه کاربری قبلاً استفاده شده است."
        elif len(password) < 6:
            error = "رمز عبور باید حداقل ۶ کاراکتر باشد."
        elif password != password2:
            error = "دو رمز عبور یکسان نیستند."
        else:
            user = User.objects.create_user(username=username, password=password, alias=username, is_active=True)
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("accounts:complete_registration")
    return render(request, "accounts/register.html", {"error": error})

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
        error = "شناسه کاربری یا رمز عبور اشتباه است."
    return render(request, "accounts/login.html", {"error": error})

def guest_start(request):
    if request.user.is_authenticated:
        return redirect("game:home")
    
    User = get_user_model()
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

@login_required
def complete_registration(request):
    user = request.user
    if user.has_completed_registration:
        return redirect("game:home")
    error = None
    if request.method == "POST":
        alias = (request.POST.get("alias") or "").strip()[:32]
        avatar_type = request.POST.get("avatar_type", "emoji")
        if avatar_type not in ("emoji", "image"):
            avatar_type = "emoji"
        avatar_raw = request.POST.get("avatar_id", "")
        
        try:
            avatar_id = int(avatar_raw)
        except (ValueError, TypeError):
            avatar_id = -1
            
        max_id = 99 if avatar_type == "emoji" else 44

        if not alias:
            error = "نام نمایشی را وارد کن."
        elif len(alias) < 2:
            error = "نام نمایشی باید حداقل ۲ کاراکتر باشد."
        elif not (0 <= avatar_id <= max_id):
            error = "لطفاً یک آواتار انتخاب کن."
        else:
            user.alias = alias
            user.avatar_id = avatar_id
            user.avatar_type = avatar_type
            user.has_chosen_avatar = True
            user.has_completed_registration = True
            user.save(update_fields=["alias", "avatar_id", "avatar_type", "has_chosen_avatar", "has_completed_registration"])
            return redirect("game:home")

    return render(request, "accounts/complete_registration.html", {
        "categories": AVATAR_CATEGORIES,
        "image_avatars": IMAGE_AVATARS,
        "current_avatar": user.avatar_id,
        "current_type": user.avatar_type,
        "error": error,
    })

@login_required
def avatar_select(request):
    if request.user.is_guest:
        return render(request, "accounts/avatar_select.html", {
            "categories": AVATAR_CATEGORIES,
            "image_avatars": IMAGE_AVATARS,
            "is_guest": True,
            "locked_message": "🔒 تغییر آواتار در حالت مهمان قفل است.",
        })
    if request.method == "POST":
        avatar_type = request.POST.get("avatar_type", "emoji")
        if avatar_type not in ("emoji", "image"):
            avatar_type = "emoji"
        try:
            aid = int(request.POST.get("avatar_id", ""))
        except (ValueError, TypeError):
            aid = -1
            
        max_id = 99 if avatar_type == "emoji" else 44
        
        if 0 <= aid <= max_id:
            request.user.avatar_id = aid
            request.user.avatar_type = avatar_type
            request.user.has_chosen_avatar = True
            request.user.save(update_fields=["avatar_id", "avatar_type", "has_chosen_avatar"])
            return redirect("accounts:profile")

    return render(request, "accounts/avatar_select.html", {
        "categories": AVATAR_CATEGORIES,
        "image_avatars": IMAGE_AVATARS,
        "current_avatar": request.user.avatar_id,
        "current_type": request.user.avatar_type,
        "is_guest": False,
    })

def logout_view(request):
    logout(request)
    return redirect("landing")

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
                error = "نام نمایشی باید حداقل ۲ کاراکتر باشد."
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

@login_required
def settings_view(request):
    return render(request, "accounts/settings.html", {"active": "profile"})

@login_required
def shop_view(request):
    return render(request, "accounts/shop.html", {"active": "profile"})
