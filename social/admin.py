from django.contrib import admin
from .models import Friendship, Notification


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ("from_user", "to_user", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("from_user__alias", "to_user__alias")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "title", "is_read", "created_at")
    list_filter = ("type", "is_read")
    search_fields = ("user__alias", "title")

from .models import DirectChat, DirectMessage


@admin.register(DirectChat)
class DirectChatAdmin(admin.ModelAdmin):
    list_display = ("user1", "user2", "last_message_at", "created_at")
    search_fields = ("user1__alias", "user2__alias")


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "chat", "body", "is_read", "sent_at")
    list_filter = ("is_read",)
