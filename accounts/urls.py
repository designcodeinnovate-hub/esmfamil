from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import shop_views
from .views import (
    shop_view,
    LoginView, MeView, RegisterView,
    avatar_select, complete_registration, guest_start, login_view, logout_view,
    profile_view, register_view, settings_view,
    support_home, support_detail,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
]

web_urlpatterns = [
    path("register/", register_view, name="register_view"),
    path("login/", login_view, name="login_view"),
    path("complete/", complete_registration, name="complete_registration"),
    path("shop/", shop_views.shop_home, name="shop"),
    path("shop/buy/<int:item_id>/", shop_views.shop_buy, name="shop_buy"),
    path("shop/exchange/", shop_views.shop_exchange, name="shop_exchange"),
    path("avatar/", avatar_select, name="avatar_select"),
    path("profile/", profile_view, name="profile"),
    path("settings/", settings_view, name="settings"),
    path("logout/", logout_view, name="logout"),
    path("support/", support_home, name="support_home"),
    path("support/<int:ticket_id>/", support_detail, name="support_detail"),
    path("guest/", guest_start, name="guest_start"),
]
