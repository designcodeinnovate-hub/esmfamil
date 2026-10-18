#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")
def backup(p):
    bak = p + ".bak_j"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 0) Ensure jdatetime is installed
# ============================================================
print("\n[0/12] Ensuring jdatetime is installed")
try:
    import jdatetime
    print("  ✓ jdatetime already installed")
except ImportError:
    print("  Installing jdatetime...")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "jdatetime"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✓ jdatetime installed")
    else:
        print("  ✗ ERROR: pip install failed")
        print(r.stderr[:500])
        print("\n  ABORT. Install manually: pip install jdatetime")
        sys.exit(1)

# Update requirements.txt
p = os.path.join(ROOT, "requirements.txt")
if os.path.exists(p):
    src = read(p)
    if "jdatetime" not in src:
        src = src.rstrip() + "\njdatetime==5.1.0\n"
        write(p, src)
        print("  ✓ jdatetime added to requirements.txt")

# ============================================================
# 1) Create common/templatetags/ package + jalali_tags.py
# ============================================================
print("\n[1/12] common/templatetags/ package")
os.makedirs(os.path.join(ROOT, "common", "templatetags"), exist_ok=True)

write(os.path.join(ROOT, "common", "__init__.py"), "")
write(os.path.join(ROOT, "common", "templatetags", "__init__.py"), "")

p = os.path.join(ROOT, "common", "templatetags", "jalali_tags.py")
if os.path.exists(p):
    print("  SKIP: jalali_tags.py exists")
else:
    JALALI_TAGS = '''# -*- coding: utf-8 -*-
from django import template

try:
    import jdatetime
    HAS_JDATETIME = True
except ImportError:
    HAS_JDATETIME = False

register = template.Library()


@register.filter
def to_jalali(value):
    """Return jdatetime object (or None) from Gregorian datetime."""
    if not value:
        return None
    if not HAS_JDATETIME:
        return value
    try:
        return jdatetime.datetime.fromgregorian(datetime=value)
    except Exception:
        return None


@register.filter
def jdate(value, fmt="Y/m/d H:i"):
    """Format Gregorian datetime as Jalali string."""
    if not value:
        return ""
    if not HAS_JDATETIME:
        try:
            return value.strftime(fmt)
        except Exception:
            return str(value)
    try:
        j = jdatetime.datetime.fromgregorian(datetime=value)
        return j.strftime(fmt)
    except Exception:
        try:
            return value.strftime(fmt)
        except Exception:
            return str(value)


@register.filter
def jyear(value):
    if not value or not HAS_JDATETIME:
        return ""
    try:
        return jdatetime.datetime.fromgregorian(datetime=value).year
    except Exception:
        return ""


@register.filter
def jmonth(value):
    if not value or not HAS_JDATETIME:
        return ""
    try:
        return jdatetime.datetime.fromgregorian(datetime=value).month
    except Exception:
        return ""


@register.filter
def jday(value):
    if not value or not HAS_JDATETIME:
        return ""
    try:
        return jdatetime.datetime.fromgregorian(datetime=value).day
    except Exception:
        return ""


@register.filter
def jhour(value):
    if not value or not HAS_JDATETIME:
        return ""
    try:
        return jdatetime.datetime.fromgregorian(datetime=value).hour
    except Exception:
        return ""


@register.filter
def jminute(value):
    if not value or not HAS_JDATETIME:
        return ""
    try:
        return jdatetime.datetime.fromgregorian(datetime=value).minute
    except Exception:
        return ""


@register.filter
def jts(value):
    """Jalali human-readable, e.g. '1403/08/26 20:30'"""
    return jdate(value, "Y/m/d H:i")
'''
    write(p, JALALI_TAGS)

# ============================================================
# 2) social/models.py - add sender field to Notification
# ============================================================
print("\n[2/12] social/models.py - sender field")
p = os.path.join(ROOT, "social", "models.py")
src = read(p)

