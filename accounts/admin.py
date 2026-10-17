from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "alias", "username", "is_active", "email_verified_at", "is_staff")
    search_fields = ("email", "alias", "username")
    ordering = ("-date_joined",)

    readonly_fields = ("date_joined", "email_verified_at")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("alias", "username")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "email_verified_at",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Timestamps", {"fields": ("date_joined",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "alias", "password1", "password2"),
            },
        ),
    )