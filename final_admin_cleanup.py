#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove send-to-all + guest-log tabs. Full guest deletion. Notification read tracking."""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    if not os.path.exists(p): return ""
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Add NotificationRead model to track per-user reads
# ============================================================
print("\n[1/6] Adding NotificationRead model")
p = "social/models.py"
src = read(p)

if "class NotificationRead(models.Model):" in src:
    print("  ✓ Already exists")
else:
    src = src.rstrip() + '''


class NotificationRead(models.Model):
    """Track when each user reads a broadcast notification."""
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="reads"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("notification", "user")
        ordering = ("-read_at",)

    def __str__(self):
        return f"{self.user.alias} read #{self.notification_id}"
'''
    write(p, src)
    print("  ✓ NotificationRead model added")

# ============================================================
# 2) Update notifications_view to create NotificationRead records
# ============================================================
print("\n[2/6] Updating notifications_view to track reads")

p = "social/views.py"
src = read(p)

# Find and replace notifications_view
pattern = re.compile(r'@login_required\ndef notifications_view\(request\):.*?(?=\n@login_required|\ndef |\Z)', re.DOTALL)
m = pattern.search(src)
if m:
    new_view = '''@login_required
def notifications_view(request):
    from .models import Notification, NotificationRead

    all_notifs = list(
        Notification.objects.filter(user=request.user)
        .select_related("sender")
        .order_by("-created_at")
    )
    unread = sum(1 for n in all_notifs if not n.is_read)

    # Record reads for broadcast notifications
    broadcast_notifs = [n for n in all_notifs if n.type == "admin_broadcast" and not n.is_read]
    for n in broadcast_notifs:
        try:
            NotificationRead.objects.get_or_create(notification=n, user=request.user)
        except Exception:
            pass

    # Mark all as read
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    return render(request, "social/notifications.html", {
        "notifications": all_notifs,
        "unread_total": unread,
        "active": "home",
    })
'''
    src = src.replace(m.group(0), new_view)
    write(p, src)
    print("  ✓ notifications_view updated with NotificationRead tracking")
else:
    print("  ⚠ Could not find notifications_view")

# ============================================================
# 3) Update announcements_list to show WHO read
# ============================================================
print("\n[3/6] Updating announcements_list to show readers")

p = "accounts/admin_views.py"
src = read(p)

pattern = re.compile(r'@never_cache\ndef announcements_list\(request\):.*?(?=\n@never_cache|\ndef |\Z)', re.DOTALL)
m = pattern.search(src)
if m:
    new_view = '''@never_cache
def announcements_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")

    from social.models import Notification, NotificationRead
    from django.contrib.auth import get_user_model
    from django.db.models import Count, Q
    User = get_user_model()

    # Handle POST actions
    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "send_all":
            # Simple announcement to all
            title = (request.POST.get("title") or "").strip()[:100]
            body = (request.POST.get("body") or "").strip()[:300]
            url = (request.POST.get("url") or "").strip()[:200]

            if not title:
                request.session["admin_message"] = {"type": "error", "text": "عنوان الزامی است."}
                return redirect("custom_admin:announcements_list")

            sender = User.objects.filter(is_staff=True).first()
            uids = User.objects.values_list("id", flat=True)
            batch = []
            total = 0
            for uid in uids.iterator(chunk_size=1000):
                batch.append(Notification(
                    user_id=uid, type="admin_broadcast",
                    title=title, body=body, url=url,
                    is_read=False, sender=sender,
                ))
                if len(batch) >= 500:
                    Notification.objects.bulk_create(batch)
                    total += len(batch)
                    batch = []
            if batch:
                Notification.objects.bulk_create(batch)
                total += len(batch)

            request.session["admin_message"] = {"type": "success", "text": f"اعلان برای {total} کاربر ارسال شد."}
            return redirect("custom_admin:announcements_list")

    # GET — show list with reader details
    qs = Notification.objects.filter(type="admin_broadcast").order_by("-created_at")

    seen = set()
    data = []
    for n in qs.iterator(chunk_size=200):
        key = (n.title, n.body or "", n.url or "")
        if key in seen:
            continue
        seen.add(key)

        # All notifications with this content
        notif_ids = Notification.objects.filter(
            type="admin_broadcast",
            title=n.title,
            body=n.body or "",
            url=n.url or "",
        ).values_list("id", flat=True)

        total = Notification.objects.filter(id__in=notif_ids).count()
        read_count = Notification.objects.filter(id__in=notif_ids, is_read=True).count()
        unread_count = total - read_count

        # Get readers with usernames
        readers = list(
            NotificationRead.objects.filter(notification_id__in=notif_ids)
            .select_related("user")
            .order_by("-read_at")[:50]
        )
        readers_data = []
        seen_users = set()
        for r in readers:
            if r.user_id in seen_users:
                continue
            seen_users.add(r.user_id)
            readers_data.append({
                "username": r.user.username,
                "alias": r.user.alias,
                "read_at": r.read_at,
            })

        data.append({
            "title": n.title,
            "body": n.body,
            "url": n.url,
            "created_at": n.created_at,
            "recipients": total,
            "read_count": read_count,
            "unread_count": unread_count,
            "readers": readers_data,
        })

    message = request.session.pop("admin_message", None)
    total_users = User.objects.count()

    return render(request, "custom_admin/announcements.html", {
        "announcements": data,
        "message": message,
        "total_users": total_users,
    })
'''
    src = src.replace(m.group(0), new_view)
    write(p, src)
    print("  ✓ announcements_list updated with reader tracking")