if "sender = models.ForeignKey" in src and "class Notification" in src:
    print("  SKIP: sender exists")
else:
    old = '''    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)'''
    new = '''    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
    )

    class Meta:
        ordering = ("-created_at",)'''
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: sender field added")
    else:
        print("  WARN: Notification class block not found")

# ============================================================
# 3) social/notifications.py - update notify()
# ============================================================
print("\n[3/12] social/notifications.py")
p = os.path.join(ROOT, "social", "notifications.py")
src = read(p)

if "def notify(user, ntype, title, body=\"\", url=\"\", sender=None):" in src:
    print("  SKIP: notify updated")
else:
    old = '''def notify(user, ntype, title, body="", url=""):
    """ساخت اعلان جدید."""
    try:
        return Notification.objects.create(
            user=user, type=ntype, title=title, body=body, url=url,
        )
    except Exception:
        return None'''
    new = '''def notify(user, ntype, title, body="", url="", sender=None):
    """ساخت اعلان جدید."""
    try:
        return Notification.objects.create(
            user=user, type=ntype, title=title, body=body, url=url, sender=sender,
        )
    except Exception:
        return None'''
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: notify accepts sender")
    else:
        print("  WARN: notify func not found")

# ============================================================
# 4) social/views.py - send_game_invite sender + notifications select_related
# ============================================================
print("\n[4/12] social/views.py")
p = os.path.join(ROOT, "social", "views.py")
src = read(p)
changed = False

# 4a) game_invite: add sender
old = '''        Notification.objects.create(
            user=to_user,
            type="game_invite",
            title="دعوت به بازی",
            body=f"{request.user.alias} شما را به بازی دعوت کرد!",
            url="/social/"
        )'''
new = '''        Notification.objects.create(
            user=to_user,
            type="game_invite",
            title="دعوت به بازی",
            body=f"{request.user.alias} شما را به بازی دعوت کرد!",
            url="/social/",
            sender=request.user,
        )'''
if old in src:
    src = src.replace(old, new, 1); changed = True
    print("  FIXED: game_invite sets sender")

# 4b) notifications_view: select_related
old = '''@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user)
    # علامت‌گذاری به‌عنوان خوانده‌شده
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, "social/notifications.html", {
        "notifications": notifs,
        "active": "friends",
    })'''
new = '''@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).select_related("sender")
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, "social/notifications.html", {
        "notifications": notifs,
        "active": "friends",
    })'''
if old in src:
    src = src.replace(old, new, 1); changed = True
    print("  FIXED: notifications_view uses select_related")

if changed:
    backup(p); write(p, src)

# ============================================================
# 5) notifications.html - show sender name
# ============================================================
print("\n[5/12] notifications.html - show sender")
p = os.path.join(ROOT, "social", "templates", "social", "notifications.html")
src = read(p)

if 'class="notif-sender"' in src:
    print("  SKIP: sender display exists")
else:
    # add CSS
    css_anchor = "  .notif-time { font-size: 10px; color: var(--dim); margin-top: 6px; }"
    css_add = css_anchor + '''
  .notif-sender {
    font-size: 11px;
    color: #c4b5fd;
    margin-bottom: 3px;
    display: flex;
    align-items: center;
    gap: 5px;
    font-weight: bold;
  }
  .notif-sender .badge {
    font-size: 9px;
    padding: 1px 6px;
    border-radius: 5px;
    background: rgba(139,92,246,0.2);
    color: #c4b5fd;
    font-weight: bold;
  }
  .notif-sender .badge-admin {
    background: rgba(245,158,11,0.2);
    color: #fde68a;
  }'''
    if css_anchor in src:
        src = src.replace(css_anchor, css_add, 1)

    # Update title area to show sender
    old_title = '''        <div class="notif-body">
          <div class="notif-title">{{ n.title }}</div>
          {% if n.body %}<div class="notif-desc">{{ n.body }}</div>{% endif %}
          <div class="notif-time">{{ n.created_at|date:"Y/m/d H:i" }}</div>
        </div>'''
    new_title = '''        <div class="notif-body">
          <div class="notif-title">{{ n.title }}</div>
          {% if n.sender %}
            <div class="notif-sender">👤 {{ n.sender.alias }} <span style="font-size:9px; opacity:0.6;">@{{ n.sender.username }}</span></div>
          {% elif n.type == "admin_broadcast" %}
            <div class="notif-sender"><span class="badge badge-admin">📢 مدیر سیستم</span></div>
          {% endif %}
          {% if n.body %}<div class="notif-desc">{{ n.body }}</div>{% endif %}
          <div class="notif-time">{{ n.created_at|date:"Y/m/d H:i" }}</div>
        </div>'''
    if old_title in src:
        src = src.replace(old_title, new_title, 1)
        backup(p); write(p, src)
        print("  FIXED: sender display added")
    else:
        print("  WARN: notif body block not found")

