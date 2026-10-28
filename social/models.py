from django.conf import settings
from django.db import models


class Friendship(models.Model):
    STATUS_CHOICES = [
        ("pending", "در انتظار"),
        ("accepted", "پذیرفته شده"),
        ("rejected", "رد شده"),
    ]

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_friend_requests",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_friend_requests",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("from_user", "to_user")

    def __str__(self):
        return f"{self.from_user.alias} -> {self.to_user.alias} ({self.status})"


class Notification(models.Model):
    TYPES = [
        ("friend_request", "درخواست دوستی"),
        ("friend_accepted", "قبول دوستی"),
        ("message", "پیام جدید"),
        ("game_invite", "دعوت به بازی"),
        ("game_result", "نتیجه بازی"),
        ("alliance_invite", "دعوت به اتحاد"),
        ("admin_broadcast", "اعلان مدیر"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=20, choices=TYPES)
    title = models.CharField(max_length=100)
    body = models.CharField(max_length=300, blank=True)
    url = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.alias} — {self.title}"


class GameInvite(models.Model):
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_invites")
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_invites")
    game = models.ForeignKey("game.Game", on_delete=models.CASCADE)
    status = models.CharField(max_length=10, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.from_user.alias} -> {self.to_user.alias} ({self.status})"


class NotificationRead(models.Model):
    """Track when each user reads a broadcast notification."""
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="reads"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("notification", "user")
        ordering = ("-read_at",)

    def __str__(self):
        return f"{self.user.alias} read #{self.notification_id}"

# ============================================================
# Direct Chat — 1-on-1 messaging between friends
# ============================================================
class DirectChat(models.Model):
    """
    A 1-on-1 conversation between two users.
    user1_id < user2_id is enforced to prevent duplicates.
    Soft-delete: each side can "clear" the chat independently.
    """
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="direct_chats_as_user1",
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="direct_chats_as_user2",
    )
    # Soft-delete flags
    user1_deleted_at = models.DateTimeField(null=True, blank=True)
    user2_deleted_at = models.DateTimeField(null=True, blank=True)
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user1", "user2")
        ordering = ("-last_message_at",)

    def save(self, *args, **kwargs):
        # Enforce ordering to prevent A->B vs B->A duplicates
        if self.user1_id and self.user2_id and self.user1_id > self.user2_id:
            self.user1_id, self.user2_id = self.user2_id, self.user1_id
        super().save(*args, **kwargs)

    def other_user(self, me):
        return self.user2 if self.user1_id == me.id else self.user1

    def __str__(self):
        return f"{self.user1.alias} ↔ {self.user2.alias}"


class DirectMessage(models.Model):
    chat = models.ForeignKey(DirectChat, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField(max_length=2000)
    is_read = models.BooleanField(default=False)
    # Soft-delete per-side (user can "delete for me" — the other still sees it)
    deleted_by_sender = models.BooleanField(default=False)
    deleted_by_receiver = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("sent_at",)
        indexes = [
            models.Index(fields=["chat", "-sent_at"]),
        ]

    def visible_to(self, user):
        """Return True if `user` should see this message."""
        if user.id == self.sender_id:
            return not self.deleted_by_sender
        return not self.deleted_by_receiver

    def __str__(self):
        return f"{self.sender.alias}: {self.body[:30]}"

