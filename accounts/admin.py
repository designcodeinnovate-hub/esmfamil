from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "alias", "public_id", "is_active", "is_staff")
    search_fields = ("email", "alias", "public_id")
    ordering = ("-date_joined",)

    # Show public_id as read-only, not as an editable input
    readonly_fields = ("public_id", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("alias", "public_id")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
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