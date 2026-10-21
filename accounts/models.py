import random
import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.db import models
from django.utils import timezone


def _generate_public_id():
    while True:
        candidate = random.randint(100_000_000, 999_999_999)
        if not User.objects.filter(public_id=candidate).exists():
            return candidate


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra):
        if not username:
            raise ValueError("نام کاربری الزامی است")
        username = username.strip().lower()
        user = self.model(username=username, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_active", True)
        extra.setdefault("has_chosen_avatar", True)
        extra.setdefault("has_completed_registration", True)
        extra.setdefault("alias", username)
        extra.setdefault("email_verified_at", timezone.now())
        return self.create_user(username, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    # ===== اطلاعات ورود =====
    username = models.CharField(max_length=32, unique=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    # ===== پروفایل =====
    alias = models.CharField(max_length=32, blank=True)  # نام نمایشی
    public_id = models.PositiveBigIntegerField(unique=True, editable=False)
    avatar_id = models.PositiveSmallIntegerField(null=True, blank=True)
    avatar_type = models.CharField(max_length=8, default="emoji")  # emoji | image
    has_chosen_avatar = models.BooleanField(default=False)
    has_completed_registration = models.BooleanField(default=False)
    is_guest = models.BooleanField(default=False)

    # ===== تنظیمات =====
    settings_json = models.JSONField(default=dict, blank=True)

    # ===== وضعیت =====
    is_active = models.BooleanField(default=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=timezone.now)
    coins = models.IntegerField(default=0)
    gems = models.IntegerField(default=0)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    DEFAULT_SETTINGS = {
        "sound": True,
        "music": True,
        "sound_vol": 80,
        "music_vol": 50,
        "notif_invite": True,
        "notif_friend": True,
        "notif_round": True,
        "theme": "dark",
        "font_size": "medium",
        "animations": True,
        "vibration": True,
    }

    def get_settings(self):
        s = dict(self.DEFAULT_SETTINGS)
        s.update(self.settings_json or {})
        return s

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = _generate_public_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.public_id})"


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_tokens")
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def issue(cls, user):
        return cls.objects.create(user=user, token=secrets.token_urlsafe(32))

    def is_valid(self):
        if self.used_at:
            return False
        return timezone.now() < self.created_at + timedelta(hours=24)


class ShopItem(models.Model):
    CATEGORY_CHOICES = [
        ("box", "جعبه شانس"),
        ("boost", "بوست"),
        ("theme", "تم"),
        ("bundle", "بسته ارز"),
        ("cosmetic", "آیتم ظاهری"),
    ]
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=8, default="🎁")
    category = models.CharField(max_length=12, choices=CATEGORY_CHOICES, default="cosmetic")
    price_coins = models.PositiveIntegerField(default=0)
    price_gems = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    reward_type = models.CharField(max_length=20, blank=True)
    reward_value = models.IntegerField(default=0)
    reward_min = models.IntegerField(default=0)
    reward_max = models.IntegerField(default=0)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sort_order", "-created_at")

    def __str__(self):
        return f"{self.icon} {self.name}"


class Purchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchases")
    item = models.ForeignKey(ShopItem, on_delete=models.SET_NULL, null=True, blank=True, related_name="purchases")
    item_name = models.CharField(max_length=60)
    item_icon = models.CharField(max_length=8, default="🎁")
    price_paid_coins = models.PositiveIntegerField(default=0)
    price_paid_gems = models.PositiveIntegerField(default=0)
    reward_given = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.alias} - {self.item_name}"

class GuestDeletionLog(models.Model):
    """Log of deleted guest accounts (kept after guest is removed)."""
    username = models.CharField(max_length=32)
    alias = models.CharField(max_length=32, blank=True)
    public_id = models.PositiveBigIntegerField(null=True, blank=True)
    avatar_id = models.PositiveSmallIntegerField(null=True, blank=True)
    total_games = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)  # when guest was created
    deleted_at = models.DateTimeField(auto_now_add=True)  # when deleted

    class Meta:
        ordering = ("-deleted_at",)

    def __str__(self):
        return f"Guest {self.username} deleted at {self.deleted_at}"


class UserUnlockedAvatar(models.Model):
    """آواتارهای تصویری بازشده (50 سکه برای هر آواتار)"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="unlocked_avatars",
    )
    avatar_type = models.CharField(max_length=10, default="image")
    avatar_id = models.PositiveSmallIntegerField()
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "avatar_type", "avatar_id")
        ordering = ("-unlocked_at",)

    def __str__(self):
        return f"{self.user.alias} - {self.avatar_type}#{self.avatar_id}"
