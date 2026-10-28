# -*- coding: utf-8 -*-
import random
import string

from django.conf import settings
from django.db import models


def _generate_invite_code():
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Alliance.objects.filter(invite_code=code).exists():
            return code


class Alliance(models.Model):
    JOIN_TYPE_CHOICES = [
        ("open", "آزاد"),
        ("request", "درخواست"),
        ("invite", "لینک دعوت"),
    ]
    WHO_CAN_CHOICES = [
        ("all", "همه اعضا"),
        ("admins", "فقط مدیران"),
        ("leader", "فقط رهبر"),
    ]

    name = models.CharField(max_length=40, unique=True)
    description = models.TextField(max_length=500, blank=True)
    emblem = models.CharField(max_length=4, default="🛡️")
    invite_code = models.CharField(max_length=8, unique=True, editable=False)
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="led_alliances",
    )
    max_members = models.PositiveIntegerField(default=50)
    join_type = models.CharField(max_length=10, choices=JOIN_TYPE_CHOICES, default="open")
    who_can_send = models.CharField(max_length=10, choices=WHO_CAN_CHOICES, default="all")
    who_can_add = models.CharField(max_length=10, choices=WHO_CAN_CHOICES, default="admins")
    who_can_edit = models.CharField(max_length=10, choices=WHO_CAN_CHOICES, default="leader")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = _generate_invite_code()
        super().save(*args, **kwargs)

    def member_count(self):
        return self.members.count()

    def __str__(self):
        return f"{self.emblem} {self.name}"


class AllianceMember(models.Model):
    ROLE_CHOICES = [
        ("leader", "رهبر"),
        ("admin", "مدیر"),
        ("member", "عضو"),
    ]
    JOINED_VIA_CHOICES = [
        ("creator", "سازنده"),
        ("invite_link", "لینک دعوت"),
        ("invite_code", "کد دعوت"),
        ("request", "درخواست"),
        ("direct_add", "افزوده شده"),
    ]

    alliance = models.ForeignKey(Alliance, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alliance_memberships")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")
    joined_via = models.CharField(max_length=20, choices=JOINED_VIA_CHOICES, default="invite_code")
    is_muted = models.BooleanField(default=False)
    notifications_enabled = models.BooleanField(default=True)
    nickname = models.CharField(max_length=32, blank=True, default="")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("alliance", "user")
        ordering = ("-role", "joined_at")

    def __str__(self):
        return f"{self.user.alias} in {self.alliance.name} ({self.role})"


class AllianceMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ("text", "متنی"),
        ("system", "سیستمی"),
    ]

    alliance = models.ForeignKey(Alliance, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True,
    )
    body = models.TextField(max_length=2000)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default="text")
    reply_to = models.ForeignKey(
        "self", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="replies",
    )
    is_deleted = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-sent_at",)

    def __str__(self):
        sender = self.sender.alias if self.sender else "سیستم"
        return f"{sender}: {self.body[:30]}"


class AllianceJoinRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "در انتظار"),
        ("accepted", "پذیرفته شده"),
        ("rejected", "رد شده"),
    ]

    alliance = models.ForeignKey(Alliance, on_delete=models.CASCADE, related_name="join_requests")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alliance_join_requests")
    message = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.alias} -> {self.alliance.name} ({self.status})"


class AllianceEvent(models.Model):
    EVENT_TYPES = [
        ("created", "ساخته شد"),
        ("member_joined", "عضو جدید"),
        ("member_left", "عضو خارج شد"),
        ("member_kicked", "عضو اخراج شد"),
        ("promoted", "ارتقا به مدیر"),
        ("demoted", "حذف از مدیریت"),
        ("info_changed", "اطلاعات تغییر کرد"),
        ("message_pinned", "پیام سنجاق شد"),
    ]

    alliance = models.ForeignKey(Alliance, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
    )
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.event_type} in {self.alliance.name}"

# ============================================================
# Alliance Game Invite — "who wants to play X?"
# ============================================================
class AllianceGameInvite(models.Model):
    STATUS_CHOICES = [
        ("open", "در حال جمع کردن"),
        ("started", "شروع شده"),
        ("cancelled", "لغو شده"),
        ("expired", "منقضی"),
    ]
    GAME_TYPE_CHOICES = [
        ("1v1", "اسم فامیل (۱v۱)"),
        ("team", "گروهی (۲v۲)"),
        ("puzzle", "معما"),
        ("memory", "حافظه"),
        ("chain", "زنجیره کلمات"),
        ("speed", "سرعتی"),
    ]

    alliance = models.ForeignKey(Alliance, on_delete=models.CASCADE, related_name="game_invites")
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="hosted_alliance_games",
    )
    game_type = models.CharField(max_length=10, choices=GAME_TYPE_CHOICES, default="1v1")
    # Was a message posted in alliance chat, or standalone? We connect both.
    chat_message = models.ForeignKey(
        AllianceMessage, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="game_invites",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    min_players = models.PositiveSmallIntegerField(default=2)
    max_players = models.PositiveSmallIntegerField(default=8)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # The actual game (created when host clicks "Start")
    game = models.ForeignKey(
        "game.Game", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="alliance_invites",
    )

    class Meta:
        ordering = ("-created_at",)

    def interested_count(self):
        return self.interests.filter(is_kicked=False).count()

    def __str__(self):
        return f"{self.host.alias} → {self.get_game_type_display()}"


class AllianceGameInterest(models.Model):
    """A member clicked 'I'm in' on a game invite."""
    invite = models.ForeignKey(
        AllianceGameInvite, on_delete=models.CASCADE,
        related_name="interests",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="alliance_game_interests",
    )
    is_kicked = models.BooleanField(default=False)  # host can kick
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("invite", "user")
        ordering = ("joined_at",)

    def __str__(self):
        return f"{self.user.alias} → {self.invite}"