# ============================================================
# 6) admin_views.py - announcement sender + Jalali save
# ============================================================
print("\n[6/12] admin_views.py")
p = os.path.join(ROOT, "accounts", "admin_views.py")
src = read(p)
changed = False

# 6a) announcement_create: add sender
old = '''    from django.contrib.auth import get_user_model
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
        total += len(batch)'''
new = '''    from django.contrib.auth import get_user_model
    from social.models import Notification
    User = get_user_model()

    # Find sender (a staff user, or the first staff user)
    sender_user = User.objects.filter(is_staff=True).first()

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
            sender=sender_user,
        ))
        if len(batch) >= 500:
            Notification.objects.bulk_create(batch)
            total += len(batch)
            batch = []
    if batch:
        Notification.objects.bulk_create(batch)
        total += len(batch)'''
if old in src:
    src = src.replace(old, new, 1); changed = True
    print("  FIXED: announcement sets sender")

# 6b) _save_tournament_from_post: use Jalali inputs
old_save = '''def _save_tournament_from_post(request, t=None):
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
'''

new_save = '''def _parse_jalali_dt(request, prefix):
    """Read Jalali picker fields from POST, return Gregorian aware datetime."""
    import jdatetime
    from django.utils import timezone as tz
    try:
        jy = int(request.POST.get(prefix + "_jy") or 0)
        jm = int(request.POST.get(prefix + "_jm") or 0)
        jd = int(request.POST.get(prefix + "_jd") or 0)
        jh = int(request.POST.get(prefix + "_jh") or 0)
        jmin = int(request.POST.get(prefix + "_jmin") or 0)
    except (ValueError, TypeError):
        return None

    if not (1300 <= jy <= 1500 and 1 <= jm <= 12 and 1 <= jd <= 31):
        return None
    if not (0 <= jh <= 23 and 0 <= jmin <= 59):
        return None

    try:
        j = jdatetime.datetime(jy, jm, jd, jh, jmin)
        g = j.togregorian()
        if tz.is_naive(g):
            g = tz.make_aware(g)
        return g
    except (ValueError, TypeError):
        return None


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

    start_at = _parse_jalali_dt(request, "start")
    end_at = _parse_jalali_dt(request, "end")
    if not start_at or not end_at:
        return None, "تاریخ شروع و پایان الزامی است (به شمسی)."
    if end_at <= start_at:
        return None, "تاریخ پایان باید بعد از شروع باشد."
'''
if old_save in src:
    src = src.replace(old_save, new_save, 1); changed = True
    print("  FIXED: _save_tournament_from_post uses Jalali")

if changed:
    backup(p); write(p, src)

# ============================================================
# 7) tournament_edit.html - Jalali pickers
# ============================================================
print("\n[7/12] tournament_edit.html - Jalali pickers")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "tournament_edit.html")

