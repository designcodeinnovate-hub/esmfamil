#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, subprocess, sys
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")
def backup(p):
    bak = p + ".bak_t"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) social/models.py - add admin_broadcast type
# ============================================================
print("\n[1/9] social/models.py")
p = os.path.join(ROOT, "social", "models.py")
src = read(p)
if '("admin_broadcast"' in src:
    print("  SKIP")
else:
    old = '        ("alliance_invite", "دعوت به اتحاد"),\n    ]'
    new = '        ("alliance_invite", "دعوت به اتحاد"),\n        ("admin_broadcast", "اعلان مدیر"),\n    ]'
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: admin_broadcast added")
    else:
        print("  WARN: TYPES block not found")

# ============================================================
# 2) game/models.py - Tournament + TournamentEntry
# ============================================================
print("\n[2/9] game/models.py - Tournament + TournamentEntry")
p = os.path.join(ROOT, "game", "models.py")
src = read(p)

if "class Tournament(models.Model):" in src:
    print("  SKIP: already exists")
else:
    tournament_code = '''

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
'''
    src = src.rstrip() + tournament_code + "\n"
    backup(p); write(p, src)
    print("  FIXED: Tournament + TournamentEntry added")

# ============================================================
# 3) admin_views.py - add announcement + tournament views
# ============================================================
print("\n[3/9] accounts/admin_views.py")
p = os.path.join(ROOT, "accounts", "admin_views.py")
src = read(p)

# Strip previously added section
marker = "# ============================================================\n# Admin — Announcements"
if marker in src:
    src = src[:src.find(marker)].rstrip() + "\n"

code = r'''

# ============================================================
# Admin — Announcements (broadcast to all users)
# ============================================================
def _parse_dt(s):
    from datetime import datetime
    from django.utils import timezone as tz
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        if tz.is_naive(dt):
            dt = tz.make_aware(dt)
        return dt
    except (ValueError, TypeError):
        return None


@never_cache
def announcements_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    from social.models import Notification

    qs = Notification.objects.filter(type="admin_broadcast").order_by("-created_at")

    # Dedupe by (title, body)
    seen = set()
    data = []
    for n in qs.iterator(chunk_size=200):
        key = (n.title, n.body or "", n.url or "")
        if key in seen:
            continue
        seen.add(key)
        # Count how many users got this
        count = Notification.objects.filter(
            type="admin_broadcast", title=n.title, body=n.body or "", url=n.url or ""
        ).count()
        data.append({
            "title": n.title,
            "body": n.body,
            "url": n.url,
            "created_at": n.created_at,
            "recipients": count,
        })

    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/announcements.html", {
        "announcements": data,
        "message": message,
    })


@never_cache
def announcement_create(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:announcements_list")

    title = (request.POST.get("title") or "").strip()[:100]
    body = (request.POST.get("body") or "").strip()[:300]
    url = (request.POST.get("url") or "").strip()[:200]

    if not title:
        request.session["admin_message"] = {"type": "error", "text": "عنوان الزامی است."}
        return redirect("custom_admin:announcements_list")

    from django.contrib.auth import get_user_model
    from social.models import Notification
    User = get_user_model()

    # Bulk create notifications for all active users
    user_ids = User.objects.values_list("id", flat=True)
    batch = []
    total = 0
    for uid in user_ids.iterator(chunk_size=1000):
        batch.append(Notification(
            user_id=uid,
            type="admin_broadcast",
            title=title,
            body=body,
            url=url,
            is_read=False,
        ))
        if len(batch) >= 500:
            Notification.objects.bulk_create(batch)
            total += len(batch)
            batch = []
    if batch:
        Notification.objects.bulk_create(batch)
        total += len(batch)

    request.session["admin_message"] = {
        "type": "success",
        "text": f"اعلان برای {total} کاربر ارسال شد.",
    }
    return redirect("custom_admin:announcements_list")


@never_cache
def announcement_delete(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:announcements_list")

    title = (request.POST.get("title") or "").strip()
    body = (request.POST.get("body") or "").strip()
    url = (request.POST.get("url") or "").strip()

    if title:
        from social.models import Notification
        q = Notification.objects.filter(type="admin_broadcast", title=title)
        if body:
            q = q.filter(body=body)
        if url:
            q = q.filter(url=url)
        n = q.delete()[0]
        request.session["admin_message"] = {"type": "success", "text": f"{n} اعلان حذف شد."}
    return redirect("custom_admin:announcements_list")


# ============================================================
# Admin — Tournaments
# ============================================================
@never_cache
def tournaments_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    from game.models import Tournament

    t_list = Tournament.objects.all().order_by("-start_at")
    data = []
    for x in t_list:
        data.append({
            "id": x.id,
            "name": x.name,
            "icon": x.icon,
            "tournament_type": x.tournament_type,
            "type_display": x.get_tournament_type_display(),
            "status": x.status,
            "status_display": x.get_status_display(),
            "start_at": x.start_at,
            "end_at": x.end_at,
            "entry_count": x.entry_count(),
            "max_players": x.max_players,
            "prize_coins": x.prize_coins,
            "prize_gems": x.prize_gems,
            "is_live": x.is_live,
            "is_finished": x.is_finished,
            "is_upcoming": x.is_upcoming,
        })

    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/tournaments.html", {
        "tournaments": data,
        "message": message,
    })


def _save_tournament_from_post(request, t=None):
    """Helper: save tournament from POST. Returns (ok, error)."""
    from game.models import Tournament

    name = (request.POST.get("name") or "").strip()[:80]
    if not name:
        return None, "نام تورنمنت الزامی است."

    description = (request.POST.get("description") or "").strip()[:300]
    icon = (request.POST.get("icon") or "🏆").strip()[:4]
    tournament_type = request.POST.get("tournament_type", "daily")
    if tournament_type not in ("daily", "hourly", "weekly"):
        tournament_type = "daily"
    status = request.POST.get("status", "scheduled")
    if status not in ("scheduled", "active", "finished", "cancelled"):
        status = "scheduled"

    start_at = _parse_dt(request.POST.get("start_at"))
    end_at = _parse_dt(request.POST.get("end_at"))
    if not start_at or not end_at:
        return None, "تاریخ شروع و پایان الزامی است."
    if end_at <= start_at:
        return None, "تاریخ پایان باید بعد از شروع باشد."

    def _int(key, default=0):
        try:
            return int(request.POST.get(key) or default)
        except (ValueError, TypeError):
            return default

    entry_fee_coins = max(0, _int("entry_fee_coins", 0))
    entry_fee_gems = max(0, _int("entry_fee_gems", 0))
    prize_coins = max(0, _int("prize_coins", 0))
    prize_gems = max(0, _int("prize_gems", 0))
    max_players = max(2, min(1000, _int("max_players", 100)))
    min_players = max(2, min(max_players, _int("min_players", 2)))

    if t is None:
        t = Tournament()

    t.name = name
    t.description = description
    t.icon = icon
    t.tournament_type = tournament_type
    t.status = status
    t.start_at = start_at
    t.end_at = end_at
    t.entry_fee_coins = entry_fee_coins
    t.entry_fee_gems = entry_fee_gems
    t.prize_coins = prize_coins
    t.prize_gems = prize_gems
    t.max_players = max_players
    t.min_players = min_players

    if t.created_by_id is None:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin = User.objects.filter(is_staff=True).first()
        if admin:
            t.created_by = admin

    t.save()
    return t, None


@never_cache
def tournament_create(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")

    if request.method == "POST":
        t, err = _save_tournament_from_post(request)
        if err:
            request.session["admin_message"] = {"type": "error", "text": err}
            return redirect("custom_admin:tournament_create")
        request.session["admin_message"] = {"type": "success", "text": "تورنمنت ساخته شد."}
        return redirect("custom_admin:tournaments_list")

    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/tournament_edit.html", {
        "tournament": None,
        "message": message,
    })


@never_cache
def tournament_edit(request, tournament_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    from game.models import Tournament
    try:
        t = Tournament.objects.get(id=tournament_id)
    except Tournament.DoesNotExist:
        return redirect("custom_admin:tournaments_list")

    if request.method == "POST":
        t2, err = _save_tournament_from_post(request, t=t)
        if err:
            request.session["admin_message"] = {"type": "error", "text": err}
            return redirect("custom_admin:tournament_edit", tournament_id=t.id)
        request.session["admin_message"] = {"type": "success", "text": "تورنمنت به‌روزرسانی شد."}
        return redirect("custom_admin:tournament_edit", tournament_id=t.id)

    # Entries
    entries = t.entries.select_related("user").order_by("-score", "joined_at")
    entries_data = [{
        "user_id": e.user.id,
        "username": e.user.username,
        "alias": e.user.alias,
        "joined_at": e.joined_at,
        "score": e.score,
    } for e in entries]

    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/tournament_edit.html", {
        "tournament": t,
        "entries": entries_data,
        "message": message,
    })


@never_cache
def tournament_delete(request, tournament_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:tournaments_list")
    from game.models import Tournament
    try:
        Tournament.objects.get(id=tournament_id).delete()
        request.session["admin_message"] = {"type": "success", "text": "تورنمنت حذف شد."}
    except Tournament.DoesNotExist:
        pass
    return redirect("custom_admin:tournaments_list")


@never_cache
def tournament_clear_entries(request, tournament_id):
    """خارج کردن همه از صف."""
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:tournament_edit", tournament_id=tournament_id)
    from game.models import Tournament, TournamentEntry
    try:
        t = Tournament.objects.get(id=tournament_id)
        n = TournamentEntry.objects.filter(tournament=t).delete()[0]
        request.session["admin_message"] = {"type": "success", "text": f"{n} نفر از صف خارج شدند."}
    except Tournament.DoesNotExist:
        pass
    return redirect("custom_admin:tournament_edit", tournament_id=tournament_id)
'''

