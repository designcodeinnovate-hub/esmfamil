from django.urls import path
from . import admin_views

app_name = "custom_admin"

urlpatterns = [
    path("", admin_views.admin_login, name="login"),
    path("dashboard/", admin_views.dashboard, name="dashboard"),
    path("logout/", admin_views.admin_logout, name="logout"),
    path("user/<int:user_id>/", admin_views.user_detail, name="user_detail"),
    path("user/<int:user_id>/toggle/", admin_views.user_toggle_active, name="user_toggle"),
    path("user/<int:user_id>/delete/", admin_views.user_delete, name="user_delete"),
    path("user/<int:user_id>/reset-password/", admin_views.user_reset_password, name="user_reset_password"),
    path("user/<int:user_id>/change-alias/", admin_views.user_change_alias, name="user_change_alias"),
]