# ============================================================
# 4) Update logout_view for full guest deletion
# ============================================================
print("\n[4/6] Updating logout_view for full guest deletion")

p = "accounts/views.py"
src = read(p)

# Find logout_view
pattern = re.compile(r'def logout_view\(request\):.*?(?=\ndef |\Z)', re.DOTALL)
m = pattern.search(src)
if m:
    new_logout = '''def logout_view(request):
    """Logout + full guest account deletion."""
    if request.user.is_authenticated and getattr(request.user, "is_guest", False):
        try:
            from .models import GuestDeletionLog
            from game.models import Player, Answer, BotAnswer
            from social.models import (
                Friendship, Notification, GameInvite, NotificationRead
            )
            from alliance.models import AllianceMember, AllianceMessage

            u = request.user
            u_id = u.id

            # Log BEFORE deletion
            try:
                from django.db.models import Sum
                total_games = Player.objects.filter(user_id=u_id).count()
                total_score = Player.objects.filter(user_id=u_id).aggregate(
                    t=Sum("score")
                )["t"] or 0

                GuestDeletionLog.objects.create(
                    username=u.username,
                    alias=u.alias or u.username,
                    public_id=u.public_id,
                    avatar_id=u.avatar_id,
                    total_games=total_games,
                    total_score=total_score,
                    joined_at=u.date_joined,
                )
            except Exception as e:
                print(f"[guest log] {e}")

            # Logout first
            logout(request)

            # Delete everything related to this guest
            try:
                # Social
                Friendship.objects.filter(
                    models.Q(from_user_id=u_id) | models.Q(to_user_id=u_id)
                ).delete()
                Notification.objects.filter(user_id=u_id).delete()
                GameInvite.objects.filter(
                    models.Q(from_user_id=u_id) | models.Q(to_user_id=u_id)
                ).delete()
                NotificationRead.objects.filter(user_id=u_id).delete()

                # Alliance
                AllianceMember.objects.filter(user_id=u_id).delete()
                AllianceMessage.objects.filter(sender_id=u_id).delete()

                # Game answers
                Answer.objects.filter(user_id=u_id).delete()

                # Player rows
                Player.objects.filter(user_id=u_id).delete()

                # Finally, user
                from django.contrib.auth import get_user_model
                User = get_user_model()
                User.objects.filter(id=u_id).delete()

                print(f"[guest] Fully deleted user {u_id}")
            except Exception as e:
                print(f"[guest deletion] {e}")

        except Exception as e:
            print(f"[logout guest] {e}")
            logout(request)

        return redirect("landing")

    logout(request)
    return redirect("landing")
'''
    # Need to add models.Q import
    if "from django.db import models" not in src and "from django.db import" not in src:
        src = src.replace("from django.shortcuts import", "from django.db import models\nfrom django.shortcuts import", 1)

    src = src.replace(m.group(0), new_logout)
    write(p, src)
    print("  ✓ logout_view: full guest deletion")