src = src.rstrip() + code + "\n"
backup(p); write(p, src)

# ============================================================
# 4) admin_urls.py - add routes
# ============================================================
print("\n[4/9] accounts/admin_urls.py")
p = os.path.join(ROOT, "accounts", "admin_urls.py")

URLS_CONTENT = '''from django.urls import path
from . import admin_views

app_name = "custom_admin"

urlpatterns = [
    path("", admin_views.admin_login, name="login"),
    path("dashboard/", admin_views.dashboard, name="dashboard"),
    path("logout/", admin_views.admin_logout, name="logout"),

    # Users
    path("user/<int:user_id>/", admin_views.user_detail, name="user_detail"),
    path("user/<int:user_id>/edit/", admin_views.user_edit, name="user_edit"),
    path("user/<int:user_id>/update/", admin_views.user_update, name="user_update"),
    path("user/<int:user_id>/toggle/", admin_views.user_toggle_active, name="user_toggle"),
    path("user/<int:user_id>/delete/", admin_views.user_delete, name="user_delete"),
    path("user/<int:user_id>/reset-password/", admin_views.user_reset_password, name="user_reset_password"),
    path("user/<int:user_id>/change-alias/", admin_views.user_change_alias, name="user_change_alias"),

    # Alliances
    path("alliances/", admin_views.alliances_list, name="alliances_list"),
    path("alliance/<int:alliance_id>/", admin_views.alliance_manage, name="alliance_manage"),

    # Rooms
    path("rooms/", admin_views.rooms_list, name="rooms_list"),
    path("rooms/active/", admin_views.rooms_active, name="rooms_active"),
    path("room/<uuid:game_id>/delete/", admin_views.room_delete, name="room_delete"),

    # Announcements
    path("announcements/", admin_views.announcements_list, name="announcements_list"),
    path("announcement/create/", admin_views.announcement_create, name="announcement_create"),
    path("announcement/delete/", admin_views.announcement_delete, name="announcement_delete"),

    # Tournaments
    path("tournaments/", admin_views.tournaments_list, name="tournaments_list"),
    path("tournament/create/", admin_views.tournament_create, name="tournament_create"),
    path("tournament/<int:tournament_id>/", admin_views.tournament_edit, name="tournament_edit"),
    path("tournament/<int:tournament_id>/delete/", admin_views.tournament_delete, name="tournament_delete"),
    path("tournament/<int:tournament_id>/clear-entries/", admin_views.tournament_clear_entries, name="tournament_clear_entries"),
]
'''
backup(p); write(p, URLS_CONTENT)

# ============================================================
# 5) admin templates - announcements.html
# ============================================================
print("\n[5/9] announcements.html")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "announcements.html")

