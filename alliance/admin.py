from django.contrib import admin
from .models import (
    Alliance, AllianceMember, AllianceMessage,
    AllianceJoinRequest, AllianceEvent,
)


@admin.register(Alliance)
class AllianceAdmin(admin.ModelAdmin):
    list_display = ("name", "leader", "member_count", "join_type", "created_at")
    search_fields = ("name", "invite_code")
    list_filter = ("join_type", "created_at")


@admin.register(AllianceMember)
class AllianceMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "alliance", "role", "is_muted", "joined_at")
    list_filter = ("role", "is_muted")


@admin.register(AllianceMessage)
class AllianceMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "alliance", "message_type", "body", "sent_at")
    list_filter = ("message_type", "is_deleted")


@admin.register(AllianceJoinRequest)
class AllianceJoinRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "alliance", "status", "created_at")
    list_filter = ("status",)


@admin.register(AllianceEvent)
class AllianceEventAdmin(admin.ModelAdmin):
    list_display = ("alliance", "event_type", "actor", "target", "created_at")
    list_filter = ("event_type",)

from .models import AllianceGameInvite, AllianceGameInterest


@admin.register(AllianceGameInvite)
class AllianceGameInviteAdmin(admin.ModelAdmin):
    list_display = ("host", "alliance", "game_type", "status", "created_at")
    list_filter = ("status", "game_type")


@admin.register(AllianceGameInterest)
class AllianceGameInterestAdmin(admin.ModelAdmin):
    list_display = ("user", "invite", "is_kicked", "joined_at")
    list_filter = ("is_kicked",)