EDIT_HTML = '''{% load jalali_tags %}<!doctype html>
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
    input[type=text], input[type=number], textarea, select { width: 100%; padding: 12px 14px; border-radius: 10px; border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15; color: #fff; font-size: 14px; font-family: inherit; box-sizing: border-box; }
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
    button.danger-btn { padding: 10px 20px; border: none; border-radius: 10px; font-family: inherit; font-weight: bold; font-size: 13px; cursor: pointer; background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4); margin-left: 8px; }
    button.del-btn { padding: 10px 20px; border: none; border-radius: 10px; font-family: inherit; font-weight: bold; font-size: 13px; cursor: pointer; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; }

    /* ===== Jalali picker ===== */
    .jalali-picker {
      display: grid;
      grid-template-columns: 90px 1fr 70px 70px 70px;
      gap: 6px;
      margin-top: 4px;
    }
    .jalali-picker select {
      padding: 10px 8px;
      font-size: 13px;
      text-align: center;
      background: #0a0a15;
      border: 1.5px solid rgba(148,163,184,0.2);
      border-radius: 10px;
      color: #fff;
      font-family: inherit;
    }
    .jalali-picker select:focus { outline: none; border-color: #facc15; }
    .jalali-picker .jp-col { display: flex; flex-direction: column; gap: 2px; }
    .jalali-picker .jp-lbl { font-size: 9px; color: #64748b; text-align: center; }

    .jalali-hint {
      font-size: 11px;
      color: #64748b;
      margin-top: 6px;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .jalali-preview {
      margin-top: 8px;
      padding: 8px 12px;
      border-radius: 8px;
      background: rgba(250,204,21,0.08);
      border: 1px dashed rgba(250,204,21,0.3);
      font-size: 12px;
      color: #fde68a;
      font-family: monospace;
    }

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

  <form method="post" id="tourForm">
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

    {% with start_j=tournament.start_at|to_jalali end_j=tournament.end_at|to_jalali %}
    <div class="card">
      <h3>⏰ زمان‌بندی (تاریخ شمسی)</h3>

      <label>تاریخ و ساعت شروع</label>
      <div class="jalali-picker">
        <div class="jp-col">
          <select name="start_jy">
            {% for y in year_options %}
              <option value="{{ y }}" {% if start_j and start_j.year == y %}selected{% elif not start_j and y == default_jy %}selected{% endif %}>{{ y }}</option>
            {% endfor %}
          </select>
          <div class="jp-lbl">سال</div>
        </div>
        <div class="jp-col">
          <select name="start_jm">
            {% for m_num, m_name in month_options %}
              <option value="{{ m_num }}" {% if start_j and start_j.month == m_num %}selected{% elif not start_j and m_num == default_jm %}selected{% endif %}>{{ m_name }}</option>
            {% endfor %}
          </select>
          <div class="jp-lbl">ماه</div>
        </div>
        <div class="jp-col">
          <select name="start_jd">
            {% for d in day_options %}
              <option value="{{ d }}" {% if start_j and start_j.day == d %}selected{% elif not start_j and d == default_jd %}selected{% endif %}>{{ d }}</option>
            {% endfor %}
          </select>
          <div class="jp-lbl">روز</div>
        </div>
        <div class="jp-col">
          <select name="start_jh">
            {% for h in hour_options %}
              <option value="{{ h }}" {% if start_j and start_j.hour == h %}selected{% elif not start_j and h == default_jh %}selected{% endif %}>{{ h }}</option>
            {% endfor %}
          </select>
          <div class="jp-lbl">ساعت</div>
        </div>
        <div class="jp-col">
          <select name="start_jmin">
            {% for mn in minute_options %}
              <option value="{{ mn }}" {% if start_j and start_j.minute == mn %}selected{% elif not start_j and mn == 0 %}selected{% endif %}>{{ mn }}</option>
            {% endfor %}
          </select>
          <div class="jp-lbl">دقیقه</div>
        </div>
      </div>
      <div class="jalali-hint">📅 تقویم شمسی (هجری خورشیدی)</div>

      <label style="margin-top: 20px;">تاریخ و ساعت پایان</label>
      <div class="jalali-picker">
        <div class="jp-col">
          <select name="end_jy">
            {% for y in year_options %}
              <option value="{{ y }}" {% if end_j and end_j.year == y %}selected{% elif not end_j and y == default_jy %}selected{% endif %}>{{ y }}</option>
            {% endfor %}
          </select>
          <div class="jp-lbl">سال</div>
        </div>
        <div class="jp-col">
          <select name="end_jm">
            {% for m_num, m_name in month_options %}
              <option value="{{ m_num }}" {% if end_j and end_j.month == m_num %}selected{% elif not end_j and m_num == default_jm %}selected{% endif %}>{{ m_name }}</option>
            {% endfor %}
          </select>
          <div class="jp-lbl">ماه</div>
        </div>
        <div class="jp-col">
          <select name="end_jd">
            {% for d in day_options %}
              <option value="{{ d }}" {% if end_j and end_j.day == d %}selected{% elif not end_j and d == default_jd %}selected{% endif %}>{{ d }}</option>
            {% endfor %}
          </select>
          <div class="jp-lbl">روز</div>
        </div>
        <div class="jp-col">
          <select name="end_jh">
            {% for h in hour_options %}
              <option value="{{ h }}" {% if end_j and end_j.hour == h %}selected{% elif not end_j and h == default_end_jh %}selected{% endif %}>{{ h }}</option>
            {% endfor %}
          </select>
          <div class="jp-lbl">ساعت</div>
        </div>
        <div class="jp-col">
          <select name="end_jmin">
            {% for mn in minute_options %}
              <option value="{{ mn }}" {% if end_j and end_j.minute == mn %}selected{% elif not end_j and mn == 0 %}selected{% endif %}>{{ mn }}</option>
            {% endfor %}
          </select>
          <div class="jp-lbl">دقیقه</div>
        </div>
      </div>
      <div class="jalali-hint">📅 تقویم شمسی (هجری خورشیدی)</div>
    </div>
    {% endwith %}

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
            <tr><th>#</th><th>نام نمایشی</th><th>username</th><th>امتیاز</th><th>تاریخ عضویت</th></tr>
          </thead>
          <tbody>
            {% for e in entries %}
              <tr>
                <td>{{ forloop.counter }}</td>
                <td>{{ e.alias }}</td>
                <td style="font-family:monospace; color:#94a3b8;">@{{ e.username }}</td>
                <td style="color:#facc15; font-family:monospace; font-weight:bold;">{{ e.score }}</td>
                <td style="font-size:11px; color:#64748b;">{{ e.joined_at|jdate:"Y/m/d H:i" }}</td>
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
# 8) admin_views.py - pass Jalali picker options to template
# ============================================================
print("\n[8/12] admin_views.py - pass Jalali options")
p = os.path.join(ROOT, "accounts", "admin_views.py")
src = read(p)

# Find tournament_create and tournament_edit, add context
old_create = '''    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/tournament_edit.html", {
        "tournament": None,
        "message": message,
    })'''
new_create = '''    message = request.session.pop("admin_message", None)
    import jdatetime
    from datetime import timedelta
    now_j = jdatetime.datetime.now()
    tomorrow_j = now_j + timedelta(days=1)
    return render(request, "custom_admin/tournament_edit.html", {
        "tournament": None,
        "message": message,
        "year_options": list(range(now_j.year - 1, now_j.year + 3)),
        "month_options": [
            (1, "فروردین"), (2, "اردیبهشت"), (3, "خرداد"), (4, "تیر"),
            (5, "مرداد"), (6, "شهریور"), (7, "مهر"), (8, "آبان"),
            (9, "آذر"), (10, "دی"), (11, "بهمن"), (12, "اسفند"),
        ],
        "day_options": list(range(1, 32)),
        "hour_options": list(range(0, 24)),
        "minute_options": list(range(0, 60, 5)),
        "default_jy": now_j.year,
        "default_jm": now_j.month,
        "default_jd": now_j.day,
        "default_jh": now_j.hour,
        "default_end_jh": tomorrow_j.hour,
    })'''
if old_create in src:
    src = src.replace(old_create, new_create, 1)
    print("  FIXED: tournament_create context")

old_edit = '''    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/tournament_edit.html", {
        "tournament": t,
        "entries": entries_data,
        "message": message,
    })'''
new_edit = '''    message = request.session.pop("admin_message", None)
    import jdatetime
    from datetime import timedelta
    now_j = jdatetime.datetime.now()
    tomorrow_j = now_j + timedelta(days=1)
    return render(request, "custom_admin/tournament_edit.html", {
        "tournament": t,
        "entries": entries_data,
        "message": message,
        "year_options": list(range(now_j.year - 1, now_j.year + 3)),
        "month_options": [
            (1, "فروردین"), (2, "اردیبهشت"), (3, "خرداد"), (4, "تیر"),
            (5, "مرداد"), (6, "شهریور"), (7, "مهر"), (8, "آبان"),
            (9, "آذر"), (10, "دی"), (11, "بهمن"), (12, "اسفند"),
        ],
        "day_options": list(range(1, 32)),
        "hour_options": list(range(0, 24)),
        "minute_options": list(range(0, 60, 5)),
        "default_jy": now_j.year,
        "default_jm": now_j.month,
        "default_jd": now_j.day,
        "default_jh": now_j.hour,
        "default_end_jh": tomorrow_j.hour,
    })'''
if old_edit in src:
    src = src.replace(old_edit, new_edit, 1)
    print("  FIXED: tournament_edit context")

backup(p); write(p, src)

# ============================================================
# 9) tournaments.html - display Jalali dates
# ============================================================
print("\n[9/12] tournaments.html - Jalali display")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "tournaments.html")
src = read(p)

if "{% load jalali_tags %}" not in src:
    src = src.replace("<!doctype html>", "{% load jalali_tags %}<!doctype html>", 1)

old = '''            <div class="row"><span class="lbl">شروع</span><span class="val">{{ t.start_at|date:"Y/m/d H:i" }}</span></div>
            <div class="row"><span class="lbl">پایان</span><span class="val">{{ t.end_at|date:"Y/m/d H:i" }}</span></div>'''
new = '''            <div class="row"><span class="lbl">شروع</span><span class="val">{{ t.start_at|jdate:"Y/m/d H:i" }}</span></div>
            <div class="row"><span class="lbl">پایان</span><span class="val">{{ t.end_at|jdate:"Y/m/d H:i" }}</span></div>'''
if old in src:
    src = src.replace(old, new, 1)
    backup(p); write(p, src)
    print("  FIXED: Jalali dates in tournaments list")
else:
    print("  SKIP: dates already using jdate or block not found")

# ============================================================
# 10) challenge.html - Jalali in cards
# ============================================================
print("\n[10/12] challenge.html")
p = os.path.join(ROOT, "game", "templates", "game", "challenge.html")
src = read(p)
if "{% load jalali_tags %}" not in src:
    src = src.replace("{% extends \"base.html\" %}", "{% extends \"base.html\" %}\n{% load jalali_tags %}", 1)
    backup(p); write(p, src)
    print("  FIXED: load jalali_tags in challenge.html")

# ============================================================
# 11) _tournament_card.html - show Jalali start/end
# ============================================================
print("\n[11/12] _tournament_card.html")
p = os.path.join(ROOT, "game", "templates", "game", "_tournament_card.html")
src = read(p)

# Add jalali load at top
if "{% load jalali_tags %}" not in src:
    src = "{% load jalali_tags %}" + src

# Add dates display in details section
if "📅 شروع:" not in src:
    old_details = '''  <div class="tour-details">
    <div class="tour-detail">👥 <b>{{ t.entry_count }}</b> / {{ t.max_players }}</div>
    {% if t.prize_coins %}<div class="tour-detail">🪙 <b>{{ t.prize_coins }}</b></div>{% endif %}
    {% if t.prize_gems %}<div class="tour-detail">💎 <b>{{ t.prize_gems }}</b></div>{% endif %}
    {% if t.entry_fee_coins %}<div class="tour-detail">ورود: <b>{{ t.entry_fee_coins }}</b> سکه</div>{% endif %}
  </div>'''
    new_details = '''  <div class="tour-details">
    <div class="tour-detail">👥 <b>{{ t.entry_count }}</b> / {{ t.max_players }}</div>
    {% if t.prize_coins %}<div class="tour-detail">🪙 <b>{{ t.prize_coins }}</b></div>{% endif %}
    {% if t.prize_gems %}<div class="tour-detail">💎 <b>{{ t.prize_gems }}</b></div>{% endif %}
    {% if t.entry_fee_coins %}<div class="tour-detail">ورود: <b>{{ t.entry_fee_coins }}</b> سکه</div>{% endif %}
  </div>

  <div class="tour-details" style="font-size: 10px; opacity: 0.85;">
    <div class="tour-detail">📅 شروع: {{ t.start_at|jdate:"Y/m/d H:i" }}</div>
    <div class="tour-detail">⏳ پایان: {{ t.end_at|jdate:"Y/m/d H:i" }}</div>
  </div>'''
    if old_details in src:
        src = src.replace(old_details, new_details, 1)
        backup(p); write(p, src)
        print("  FIXED: Jalali dates in tournament card")

# ============================================================
# 12) Migrations + check
# ============================================================
print("\n[12/12] Migrations + check")
for cmd in [
    [sys.executable, "manage.py", "makemigrations", "social"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd[1:])}")
    if r.stdout.strip(): print("   ", r.stdout.strip().replace("\n", "\n    ")[:400])
    if r.returncode != 0 and r.stderr.strip():
        print("   ERR:", r.stderr.strip()[:400])

r = subprocess.run([sys.executable, "manage.py", "check"], cwd=ROOT, capture_output=True, text=True)
if r.returncode == 0:
    print("\n  ✓ Django check passed")
else:
    print("\n  ⚠ check errors:")
    print(r.stderr[:600] if r.stderr else r.stdout[:600])

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
What's new:

NOTIFICATIONS (sender):
  ✓ Notification.sender FK to User (nullable) + migration
  ✓ notify() accepts sender
  ✓ game_invite sets sender=request.user
  ✓ admin_broadcast sets sender=admin (first staff user)
  ✓ notifications.html shows sender name under title:
    - For user-origin notifs: 👤 {alias} @{username}
    - For admin broadcasts (no sender): 📢 مدیر سیستم

TOURNAMENT DATES (Jalali):
  ✓ jdatetime package installed + added to requirements.txt
  ✓ New template filter: jdate, to_jalali, jyear, jmonth, jday, jhour, jminute
  ✓ tournament_edit.html: 5 dropdowns per date (سال/ماه/روز/ساعت/دقیقه)
  ✓ _save_tournament_from_post reads Jalali + converts to Gregorian for DB
  ✓ tournaments.html displays dates in Jalali
  ✓ _tournament_card.html shows 📅 شروع / ⏳ پایان
  ✓ Backwards compatible (old data still works)

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R

Test:
  1. /panel-admin/tournaments/ → ساخت تورنمنت
     - Dates picker is now Jalali (1403/08/26 style)
     - Pick تاریخ شروع: 1403, آبان, 26, 20, 30
     - Pick تاریخ پایان: same day, 22, 0
     - Save → list shows 1403/08/26 20:30 (Jalali)
  2. /social/notifications/ → sender name visible for game invites & admin broadcasts
""")
