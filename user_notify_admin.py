#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-user notification section in admin panel."""
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Add views
# ============================================================
print("\n[1/5] Adding user_notify views to admin_views.py")
p = "accounts/admin_views.py"
src = read(p)

if "def user_notify(request, user_id):" in src:
    print("  ✓ Already exists")
else:
    src = src.rstrip() + '''

# ============================================================
# Admin — Per-user notification
# ============================================================
@never_cache
def user_notify(request, user_id):
    """Send notification to a single user + view history."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("custom_admin:dashboard")

    from social.models import Notification

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()[:100]
        body = (request.POST.get("body") or "").strip()[:300]
        url = (request.POST.get("url") or "").strip()[:200]

        if not title:
            request.session["admin_message"] = {"type": "error", "text": "عنوان الزامی است."}
            return redirect("custom_admin:user_notify", user_id=u.id)

        # Find sender (first staff user)
        sender_user = User.objects.filter(is_staff=True).first()

        try:
            Notification.objects.create(
                user=u,
                type="admin_broadcast",
                title=title,
                body=body,
                url=url,
                sender=sender_user,
            )
            request.session["admin_message"] = {"type": "success", "text": f"اعلان به {u.alias or u.username} ارسال شد."}
        except Exception as e:
            request.session["admin_message"] = {"type": "error", "text": f"خطا: {str(e)[:100]}"}

        return redirect("custom_admin:user_notify", user_id=u.id)

    # Get history
    try:
        notifications = list(
            Notification.objects.filter(user=u)
            .select_related("sender")
            .order_by("-created_at")[:50]
        )
    except Exception:
        notifications = []

    message = request.session.pop("admin_message", None)

    return render(request, "custom_admin/user_notify.html", {
        "u": u,
        "notifications": notifications,
        "message": message,
        "total_count": Notification.objects.filter(user=u).count(),
    })


@never_cache
def user_notify_delete(request, user_id, notif_id):
    """Delete a single notification."""
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:user_notify", user_id=user_id)

    from social.models import Notification
    try:
        n = Notification.objects.get(id=notif_id, user_id=user_id)
        n.delete()
        request.session["admin_message"] = {"type": "success", "text": "اعلان حذف شد."}
    except Notification.DoesNotExist:
        request.session["admin_message"] = {"type": "error", "text": "اعلان پیدا نشد."}

    return redirect("custom_admin:user_notify", user_id=user_id)


@never_cache
def user_notify_clear(request, user_id):
    """Delete all notifications for a user."""
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:user_notify", user_id=user_id)

    from social.models import Notification
    n = Notification.objects.filter(user_id=user_id).delete()[0]
    request.session["admin_message"] = {"type": "success", "text": f"{n} اعلان حذف شد."}
    return redirect("custom_admin:user_notify", user_id=user_id)
'''
    write(p, src)
    print("  ✓ Views added")

# ============================================================
# 2) Add routes
# ============================================================
print("\n[2/5] Adding routes to admin_urls.py")
p = "accounts/admin_urls.py"
src = read(p)

if "user_notify" in src:
    print("  ✓ Routes already exist")
else:
    old = '    path("user/<int:user_id>/edit/", admin_views.user_edit, name="user_edit"),'
    new = old + '''
    path("user/<int:user_id>/notify/", admin_views.user_notify, name="user_notify"),
    path("user/<int:user_id>/notify/<int:notif_id>/delete/", admin_views.user_notify_delete, name="user_notify_delete"),
    path("user/<int:user_id>/notify/clear/", admin_views.user_notify_clear, name="user_notify_clear"),'''
    if old in src:
        src = src.replace(old, new, 1)
        write(p, src)
        print("  ✓ Routes added")
    else:
        print("  ⚠ user_edit route not found — adding before closing")
        src = src.rsplit("]", 1)[0] + '''    path("user/<int:user_id>/notify/", admin_views.user_notify, name="user_notify"),
    path("user/<int:user_id>/notify/<int:notif_id>/delete/", admin_views.user_notify_delete, name="user_notify_delete"),
    path("user/<int:user_id>/notify/clear/", admin_views.user_notify_clear, name="user_notify_clear"),
]'''
        write(p, src)
        print("  ✓ Routes added (fallback)")

