from django.urls import path
from . import views
from . import shop_views

app_name = "accounts"

# Web routes (used with namespace accounts)
web_urlpatterns = [
    path("register/", views.register_view, name="register_view"),
    path("check-username/", views.check_username, name="check_username"),
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