ANN_HTML = '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>اعلان‌ها — پنل ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 1000px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; }
    .topbar h1 { font-size: 20px; color: #fca5a5; }
    .topbar a { padding: 9px 16px; border-radius: 10px; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold; }

    .admin-tabs { display: flex; gap: 6px; margin-bottom: 20px; background: #12121f; border: 1px solid rgba(148,163,184,0.15); padding: 6px; border-radius: 14px; overflow-x: auto; }
    .admin-tab { flex: 1; min-width: 100px; padding: 12px 16px; border-radius: 10px; text-align: center; text-decoration: none; font-size: 12px; font-weight: bold; color: #94a3b8; transition: 0.2s; white-space: nowrap; }
    .admin-tab:hover { background: rgba(148,163,184,0.1); color: #fff; }
    .admin-tab.active { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; box-shadow: 0 6px 20px rgba(239,68,68,0.4); }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .card { background: #12121f; border: 1px solid rgba(148,163,184,0.15); border-radius: 16px; padding: 22px; margin-bottom: 16px; }
    .card h3 { color: #fdba74; font-size: 15px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }

    label { display: block; color: #94a3b8; font-size: 12px; margin: 12px 0 6px; font-weight: bold; }
    input[type=text], textarea { width: 100%; padding: 12px 14px; border-radius: 10px; border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15; color: #fff; font-size: 14px; font-family: inherit; box-sizing: border-box; }
    textarea { resize: vertical; min-height: 80px; }
    input:focus, textarea:focus { outline: none; border-color: #facc15; }

    button.submit { width: 100%; margin-top: 16px; padding: 14px; border: none; border-radius: 12px; font-size: 15px; font-weight: bold; font-family: inherit; cursor: pointer; color: #fff; background: linear-gradient(135deg, #f59e0b, #d97706); box-shadow: 0 8px 20px rgba(245,158,11,0.4); }
    button.submit:hover { transform: translateY(-1px); }

    .ann-card { background: linear-gradient(135deg, #1a1a2e, #12121f); border: 1px solid rgba(245,158,11,0.3); border-radius: 14px; padding: 16px; margin-bottom: 10px; position: relative; }
    .ann-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
    .ann-icon { width: 42px; height: 42px; border-radius: 10px; background: rgba(245,158,11,0.2); display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
    .ann-info { flex: 1; min-width: 0; }
    .ann-title { font-size: 14px; font-weight: bold; color: #fde68a; margin-bottom: 2px; }
    .ann-meta { font-size: 11px; color: #64748b; font-family: monospace; }
    .ann-body { font-size: 12px; color: #cbd5e1; line-height: 1.6; padding: 8px 0; }
    .ann-del { padding: 6px 12px; border: none; border-radius: 8px; background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); font-family: inherit; font-size: 11px; font-weight: bold; cursor: pointer; }
    .ann-del:hover { background: rgba(239,68,68,0.3); }

    .empty { text-align: center; padding: 40px 20px; color: #64748b; font-size: 13px; }
    .empty .icon { font-size: 60px; display: block; margin-bottom: 12px; opacity: 0.5; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>📢 اعلان‌های سراسری</h1>
    <a href="{% url 'custom_admin:logout' %}">خروج</a>
  </div>

  <div class="admin-tabs">
    <a href="/panel-admin/dashboard/" class="admin-tab">👥 کاربران</a>
    <a href="/panel-admin/alliances/" class="admin-tab">🛡️ اتحادها</a>
    <a href="/panel-admin/rooms/" class="admin-tab">🚪 اتاق‌ها</a>
    <a href="/panel-admin/rooms/active/" class="admin-tab">🎮 در حال بازی</a>
    <a href="/panel-admin/announcements/" class="admin-tab active">📢 اعلان‌ها</a>
    <a href="/panel-admin/tournaments/" class="admin-tab">🏆 تورنمنت‌ها</a>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <div class="card">
    <h3>📝 ارسال اعلان جدید</h3>
    <form method="post" action="{% url 'custom_admin:announcement_create' %}">
      {% csrf_token %}
      <label>عنوان</label>
      <input type="text" name="title" required maxlength="100" placeholder="مثلاً: تورنمنت ویژه امشب!">
      <label>متن اعلان</label>
      <textarea name="body" maxlength="300" placeholder="متن کامل اعلان..."></textarea>
      <label>لینک (اختیاری)</label>
      <input type="text" name="url" maxlength="200" placeholder="مثلاً /game/challenge/">
      <button type="submit" class="submit">📢 ارسال به همه</button>
    </form>
  </div>

  <div class="card">
    <h3>📜 اعلان‌های ارسال‌شده ({{ announcements|length }})</h3>
    {% if announcements %}
      {% for a in announcements %}
        <div class="ann-card">
          <div class="ann-head">
            <div class="ann-icon">📢</div>
            <div class="ann-info">
              <div class="ann-title">{{ a.title }}</div>
              <div class="ann-meta">{{ a.created_at|date:"Y/m/d H:i" }} · {{ a.recipients }} گیرنده</div>
            </div>
            <form method="post" action="{% url 'custom_admin:announcement_delete' %}" onsubmit="return confirm('حذف این اعلان از صندوق همه کاربران؟');">
              {% csrf_token %}
              <input type="hidden" name="title" value="{{ a.title }}">
              <input type="hidden" name="body" value="{{ a.body }}">
              <input type="hidden" name="url" value="{{ a.url }}">
              <button type="submit" class="ann-del">🗑️ حذف</button>
            </form>
          </div>
          {% if a.body %}<div class="ann-body">{{ a.body }}</div>{% endif %}
          {% if a.url %}<div class="ann-meta">🔗 {{ a.url }}</div>{% endif %}
        </div>
      {% endfor %}
    {% else %}
      <div class="empty">
        <span class="icon">📭</span>
        هنوز اعلانی ارسال نشده.
      </div>
    {% endif %}
  </div>
</div>
</body>
</html>
'''
backup(p); write(p, ANN_HTML)

# ============================================================
# 6) tournaments.html
# ============================================================
print("\n[6/9] tournaments.html")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "tournaments.html")

TOUR_HTML = '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>تورنمنت‌ها — پنل ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 1300px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
    .topbar h1 { font-size: 20px; color: #fca5a5; }
    .topbar-actions { display: flex; gap: 8px; }
    .topbar a { padding: 9px 16px; border-radius: 10px; text-decoration: none; font-size: 13px; font-weight: bold; color: #fff; }
    .btn-logout { background: linear-gradient(135deg, #ef4444, #dc2626); }
    .btn-create { background: linear-gradient(135deg, #22c55e, #16a34a); }

    .admin-tabs { display: flex; gap: 6px; margin-bottom: 20px; background: #12121f; border: 1px solid rgba(148,163,184,0.15); padding: 6px; border-radius: 14px; overflow-x: auto; }
    .admin-tab { flex: 1; min-width: 100px; padding: 12px 16px; border-radius: 10px; text-align: center; text-decoration: none; font-size: 12px; font-weight: bold; color: #94a3b8; transition: 0.2s; white-space: nowrap; }
    .admin-tab:hover { background: rgba(148,163,184,0.1); color: #fff; }
    .admin-tab.active { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; box-shadow: 0 6px 20px rgba(239,68,68,0.4); }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .tour-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 14px; }
    .tour-card { background: linear-gradient(135deg, #12121f, #1a1a2e); border: 1.5px solid rgba(148,163,184,0.15); border-radius: 18px; padding: 18px; transition: 0.2s; position: relative; overflow: hidden; }
    .tour-card:hover { transform: translateY(-2px); }
    .tour-card.live { border-color: rgba(34,197,94,0.6); box-shadow: 0 8px 25px rgba(34,197,94,0.2); }
    .tour-card.live::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #22c55e, #4ade80, #22c55e); animation: pulse 2s infinite; }
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
    .tour-card.finished { opacity: 0.7; border-color: rgba(100,116,139,0.4); }

    .tour-head { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
    .tour-icon { width: 54px; height: 54px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 28px; flex-shrink: 0; border: 1px solid rgba(255,255,255,0.1); }
    .tour-icon.weekly { background: linear-gradient(135deg, rgba(234,179,8,0.3), rgba(244,197,66,0.15)); }
    .tour-icon.daily { background: linear-gradient(135deg, rgba(59,130,246,0.3), rgba(96,165,250,0.15)); }
    .tour-icon.hourly { background: linear-gradient(135deg, rgba(6,182,212,0.3), rgba(34,211,238,0.15)); }
    .tour-info { flex: 1; min-width: 0; }
    .tour-name { font-size: 15px; font-weight: bold; color: #fff; margin-bottom: 3px; }
    .tour-meta { font-size: 11px; color: #94a3b8; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
    .tour-badge { padding: 2px 8px; border-radius: 6px; font-size: 10px; font-weight: bold; }
    .badge-scheduled { background: rgba(234,179,8,0.2); color: #fde68a; }
    .badge-active { background: rgba(34,197,94,0.2); color: #4ade80; }
    .badge-finished { background: rgba(100,116,139,0.2); color: #cbd5e1; }
    .badge-cancelled { background: rgba(239,68,68,0.2); color: #fca5a5; }

    .tour-times { background: rgba(15,23,42,0.5); border-radius: 10px; padding: 10px 12px; margin-bottom: 12px; font-size: 11px; }
    .tour-times .row { display: flex; justify-content: space-between; padding: 3px 0; }
    .tour-times .row .lbl { color: #64748b; }
    .tour-times .row .val { color: #e2e8f0; font-family: monospace; }

    .tour-stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 12px; }
    .tour-stat { padding: 8px 10px; background: rgba(15,23,42,0.5); border-radius: 10px; text-align: center; }
    .tour-stat .lbl { font-size: 10px; color: #64748b; margin-bottom: 2px; }
    .tour-stat .val { font-size: 13px; font-weight: bold; color: #facc15; font-family: monospace; }

    .tour-actions { display: flex; gap: 8px; }
    .tour-actions a, .tour-actions button { flex: 1; padding: 10px; border-radius: 10px; border: none; font-family: inherit; font-weight: bold; font-size: 12px; cursor: pointer; text-align: center; text-decoration: none; }
    .btn-edit { background: rgba(139,92,246,0.2); color: #c4b5fd; border: 1px solid rgba(139,92,246,0.4) !important; }
    .btn-edit:hover { background: rgba(139,92,246,0.35); }
    .btn-del2 { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3) !important; }
    .btn-del2:hover { background: rgba(239,68,68,0.3); }

    .empty { text-align: center; padding: 60px 20px; color: #64748b; }
    .empty .icon { font-size: 60px; display: block; margin-bottom: 12px; opacity: 0.5; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>🏆 مدیریت تورنمنت‌ها</h1>
    <div class="topbar-actions">
      <a href="{% url 'custom_admin:tournament_create' %}" class="btn-create">+ ساخت تورنمنت</a>
      <a href="{% url 'custom_admin:logout' %}" class="btn-logout">خروج</a>
    </div>
  </div>

  <div class="admin-tabs">
    <a href="/panel-admin/dashboard/" class="admin-tab">👥 کاربران</a>
    <a href="/panel-admin/alliances/" class="admin-tab">🛡️ اتحادها</a>
    <a href="/panel-admin/rooms/" class="admin-tab">🚪 اتاق‌ها</a>
    <a href="/panel-admin/rooms/active/" class="admin-tab">🎮 در حال بازی</a>
    <a href="/panel-admin/announcements/" class="admin-tab">📢 اعلان‌ها</a>
    <a href="/panel-admin/tournaments/" class="admin-tab active">🏆 تورنمنت‌ها</a>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  {% if tournaments %}
    <div class="tour-grid">
      {% for t in tournaments %}
        <div class="tour-card {% if t.is_live %}live{% elif t.is_finished %}finished{% endif %}">
          <div class="tour-head">
            <div class="tour-icon {{ t.tournament_type }}">{{ t.icon }}</div>
            <div class="tour-info">
              <div class="tour-name">{{ t.name }}</div>
              <div class="tour-meta">
                <span class="tour-badge badge-{{ t.status }}">{{ t.status_display }}</span>
                <span>{{ t.type_display }}</span>
              </div>
            </div>
          </div>
          <div class="tour-times">
            <div class="row"><span class="lbl">شروع</span><span class="val">{{ t.start_at|date:"Y/m/d H:i" }}</span></div>
            <div class="row"><span class="lbl">پایان</span><span class="val">{{ t.end_at|date:"Y/m/d H:i" }}</span></div>
          </div>
          <div class="tour-stats">
            <div class="tour-stat"><div class="lbl">شرکت‌کننده</div><div class="val">{{ t.entry_count }} / {{ t.max_players }}</div></div>
            <div class="tour-stat"><div class="lbl">🪙 جایزه</div><div class="val">{{ t.prize_coins }}</div></div>
            <div class="tour-stat"><div class="lbl">💎 جایزه</div><div class="val">{{ t.prize_gems }}</div></div>
          </div>
          <div class="tour-actions">
            <a href="{% url 'custom_admin:tournament_edit' t.id %}" class="btn-edit">⚙️ ویرایش</a>
            <form method="post" action="{% url 'custom_admin:tournament_delete' t.id %}" style="flex:1;" onsubmit="return confirm('حذف تورنمنت {{ t.name }}؟');">
              {% csrf_token %}
              <button type="submit" class="btn-del2" style="width:100%;">🗑️ حذف</button>
            </form>
          </div>
        </div>
      {% endfor %}
    </div>
  {% else %}
    <div class="empty">
      <span class="icon">🏆</span>
      هنوز تورنمنتی ساخته نشده.<br>
      <a href="{% url 'custom_admin:tournament_create' %}" style="color: #22c55e; text-decoration: none; margin-top: 12px; display: inline-block;">+ ساخت اولین تورنمنت</a>
    </div>
  {% endif %}
</div>
</body>
</html>
'''
backup(p); write(p, TOUR_HTML)

# ============================================================
# 7) tournament_edit.html
# ============================================================
print("\n[7/9] tournament_edit.html")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "tournament_edit.html")

EDIT_HTML = '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% if tournament %}ویرایش{% else %}ساخت{% endif %} تورنمنت</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 900px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
    .topbar h1 { font-size: 19px; color: #fca5a5; }
    .topbar-actions { display: flex; gap: 8px; }
    .topbar a { padding: 9px 16px; border-radius: 10px; text-decoration: none; font-size: 13px; font-weight: bold; color: #fff; }
    .btn-back { background: rgba(148,163,184,0.2); }
    .btn-logout { background: linear-gradient(135deg, #ef4444, #dc2626); }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .card { background: #12121f; border: 1px solid rgba(148,163,184,0.15); border-radius: 16px; padding: 22px; margin-bottom: 16px; }
    .card h3 { color: #fdba74; font-size: 15px; margin-bottom: 16px; }

    label { display: block; color: #94a3b8; font-size: 12px; margin: 12px 0 6px; font-weight: bold; }
    input[type=text], input[type=number], input[type=datetime-local], textarea, select { width: 100%; padding: 12px 14px; border-radius: 10px; border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15; color: #fff; font-size: 14px; font-family: inherit; box-sizing: border-box; }
    textarea { resize: vertical; min-height: 70px; }
    input:focus, textarea:focus, select:focus { outline: none; border-color: #facc15; }

    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    @media (max-width: 500px) { .row { grid-template-columns: 1fr; } }

    .emojis { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
    .emoji-opt { padding: 12px; text-align: center; font-size: 24px; background: #1a1a2e; border: 2px solid transparent; border-radius: 10px; cursor: pointer; transition: 0.15s; }
    .emoji-opt:hover { border-color: #facc15; }
    .emoji-opt input { display: none; }
    .emoji-opt:has(input:checked) { border-color: #facc15; background: linear-gradient(135deg, rgba(250,204,21,0.2), rgba(139,92,246,0.1)); }

    button.submit { width: 100%; margin-top: 18px; padding: 14px; border: none; border-radius: 12px; font-size: 15px; font-weight: bold; font-family: inherit; cursor: pointer; color: #fff; background: linear-gradient(135deg, #22c55e, #16a34a); box-shadow: 0 8px 20px rgba(34,197,94,0.4); }
    button.submit:hover { transform: translateY(-1px); }

    .danger-card { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.3); border-radius: 16px; padding: 22px; }
    .danger-card h3 { color: #fca5a5; }
    .danger-card p { font-size: 12px; color: #94a3b8; margin-bottom: 12px; line-height: 1.6; }
    button.danger-btn { padding: 10px 20px; border: none; border-radius: 10px; font-family: inherit; font-weight: bold; font-size: 13px; cursor: pointer; background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4); margin-right: 8px; }
    button.danger-btn:hover { background: rgba(239,68,68,0.35); }
    button.del-btn { padding: 10px 20px; border: none; border-radius: 10px; font-family: inherit; font-weight: bold; font-size: 13px; cursor: pointer; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; }

    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 10px 12px; text-align: right; font-size: 12px; border-bottom: 1px solid rgba(148,163,184,0.1); }
    th { color: #94a3b8; font-size: 11px; font-weight: bold; }
    tr:last-child td { border-bottom: none; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>🏆 {% if tournament %}ویرایش: {{ tournament.name }}{% else %}ساخت تورنمنت جدید{% endif %}</h1>
    <div class="topbar-actions">
      <a href="{% url 'custom_admin:tournaments_list' %}" class="btn-back">← بازگشت</a>
      <a href="{% url 'custom_admin:logout' %}" class="btn-logout">خروج</a>
    </div>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <form method="post">
    {% csrf_token %}

    <div class="card">
      <h3>📝 اطلاعات پایه</h3>

      <label>آیکن</label>
      <div class="emojis">
        {% for e in "🏆🥇🏅🎯⚔️🔥🌟💎👑🎮🏰🛡️" %}
          <label class="emoji-opt">
            <input type="radio" name="icon" value="{{ e }}" {% if tournament and tournament.icon == e %}{% elif not tournament and e == '🏆' %}checked{% endif %}>
            {{ e }}
          </label>
        {% endfor %}
      </div>

      <label>نام تورنمنت</label>
      <input type="text" name="name" value="{{ tournament.name|default:'' }}" required maxlength="80">

      <label>توضیح</label>
      <textarea name="description" maxlength="300">{{ tournament.description|default:'' }}</textarea>

      <div class="row">
        <div>
          <label>نوع</label>
          <select name="tournament_type">
            <option value="daily" {% if tournament.tournament_type == 'daily' or not tournament %}selected{% endif %}>روزانه</option>
            <option value="hourly" {% if tournament.tournament_type == 'hourly' %}selected{% endif %}>ساعتی</option>
            <option value="weekly" {% if tournament.tournament_type == 'weekly' %}selected{% endif %}>هفتگی</option>
          </select>
        </div>
        <div>
          <label>وضعیت</label>
          <select name="status">
            <option value="scheduled" {% if tournament.status == 'scheduled' or not tournament %}selected{% endif %}>برنامه‌ریزی شده</option>
            <option value="active" {% if tournament.status == 'active' %}selected{% endif %}>در حال برگزاری</option>
            <option value="finished" {% if tournament.status == 'finished' %}selected{% endif %}>پایان یافته</option>
            <option value="cancelled" {% if tournament.status == 'cancelled' %}selected{% endif %}>لغو شده</option>
          </select>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>⏰ زمان‌بندی</h3>
      <div class="row">
        <div>
          <label>تاریخ و ساعت شروع</label>
          <input type="datetime-local" name="start_at" value="{% if tournament %}{{ tournament.start_at|date:'Y-m-d\\TH:i' }}{% endif %}" required>
        </div>
        <div>
          <label>تاریخ و ساعت پایان</label>
          <input type="datetime-local" name="end_at" value="{% if tournament %}{{ tournament.end_at|date:'Y-m-d\\TH:i' }}{% endif %}" required>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>💰 هزینه و جایزه</h3>
      <div class="row">
        <div>
          <label>هزینه ورود (سکه)</label>
          <input type="number" name="entry_fee_coins" value="{{ tournament.entry_fee_coins|default:0 }}" min="0">
        </div>
        <div>
          <label>هزینه ورود (جم)</label>
          <input type="number" name="entry_fee_gems" value="{{ tournament.entry_fee_gems|default:0 }}" min="0">
        </div>
      </div>
      <div class="row">
        <div>
          <label>جایزه برنده (سکه)</label>
          <input type="number" name="prize_coins" value="{{ tournament.prize_coins|default:0 }}" min="0">
        </div>
        <div>
          <label>جایزه برنده (جم)</label>
          <input type="number" name="prize_gems" value="{{ tournament.prize_gems|default:0 }}" min="0">
        </div>
      </div>
    </div>

    <div class="card">
      <h3>👥 ظرفیت</h3>
      <div class="row">
        <div>
          <label>حداقل بازیکن</label>
          <input type="number" name="min_players" value="{{ tournament.min_players|default:2 }}" min="2">
        </div>
        <div>
          <label>حداکثر بازیکن</label>
          <input type="number" name="max_players" value="{{ tournament.max_players|default:100 }}" min="2">
        </div>
      </div>
    </div>

    <button type="submit" class="submit">💾 ذخیره</button>
  </form>

  {% if tournament %}
    <div class="card" style="margin-top: 16px;">
      <h3>👥 شرکت‌کننده‌ها ({{ entries|length }})</h3>
      {% if entries %}
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>نام نمایشی</th>
              <th>username</th>
              <th>امتیاز</th>
              <th>تاریخ عضویت</th>
            </tr>
          </thead>
          <tbody>
            {% for e in entries %}
              <tr>
                <td>{{ forloop.counter }}</td>
                <td>{{ e.alias }}</td>
                <td style="font-family:monospace; color:#94a3b8;">@{{ e.username }}</td>
                <td style="color:#facc15; font-family:monospace; font-weight:bold;">{{ e.score }}</td>
                <td style="font-size:11px; color:#64748b;">{{ e.joined_at|date:"Y/m/d H:i" }}</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      {% else %}
        <p style="color:#64748b; text-align:center; padding: 20px;">هنوز کسی ثبت‌نام نکرده.</p>
      {% endif %}
    </div>

    <div class="danger-card" style="margin-top: 16px;">
      <h3>⚠️ اقدامات خطرناک</h3>
      <p>خارج کردن همه از صف یا حذف کامل تورنمنت غیرقابل بازگشت است.</p>
      <form method="post" action="{% url 'custom_admin:tournament_clear_entries' tournament.id %}" style="display:inline;" onsubmit="return confirm('همه از صف خارج شوند؟');">
        {% csrf_token %}
        <button type="submit" class="danger-btn">🧹 خالی کردن صف</button>
      </form>
      <form method="post" action="{% url 'custom_admin:tournament_delete' tournament.id %}" style="display:inline;" onsubmit="return confirm('حذف کامل تورنمنت؟');">
        {% csrf_token %}
        <button type="submit" class="del-btn">🗑️ حذف تورنمنت</button>
      </form>
    </div>
  {% endif %}
</div>
</body>
</html>
'''
backup(p); write(p, EDIT_HTML)

# ============================================================
# 8) challenge.html + notifications.html updates
# ============================================================
print("\n[8/9] challenge.html + notifications.html")

# 8a) challenge.html rewrite with dynamic tournaments
p = os.path.join(ROOT, "game", "templates", "game", "challenge.html")
CHALLENGE_HTML = '''{% extends "base.html" %}
{% block title %}چالش{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }

  .intro-card {
    text-align: center; padding: 24px 20px;
    background: radial-gradient(circle at 100% 0%, rgba(239,68,68,0.25), transparent 60%),
                radial-gradient(circle at 0% 100%, rgba(244,197,66,0.15), transparent 60%),
                linear-gradient(135deg, #2a0a0a, #0f0f1e);
    border: 1.5px solid rgba(239,68,68,0.4);
    border-radius: 20px; margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(239,68,68,0.15);
  }
  .intro-card .icon { font-size: 56px; margin-bottom: 8px; filter: drop-shadow(0 0 20px rgba(239,68,68,0.4)); }
  .intro-card h2 {
    font-size: 20px; font-weight: 900; margin-bottom: 8px;
    background: linear-gradient(135deg, #fca5a5, #f4c542);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .intro-card p { color: var(--muted); font-size: 13px; line-height: 1.7; }

  .section-title { font-size: 14px; color: var(--gold); margin: 20px 0 12px; display: flex; align-items: center; gap: 8px; }
  .section-title .count { font-size: 11px; padding: 2px 8px; background: rgba(244,197,66,0.15); border-radius: 6px; font-family: monospace; }

  .tour-card {
    padding: 16px; border-radius: 18px; margin-bottom: 12px;
    border: 1.5px solid; position: relative; overflow: hidden;
    transition: 0.2s;
  }
  .tour-card:hover { transform: translateY(-2px); }
  .tour-weekly { background: radial-gradient(circle at 100% 0%, rgba(234,179,8,0.3), transparent 60%), linear-gradient(135deg, #2a1e0a, #1a0f1a); border-color: rgba(234,179,8,0.5); }
  .tour-daily { background: radial-gradient(circle at 100% 0%, rgba(59,130,246,0.3), transparent 60%), linear-gradient(135deg, #0a1a2a, #0f0f1e); border-color: rgba(59,130,246,0.5); }
  .tour-hourly { background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.3), transparent 60%), linear-gradient(135deg, #0a1e2a, #0f0f1e); border-color: rgba(6,182,212,0.5); }

  .tour-head { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
  .tour-icon { width: 52px; height: 52px; border-radius: 14px; background: rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; font-size: 28px; flex-shrink: 0; }
  .tour-info { flex: 1; min-width: 0; }
  .tour-name { font-size: 15px; font-weight: bold; color: #fff; margin-bottom: 3px; }
  .tour-sub { font-size: 11px; color: var(--muted); }

  .tour-status-live {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 10px; border-radius: 999px;
    background: rgba(34,197,94,0.2); color: #4ade80;
    font-size: 10px; font-weight: 900;
  }
  .tour-status-live::before {
    content: ""; width: 6px; height: 6px; border-radius: 50%; background: #4ade80;
    box-shadow: 0 0 8px #4ade80;
    animation: livePulse 1.5s infinite;
  }
  @keyframes livePulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

  .tour-details { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; }
  .tour-detail { display: flex; align-items: center; gap: 4px; font-size: 11px; color: #cbd5e1; padding: 4px 10px; background: rgba(15,23,42,0.5); border-radius: 8px; }
  .tour-detail b { color: var(--gold); font-family: monospace; }

  .tour-btn {
    display: block; width: 100%; padding: 12px; border: none; border-radius: 12px;
    font-family: inherit; font-weight: 900; font-size: 14px; cursor: pointer;
    text-decoration: none; text-align: center;
    background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff;
    box-shadow: 0 8px 20px rgba(34,197,94,0.4); transition: 0.2s;
  }
  .tour-btn:hover { transform: translateY(-1px); }
  .tour-btn.disabled { background: rgba(148,163,184,0.2); color: #94a3b8; box-shadow: none; cursor: not-allowed; }

  .countdown {
    display: flex; gap: 6px; justify-content: center; margin: 8px 0;
    font-family: monospace; font-size: 16px; font-weight: 900;
  }
  .cd-box { padding: 6px 10px; background: rgba(15,23,42,0.8); border-radius: 8px; color: var(--gold); min-width: 44px; text-align: center; }
  .cd-lbl { font-size: 9px; color: var(--muted); display: block; margin-top: 2px; }

  .empty-section { text-align: center; padding: 30px 20px; background: var(--card); border: 1px dashed var(--border); border-radius: 14px; color: var(--muted); font-size: 13px; margin-bottom: 12px; }
  .empty-section .icon { font-size: 40px; display: block; margin-bottom: 8px; opacity: 0.4; }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <a href="/game/rooms/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>⚔️ <span>چالش</span></h1>
  </div>

  <div class="intro-card">
    <div class="icon">⚔️</div>
    <h2>میدون نبرد بازیکنان</h2>
    <p>با بهترین‌ها رقابت کن، امتیاز بگیر و به بالای جدول برس</p>
  </div>

  <!-- Weekly -->
  <div class="section-title">
    <span>🏆 تورنمنت هفتگی</span>
    <span class="count">{{ weekly|length }}</span>
  </div>
  {% if weekly %}
    {% for t in weekly %}
      {% include "game/_tournament_card.html" with t=t %}
    {% endfor %}
  {% else %}
    <div class="empty-section"><span class="icon">🏆</span>هنوز تورنمنت هفتگی برگزار نشده</div>
  {% endif %}

  <!-- Daily -->
  <div class="section-title">
    <span>📅 مسابقه روزانه</span>
    <span class="count">{{ daily|length }}</span>
  </div>
  {% if daily %}
    {% for t in daily %}
      {% include "game/_tournament_card.html" with t=t %}
    {% endfor %}
  {% else %}
    <div class="empty-section"><span class="icon">📅</span>هنوز مسابقه روزانه برگزار نشده</div>
  {% endif %}

  <!-- Hourly -->
  <div class="section-title">
    <span>⏰ مسابقه ساعتی</span>
    <span class="count">{{ hourly|length }}</span>
  </div>
  {% if hourly %}
    {% for t in hourly %}
      {% include "game/_tournament_card.html" with t=t %}
    {% endfor %}
  {% else %}
    <div class="empty-section"><span class="icon">⏰</span>هنوز مسابقه ساعتی برگزار نشده</div>
  {% endif %}

{% endblock %}

{% block extra_js %}
<script>
  // Countdown updater
  document.querySelectorAll('[data-end-ts]').forEach(function(el) {
    function update() {
      var end = parseInt(el.dataset.endTs);
      var now = Math.floor(Date.now() / 1000);
      var left = end - now;
      if (left < 0) { el.innerHTML = '<span style="color:#f87171; font-size:12px;">پایان یافت</span>'; return; }
      var h = Math.floor(left / 3600);
      var m = Math.floor((left % 3600) / 60);
      var s = left % 60;
      el.innerHTML = '<div class="cd-box">' + String(h).padStart(2,'0') + '<span class="cd-lbl">ساعت</span></div>' +
                     '<div class="cd-box">' + String(m).padStart(2,'0') + '<span class="cd-lbl">دقیقه</span></div>' +
                     '<div class="cd-box">' + String(s).padStart(2,'0') + '<span class="cd-lbl">ثانیه</span></div>';
    }
    update();
    setInterval(update, 1000);
  });
</script>
{% endblock %}
'''
backup(p); write(p, CHALLENGE_HTML)

# 8b) _tournament_card.html - partial
print("\n[8b] _tournament_card.html")
p = os.path.join(ROOT, "game", "templates", "game", "_tournament_card.html")
PARTIAL_HTML = '''<div class="tour-card tour-{{ t.tournament_type }}">
  <div class="tour-head">
    <div class="tour-icon">{{ t.icon }}</div>
    <div class="tour-info">
      <div class="tour-name">{{ t.name }}</div>
      <div class="tour-sub">
        {% if t.is_live %}
          <span class="tour-status-live">در حال برگزاری</span>
        {% elif t.is_finished %}
          <span style="color:#94a3b8;">پایان یافته</span>
        {% elif t.is_upcoming %}
          <span style="color:#fde68a;">شروع در آینده</span>
        {% else %}
          <span style="color:#94a3b8;">{{ t.get_status_display }}</span>
        {% endif %}
      </div>
    </div>
  </div>

  <div class="tour-details">
    <div class="tour-detail">👥 <b>{{ t.entry_count }}</b> / {{ t.max_players }}</div>
    {% if t.prize_coins %}<div class="tour-detail">🪙 <b>{{ t.prize_coins }}</b></div>{% endif %}
    {% if t.prize_gems %}<div class="tour-detail">💎 <b>{{ t.prize_gems }}</b></div>{% endif %}
    {% if t.entry_fee_coins %}<div class="tour-detail">ورود: <b>{{ t.entry_fee_coins }}</b> سکه</div>{% endif %}
  </div>

  {% if t.is_upcoming %}
    <div style="font-size: 11px; color: var(--muted); text-align: center; margin: 8px 0;">شروع تا:</div>
    <div class="countdown" data-end-ts="{{ t.start_at_ts }}"></div>
    <button class="tour-btn disabled" disabled>⏳ هنوز شروع نشده</button>
  {% elif t.is_live %}
    <div style="font-size: 11px; color: var(--muted); text-align: center; margin: 8px 0;">پایان تا:</div>
    <div class="countdown" data-end-ts="{{ t.end_at_ts }}"></div>
    {% if t.is_joined %}
      <button class="tour-btn" style="background: linear-gradient(135deg, #f59e0b, #d97706);" disabled>✓ در صف هستی</button>
    {% else %}
      <a href="/game/challenge/{{ t.id }}/join/" class="tour-btn">🚀 شرکت در مسابقه</a>
    {% endif %}
  {% elif t.is_finished %}
    <button class="tour-btn disabled" disabled>🏁 پایان یافته</button>
  {% else %}
    <button class="tour-btn disabled" disabled>{{ t.get_status_display }}</button>
  {% endif %}
</div>
'''
backup(p); write(p, PARTIAL_HTML)

# 8c) notifications.html - add admin_broadcast icon
p = os.path.join(ROOT, "social", "templates", "social", "notifications.html")
src = read(p)
if '{% elif n.type == "admin_broadcast" %}' in src:
    print("  SKIP: notifications icon exists")
else:
    old = '{% elif n.type == "alliance_invite" %}🛡️'
    new = '{% elif n.type == "alliance_invite" %}🛡️\n          {% elif n.type == "admin_broadcast" %}📢'
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: notifications.html icon")

# ============================================================
# 9) game/views.py - challenge_home update + tournament_join
# ============================================================
print("\n[9/9] game/views.py - challenge_home + tournament_join")
p = os.path.join(ROOT, "game", "views.py")
src = read(p)

# Replace challenge_home
old_ch = '''@login_required
def challenge_home(request):
    check = _require_complete(request.user)
    if check:
        return check

    return render(request, "game/challenge.html", {
        "active": "games",
    })'''

new_ch = '''@login_required
def challenge_home(request):
    check = _require_complete(request.user)
    if check:
        return check

    from django.utils import timezone
    from .models import Tournament, TournamentEntry

    now = timezone.now()

    # Auto-finish expired
    Tournament.objects.filter(
        end_at__lt=now,
        status__in=["scheduled", "active"],
    ).update(status="finished")

    def _list(t_type):
        qs = Tournament.objects.filter(tournament_type=t_type).order_by("-start_at")[:10]
        out = []
        for x in qs:
            is_joined = TournamentEntry.objects.filter(tournament=x, user=request.user).exists()
            out.append({
                "id": x.id,
                "name": x.name,
                "icon": x.icon,
                "description": x.description,
                "tournament_type": x.tournament_type,
                "status": x.status,
                "get_status_display": x.get_status_display(),
                "start_at": x.start_at,
                "end_at": x.end_at,
                "start_at_ts": int(x.start_at.timestamp()),
                "end_at_ts": int(x.end_at.timestamp()),
                "entry_count": x.entry_count(),
                "max_players": x.max_players,
                "prize_coins": x.prize_coins,
                "prize_gems": x.prize_gems,
                "entry_fee_coins": x.entry_fee_coins,
                "is_live": x.is_live,
                "is_finished": x.is_finished,
                "is_upcoming": x.is_upcoming,
                "is_joined": is_joined,
            })
        return out

    return render(request, "game/challenge.html", {
        "weekly": _list("weekly"),
        "daily": _list("daily"),
        "hourly": _list("hourly"),
        "active": "games",
    })


@login_required
def tournament_join(request, tournament_id):
    check = _require_complete(request.user)
    if check:
        return check

    from django.utils import timezone
    from .models import Tournament, TournamentEntry
    from django.contrib import messages

    t = Tournament.objects.filter(id=tournament_id).first()
    if not t:
        messages.error(request, "تورنمنت پیدا نشد.")
        return redirect("game:challenge")

    now = timezone.now()

    if not t.is_live:
        messages.error(request, "این تورنمنت در حال برگزاری نیست.")
        return redirect("game:challenge")

    if t.entry_count() >= t.max_players:
        messages.error(request, "ظرفیت این تورنمنت پر شده.")
        return redirect("game:challenge")

    if TournamentEntry.objects.filter(tournament=t, user=request.user).exists():
        messages.info(request, "قبلاً در این تورنمنت ثبت‌نام کردی.")
        return redirect("game:challenge")

    # Check fees
    if t.entry_fee_coins and (request.user.coins or 0) < t.entry_fee_coins:
        messages.error(request, f"سکه کافی نداری (نیاز: {t.entry_fee_coins}).")
        return redirect("game:challenge")

    if t.entry_fee_gems and (request.user.gems or 0) < t.entry_fee_gems:
        messages.error(request, f"جم کافی نداری (نیاز: {t.entry_fee_gems}).")
        return redirect("game:challenge")

    # Deduct fees
    if t.entry_fee_coins:
        request.user.coins -= t.entry_fee_coins
    if t.entry_fee_gems:
        request.user.gems -= t.entry_fee_gems
    if t.entry_fee_coins or t.entry_fee_gems:
        request.user.save(update_fields=["coins", "gems"])

    TournamentEntry.objects.create(tournament=t, user=request.user)
    messages.success(request, f"در تورنمنت «{t.name}» ثبت‌نام کردی!")
    return redirect("game:challenge")'''

if old_ch in src:
    src = src.replace(old_ch, new_ch, 1)
    print("  FIXED: challenge_home rewritten + tournament_join added")
else:
    print("  WARN: challenge_home block not found")

backup(p); write(p, src)

# ============================================================
# Add tournament route
# ============================================================
print("\n[Extra] game/urls.py - tournament route")
p = os.path.join(ROOT, "game", "urls.py")
src = read(p)
if "tournament" in src:
    print("  SKIP: route exists")
else:
    old = '    path("challenge/", views.challenge_home, name="challenge"),'
    new = old + '\n    path("challenge/<int:tournament_id>/join/", views.tournament_join, name="tournament_join"),'
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: route added")
    else:
        print("  WARN: challenge route not found")

# ============================================================
# Update dashboard.html to add new tabs
# ============================================================
print("\n[Extra] dashboard.html - add 2 new tabs")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "dashboard.html")
src = read(p)
if "/panel-admin/announcements/" in src:
    print("  SKIP: tabs exist")
else:
    old = '    <a href="/panel-admin/rooms/active/" class="admin-tab">🎮 در حال بازی</a>\n  </div>'
    new = '''    <a href="/panel-admin/rooms/active/" class="admin-tab">🎮 در حال بازی</a>
    <a href="/panel-admin/announcements/" class="admin-tab">📢 اعلان‌ها</a>
    <a href="/panel-admin/tournaments/" class="admin-tab">🏆 تورنمنت‌ها</a>
  </div>'''
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: tabs added")
    else:
        print("  WARN: tabs block not found")

# ============================================================
# Update existing templates to also have new tabs
# ============================================================
for tpl_name in ["alliances.html", "rooms.html"]:
    p = os.path.join(ROOT, "accounts", "templates", "custom_admin", tpl_name)
    if not os.path.exists(p): continue
    src = read(p)
    if "/panel-admin/announcements/" in src:
        continue
    old = '<a href="/panel-admin/rooms/active/" class="admin-tab {% if status_filter == \'in_round\' %}active{% endif %}">🎮 در حال بازی</a>'
    new = old + '''
    <a href="/panel-admin/announcements/" class="admin-tab">📢 اعلان‌ها</a>
    <a href="/panel-admin/tournaments/" class="admin-tab">🏆 تورنمنت‌ها</a>'''
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print(f"  FIXED: tabs in {tpl_name}")

# ============================================================
# Migrations
# ============================================================
print("\n[Migrations]")
for cmd in [
    [sys.executable, "manage.py", "makemigrations", "social", "game"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd[1:])}")
    if r.stdout.strip(): print("   ", r.stdout.strip().replace("\n", "\n    ")[:400])
    if r.returncode != 0 and r.stderr.strip():
        print("   ERR:", r.stderr.strip()[:400])

# Final check
print("\n[check]")
r = subprocess.run([sys.executable, "manage.py", "check"], cwd=ROOT, capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check passed")
else:
    print("  ⚠ check errors:")
    print(r.stderr[:500] if r.stderr else r.stdout[:500])

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Summary:

NEW ADMIN TABS:
  📢 اعلان‌ها      → /panel-admin/announcements/
  🏆 تورنمنت‌ها   → /panel-admin/tournaments/

ANNOUNCEMENTS:
  ✓ ارسال اعلان به همه کاربران (bulk notification)
  ✓ لیست اعلان‌های ارسال‌شده + تعداد گیرنده
  ✓ حذف اعلان از صندوق همه کاربران
  ✓ نمایش با آیکن 📢 در صفحه اعلان بازیکن

TOURNAMENTS:
  ✓ ساخت با آیکن، نوع (روزانه/ساعتی/هفتگی)، وضعیت
  ✓ تاریخ شروع و پایان (datetime-local)
  ✓ هزینه ورود (سکه/جم)، جایزه (سکه/جم)
  ✓ حداقل/حداکثر بازیکن
  ✓ ویرایش کامل + حذف + خالی کردن صف
  ✓ نمایش لیست شرکت‌کننده‌ها

PLAYER SIDE:
  ✓ /game/challenge/ → ۳ بخش (هفتگی، روزانه، ساعتی)
  ✓ شمارش معکوس زنده تا شروع/پایان
  ✓ دکمه شرکت در مسابقه (deducts fee)
  ✓ نمایش «در صف هستی» بعد از ثبت‌نام
  ✓ تورنمنت‌های منقضی خودکار بسته می‌شن

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R

Login to /panel-admin/ → admin74 / Amir2255ds
""")