# ============================================================
# 3) Create template
# ============================================================
print("\n[3/5] Creating user_notify.html template")

TEMPLATE = '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>اعلان به {{ u.username }} — پنل ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 1000px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(139,92,246,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
    .topbar h1 { font-size: 19px; color: #c4b5fd; }
    .topbar-actions { display: flex; gap: 8px; flex-wrap: wrap; }
    .topbar a { padding: 9px 16px; border-radius: 10px; font-size: 13px; font-weight: bold; text-decoration: none; }
    .topbar .back { background: rgba(148,163,184,0.2); color: #fff; }
    .topbar .view { background: rgba(139,92,246,0.2); color: #c4b5fd; border: 1px solid rgba(139,92,246,0.4); }
    .topbar .edit { background: rgba(59,130,246,0.2); color: #93c5fd; border: 1px solid rgba(59,130,246,0.4); }
    .topbar .logout { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; }

    .user-card { display: flex; align-items: center; gap: 16px; padding: 18px 22px; background: linear-gradient(135deg, #12121f, #1a1a2e); border: 1.5px solid rgba(139,92,246,0.3); border-radius: 18px; margin-bottom: 20px; }
    .user-av { width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #6b4eff); display: flex; align-items: center; justify-content: center; font-size: 30px; flex-shrink: 0; border: 2px solid rgba(255,255,255,0.15); }
    .user-info { flex: 1; }
    .user-name { font-size: 18px; font-weight: bold; color: #fff; margin-bottom: 4px; }
    .user-meta { font-size: 12px; color: #94a3b8; font-family: monospace; }
    .badge { display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 10px; font-weight: bold; margin-right: 6px; }
    .badge-guest { background: rgba(234,179,8,0.2); color: #fde68a; }
    .badge-staff { background: rgba(139,92,246,0.2); color: #c4b5fd; }
    .badge-active { background: rgba(34,197,94,0.2); color: #4ade80; }
    .badge-inactive { background: rgba(239,68,68,0.2); color: #fca5a5; }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .card { background: #12121f; border: 1px solid rgba(148,163,184,0.15); border-radius: 16px; padding: 22px; margin-bottom: 16px; }
    .card h3 { color: #fdba74; font-size: 15px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }

    label { display: block; color: #94a3b8; font-size: 12px; margin: 12px 0 6px; font-weight: bold; }
    input[type=text], textarea { width: 100%; padding: 12px 14px; border-radius: 10px; border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15; color: #fff; font-size: 14px; font-family: inherit; box-sizing: border-box; }
    textarea { resize: vertical; min-height: 90px; }
    input:focus, textarea:focus { outline: none; border-color: #facc15; }

    button.submit { width: 100%; margin-top: 16px; padding: 14px; border: none; border-radius: 12px; font-size: 15px; font-weight: bold; font-family: inherit; cursor: pointer; color: #fff; background: linear-gradient(135deg, #8b5cf6, #6b4eff); box-shadow: 0 8px 20px rgba(139,92,246,0.4); transition: 0.2s; }
    button.submit:hover { transform: translateY(-1px); }

    .notif-item { display: flex; gap: 12px; padding: 14px; background: rgba(15,23,42,0.5); border: 1px solid rgba(148,163,184,0.1); border-radius: 12px; margin-bottom: 8px; }
    .notif-icon { width: 42px; height: 42px; border-radius: 10px; background: rgba(245,158,11,0.2); display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
    .notif-body { flex: 1; min-width: 0; }
    .notif-title { font-size: 14px; font-weight: bold; color: #fff; margin-bottom: 4px; }
    .notif-desc { font-size: 12px; color: #cbd5e1; line-height: 1.5; margin-bottom: 4px; }
    .notif-meta { font-size: 10px; color: #64748b; font-family: monospace; }
    .notif-meta .read { color: #4ade80; font-weight: bold; }
    .notif-meta .unread { color: #facc15; font-weight: bold; }
    .btn-del-small { padding: 6px 10px; background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); border-radius: 8px; font-family: inherit; font-size: 11px; font-weight: bold; cursor: pointer; height: fit-content; }
    .btn-del-small:hover { background: rgba(239,68,68,0.3); }

    .clear-btn { padding: 10px 20px; background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); border-radius: 10px; font-family: inherit; font-size: 12px; font-weight: bold; cursor: pointer; }
    .clear-btn:hover { background: rgba(239,68,68,0.3); }

    .empty-state { text-align: center; padding: 40px 20px; color: #64748b; }
    .empty-state .icon { font-size: 60px; display: block; margin-bottom: 12px; opacity: 0.5; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>🔔 ارسال اعلان به کاربر</h1>
    <div class="topbar-actions">
      <a href="{% url 'custom_admin:user_detail' u.id %}" class="view">👁 مشاهده</a>
      <a href="{% url 'custom_admin:user_edit' u.id %}" class="edit">✏️ ویرایش</a>
      <a href="{% url 'custom_admin:dashboard' %}" class="back">← بازگشت</a>
      <a href="{% url 'custom_admin:logout' %}" class="logout">خروج</a>
    </div>
  </div>

  <div class="user-card">
    <div class="user-av">
      {% if u.avatar_id is not None %}{{ u.avatar_id }}{% else %}👤{% endif %}
    </div>
    <div class="user-info">
      <div class="user-name">
        {{ u.alias|default:u.username }}
        {% if u.is_guest %}<span class="badge badge-guest">مهمان</span>{% endif %}
        {% if u.is_staff %}<span class="badge badge-staff">ادمین</span>{% endif %}
        {% if u.is_active %}<span class="badge badge-active">فعال</span>{% else %}<span class="badge badge-inactive">غیرفعال</span>{% endif %}
      </div>
      <div class="user-meta">@{{ u.username }} · #{{ u.public_id }}</div>
    </div>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <div class="card">
    <h3>📤 ارسال اعلان جدید</h3>
    <form method="post">
      {% csrf_token %}
      <label>عنوان اعلان</label>
      <input type="text" name="title" maxlength="100" required placeholder="مثلاً: هدیه ویژه برای شما!">
      <label>متن اعلان</label>
      <textarea name="body" maxlength="300" placeholder="متن کامل اعلان که کاربر می‌بیند..."></textarea>
      <label>لینک (اختیاری)</label>
      <input type="text" name="url" maxlength="200" placeholder="مثلاً /accounts/shop/">
      <button type="submit" class="submit">📤 ارسال اعلان</button>
    </form>
  </div>

  <div class="card">
    <h3>
      📋 اعلان‌های {{ u.alias|default:u.username }} ({{ total_count }})
      {% if total_count > 0 %}
      <form method="post" action="{% url 'custom_admin:user_notify_clear' u.id %}" style="display:inline; margin-right:auto;" onsubmit="return confirm('همه اعلان‌های این کاربر حذف شوند؟');">
        {% csrf_token %}
        <button type="submit" class="clear-btn">🗑️ پاک کردن همه</button>
      </form>
      {% endif %}
    </h3>

    {% if notifications %}
      {% for n in notifications %}
        <div class="notif-item">
          <div class="notif-icon">
            {% if n.type == "admin_broadcast" %}📢
            {% elif n.type == "friend_request" %}👋
            {% elif n.type == "game_invite" %}🎮
            {% else %}🔔{% endif %}
          </div>
          <div class="notif-body">
            <div class="notif-title">{{ n.title }}</div>
            {% if n.body %}<div class="notif-desc">{{ n.body }}</div>{% endif %}
            <div class="notif-meta">
              {% if n.sender %}👤 {{ n.sender.alias }}{% else %}📢 مدیر{% endif %}
              · {{ n.created_at|jdate:"Y/m/d H:i" }}
              · {% if n.is_read %}<span class="read">✓ خوانده شد</span>{% else %}<span class="unread">● نخوانده</span>{% endif %}
              {% if n.url %} · 🔗 {{ n.url }}{% endif %}
            </div>
          </div>
          <form method="post" action="{% url 'custom_admin:user_notify_delete' u.id n.id %}" onsubmit="return confirm('حذف این اعلان؟');">
            {% csrf_token %}
            <button type="submit" class="btn-del-small">حذف</button>
          </form>
        </div>
      {% endfor %}
    {% else %}
      <div class="empty-state">
        <span class="icon">📭</span>
        هنوز اعلانی برای این کاربر ارسال نشده.
      </div>
    {% endif %}
  </div>
</div>
</body>
</html>
'''

write("accounts/templates/custom_admin/user_notify.html", TEMPLATE)

# ============================================================
# 4) Add link from user_detail + dashboard
# ============================================================
print("\n[4/5] Adding notification buttons to existing pages")

# Add link in user_detail.html
p = "accounts/templates/custom_admin/user_detail.html"
if os.path.exists(p):
    src = read(p)
    if "user_notify" not in src:
        old = '''  <h1>👤 جزئیات کاربر: {{ u.username }}</h1>'''
        if old in src:
            new = '''  <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
    <h1 style="margin: 14px 0 0;">👤 جزئیات کاربر: {{ u.username }}</h1>
    <div style="display:flex; gap:8px; margin-top:14px; flex-wrap:wrap;">
      <a href="{% url 'custom_admin:user_edit' u.id %}" style="padding: 10px 18px; border-radius: 10px; background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold;">✏️ ویرایش</a>
      <a href="{% url 'custom_admin:user_notify' u.id %}" style="padding: 10px 18px; border-radius: 10px; background: linear-gradient(135deg, #f59e0b, #d97706); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold;">🔔 ارسال اعلان</a>
    </div>
  </div>'''
            src = src.replace(old, new, 1)
            write(p, src)
            print("  ✓ Notify link added to user_detail.html")
        elif "user_edit" in src:
            # Fallback: add notify button next to edit
            old2 = '''<a href="{% url 'custom_admin:user_edit' u.id %}" style="margin-top: 14px; padding: 10px 18px; border-radius: 10px; background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold;">✏️ ویرایش کامل</a>'''
            if old2 in src:
                new2 = old2 + '''
      <a href="{% url 'custom_admin:user_notify' u.id %}" style="margin-top: 14px; padding: 10px 18px; border-radius: 10px; background: linear-gradient(135deg, #f59e0b, #d97706); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold;">🔔 ارسال اعلان</a>'''
                src = src.replace(old2, new2, 1)
                write(p, src)
                print("  ✓ Notify link added (fallback)")
    else:
        print("  ✓ user_detail already has notify link")

# Add button in dashboard rows
p = "accounts/templates/custom_admin/dashboard.html"
if os.path.exists(p):
    src = read(p)
    if "user_notify" not in src:
        old = '''                <a href="{% url 'custom_admin:user_edit' u.id %}"'''
        if old in src:
            # Find the closing </a> of the edit link
            idx = src.find(old)
            end = src.find("</a>", idx) + 4
            new_btn = '''
                <a href="{% url 'custom_admin:user_notify' u.id %}" style="background:rgba(245,158,11,0.2); color:#fde68a; padding:6px 10px; font-size:11px; border-radius:8px; text-decoration:none; font-weight:bold;">🔔</a>'''
            src = src[:end] + new_btn + src[end:]
            write(p, src)
            print("  ✓ Notify button added to dashboard rows")
    else:
        print("  ✓ dashboard already has notify button")

# Add to user_edit.html as well
p = "accounts/templates/custom_admin/user_edit.html"
if os.path.exists(p):
    src = read(p)
    if "user_notify" not in src:
        old = '''<a href="{% url 'custom_admin:user_detail' u.id %}" class="view">👁 مشاهده</a>'''
        if old in src:
            new = old + '''
      <a href="{% url 'custom_admin:user_notify' u.id %}" style="background: rgba(245,158,11,0.2); color: #fde68a; padding: 9px 16px; border-radius: 10px; font-size: 13px; font-weight: bold; text-decoration: none; border: 1px solid rgba(245,158,11,0.4);">🔔 اعلان</a>'''
            src = src.replace(old, new, 1)
            write(p, src)
            print("  ✓ Notify link added to user_edit.html")

# ============================================================
# 5) Test
# ============================================================
print("\n[5/5] Testing")

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from social.models import Notification
User = get_user_model()

# Create test user
tu, created = User.objects.get_or_create(
    username="__notify_test__",
    defaults={
        "alias": "notify-test",
        "is_active": True,
        "has_chosen_avatar": True,
        "has_completed_registration": True,
    }
)
if created:
    tu.set_password("x")
    tu.save()

c = Client()
c.session["custom_admin_logged_in"] = True
c.session.save()

# Test page loads
print(f"\n  Test: GET /panel-admin/user/{tu.id}/notify/")
r = c.get(f"/panel-admin/user/{tu.id}/notify/", follow=False)
print(f"    Status: {r.status_code}")
if r.status_code == 200:
    print(f"    ✓ Page loads")
elif r.status_code == 500:
    print(f"    ❌ {r.content.decode()[:300]}")

# Test sending notification
print(f"\n  Test: POST send notification")
before = Notification.objects.filter(user=tu).count()
r = c.post(f"/panel-admin/user/{tu.id}/notify/", {
    "title": "__TEST_NOTIFICATION__",
    "body": "This is a test",
    "url": "/game/",
}, follow=False)
after = Notification.objects.filter(user=tu).count()
print(f"    Status: {r.status_code}")
print(f"    Notifications: {before} → {after}")
if after > before:
    print(f"    ✓ Notification created")
    n = Notification.objects.filter(user=tu, title="__TEST_NOTIFICATION__").first()
    if n:
        print(f"      - Title: {n.title}")
        print(f"      - Body: {n.body}")
        print(f"      - Type: {n.type}")
        # Cleanup
        n.delete()
else:
    print(f"    ❌ Notification NOT created")

# Cleanup
if created:
    tu.delete()

# Django check
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("\n  ✓ Django check PASSED")
else:
    print(f"\n  ⚠ {r.stderr[:400]}")

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
What was added:

  🔔 Per-user notification system:
     - New page: /panel-admin/user/<id>/notify/
     - Send custom title + body + URL to any single user
     - View all notifications sent to that user (read/unread)
     - Delete individual notifications
     - Clear all notifications for a user

  🎯 Access points:
     1. Dashboard row → bell button 🔔
     2. User detail page → "🔔 ارسال اعلان" button
     3. User edit page → "🔔 اعلان" button

  📋 The notification appears in:
     - The user's notification page at /notifications/
     - With sender name "مدیر" (if no staff user exists)
     - Or the first staff user's alias as sender

How to use:
  1. Go /panel-admin/dashboard/
  2. Find any user → click 🔔
  3. Fill in title, body, URL
  4. Click "📤 ارسال اعلان"
  5. User sees it in their notifications

Admin panel tabs to visit:
  /panel-admin/            → dashboard
  /panel-admin/user/<id>/notify/  → send notification to user

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R
""")