# ============================================================
# 5) Remove guest-log and send-to-all tabs from all admin templates
# ============================================================
print("\n[5/6] Removing guest-log and send-to-all tabs")

admin_files = [
    "dashboard.html", "alliances.html", "alliance_detail.html",
    "rooms.html", "announcements.html", "tournaments.html",
    "tournament_edit.html", "shop_items.html",
    "user_detail.html", "user_edit.html", "user_notify.html",
]

for fname in admin_files:
    path = f"accounts/templates/custom_admin/{fname}"
    if not os.path.exists(path): continue
    src = read(path)
    original = src

    # Remove guest-log tab
    src = re.sub(
        r'\s*<a\s+href="/panel-admin/guest-log/"[^>]*>.*?</a>',
        '',
        src,
        flags=re.DOTALL
    )

    # Remove send-to-all tab
    src = re.sub(
        r'\s*<a\s+href="/panel-admin/send-to-all/"[^>]*>.*?</a>',
        '',
        src,
        flags=re.DOTALL
    )

    if src != original:
        write(path, src)
        print(f"  ✓ Removed tabs from {fname}")

# ============================================================
# 6) Update announcements.html template — compact form + reader names
# ============================================================
print("\n[6/6] Rebuilding announcements.html")

ANN_HTML = '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>اعلان‌ها — پنل ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 16px 16px 40px; }
    .container { max-width: 1400px; margin: 0 auto; }

    .admin-sticky-header {
      position: sticky; top: 0; z-index: 500;
      background: #0a0a15; padding: 4px 0 8px;
      margin-bottom: 20px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.7);
    }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 8px; }
    .topbar h1 { font-size: 20px; color: #fca5a5; }

    .admin-tabs {
      display: flex !important; gap: 6px !important;
      overflow-x: auto !important; overflow-y: hidden !important;
      white-space: nowrap !important; padding: 8px !important;
      background: #12121f !important;
      border: 1px solid rgba(148,163,184,0.15) !important;
      border-radius: 14px !important;
      scrollbar-width: none !important;
      height: 48px !important;
    }
    .admin-tabs::-webkit-scrollbar { display: none; }
    .admin-tab {
      flex: 0 0 auto !important; height: 40px !important;
      display: inline-flex !important; align-items: center !important;
      padding: 0 14px !important; border-radius: 10px !important;
      text-decoration: none !important; font-size: 12px !important;
      font-weight: bold !important; color: #94a3b8 !important;
      white-space: nowrap !important;
    }
    .admin-tab:hover { background: rgba(148,163,184,0.1) !important; color: #fff !important; }
    .admin-tab.active { background: linear-gradient(135deg, #ef4444, #dc2626) !important; color: #fff !important; }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .card { background: #12121f; border: 1px solid rgba(148,163,184,0.15); border-radius: 16px; padding: 22px; margin-bottom: 16px; }
    .card h3 { color: #fdba74; font-size: 15px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }

    .form-row { margin-bottom: 10px; }
    .form-row label { display: block; font-size: 11px; color: #94a3b8; margin-bottom: 4px; font-weight: bold; }
    .form-row input[type=text], .form-row textarea { width: 100%; padding: 10px 12px; border-radius: 10px; border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15; color: #fff; font-size: 13px; font-family: inherit; }
    .form-row input:focus, .form-row textarea:focus { outline: none; border-color: #facc15; }
    .form-row textarea { min-height: 60px; resize: vertical; }

    .send-btn { padding: 12px 24px; border: none; border-radius: 10px; background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; font-family: inherit; font-weight: bold; font-size: 14px; cursor: pointer; }
    .send-btn:hover { transform: translateY(-1px); }

    /* Announcement items */
    .ann-card { background: linear-gradient(135deg, #1a1a2e, #12121f); border: 1px solid rgba(245,158,11,0.3); border-radius: 14px; padding: 16px; margin-bottom: 12px; }
    .ann-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
    .ann-icon { width: 40px; height: 40px; border-radius: 10px; background: rgba(245,158,11,0.2); display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
    .ann-info { flex: 1; min-width: 150px; }
    .ann-title { font-size: 15px; font-weight: bold; color: #fde68a; margin-bottom: 3px; }
    .ann-meta { font-size: 10px; color: #64748b; font-family: monospace; }
    .ann-body { font-size: 13px; color: #cbd5e1; line-height: 1.6; margin: 10px 0; padding: 10px; background: rgba(15,23,42,0.4); border-radius: 8px; }

    .stat-chips { display: flex; gap: 6px; margin: 10px 0; flex-wrap: wrap; }
    .stat-chip { padding: 5px 12px; border-radius: 8px; font-size: 11px; font-weight: bold; font-family: monospace; }
    .stat-chip.total { background: rgba(148,163,184,0.15); color: #cbd5e1; }
    .stat-chip.read { background: rgba(34,197,94,0.2); color: #4ade80; }
    .stat-chip.unread { background: rgba(234,179,8,0.2); color: #fde68a; }

    /* Readers list */
    .readers-section { margin-top: 10px; padding: 10px; background: rgba(34,197,94,0.05); border: 1px solid rgba(34,197,94,0.2); border-radius: 10px; }
    .readers-title { font-size: 11px; color: #4ade80; font-weight: bold; margin-bottom: 8px; }
    .readers-list { display: flex; flex-wrap: wrap; gap: 6px; }
    .reader-chip {
      padding: 4px 10px; border-radius: 16px;
      background: rgba(34,197,94,0.15); border: 1px solid rgba(34,197,94,0.3);
      color: #86efac; font-size: 11px; font-weight: bold;
    }
    .reader-chip .time { font-size: 9px; opacity: 0.6; margin-right: 4px; }
    .readers-empty { color: #64748b; font-size: 11px; font-style: italic; }

    /* Unread users */
    .unread-section { margin-top: 10px; padding: 10px; background: rgba(234,179,8,0.05); border: 1px solid rgba(234,179,8,0.2); border-radius: 10px; }
    .unread-title { font-size: 11px; color: #fde68a; font-weight: bold; margin-bottom: 8px; }

    .ann-actions { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 12px; }
    .ann-actions form { display: inline; }
    .btn-sm { padding: 7px 14px; border: none; border-radius: 8px; font-family: inherit; font-size: 11px; font-weight: bold; cursor: pointer; }
    .btn-mark-read { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .btn-mark-unread { background: rgba(234,179,8,0.15); color: #fde68a; border: 1px solid rgba(234,179,8,0.3); }
    .btn-del-ann { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
    .btn-sm:hover { transform: translateY(-1px); }

    .empty-state { text-align: center; padding: 40px 20px; color: #64748b; font-size: 13px; }
    .empty-state .icon { font-size: 60px; display: block; margin-bottom: 12px; opacity: 0.5; }
  </style>
</head>
<body>
<div class="container">
  <div class="admin-sticky-header">
    <div class="topbar">
      <h1>📢 اعلان‌ها</h1>
    </div>

    <div class="admin-tabs">
      <a href="/panel-admin/dashboard/" class="admin-tab {% if '/panel-admin/dashboard/' in request.path or request.path == '/panel-admin/' %}active{% endif %}">👥 کاربران</a>
      <a href="/panel-admin/alliances/" class="admin-tab {% if '/panel-admin/alliance' in request.path %}active{% endif %}">🛡️ اتحادها</a>
      <a href="/panel-admin/rooms/" class="admin-tab {% if '/panel-admin/room' in request.path %}active{% endif %}">🚪 اتاق‌ها</a>
      <a href="/panel-admin/announcements/" class="admin-tab {% if '/panel-admin/announcement' in request.path %}active{% endif %}">📢 اعلان‌ها</a>
      <a href="/panel-admin/tournaments/" class="admin-tab {% if '/panel-admin/tournament' in request.path %}active{% endif %}">🏆 تورنمنت</a>
      <a href="/panel-admin/shop/" class="admin-tab {% if '/panel-admin/shop/' in request.path %}active{% endif %}">🛒 فروشگاه</a>
    </div>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <!-- Send new announcement -->
  <div class="card">
    <h3>📝 ارسال اعلان جدید ({{ total_users }} کاربر)</h3>
    <form method="post">
      {% csrf_token %}
      <input type="hidden" name="action" value="send_all">
      <div class="form-row">
        <label>عنوان</label>
        <input type="text" name="title" required maxlength="100" placeholder="عنوان اعلان...">
      </div>
      <div class="form-row">
        <label>متن</label>
        <textarea name="body" maxlength="300" placeholder="متن کامل..."></textarea>
      </div>
      <div class="form-row">
        <label>لینک (اختیاری)</label>
        <input type="text" name="url" maxlength="200" placeholder="/game/">
      </div>
      <button type="submit" class="send-btn">📤 ارسال به همه</button>
    </form>
  </div>

  <!-- History with readers -->
  <div class="card">
    <h3>📜 تاریخچه اعلان‌ها ({{ announcements|length }})</h3>
    {% if announcements %}
      {% for a in announcements %}
        <div class="ann-card">
          <div class="ann-head">
            <div class="ann-icon">📢</div>
            <div class="ann-info">
              <div class="ann-title">{{ a.title }}</div>
              <div class="ann-meta">{{ a.created_at|jdate:"Y/m/d H:i" }}</div>
            </div>
          </div>
          {% if a.body %}<div class="ann-body">{{ a.body }}</div>{% endif %}

          <div class="stat-chips">
            <span class="stat-chip total">👥 {{ a.recipients }} گیرنده</span>
            <span class="stat-chip read">✓ {{ a.read_count }} خوانده</span>
            <span class="stat-chip unread">● {{ a.unread_count }} نخوانده</span>
          </div>

          {% if a.url %}<div class="ann-meta" style="margin:8px 0;">🔗 {{ a.url }}</div>{% endif %}

          <!-- Readers list -->
          {% if a.readers %}
            <div class="readers-section">
              <div class="readers-title">✓ خوانده‌شده توسط:</div>
              <div class="readers-list">
                {% for r in a.readers %}
                  <span class="reader-chip">
                    {{ r.alias|default:r.username }}
                    <span class="time">{{ r.read_at|jdate:"H:i" }}</span>
                  </span>
                {% endfor %}
                {% if a.read_count > a.readers|length %}
                  <span class="reader-chip" style="opacity:0.6;">و {{ a.read_count|add:"-"|add:a.readers|length }} نفر دیگر...</span>
                {% endif %}
              </div>
            </div>
          {% else %}
            <div class="readers-section">
              <div class="readers-title" style="color:#94a3b8;">هنوز کسی نخونده</div>
            </div>
          {% endif %}

          <div class="ann-actions">
            <form method="post" action="{% url 'custom_admin:announcement_toggle_read' %}">
              {% csrf_token %}
              <input type="hidden" name="title" value="{{ a.title }}">
              <input type="hidden" name="body" value="{{ a.body }}">
              <input type="hidden" name="url" value="{{ a.url }}">
              <input type="hidden" name="mark_as" value="read">
              <button type="submit" class="btn-sm btn-mark-read" onclick="return confirm('همه گیرنده‌ها «خوانده شد» شوند؟');">✓ علامت خوانده برای همه</button>
            </form>
            <form method="post" action="{% url 'custom_admin:announcement_toggle_read' %}">
              {% csrf_token %}
              <input type="hidden" name="title" value="{{ a.title }}">
              <input type="hidden" name="body" value="{{ a.body }}">
              <input type="hidden" name="url" value="{{ a.url }}">
              <input type="hidden" name="mark_as" value="unread">
              <button type="submit" class="btn-sm btn-mark-unread" onclick="return confirm('همه گیرنده‌ها «نخوانده» شوند؟');">● علامت نخوانده برای همه</button>
            </form>
            <form method="post" action="{% url 'custom_admin:announcement_delete' %}">
              {% csrf_token %}
              <input type="hidden" name="title" value="{{ a.title }}">
              <input type="hidden" name="body" value="{{ a.body }}">
              <input type="hidden" name="url" value="{{ a.url }}">
              <button type="submit" class="btn-sm btn-del-ann" onclick="return confirm('حذف این اعلان از همه کاربران؟');">🗑️ حذف</button>
            </form>
          </div>
        </div>
      {% endfor %}
    {% else %}
      <div class="empty-state">
        <span class="icon">📭</span>
        هنوز اعلانی ارسال نشده.
      </div>
    {% endif %}
  </div>
</div>
</body>
</html>
'''
write("accounts/templates/custom_admin/announcements.html", ANN_HTML)
print("  ✓ announcements.html rebuilt with reader tracking")

# ============================================================
# Migrations + Test
# ============================================================
print("\n" + "="*60)
print("MIGRATIONS + TEST")
print("="*60)

for cmd in [
    [sys.executable, "manage.py", "makemigrations", "social", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 and r.stderr.strip():
        print(f"  ⚠ {r.stderr[:300]}")
    else:
        print(f"  ✓ {cmd[2]}")

r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:400]}")

# Test
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

tu, created = User.objects.get_or_create(
    username="__final_test__",
    defaults={"alias": "test", "is_active": True, "is_staff": True, "has_chosen_avatar": True, "has_completed_registration": True}
)
if created:
    tu.set_password("x")
    tu.save()

c = Client()
c.session["custom_admin_logged_in"] = True
c.session["beta_unlocked"] = True
c.session.save()

print("\n  URL test:")
for url in ["/panel-admin/dashboard/", "/panel-admin/announcements/", "/panel-admin/rooms/"]:
    try:
        r = c.get(url, follow=False)
        mark = "✓" if r.status_code == 200 else "✗"
        print(f"    {mark} {url} → {r.status_code}")
    except Exception as e:
        print(f"    ✗ {url} → {type(e).__name__}")

if created:
    tu.delete()

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
What changed:

  1. REMOVED "جایزه همه" tab from all admin pages
  2. REMOVED "مهمان‌ها" tab from all admin pages
  3. Send-to-all merged into announcements (only simple message)

  4. GUEST FULL DELETION:
     - logout_view now deletes ALL guest data:
       - Friendships (both directions)
       - Notifications
       - GameInvites
       - NotificationRead
       - AllianceMember (left alliance)
       - AllianceMessage (their messages)
       - Answers (their answers)
       - Player rows
       - User record itself
     - GuestDeletionLog still created for admin record

  5. NOTIFICATION READ TRACKING:
     - New model: NotificationRead (notification, user, read_at)
     - When user opens /notifications/, creates NotificationRead
     - Admin announcements page shows:
       - 👥 N گیرنده
       - ✓ N خوانده
       - ● N نخوانده
       - List of reader names with time
       - "هنوز کسی نخونده" if no reads

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R

Test:
  1. /panel-admin/ — only 6 tabs now (no "جایزه همه", no "مهمان‌ها")
  2. /panel-admin/announcements/ — send announcement
  3. Login as a user, open /notifications/
  4. Back in admin → announcements → see "خوانده توسط: علی (20:30)"
  5. Guest logout test:
     - Login as guest
     - Click logout
     - Guest fully deleted from all tables
     - Log entry in /panel-admin/guest-log/
""")
