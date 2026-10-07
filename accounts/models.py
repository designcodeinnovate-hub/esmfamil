import random

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


def _generate_public_id() -> int:
    """Random unique 9-digit public id."""
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
        return self.create_user(email, alias, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    alias = models.CharField(max_length=32, unique=True)
    public_id = models.PositiveBigIntegerField(unique=True, editable=False)

    is_active = models.BooleanField(default=True)   # set False once email verification lands
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["alias"]

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = _generate_public_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.alias} ({self.public_id})"