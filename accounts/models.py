import random
import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


def _generate_public_id() -> int:
    while True:
        candidate = random.randint(100_000_000, 999_999_999)
        if not User.objects.filter(public_id=candidate).exists():
            return candidate


class UserManager(BaseUserManager):
    def create_user(self, email, alias, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        if not alias:
            raise ValueError("Alias is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, alias=alias, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, alias, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_active", True)
        extra.setdefault("email_verified_at", timezone.now())
        extra.setdefault("has_chosen_avatar", True)
        return self.create_user(email, alias, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    alias = models.CharField(max_length=32, unique=True)
    public_id = models.PositiveBigIntegerField(unique=True, editable=False)

    is_active = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    avatar_id = models.PositiveSmallIntegerField(null=True, blank=True)
    has_chosen_avatar = models.BooleanField(default=False)

    # تنظیمات کاربر (JSON)
    settings_json = models.JSONField(default=dict, blank=True)

    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["alias"]

    DEFAULT_SETTINGS = {
        "sound": True,
        "music": True,
        "notif_invite": True,
        "notif_friend": True,
        "notif_round": True,
        "theme": "dark",
        "vibration": True,
    }

    def get_settings(self):
        """تنظیمات کاربر با مقادیر پیش‌فرض."""
        s = dict(self.DEFAULT_SETTINGS)
        s.update(self.settings_json or {})
        return s

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = _generate_public_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.alias} ({self.public_id})"


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
