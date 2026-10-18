import random
import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
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
