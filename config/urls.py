from django.contrib import admin
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
    path("support/", include("support.urls")),

    # Landing
    path("", landing, name="landing"),
]
