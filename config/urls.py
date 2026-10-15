from django.contrib import admin
from django.urls import include, path

from accounts.urls import web_urlpatterns as accounts_web
from accounts.views import landing

urlpatterns = [
    path("", landing, name="landing"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("accounts/", include(accounts_web)),
    path("game/", include("game.urls")),
    path("social/", include("social.urls")),
    path("alliance/", include("alliance.urls")),
]
