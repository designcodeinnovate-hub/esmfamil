#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""بازسازی کامل accounts از صفر — بدون قفل"""
import os, sys, subprocess, re

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def read(p):
    try:
        with open(p, "r", encoding="utf-8") as f: return f.read()
    except: return ""
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) حذف Beta Gate از settings
# ============================================================
print("\n[1/8] حذف Beta Gate از settings")
settings = read("config/settings.py")
if "config.beta_gate.BetaGateMiddleware" in settings:
    settings = re.sub(
        r'\s*"config\.beta_gate\.BetaGateMiddleware",?\s*\n',
        '\n', settings
    )
    print("  ✓ از MIDDLEWARE حذف شد")
if "DEBUG = False" in settings:
    settings = settings.replace("DEBUG = False", "DEBUG = True")
if 'ALLOWED_HOSTS = ["*"]' not in settings:
    settings = re.sub(r'ALLOWED_HOSTS\s*=\s*\[[^\]]*\]', 'ALLOWED_HOSTS = ["*"]', settings)
write("config/settings.py", settings)

# ============================================================
# 2) حذف beta routes از config/urls.py
# ============================================================
print("\n[2/8] حذف beta routes از config/urls.py")
urls = read("config/urls.py")
urls = re.sub(r'from config\.beta_views import[^\n]*\n', '', urls)
urls = re.sub(r'\s*path\("beta-lock/"[^\n]*\n', '\n', urls)
urls = re.sub(r'\s*path\("beta-logout/"[^\n]*\n', '\n', urls)
write("config/urls.py", urls)

# ============================================================
# 3) accounts/views.py - کامل
# ============================================================
print("\n[3/8] accounts/views.py")

VIEWS = '''# -*- coding: utf-8 -*-
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
                alias=username, is_active=True,
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
            error = "نام باید حداقل ۲ حرف باشد."
        elif not (0 <= avatar_id <= max_id):
            error = "یک آواتار انتخاب کن."
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
        "image_avatars": IMAGE_AVATARS,
        "error": error,
    })


# ============================================================
# Avatar select (for changing later)
# ============================================================
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
            request.user.save(update_fields=[
                "avatar_id", "avatar_type", "has_chosen_avatar",
            ])
            return redirect("accounts:profile")

    return render(request, "accounts/avatar_select.html", {
        "categories": AVATAR_CATEGORIES,
        "image_avatars": IMAGE_AVATARS,
        "current_avatar": request.user.avatar_id,
        "current_type": request.user.avatar_type,
        "is_guest": False,
    })


# ============================================================
# Logout
# ============================================================
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
'''
write("accounts/views.py", VIEWS)

# ============================================================
# 4) accounts/urls.py - کامل
# ============================================================
print("\n[4/8] accounts/urls.py")

URLS = '''from django.urls import path
from . import views
from . import shop_views

app_name = "accounts"

# Web routes (used with namespace accounts)
web_urlpatterns = [
    path("register/", views.register_view, name="register_view"),
    path("login/", views.login_view, name="login_view"),
    path("complete/", views.complete_registration, name="complete_registration"),
    path("avatar/", views.avatar_select, name="avatar_select"),
    path("profile/", views.profile_view, name="profile"),
    path("settings/", views.settings_view, name="settings"),
    path("shop/", shop_views.shop_home, name="shop"),
    path("shop/buy/<int:item_id>/", shop_views.shop_buy, name="shop_buy"),
    path("shop/exchange/", shop_views.shop_exchange, name="shop_exchange"),
    path("logout/", views.logout_view, name="logout"),
    path("guest/", views.guest_start, name="guest_start"),
]

# Also expose as urlpatterns for direct include
urlpatterns = web_urlpatterns
'''
write("accounts/urls.py", URLS)

# ============================================================
# 5) config/urls.py - کامل و تمیز
# ============================================================
print("\n[5/8] config/urls.py")

CONFIG_URLS = '''from django.contrib import admin
from django.urls import include, path

from accounts.views import landing


urlpatterns = [
    # Django admin
    path("django-admin/", admin.site.urls),

    # Custom admin panel
    path("panel-admin/", include("accounts.admin_urls")),

    # Accounts (web + shop)
    path("accounts/", include("accounts.urls")),

    # Apps
    path("game/", include("game.urls")),
    path("social/", include("social.urls")),
    path("alliance/", include("alliance.urls")),

    # Landing
    path("", landing, name="landing"),
]
'''
write("config/urls.py", CONFIG_URLS)

# ============================================================
# 6) Templates - register + login + landing + profile + complete + avatar
# ============================================================
print("\n[6/8] Templates")

