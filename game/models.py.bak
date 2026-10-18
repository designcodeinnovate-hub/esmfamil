import random
import uuid

from django.conf import settings
from django.db import models


PERSIAN_LETTERS = list("آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی")

DEFAULT_CATEGORIES = [
    "اسم", "فامیل", "میوه", "رنگ", "شهر", "کشور", "ماشین", "حیوان", "اشیاء", "غذا",
    "شغل", "اعضای بدن", "نام گل", "فیلم", "خواننده", "برند", "ورزش", "ابزار", "لباس", 
    "شخصیت کارتونی", "کتاب", "مکان", "گیاه", "مزه", "صدا", "پارچه", "بیماری", 
    "زبان", "عدد", "کلمه انگلیسی"
]


class Game(models.Model):
    STATUS_CHOICES = [
        ("waiting", "waiting"),
        ("in_round", "in_round"),
        ("round_result", "round_result"),
        ("finished", "finished"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=6, unique=True, editable=False, null=True, blank=True)
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hosted_games",
    )
    password = models.CharField(max_length=32, blank=True)
    room_name = models.CharField(max_length=50, blank=True, default="اتاق بازی")
    max_players = models.PositiveIntegerField(default=8)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="waiting")
    categories = models.JSONField(default=list)
    mode = models.CharField(max_length=16, default="group")
    difficulty = models.CharField(max_length=8, default="medium")
    letter_mode = models.CharField(max_length=16, default="random")
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_code():
        while True:
            c = str(random.randint(1000, 9999))
            if not Game.objects.filter(code=c).exists():
                return c

    def __str__(self):
        return f"Game {self.code} ({self.status})"


class Player(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="players")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    is_ready = models.BooleanField(default=False)

    class Meta:
        unique_together = ("game", "user")


class Round(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="rounds")
    number = models.PositiveIntegerField(default=1)
    letter = models.CharField(max_length=2)
    duration = models.PositiveIntegerField(default=60)
    started_at = models.DateTimeField(auto_now_add=True)
    stopped_at = models.DateTimeField(null=True, blank=True)
    stopper = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
    )

    class Meta:
        unique_together = ("game", "number")


class Answer(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="answers")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=32)
    value = models.CharField(max_length=64, blank=True)
    normalized = models.CharField(max_length=64, blank=True)
    score = models.IntegerField(default=0)

    class Meta:
        unique_together = ("round", "user", "category")


class BotAnswer(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="bot_answers")
    category = models.CharField(max_length=32)
    value = models.CharField(max_length=64, blank=True)
    normalized = models.CharField(max_length=64, blank=True)
    score = models.IntegerField(default=0)

    class Meta:
        unique_together = ("round", "category")


class MatchQueue(models.Model):
    """صف انتظار برای بازی رندم."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="match_queue",
    )
    difficulty = models.CharField(max_length=8, default="medium")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("joined_at",)

    def __str__(self):
        return f"{self.user.alias} in queue"
