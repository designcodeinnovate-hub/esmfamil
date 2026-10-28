import random
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


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
    GAME_TYPE_CHOICES = [
        ("esm_famil", "اسم فامیل"),
        ("puzzle", "معما"),
        ("memory", "حافظه"),
        ("guess", "۰ تا ۱۰۰"),
        ("chain", "زنجیره"),
        ("speed", "سرعتی"),
        ("custom", "سفارشی"),
    ]
    game_type = models.CharField(max_length=15, choices=GAME_TYPE_CHOICES, default="esm_famil")
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

class DailyRewardClaim(models.Model):
    """7-day streak daily reward with midnight reset."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="daily_rewards",
    )
    amount = models.PositiveIntegerField(default=50)
    day_number = models.PositiveSmallIntegerField(default=1)  # 1..7
    claim_date = models.DateField(default=timezone.localdate)  # Gregorian date
    claimed_at = models.DateTimeField(auto_now_add=True)

    # 7-day streak rewards (coins)
    REWARDS = [50, 75, 100, 125, 150, 175, 250]

    class Meta:
        ordering = ("-claimed_at",)
        unique_together = ("user", "claim_date")

    def __str__(self):
        return f"{self.user_id}:day{self.day_number}:+{self.amount}"

    @classmethod
    def get_status(cls, user):
        """
        Returns dict:
          - can_claim: bool (hasn't claimed today AND streak is valid)
          - today_claimed: bool
          - current_streak: 0..7 (from last claim)
          - next_day: 1..7 (which day to claim)
          - seconds_until_midnight: seconds until 00:00
          - rewards: list of 7 rewards
        """
        from django.utils import timezone
        from datetime import timedelta, datetime as dt

        now = timezone.now()
        today = now.date()

        # Midnight next
        tomorrow_midnight = dt.combine(today + timedelta(days=1), dt.min.time())
        seconds_until_midnight = int((tomorrow_midnight - now.replace(tzinfo=None)).total_seconds())
        if seconds_until_midnight < 0:
            seconds_until_midnight = 0

        # Check today's claim
        today_claim = cls.objects.filter(user=user, claim_date=today).first()
        today_claimed = today_claim is not None

        # Get latest claim (any day)
        last = cls.objects.filter(user=user).order_by("-claim_date").first()

        if not last:
            # New user
            return {
                "can_claim": True,
                "today_claimed": False,
                "current_streak": 0,
                "next_day": 1,
                "seconds_until_midnight": seconds_until_midnight,
                "rewards": cls.REWARDS,
            }

        days_since_last = (today - last.claim_date).days

        if days_since_last == 0:
            # Claimed today already
            current_streak = last.day_number
            next_day = last.day_number + 1
            if next_day > 7:
                next_day = 1  # start over after day 7
            return {
                "can_claim": False,
                "today_claimed": True,
                "current_streak": current_streak,
                "next_day": next_day,
                "seconds_until_midnight": seconds_until_midnight,
                "rewards": cls.REWARDS,
            }

        elif days_since_last == 1:
            # Claimed yesterday — streak continues
            current_streak = last.day_number
            next_day = current_streak + 1
            if next_day > 7:
                next_day = 1
            return {
                "can_claim": True,
                "today_claimed": False,
                "current_streak": current_streak,
                "next_day": next_day,
                "seconds_until_midnight": seconds_until_midnight,
                "rewards": cls.REWARDS,
            }

        else:
            # More than 1 day gap — streak broken
            return {
                "can_claim": True,
                "today_claimed": False,
                "current_streak": 0,
                "next_day": 1,
                "seconds_until_midnight": seconds_until_midnight,
                "rewards": cls.REWARDS,
            }

    @classmethod
    def claim(cls, user):
        """Claim today's reward if possible. Returns (success, message, amount)."""
        status = cls.get_status(user)
        if not status["can_claim"]:
            return False, "امروز قبلاً جایزه‌تون رو گرفتید. فردا دوباره سر بزنید!", 0

        day_num = status["next_day"]
        amount = cls.REWARDS[day_num - 1]

        try:
            cls.objects.create(user=user, amount=amount, day_number=day_num)
        except Exception:
            # Already claimed (race condition)
            return False, "شما قبلاً جایزه امروز رو گرفتید.", 0

        user.coins = (user.coins or 0) + amount
        user.save(update_fields=["coins"])
        return True, f"🎉 روز {day_num}: {amount} سکه به حسابتون اضافه شد!", amount


# ============================================================
# ONLINE MULTIPLAYER — پایه مشترک برای همه مودها
# ============================================================

class OnlineGame(models.Model):
    """بازی آنلاین ۱v۱ — محتوای مشترک هر دو بازیکن رو نگه می‌داره."""
    MODES = [
        ("1v1", "اسم فامیل"),         # match فعلی (اسم فامیل)
        ("puzzle", "معما"),
        ("memory", "حافظه"),
        ("guess", "۰ تا ۱۰۰"),
        ("chain", "زنجیره کلمات"),
    ]

    STATUS = [
        ("waiting", "در انتظار شروع"),
        ("playing", "در حال بازی"),
        ("finished", "پایان یافته"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mode = models.CharField(max_length=12, choices=MODES)
    status = models.CharField(max_length=12, choices=STATUS, default="waiting")

    # محتوای مشترک بازی (برای هر مود ساختارش فرق می‌کنه)
    payload = models.JSONField(default=dict, blank=True)

    # نتیجه
    winner_user_id = models.IntegerField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.mode}:{self.id} ({self.status})"


class OnlinePlayer(models.Model):
    """بازیکن تو یه بازی آنلاین — با امتیاز و زمان پایان."""
    game = models.ForeignKey(OnlineGame, on_delete=models.CASCADE, related_name="players")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    finished_at = models.DateTimeField(null=True, blank=True)
    is_ready = models.BooleanField(default=False)

    class Meta:
        unique_together = ("game", "user")

    def __str__(self):
        return f"{self.user.alias} in {self.game_id}"


# === ONLINE MULTIPLAYER (Phase 1) ===
