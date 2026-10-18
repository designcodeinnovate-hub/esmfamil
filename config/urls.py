from django.contrib import admin
from django.urls import include, path

from accounts.urls import web_urlpatterns as accounts_web
from accounts.views import landing
from config.beta_views import beta_lock, beta_logout
from config.service_worker_view import service_worker


urlpatterns = [
    # Beta Gate
    path("beta-lock/", beta_lock, name="beta_lock"),
    path("beta-logout/", beta_logout, name="beta_logout"),

    # پنل ادمین پیش‌فرض Django
    path("django-admin/", admin.site.urls),

    # پنل ادمین سفارشی
    path("panel-admin/", include("accounts.admin_urls")),

    # API
    path("api/auth/", include("accounts.urls")),

    # Web (با namespace "accounts")
    path("accounts/", include((accounts_web, "accounts"), namespace="accounts")),

    # سایر اپ‌ها
    path("game/", include("game.urls")),
    path("social/", include("social.urls")),
    path("alliance/", include("alliance.urls")),

    # اعلان‌ها (در خانه)
    path("notifications/", __import__("social.views", fromlist=["notifications_view"]).notifications_view, name="notifications_root"),

    # PWA service worker
    path("sw.js", service_worker, name="service_worker"),

    # ریشه → landing
    path("", landing, name="landing"),
]