# Register
write("accounts/templates/accounts/register.html", '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <meta name="theme-color" content="#0a0a15">
  <title>ساخت اکانت کاربری</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: radial-gradient(circle at 30% 10%, #1e1b4b 0%, #0f0f1e 45%, #060608 100%); color: #e2e8f0; display: flex; justify-content: center; align-items: center; padding: 24px 20px; }
    .glow { position: fixed; width: 500px; height: 500px; border-radius: 50%; filter: blur(130px); opacity: 0.28; z-index: 0; pointer-events: none; }
    .glow-1 { top: -180px; right: -150px; background: #f4c542; }
    .glow-2 { bottom: -180px; left: -150px; background: #8b5cf6; }
    .box { position: relative; z-index: 10; background: rgba(30, 41, 59, 0.75); backdrop-filter: blur(14px); border: 1px solid rgba(148, 163, 184, 0.18); padding: 34px 28px; border-radius: 22px; width: 420px; max-width: 100%; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
    h1 { font-size: 24px; text-align: center; background: linear-gradient(135deg, #f4c542, #f97316); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 6px; }
    p.sub { color: #94a3b8; font-size: 13px; text-align: center; margin-bottom: 22px; line-height: 1.6; }
    label { display: block; color: #cbd5e1; font-size: 13px; margin: 14px 0 6px; }
    input { width: 100%; padding: 13px 16px; border-radius: 12px; border: 1.5px solid rgba(148, 163, 184, 0.2); background: rgba(15, 23, 42, 0.7); color: #fff; font-size: 15px; font-family: inherit; transition: border 0.2s; }
    input:focus { outline: none; border-color: #f4c542; box-shadow: 0 0 0 3px rgba(244,197,66,0.15); }
    .hint { font-size: 11px; color: #64748b; margin-top: 5px; line-height: 1.5; }
    .error { background: rgba(239, 68, 68, 0.15); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.35); padding: 12px 16px; border-radius: 12px; font-size: 13.5px; margin-bottom: 8px; text-align: right; line-height: 1.6; }
    button { width: 100%; margin-top: 24px; padding: 15px; border: none; border-radius: 12px; font-size: 16px; font-weight: bold; font-family: inherit; cursor: pointer; color: #1a1a1a; background: linear-gradient(135deg, #f4c542, #eab308); box-shadow: 0 10px 30px rgba(244,197,66,0.4); transition: transform 0.15s; }
    button:hover { transform: translateY(-2px); }
    .links { margin-top: 20px; text-align: center; font-size: 13px; color: #94a3b8; }
    .links a { color: #fdba74; text-decoration: none; }
    .links a:hover { text-decoration: underline; }
    .divider { height: 1px; background: rgba(148,163,184,0.15); margin: 18px 0; }
  </style>
</head>
<body>
  <div class="glow glow-1"></div>
  <div class="glow glow-2"></div>
  <div class="box">
    <h1>✍️ ساخت اکانت</h1>
    <p class="sub">فقط یه نام کاربری و رمز بساز و بریم!</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="post" autocomplete="off">
      {% csrf_token %}
      <label>شناسه کاربری</label>
      <input type="text" name="username" maxlength="32" required autofocus value="{{ request.POST.username|default:'' }}" placeholder="مثلاً: ali_71" autocomplete="off">
      <div class="hint">فقط حروف انگلیسی، اعداد و _ — ۳ تا ۳۲ حرف</div>
      <label>رمز عبور</label>
      <input type="password" name="password" required minlength="6" placeholder="حداقل ۶ حرف" autocomplete="new-password">
      <label>تکرار رمز</label>
      <input type="password" name="password2" required minlength="6" placeholder="همون رمز رو دوباره بزن" autocomplete="new-password">
      <button type="submit">🚀 ساخت اکانت</button>
    </form>
    <div class="divider"></div>
    <div class="links">
      قبلاً اکانت داری؟ <a href="/accounts/login/">وارد شو</a> | <a href="/">بازگشت</a>
    </div>
  </div>
</body>
</html>
''')

# Login
write("accounts/templates/accounts/login.html", '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <meta name="theme-color" content="#0a0a15">
  <title>ورود</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: radial-gradient(circle at 30% 10%, #1e1b4b 0%, #0f0f1e 45%, #060608 100%); color: #e2e8f0; display: flex; justify-content: center; align-items: center; padding: 24px 20px; }
    .glow { position: fixed; width: 500px; height: 500px; border-radius: 50%; filter: blur(130px); opacity: 0.28; z-index: 0; pointer-events: none; }
    .glow-1 { top: -180px; right: -150px; background: #06b6d4; }
    .glow-2 { bottom: -180px; left: -150px; background: #8b5cf6; }
    .box { position: relative; z-index: 10; background: rgba(30, 41, 59, 0.75); backdrop-filter: blur(14px); border: 1px solid rgba(148, 163, 184, 0.18); padding: 34px 28px; border-radius: 22px; width: 400px; max-width: 100%; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
    h1 { font-size: 24px; text-align: center; background: linear-gradient(135deg, #06b6d4, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 6px; }
    p.sub { color: #94a3b8; font-size: 13px; text-align: center; margin-bottom: 22px; }
    label { display: block; color: #cbd5e1; font-size: 13px; margin: 14px 0 6px; }
    input { width: 100%; padding: 13px 16px; border-radius: 12px; border: 1.5px solid rgba(148, 163, 184, 0.2); background: rgba(15, 23, 42, 0.7); color: #fff; font-size: 15px; font-family: inherit; }
    input:focus { outline: none; border-color: #06b6d4; box-shadow: 0 0 0 3px rgba(6,182,212,0.15); }
    .error { background: rgba(239, 68, 68, 0.15); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.35); padding: 12px 16px; border-radius: 12px; font-size: 13.5px; margin-bottom: 12px; text-align: right; }
    button { width: 100%; margin-top: 24px; padding: 15px; border: none; border-radius: 12px; font-size: 16px; font-weight: bold; font-family: inherit; cursor: pointer; color: #fff; background: linear-gradient(135deg, #06b6d4, #3b82f6); box-shadow: 0 10px 30px rgba(6,182,212,0.35); transition: transform 0.15s; }
    button:hover { transform: translateY(-2px); }
    .links { margin-top: 20px; text-align: center; font-size: 13px; color: #94a3b8; }
    .links a { color: #fdba74; text-decoration: none; }
    .links a:hover { text-decoration: underline; }
    .divider { height: 1px; background: rgba(148,163,184,0.15); margin: 18px 0; }
  </style>
</head>
<body>
  <div class="glow glow-1"></div>
  <div class="glow glow-2"></div>
  <div class="box">
    <h1>🔐 ورود</h1>
    <p class="sub">شناسه و رمزت رو وارد کن.</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="post">
      {% csrf_token %}
      <label>شناسه</label>
      <input type="text" name="username" required autofocus value="{{ request.POST.username|default:'' }}" placeholder="ali_71" autocomplete="username">
      <label>رمز</label>
      <input type="password" name="password" required placeholder="رمزت" autocomplete="current-password">
      <button type="submit">🔓 وارد شو</button>
    </form>
    <div class="divider"></div>
    <div class="links">
      حساب نداری؟ <a href="/accounts/register/">ثبت‌نام</a> | <a href="/">بازگشت</a>
    </div>
  </div>
</body>
</html>
''')

# Landing
write("accounts/templates/accounts/landing.html", '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <meta name="theme-color" content="#0a0a15">
  <title>اسم فامیل آنلاین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { height: 100%; overflow-y: auto; overflow-x: hidden; }
    body { font-family: Tahoma, sans-serif; background: radial-gradient(circle at 20% 10%, #1e1b4b 0%, #0f0f1e 45%, #060608 100%); color: #e2e8f0; min-height: 100vh; }
    .glow { position: fixed; width: 400px; height: 400px; border-radius: 50%; filter: blur(130px); z-index: 0; pointer-events: none; }
    .glow-1 { top: -100px; right: -100px; background: #8b5cf6; opacity: 0.28; }
    .glow-2 { bottom: -100px; left: -100px; background: #f4c542; opacity: 0.18; }
    .content { position: relative; z-index: 10; display: flex; flex-direction: column; align-items: center; padding: 30px 20px; min-height: 100vh; }
    .logo-wrap { text-align: center; margin-top: 40px; margin-bottom: 10px; }
    .logo-name { font-size: 48px; font-weight: 900; background: linear-gradient(180deg, #fde68a 0%, #f4c542 50%, #ca8a04 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .logo-crown { font-size: 46px; display: inline-block; transform: translateY(-10px) rotate(-8deg); filter: drop-shadow(0 6px 20px rgba(244,197,66,0.6)); }
    .tagline { color: #94a3b8; font-size: 14px; text-align: center; margin-bottom: 40px; letter-spacing: 1.5px; }
    .options { display: flex; flex-direction: column; gap: 12px; width: 340px; max-width: 90vw; }
    .btn-opt { display: flex; align-items: center; gap: 14px; padding: 16px 20px; border-radius: 18px; font-size: 16px; font-weight: bold; text-decoration: none; border: 1.5px solid; transition: all 0.2s; color: #e2e8f0; }
    .btn-opt:hover { transform: translateY(-3px); }
    .btn-opt .icon { font-size: 26px; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; background: rgba(15, 23, 42, 0.6); border-radius: 12px; flex-shrink: 0; }
    .btn-opt .label { flex: 1; text-align: right; }
    .btn-register { background: linear-gradient(135deg, #f4c542, #eab308); color: #1a1a1a; border-color: transparent; padding: 20px 22px; font-size: 18px; box-shadow: 0 14px 40px rgba(244,197,66,0.45); }
    .btn-register .icon { background: rgba(0,0,0,0.15); font-size: 28px; width: 48px; height: 48px; }
    .btn-account { background: rgba(30, 41, 59, 0.75); border-color: rgba(6, 182, 212, 0.3); }
    .btn-account:hover { border-color: #06b6d4; background: rgba(30, 41, 59, 0.95); }
    .btn-guest { background: rgba(30, 41, 59, 0.6); color: #cbd5e1; border-color: rgba(148, 163, 184, 0.2); }
    .btn-guest:hover { border-color: #94a3b8; background: rgba(30, 41, 59, 0.85); }
    .divider { display: flex; align-items: center; gap: 10px; margin: 6px 0; color: #475569; font-size: 11px; }
    .divider::before, .divider::after { content: ""; flex: 1; height: 1px; background: rgba(148, 163, 184, 0.15); }
    .footer { margin-top: 40px; margin-bottom: 30px; text-align: center; color: #475569; font-size: 11px; line-height: 1.8; }
  </style>
</head>
<body>
  <div class="glow glow-1"></div>
  <div class="glow glow-2"></div>
  <div class="content">
    <div class="logo-wrap">
      <span class="logo-crown">👑</span>
      <span class="logo-name">اسم فامیل</span>
    </div>
    <div class="tagline">بازی نوستالژیک، حال و آنلاین</div>
    <div class="options">
      <a class="btn-opt btn-register" href="/accounts/register/">
        <span class="icon">✨</span>
        <span class="label">ساخت حساب جدید</span>
        <span>←</span>
      </a>
      <div class="divider">یا</div>
      <a class="btn-opt btn-account" href="/accounts/login/">
        <span class="icon">🔐</span>
        <span class="label">ورود با حساب کاربری</span>
        <span>←</span>
      </a>
      <a class="btn-opt btn-guest" href="/accounts/guest/">
        <span class="icon">🎲</span>
        <span class="label">ورود مهمان</span>
        <span>←</span>
      </a>
    </div>
    <div class="footer">
      <div>اسم فامیل آنلاین</div>
      <div>v3.0</div>
    </div>
  </div>
</body>
</html>
''')

# Complete registration
write("accounts/templates/accounts/complete_registration.html", '''{% extends "base.html" %}
{% block title %}تکمیل پروفایل{% endblock %}
{% block extra_css %}
<style>
  .page-head { text-align: center; margin-bottom: 24px; }
  .page-head h1 { font-size: 24px; font-weight: 900; color: var(--gold); margin-bottom: 6px; }
  .page-head p { color: var(--muted); font-size: 13px; }
  .box { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 24px; margin-bottom: 20px; }
  .box h3 { font-size: 15px; color: var(--gold); margin-bottom: 16px; }
  input[type=text] { width: 100%; padding: 14px; border-radius: 12px; border: 1.5px solid var(--border); background: var(--bg); color: var(--text); font-size: 16px; font-family: inherit; text-align: center; }
  input[type=text]:focus { outline: none; border-color: var(--gold); }
  .error-box { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); padding: 12px 16px; border-radius: 12px; margin-bottom: 16px; text-align: center; font-size: 13px; }
  .tabs { display: flex; gap: 8px; background: var(--bg); padding: 6px; border-radius: 14px; margin-bottom: 20px; }
  .tab { flex: 1; padding: 12px; text-align: center; border-radius: 10px; font-size: 14px; font-weight: bold; cursor: pointer; color: var(--muted); transition: 0.2s; border: none; background: transparent; font-family: inherit; }
  .tab.active { background: var(--gold); color: #000; box-shadow: 0 4px 15px rgba(244,197,66,0.3); }
  .tab-content { display: none; }
  .tab-content.active { display: block; }
  .avatar-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; max-height: 400px; overflow-y: auto; padding: 4px; }
  .avatar-grid::-webkit-scrollbar { width: 4px; }
  .avatar-grid::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.3); border-radius: 4px; }
  .avatar-item { position: relative; }
  .avatar-item input { position: absolute; opacity: 0; pointer-events: none; }
  .avatar-item label { display: flex; align-items: center; justify-content: center; aspect-ratio: 1; background-color: #e2e8f0; border: 2px solid transparent; border-radius: 14px; cursor: pointer; transition: 0.2s; font-size: 38px; background-size: cover; background-position: center; }
  .avatar-item input:checked + label { border-color: var(--gold); transform: scale(1.05); box-shadow: 0 0 20px rgba(244,197,66,0.5); }
  button.submit { width: 100%; padding: 16px; border: none; border-radius: 14px; font-size: 17px; font-weight: 900; font-family: inherit; cursor: pointer; color: #000; background: linear-gradient(135deg, #f4c542, #eab308); box-shadow: 0 10px 30px rgba(244,197,66,0.4); margin-top: 10px; }
</style>
{% endblock %}
{% block content %}
  <div class="page-head">
    <h1>🎨 تکمیل پروفایل</h1>
    <p>یک نام نمایشی و آواتار انتخاب کن.</p>
  </div>
  {% if error %}<div class="error-box">{{ error }}</div>{% endif %}
  <form method="post" id="regForm">
    {% csrf_token %}
    <input type="hidden" name="avatar_type" id="avatarType" value="emoji">
    <input type="hidden" name="avatar_id" id="avatarId" value="">
    <div class="box">
      <h3>👤 نام نمایشی</h3>
      <input type="text" name="alias" maxlength="32" required value="{{ request.POST.alias|default:user.alias }}" placeholder="مثلاً: علی">
    </div>
    <div class="box">
      <h3>🎨 آواتار</h3>
      <div class="tabs">
        <button type="button" class="tab active" onclick="switchTab('emoji')">😊 ایموجی</button>
        <button type="button" class="tab" onclick="switchTab('image')">🖼️ شخصیت‌ها</button>
      </div>
      <div id="tab-emoji" class="tab-content active">
        <div class="avatar-grid">
          {% for cat in categories %}
            {% for emoji in cat.items %}
              <div class="avatar-item">
                <input type="radio" name="pick_emoji" id="em-{{ cat.key }}-{{ forloop.counter }}" data-cat="{{ cat.key }}" data-idx="{{ forloop.counter0 }}" onchange="pickEmoji(this)">
                <label for="em-{{ cat.key }}-{{ forloop.counter }}">{{ emoji }}</label>
              </div>
            {% endfor %}
          {% endfor %}
        </div>
      </div>
      <div id="tab-image" class="tab-content">
        <div class="avatar-grid">
          {% for img in image_avatars %}
            <div class="avatar-item">
              <input type="radio" name="pick_image" id="im-{{ img.id }}" data-id="{{ img.id }}" onchange="pickImage(this)">
              <label for="im-{{ img.id }}" style="background-image: url('{{ img.url }}');"></label>
            </div>
          {% endfor %}
        </div>
      </div>
    </div>
    <button type="submit" class="submit" onclick="prepareSubmit()">✅ تمام! بریم بازی</button>
  </form>
{% endblock %}
{% block extra_js %}
<script>
const catOrder = [{% for cat in categories %}"{{ cat.key }}"{% if not forloop.last %},{% endif %}{% endfor %}];
function switchTab(type) {
  document.getElementById('avatarType').value = type;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  if (type === 'emoji') { document.querySelectorAll('.tab')[0].classList.add('active'); document.getElementById('tab-emoji').classList.add('active'); }
  else { document.querySelectorAll('.tab')[1].classList.add('active'); document.getElementById('tab-image').classList.add('active'); }
  document.getElementById('avatarId').value = '';
}
function pickEmoji(el) { document.getElementById('avatarId').value = catOrder.indexOf(el.dataset.cat) * 10 + parseInt(el.dataset.idx); document.getElementById('avatarType').value = 'emoji'; }
function pickImage(el) { document.getElementById('avatarId').value = parseInt(el.dataset.id); document.getElementById('avatarType').value = 'image'; }
function prepareSubmit() { if (!document.getElementById('avatarId').value) { alert('لطفاً یک آواتار انتخاب کنید!'); event.preventDefault(); } }
</script>
{% endblock %}
''')

# Avatar select (change later)
write("accounts/templates/accounts/avatar_select.html", '''{% extends "base.html" %}
{% block title %}تغییر آواتار{% endblock %}
{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }
  .box { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 20px; margin-bottom: 20px; }
  .tabs { display: flex; gap: 8px; background: var(--bg); padding: 6px; border-radius: 14px; margin-bottom: 20px; }
  .tab { flex: 1; padding: 12px; text-align: center; border-radius: 10px; font-size: 14px; font-weight: bold; cursor: pointer; color: var(--muted); transition: 0.2s; border: none; background: transparent; font-family: inherit; }
  .tab.active { background: var(--gold); color: #000; }
  .tab-content { display: none; }
  .tab-content.active { display: block; }
  .avatar-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; max-height: 400px; overflow-y: auto; padding: 4px; }
  .avatar-grid::-webkit-scrollbar { width: 4px; }
  .avatar-grid::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.3); border-radius: 4px; }
  .avatar-item { position: relative; }
  .avatar-item input { position: absolute; opacity: 0; pointer-events: none; }
  .avatar-item label { display: flex; align-items: center; justify-content: center; aspect-ratio: 1; background-color: #e2e8f0; border: 2px solid transparent; border-radius: 14px; cursor: pointer; transition: 0.2s; font-size: 38px; background-size: cover; background-position: center; }
  .avatar-item input:checked + label { border-color: var(--gold); transform: scale(1.05); box-shadow: 0 0 20px rgba(244,197,66,0.5); }
  button.submit { width: 100%; padding: 16px; border: none; border-radius: 14px; font-size: 17px; font-weight: bold; font-family: inherit; cursor: pointer; color: #000; background: linear-gradient(135deg, #f4c542, #eab308); }
</style>
{% endblock %}
{% block content %}
  <div class="page-head">
    <a href="/accounts/profile/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>🎨 <span>تغییر آواتار</span></h1>
  </div>
  {% if is_guest %}
    <div class="box" style="text-align:center; color:var(--muted);">
      <h3 style="color:#f87171;">🔒 قفل است</h3>
      <p>{{ locked_message }}</p>
    </div>
  {% else %}
    <form method="post" id="avatarForm">
      {% csrf_token %}
      <input type="hidden" name="avatar_type" id="avatarType" value="{{ current_type|default:'emoji' }}">
      <input type="hidden" name="avatar_id" id="avatarId" value="{{ current_avatar|default:'' }}">
      <div class="box">
        <div class="tabs">
          <button type="button" class="tab {% if current_type != 'image' %}active{% endif %}" onclick="switchTab('emoji')">😊 ایموجی</button>
          <button type="button" class="tab {% if current_type == 'image' %}active{% endif %}" onclick="switchTab('image')">🖼️ شخصیت‌ها</button>
        </div>
        <div id="tab-emoji" class="tab-content {% if current_type != 'image' %}active{% endif %}">
          <div class="avatar-grid">
            {% for cat in categories %}
              {% for emoji in cat.items %}
                <div class="avatar-item">
                  <input type="radio" name="pick_emoji" id="em-{{ cat.key }}-{{ forloop.counter }}" data-cat="{{ cat.key }}" data-idx="{{ forloop.counter0 }}" onchange="pickEmoji(this)">
                  <label for="em-{{ cat.key }}-{{ forloop.counter }}">{{ emoji }}</label>
                </div>
              {% endfor %}
            {% endfor %}
          </div>
        </div>
        <div id="tab-image" class="tab-content {% if current_type == 'image' %}active{% endif %}">
          <div class="avatar-grid">
            {% for img in image_avatars %}
              <div class="avatar-item">
                <input type="radio" name="pick_image" id="im-{{ img.id }}" data-id="{{ img.id }}" onchange="pickImage(this)">
                <label for="im-{{ img.id }}" style="background-image: url('{{ img.url }}');"></label>
              </div>
            {% endfor %}
          </div>
        </div>
      </div>
      <button type="submit" class="submit" onclick="prepareSubmit()">✅ تأیید و ذخیره</button>
    </form>
  {% endif %}
{% endblock %}
{% block extra_js %}
<script>
const catOrder = [{% for cat in categories %}"{{ cat.key }}"{% if not forloop.last %},{% endif %}{% endfor %}];
function switchTab(type) {
  document.getElementById('avatarType').value = type;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  if (type === 'emoji') { document.querySelectorAll('.tab')[0].classList.add('active'); document.getElementById('tab-emoji').classList.add('active'); }
  else { document.querySelectorAll('.tab')[1].classList.add('active'); document.getElementById('tab-image').classList.add('active'); }
  document.getElementById('avatarId').value = '';
}
function pickEmoji(el) { document.getElementById('avatarId').value = catOrder.indexOf(el.dataset.cat) * 10 + parseInt(el.dataset.idx); document.getElementById('avatarType').value = 'emoji'; }
function pickImage(el) { document.getElementById('avatarId').value = parseInt(el.dataset.id); document.getElementById('avatarType').value = 'image'; }
function prepareSubmit() { if (!document.getElementById('avatarId').value) { alert('لطفاً یک آواتار انتخاب کنید!'); event.preventDefault(); } }
</script>
{% endblock %}
''')

# Profile
write("accounts/templates/accounts/profile.html", '''{% extends "base.html" %}
{% block title %}پروفایل{% endblock %}
{% block extra_css %}
<style>
  .profile-head { text-align: center; padding: 32px 20px 26px; background: var(--card); border: 1px solid var(--border); border-radius: 24px; position: relative; margin-bottom: 16px; cursor: pointer; user-select: none; overflow: hidden; }
  .profile-head.expanded { padding: 40px 20px 32px; border-color: var(--gold); box-shadow: 0 24px 60px rgba(244,197,66,0.28); transform: translateY(-3px); }
  .guest-badge { position: absolute; top: 16px; left: 16px; background: rgba(234, 179, 8, 0.2); color: var(--gold); font-size: 11px; padding: 5px 10px; border-radius: 8px; font-weight: bold; }
  .avatar-big { font-size: 82px; width: 130px; height: 130px; margin: 0 auto 14px; border-radius: 50%; background: linear-gradient(135deg, rgba(249,115,22,0.3), rgba(234,179,8,0.2)); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 40px rgba(249,115,22,0.4); border: 3px solid rgba(249,115,22,0.5); background-size: cover; background-position: center; overflow: hidden; transition: all 0.35s; }
  .profile-head.expanded .avatar-big { width: 155px; height: 155px; font-size: 96px; box-shadow: 0 0 70px rgba(249,115,22,0.75); border-color: rgba(249,115,22,0.9); }
  .avatar-big.image-mode { color: transparent; }
  .alias-big { font-size: 24px; font-weight: bold; background: linear-gradient(135deg, #f97316, #eab308, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 8px; }
  .username-badge { display: inline-block; background: var(--bg); border: 1px solid var(--border); padding: 5px 14px; border-radius: 18px; font-size: 13px; letter-spacing: 1px; color: var(--muted); font-family: monospace; margin: 2px; }
  .username-badge b { color: var(--gold); }
  .level-box { display: none; margin-top: 22px; padding: 20px 16px; background: var(--bg); border: 1px solid var(--border); border-radius: 18px; }
  .profile-head.expanded .level-box { display: block; animation: slideDown 0.35s ease-out; }
  @keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
  .level-title { font-size: 11px; color: var(--muted); margin-bottom: 10px; letter-spacing: 1.5px; text-transform: uppercase; }
  .level-badge-big { display: inline-block; font-size: 44px; font-weight: 900; background: linear-gradient(135deg, #8b5cf6, #6b4eff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 12px; font-family: monospace; line-height: 1; }
  .level-progress { width: 100%; height: 12px; background: rgba(148,163,184,0.15); border-radius: 12px; overflow: hidden; margin-top: 4px; }
  .level-progress-fill { height: 100%; background: linear-gradient(90deg, #8b5cf6, #eab308); border-radius: 12px; box-shadow: 0 0 12px rgba(139,92,246,0.7); }
  .level-points { font-size: 11.5px; color: var(--muted); margin-top: 10px; font-family: monospace; }
  .expand-hint { color: var(--dim); font-size: 11.5px; margin-top: 14px; letter-spacing: 0.5px; }
  .profile-head.expanded .expand-hint { display: none; }
  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px; }
  @media (max-width: 520px) { .stats { grid-template-columns: repeat(2, 1fr); } }
  .stat-card { background: var(--card); border: 1px solid var(--border); padding: 14px 10px; border-radius: 14px; text-align: center; }
  .stat-num { font-size: 22px; font-weight: bold; color: #fdba74; margin-bottom: 4px; }
  .stat-label { font-size: 11px; color: var(--muted); }
  .box { background: var(--card); border: 1px solid var(--border); padding: 22px; border-radius: 18px; margin-bottom: 14px; }
  .box h3 { font-size: 15px; color: var(--gold); margin-bottom: 14px; }
  label.lbl { display: block; color: var(--muted); font-size: 13px; margin-bottom: 6px; }
  input[type=text] { width: 100%; padding: 12px 14px; border-radius: 10px; border: 1.5px solid var(--border); background: var(--bg); color: var(--text); font-size: 16px; font-family: inherit; margin-bottom: 12px; box-sizing: border-box; }
  input:focus { outline: none; border-color: #f97316; }
  input:disabled { opacity: 0.5; cursor: not-allowed; }
  button.save { background: linear-gradient(135deg, #f97316, #eab308); color: #fff; border: none; padding: 12px 26px; border-radius: 12px; font-size: 15px; font-weight: bold; font-family: inherit; cursor: pointer; box-shadow: 0 8px 22px rgba(249,115,22,0.35); }
  .msg { padding: 12px 16px; border-radius: 12px; font-size: 13.5px; margin-bottom: 12px; text-align: right; line-height: 1.6; }
  .msg-ok { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
  .msg-err { background: rgba(239, 68, 68, 0.15); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.35); }
  .msg-lock { background: rgba(234, 179, 8, 0.15); color: #fde68a; border: 1px solid rgba(234, 179, 8, 0.35); }
  .register-cta { display: block; text-align: center; padding: 16px; border-radius: 14px; background: linear-gradient(135deg, #f4c542, #eab308); color: #1a1a1a; font-weight: bold; text-decoration: none; margin-top: 12px; }
  .action-btn { display: flex; align-items: center; gap: 12px; padding: 16px; border-radius: 14px; background: var(--bg); border: 1px solid var(--border); text-decoration: none; color: var(--text); font-weight: bold; font-size: 15px; margin-bottom: 10px; transition: all 0.15s; }
  .action-btn:hover { border-color: var(--gold); transform: translateX(-3px); }
  .action-btn .ab-icon { width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, rgba(244,197,66,0.2), rgba(249,115,22,0.1)); display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
  .action-btn .ab-text { flex: 1; }
  .action-btn .ab-title { font-size: 15px; margin-bottom: 2px; }
  .action-btn .ab-sub { font-size: 11px; color: var(--muted); font-weight: normal; }
  .action-btn .ab-arrow { color: var(--dim); font-size: 18px; }
</style>
{% endblock %}
{% block content %}
  {% if message %}<div class="msg msg-ok">{{ message }}</div>{% endif %}
  {% if error %}<div class="msg msg-err">{{ error }}</div>{% endif %}
  <div class="profile-head" id="profileHead" onclick="toggleProfileExpand(event)">
    {% if is_guest %}<div class="guest-badge">🎲 مهمان</div>{% endif %}
    {% if avatar_type == "image" and profile_user.avatar_id %}
      <div class="avatar-big image-mode" style="background-image: url('{{ avatar_value }}');"></div>
    {% else %}
      <div class="avatar-big">{{ avatar_emoji }}</div>
    {% endif %}
    <div class="alias-big">{{ profile_user.alias }}</div>
    <div class="username-badge">@{{ profile_user.username }}</div>
    <div class="level-box">
      <div class="level-title">سطح فعلی</div>
      <div class="level-badge-big">Lv {{ level|default:1 }}</div>
      <div class="level-progress"><div class="level-progress-fill" style="width: {{ level_progress|default:0 }}%;"></div></div>
      <div class="level-points">{{ level_progress_text|default:"0 / 100 امتیاز تا لول بعد" }}</div>
    </div>
    <div class="expand-hint">👆 برای دیدن سطح، ضربه بزن</div>
  </div>
  <div class="stats">
    <div class="stat-card"><div class="stat-num">{{ stats.total_games }}</div><div class="stat-label">بازی‌ها</div></div>
    <div class="stat-card"><div class="stat-num">{{ stats.total_score }}</div><div class="stat-label">مجموع</div></div>
    <div class="stat-card"><div class="stat-num">{{ stats.avg_score }}</div><div class="stat-label">میانگین</div></div>
    <div class="stat-card"><div class="stat-num">{{ stats.best_score }}</div><div class="stat-label">بهترین</div></div>
  </div>
  {% if is_guest %}
    <div class="box">
      <h3>🔒 حساب مهمان</h3>
      <div class="msg msg-lock">برای دسترسی به همه امکانات، یک حساب بساز.</div>
      <a href="/accounts/register/" class="register-cta">✨ ساخت حساب کاربری</a>
    </div>
  {% else %}
    <div class="box">
      <h3>✏️ ویرایش پروفایل</h3>
      <form method="post" onclick="event.stopPropagation();">
        {% csrf_token %}
        <label class="lbl">نام نمایشی</label>
        <input type="text" name="alias" value="{{ profile_user.alias }}" maxlength="32" required>
        <label class="lbl">نام کاربری</label>
        <input type="text" value="{{ profile_user.username }}" disabled>
        <button type="submit" class="save">💾 ذخیره</button>
      </form>
    </div>
    <div class="box">
      <h3>⚙️ تنظیمات</h3>
      <a href="/accounts/avatar/" class="action-btn">
        <div class="ab-icon">🎨</div>
        <div class="ab-text"><div class="ab-title">تغییر آواتار</div><div class="ab-sub">ایموجی یا کاراکتر</div></div>
        <div class="ab-arrow">←</div>
      </a>
      <a href="/accounts/settings/" class="action-btn">
        <div class="ab-icon">⚙️</div>
        <div class="ab-text"><div class="ab-title">تنظیمات</div><div class="ab-sub">صدا، تم، اعلان‌ها</div></div>
        <div class="ab-arrow">←</div>
      </a>
      <a href="/accounts/logout/" class="action-btn" style="border-color: rgba(239,68,68,0.3);">
        <div class="ab-icon" style="background: rgba(239,68,68,0.2);">🚪</div>
        <div class="ab-text"><div class="ab-title" style="color:#f87171">خروج</div><div class="ab-sub">خروج از حساب</div></div>
        <div class="ab-arrow">←</div>
      </a>
    </div>
  {% endif %}
{% endblock %}
{% block extra_js %}
<script>
function toggleProfileExpand(e) {
  if (e.target.closest('form, a, button, input')) return;
  document.getElementById('profileHead').classList.toggle('expanded');
}
</script>
{% endblock %}
''')

# ============================================================
# 7) base.html — نوار پایین با پروفایل
# ============================================================
print("\n[7/8] base.html bottom nav")
base = read("templates/base.html")
nav_pattern = re.compile(r'<nav class="bottom-nav">.*?</nav>', re.DOTALL)
m = nav_pattern.search(base)
if m:
    new_nav = '''<nav class="bottom-nav">
  <a href="/game/" class="nav-link {% if active == 'home' %}active{% endif %}">
    <span class="nav-icon">🏠</span>
    <span>خانه</span>
  </a>
  <a href="/game/rooms/" class="nav-link {% if active == 'games' %}active{% endif %}">
    <span class="nav-icon">🎮</span>
    <span>بازی‌ها</span>
  </a>
  <a href="/game/rooms/manage/" class="nav-link {% if active == 'rooms' %}active{% endif %}">
    <span class="nav-icon">🚪</span>
    <span>اتاق‌ها</span>
  </a>
  <a href="/social/" class="nav-link {% if active == 'friends' %}active{% endif %}">
    <span class="nav-icon">👥</span>
    <span>دوستان</span>
  </a>
  <a href="/accounts/profile/" class="nav-link {% if active == 'profile' %}active{% endif %}">
    <span class="nav-icon">👤</span>
    <span>پروفایل</span>
  </a>
</nav>'''
    base = base[:m.start()] + new_nav + base[m.end():]
    write("templates/base.html", base)
    print("  ✓ نوار پایین با ۵ آیتم + پروفایل")
else:
    print("  ⚠ nav پیدا نشد")

# ============================================================
# 8) migrate + تست
# ============================================================
print("\n[8/8] migrate + تست")
r = subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"],
                   capture_output=True, text=True)
print("  ✓ migrate OK" if r.returncode == 0 else f"  ⚠ {r.stderr[:200]}")

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

TEST = '''
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
import django
django.setup()
from django.test import Client
from accounts.models import User

User.objects.filter(username__startswith="__q_").delete()
c = Client()

print("=" * 55)
print("تست کامل")
print("=" * 55)

# ۱. Landing
r = c.get("/", follow=False)
print(f"1. GET /              → {r.status_code}")
if r.status_code == 200:
    has_btn = "ساخت حساب" in r.content.decode(errors="ignore")
    print(f"   دکمه ثبت‌نام: {'✓' if has_btn else '✗'}")

# ۲. Register page
r = c.get("/accounts/register/", follow=False)
print(f"2. GET /accounts/register/  → {r.status_code}")

# ۳. Register POST
r = c.post("/accounts/register/", {
    "username": "__q_test__",
    "password": "test123456",
    "password2": "test123456",
}, follow=False)
print(f"3. POST /accounts/register/ → {r.status_code}")
if r.status_code == 302:
    print(f"   ✓ redirect → {r.get('Location', '')}")
    u = User.objects.filter(username="__q_test__").first()
    if u:
        print(f"   ✓ کاربر ساخته شد: {u.username}")

# ۴. Complete registration
u = User.objects.filter(username="__q_test__").first()
if u:
    c2 = Client()
    c2.force_login(u)
    r = c2.post("/accounts/complete/", {
        "alias": "کاربر تست",
        "avatar_type": "emoji",
        "avatar_id": "0",
    }, follow=False)
    print(f"4. POST /accounts/complete/ → {r.status_code}")
    if r.status_code == 302:
        print(f"   ✓ redirect → {r.get('Location', '')}")
    u.refresh_from_db()
    print(f"   ✓ has_completed: {u.has_completed_registration}")

    # ۵. Game
    r = c2.get("/game/", follow=False)
    print(f"5. GET /game/         → {r.status_code}")

    # ۶. Profile
    r = c2.get("/accounts/profile/", follow=False)
    print(f"6. GET /accounts/profile/   → {r.status_code}")
    if r.status_code == 200:
        has_name = "کاربر تست" in r.content.decode(errors="ignore")
        print(f"   نام نمایشی: {'✓' if has_name else '✗'}")

    # ۷. Avatar change
    r = c2.get("/accounts/avatar/", follow=False)
    print(f"7. GET /accounts/avatar/    → {r.status_code}")

    # ۸. Settings
    r = c2.get("/accounts/settings/", follow=False)
    print(f"8. GET /accounts/settings/  → {r.status_code}")

# ۹. Login page
c3 = Client()
r = c3.get("/accounts/login/", follow=False)
print(f"9. GET /accounts/login/     → {r.status_code}")

# ۱۰. Login POST
r = c3.post("/accounts/login/", {
    "username": "__q_test__",
    "password": "test123456",
}, follow=False)
print(f"10. POST /accounts/login/   → {r.status_code}")

# پاک‌سازی
User.objects.filter(username__startswith="__q_").delete()
print("\\n✓ تمیز")
'''

r = subprocess.run(
    [sys.executable, "-c", TEST],
    env={**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings"},
    capture_output=True, text=True
)
print(r.stdout)
if r.stderr and "Traceback" in r.stderr:
    print("STDERR:", r.stderr[:600])

print("\n" + "="*60)
print("✅ تمام")
print("="*60)
print("""
حالا:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver

مرورگر:
  http://127.0.0.1:8000/                       ← صفحه اصلی (بدون قفل)
  http://127.0.0.1:8000/accounts/register/     ← ثبت‌نام
  http://127.0.0.1:8000/accounts/login/        ← ورود
  http://127.0.0.1:8000/accounts/profile/      ← پروفایل

نوار پایین: 🏠 خانه | 🎮 بازی‌ها | 🚪 اتاق‌ها | 👥 دوستان | 👤 پروفایل
""")
