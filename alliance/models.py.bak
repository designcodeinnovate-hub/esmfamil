import random
import string

from django.conf import settings
from django.db import models
from django.utils import timezone


def _generate_invite_code():
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Alliance.objects.filter(invite_code=code).exists():
            return code


class Alliance(models.Model):
    name = models.CharField(max_length=40, unique=True)
    tag = models.CharField(max_length=8, blank=True)  # مثلا [IRN]
    description = models.CharField(max_length=200, blank=True)
    emblem = models.CharField(max_length=4, default="🛡️")  # emoji
    invite_code = models.CharField(max_length=6, unique=True, editable=False)
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="led_alliances",
    )
    max_members = models.PositiveIntegerField(default=30)
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
        ("officer", "افسر"),
        ("member", "عضو"),
    ]

    alliance = models.ForeignKey(Alliance, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alliance_memberships")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("alliance", "user")

    def __str__(self):
        return f"{self.user.alias} in {self.alliance.name} ({self.role})"


class AllianceMessage(models.Model):
    alliance = models.ForeignKey(Alliance, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.CharField(max_length=500)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sent_at",)

    def __str__(self):
        return f"{self.sender.alias}: {self.body[:30]}"
