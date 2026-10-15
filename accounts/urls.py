from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView, MeView, RegisterView, ResendVerificationView, VerifyEmailView,
    avatar_select, email_login, guest_name, guest_start, logout_view, profile_view, settings_view,
    register_view, verify_email_web,
)

urlpatterns = [
    # API
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend_verification"),
]

# Web (HTML)
web_urlpatterns = [
    path("avatar/", avatar_select, name="avatar_select"),
    path("profile/", profile_view, name="profile"),
    path("signup/", register_view, name="signup"),
    path("verify/", verify_email_web, name="verify_web"),
    path("login/", email_login, name="email_login"),
    path("settings/", settings_view, name="settings"),
    path("logout/", logout_view, name="logout"),
    path("guest/start/", guest_start, name="guest_start"),
    path("guest/name/", guest_name, name="guest_name"),
]
