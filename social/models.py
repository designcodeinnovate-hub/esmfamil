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
