from django.contrib import admin
from .models import Alliance, AllianceMember, AllianceMessage


@admin.register(Alliance)
class AllianceAdmin(admin.ModelAdmin):
    list_display = ("name", "tag", "leader", "member_count", "created_at")
    search_fields = ("name", "tag", "invite_code")


@admin.register(AllianceMember)
class AllianceMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "alliance", "role", "joined_at")
    list_filter = ("role",)


@admin.register(AllianceMessage)
class AllianceMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "alliance", "body", "sent_at")
