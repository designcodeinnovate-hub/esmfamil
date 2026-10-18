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
    intended_game_type = models.CharField(max_length=16, blank=True, default="")
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
    team = models.CharField(max_length=1, blank=True, default="")
    team_ready = models.BooleanField(default=False)
    stopped_round = models.PositiveIntegerField(default=0)

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
    mode = models.CharField(max_length=8, default="1v1")
    difficulty = models.CharField(max_length=8, default="medium")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("joined_at",)

    def __str__(self):
        return f"{self.user.alias} in queue"

class Tournament(models.Model):
    STATUS = [
        ("scheduled", "برنامه‌ریزی شده"),
        ("active", "در حال برگزاری"),
        ("finished", "پایان یافته"),
        ("cancelled", "لغو شده"),
    ]
    TYPE = [
        ("daily", "روزانه"),
        ("hourly", "ساعتی"),
        ("weekly", "هفتگی"),
    ]
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True, max_length=300)
    tournament_type = models.CharField(max_length=10, choices=TYPE, default="daily")
    status = models.CharField(max_length=12, choices=STATUS, default="scheduled")
    icon = models.CharField(max_length=4, default="🏆")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    entry_fee_coins = models.IntegerField(default=0)
    entry_fee_gems = models.IntegerField(default=0)
    prize_coins = models.IntegerField(default=0)
    prize_gems = models.IntegerField(default=0)
    max_players = models.PositiveIntegerField(default=100)
    min_players = models.PositiveIntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
    )

    class Meta:
        ordering = ("-start_at",)

    def __str__(self):
        return f"{self.icon} {self.name}"

    @property
    def is_upcoming(self):
        from django.utils import timezone
        return self.status == "scheduled" and timezone.now() < self.start_at

    @property
    def is_live(self):
        from django.utils import timezone
        now = timezone.now()
        return self.status == "active" or (self.status == "scheduled" and self.start_at <= now < self.end_at)

    @property
    def is_finished(self):
        from django.utils import timezone
        return self.status == "finished" or timezone.now() >= self.end_at

    def time_until_start(self):
        from django.utils import timezone
        if self.start_at <= timezone.now():
            return 0
        return int((self.start_at - timezone.now()).total_seconds())

    def time_until_end(self):
        from django.utils import timezone
        if self.end_at <= timezone.now():
            return 0
        return int((self.end_at - timezone.now()).total_seconds())

    def entry_count(self):
        return self.entries.count()


class TournamentEntry(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="entries")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=0)

    class Meta:
        unique_together = ("tournament", "user")
        ordering = ("-score", "joined_at")

