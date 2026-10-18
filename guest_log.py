#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Delete guest on logout + log in admin panel."""
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
# 1) Add GuestDeletionLog model
# ============================================================
print("\n[1/5] Adding GuestDeletionLog model to accounts/models.py")
p = "accounts/models.py"
src = read(p)

if "class GuestDeletionLog(models.Model):" in src:
    print("  ✓ Already exists")
else:
    src = src.rstrip() + '''

class GuestDeletionLog(models.Model):
    """Log of deleted guest accounts (kept after guest is removed)."""
    username = models.CharField(max_length=32)
    alias = models.CharField(max_length=32, blank=True)
    public_id = models.PositiveBigIntegerField(null=True, blank=True)
    avatar_id = models.PositiveSmallIntegerField(null=True, blank=True)
    total_games = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)  # when guest was created
    deleted_at = models.DateTimeField(auto_now_add=True)  # when deleted

    class Meta:
        ordering = ("-deleted_at",)

    def __str__(self):
        return f"Guest {self.username} deleted at {self.deleted_at}"
'''
    write(p, src)
    print("  ✓ GuestDeletionLog added")

# ============================================================
# 2) Update logout_view to delete guest + log
# ============================================================
print("\n[2/5] Updating logout_view")

p = "accounts/views.py"
src = read(p)

# Find old logout_view
old_logout_patterns = [
    '''def logout_view(request):
    logout(request)
    return redirect("landing")''',
    '''def logout_view(request):
    logout(request)
    return redirect("landing")
''',
]

new_logout = '''def logout_view(request):
    if request.user.is_authenticated and request.user.is_guest:
        # Log the deletion BEFORE deleting the user
        from .models import GuestDeletionLog
        from game.models import Player

        try:
            u = request.user
            total_games = Player.objects.filter(user=u).count()
            total_score = sum(p.score for p in Player.objects.filter(user=u))

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
            print(f"Failed to log guest deletion: {e}")

        # Now logout
        logout(request)

        # Then delete the guest user (cascade deletes Player, etc.)
        try:
            User = get_user_model()
            User.objects.filter(id=u.id).delete()
        except Exception as e:
            print(f"Failed to delete guest user: {e}")

        return redirect("landing")

    logout(request)
    return redirect("landing")'''

replaced = False
for old in old_logout_patterns:
    if old in src:
        src = src.replace(old, new_logout, 1)
        replaced = True
        print("  ✓ logout_view updated")
        break

if not replaced:
    # Try regex
    import re
    pattern = re.compile(r'def logout_view\(request\):\s*\n\s*logout\(request\)\s*\n\s*return redirect\("landing"\)', re.MULTILINE)
    m = pattern.search(src)
    if m:
        src = src[:m.start()] + new_logout + src[m.end():]
        replaced = True
        print("  ✓ logout_view updated (regex)")
    else:
        print("  ⚠ Could not find logout_view - checking current version")

if replaced:
    write(p, src)

# ============================================================
# 3) Add admin view for guest log
# ============================================================
print("\n[3/5] Adding admin view for guest deletion log")

p = "accounts/admin_views.py"
src = read(p)

if "def guest_log_list" in src:
    print("  ✓ Already exists")
else:
    src = src.rstrip() + '''

# ============================================================
# Admin — Guest Deletion Log
# ============================================================
@never_cache
def guest_log_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")

    from accounts.models import GuestDeletionLog

    search = (request.GET.get("q") or "").strip()
    qs = GuestDeletionLog.objects.all().order_by("-deleted_at")

    if search:
        from django.db.models import Q
        qs = qs.filter(Q(username__icontains=search) | Q(alias__icontains=search))

    data = []
    for log in qs[:200]:
        data.append({
            "id": log.id,
            "username": log.username,
            "alias": log.alias,
            "public_id": log.public_id,
            "avatar_id": log.avatar_id,
            "total_games": log.total_games,
            "total_score": log.total_score,
            "joined_at": log.joined_at,
            "deleted_at": log.deleted_at,
        })

    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/guest_log.html", {
        "logs": data,
        "search": search,
        "message": message,
        "total_count": GuestDeletionLog.objects.count(),
    })


@never_cache
def guest_log_clear(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:guest_log_list")

    from accounts.models import GuestDeletionLog
    n = GuestDeletionLog.objects.all().delete()[0]
    request.session["admin_message"] = {"type": "success", "text": f"{n} رکورد حذف شد."}
    return redirect("custom_admin:guest_log_list")
'''
    write(p, src)
    print("  ✓ guest_log_list + guest_log_clear added")

# ============================================================
# 4) Add routes
# ============================================================
print("\n[4/5] Adding routes to admin_urls.py")

p = "accounts/admin_urls.py"
src = read(p)

if "guest_log_list" not in src:
    # Add before closing ]
    old = '    path("shop/<int:item_id>/delete/", admin_views.shop_item_delete, name="shop_item_delete"),'
    new = old + '''
    path("guest-log/", admin_views.guest_log_list, name="guest_log_list"),
    path("guest-log/clear/", admin_views.guest_log_clear, name="guest_log_clear"),'''

    if old in src:
        src = src.replace(old, new, 1)
        write(p, src)
        print("  ✓ Routes added")
    else:
        # Fallback
        src = src.rsplit("]", 1)[0] + '''    path("guest-log/", admin_views.guest_log_list, name="guest_log_list"),
    path("guest-log/clear/", admin_views.guest_log_clear, name="guest_log_clear"),
]'''
        write(p, src)
        print("  ✓ Routes added (fallback)")
else:
    print("  ✓ Routes already exist")

# ============================================================
# 5) Create template + add to dashboard
# ============================================================
print("\n[5/5] Creating guest_log.html template")

GUEST_LOG_TEMPLATE = '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>لاگ مهمان‌های حذف‌شده — پنل ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 1300px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
    .topbar h1 { font-size: 20px; color: #fca5a5; }
    .topbar-actions { display: flex; gap: 8px; }
    .topbar a { padding: 9px 16px; border-radius: 10px; text-decoration: none; font-size: 13px; font-weight: bold; color: #fff; }
    .btn-logout { background: linear-gradient(135deg, #ef4444, #dc2626); }
    .btn-clear { background: rgba(239,68,68,0.2); border: 1px solid rgba(239,68,68,0.4); }

    .admin-tabs { display: flex; gap: 6px; margin-bottom: 20px; background: #12121f; border: 1px solid rgba(148,163,184,0.15); padding: 6px; border-radius: 14px; overflow-x: auto; }
    .admin-tab { flex: 1; min-width: 90px; padding: 12px 14px; border-radius: 10px; text-align: center; text-decoration: none; font-size: 12px; font-weight: bold; color: #94a3b8; transition: 0.2s; white-space: nowrap; }
    .admin-tab:hover { background: rgba(148,163,184,0.1); color: #fff; }
    .admin-tab.active { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; box-shadow: 0 6px 20px rgba(239,68,68,0.4); }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .stats-mini { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
    .stat-mini { padding: 10px 16px; border-radius: 10px; background: rgba(30,41,59,0.6); border: 1px solid rgba(148,163,184,0.15); font-size: 12px; }
    .stat-mini b { color: #facc15; font-family: monospace; }

    .search-row { display: flex; gap: 10px; margin-bottom: 16px; }
    .search-row input { flex: 1; padding: 13px 18px; border-radius: 12px; border: 1px solid rgba(148,163,184,0.2); background: #1a1a2e; color: #fff; font-size: 15px; font-family: inherit; }
    .search-row input:focus { outline: none; border-color: #facc15; }
    .search-row button { padding: 13px 22px; border-radius: 12px; border: none; background: linear-gradient(135deg, #facc15, #eab308); color: #1a1a1a; font-weight: bold; font-size: 14px; font-family: inherit; cursor: pointer; }

    .table-wrap { background: #12121f; border: 1px solid rgba(148,163,184,0.12); border-radius: 16px; overflow: auto; }
    table { width: 100%; border-collapse: collapse; min-width: 900px; }
    th { background: rgba(30,41,59,0.7); padding: 14px 12px; text-align: right; font-size: 12px; color: #94a3b8; font-weight: bold; white-space: nowrap; border-bottom: 1px solid rgba(148,163,184,0.15); position: sticky; top: 0; }
    td { padding: 12px; text-align: right; font-size: 13px; border-bottom: 1px solid rgba(148,163,184,0.08); white-space: nowrap; }
    tr:hover td { background: rgba(244,197,66,0.03); }

    .username { font-family: monospace; font-weight: bold; color: #fca5a5; }
    .pid { font-family: monospace; color: #94a3b8; font-size: 11px; }
    .score { font-family: monospace; color: #facc15; font-weight: bold; }
    .date { font-size: 11px; color: #64748b; }

    .empty-state { text-align: center; padding: 60px 20px; color: #64748b; }
    .empty-state .icon { font-size: 60px; display: block; margin-bottom: 12px; opacity: 0.5; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>🎲 لاگ مهمان‌های حذف‌شده</h1>
    <div class="topbar-actions">
      {% if total_count > 0 %}
      <form method="post" action="{% url 'custom_admin:guest_log_clear' %}" onsubmit="return confirm('همه لاگ‌ها حذف شوند؟');" style="display:inline;">
        {% csrf_token %}
        <button type="submit" class="btn-clear" style="border:none; cursor:pointer; font-family:inherit; padding:9px 16px; border-radius:10px; color:#fca5a5; font-size:13px; font-weight:bold;">🗑️ پاک کردن همه</button>
      </form>
      {% endif %}
      <a href="{% url 'custom_admin:logout' %}" class="btn-logout">خروج</a>
    </div>
  </div>

  <div class="admin-tabs">
    <a href="/panel-admin/dashboard/" class="admin-tab">👥 کاربران</a>
    <a href="/panel-admin/alliances/" class="admin-tab">🛡️ اتحادها</a>
    <a href="/panel-admin/rooms/" class="admin-tab">🚪 اتاق‌ها</a>
    <a href="/panel-admin/announcements/" class="admin-tab">📢 اعلان‌ها</a>
    <a href="/panel-admin/tournaments/" class="admin-tab">🏆 تورنمنت‌ها</a>
    <a href="/panel-admin/shop/" class="admin-tab">🛒 فروشگاه</a>
    <a href="/panel-admin/guest-log/" class="admin-tab active">🎲 مهمان‌ها</a>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <div class="stats-mini">
    <div class="stat-mini">کل مهمان‌های حذف‌شده: <b>{{ total_count }}</b></div>
  </div>

  <form method="get" class="search-row">
    <input type="text" name="q" value="{{ search }}" placeholder="جستجو با username یا alias...">
    <button type="submit">🔍 جستجو</button>
  </form>

  {% if logs %}
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>👤 آواتار</th>
            <th>Username</th>
            <th>Alias</th>
            <th>شناسه</th>
            <th>🎮 بازی‌ها</th>
            <th>⭐ امتیاز</th>
            <th>📅 عضویت</th>
            <th>🗑️ حذف</th>
          </tr>
        </thead>
        <tbody>
          {% for log in logs %}
            <tr>
              <td style="color:#64748b;">{{ forloop.counter }}</td>
              <td>
                {% if log.avatar_id is not None %}
                  <span style="display:inline-block; width:32px; height:32px; border-radius:50%; background:linear-gradient(135deg,#8b5cf6,#6b4eff); color:#fff; line-height:32px; text-align:center; font-family:monospace; font-size:11px; font-weight:bold;">{{ log.avatar_id }}</span>
                {% else %}
                  <span style="opacity:0.4;">—</span>
                {% endif %}
              </td>
              <td><span class="username">{{ log.username }}</span></td>
              <td>{{ log.alias|default:"—" }}</td>
              <td><span class="pid">#{{ log.public_id|default:"—" }}</span></td>
              <td>{{ log.total_games }}</td>
              <td><span class="score">{{ log.total_score }}</span></td>
              <td><span class="date">{{ log.joined_at|date:"Y/m/d H:i" }}</span></td>
              <td><span class="date">{{ log.deleted_at|date:"Y/m/d H:i" }}</span></td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  {% else %}
    <div class="empty-state">
      <span class="icon">🎲</span>
      {% if search %}نتیجه‌ای پیدا نشد.{% else %}هنوز هیچ مهمانی حذف نشده.{% endif %}
    </div>
  {% endif %}
</div>
</body>
</html>
'''

write("accounts/templates/custom_admin/guest_log.html", GUEST_LOG_TEMPLATE)

# Add "مهمان‌ها" tab to dashboard.html
print("\n  Adding tab to dashboard.html...")
p = "accounts/templates/custom_admin/dashboard.html"
src = read(p)

if "/panel-admin/guest-log/" not in src:
    old = '<a href="/panel-admin/shop/" class="admin-tab'
    if old in src:
        # Find the closing of this tag
        idx = src.find(old)
        end = src.find("</a>", idx) + 4
        new_tab = '\n    <a href="/panel-admin/guest-log/" class="admin-tab">🎲 مهمان‌ها</a>'
        src = src[:end] + new_tab + src[end:]
        write(p, src)
        print("  ✓ Tab added to dashboard")
    else:
        # Add before last </div>
        idx = src.rfind("</div>")
        if idx > 0:
            new_tab = '\n    <a href="/panel-admin/guest-log/" class="admin-tab">🎲 مهمان‌ها</a>\n'
            src = src[:idx] + new_tab + src[idx:]
            write(p, src)
            print("  ✓ Tab added (fallback)")

# Also add tab to other admin pages
for tpl_name in ["alliances.html", "rooms.html", "announcements.html", "tournaments.html", "shop_items.html"]:
    tpl_path = f"accounts/templates/custom_admin/{tpl_name}"
    if not os.path.exists(tpl_path):
        continue
    src = read(tpl_path)
    if "/panel-admin/guest-log/" in src:
        continue
    old = '<a href="/panel-admin/shop/" class="admin-tab'
    if old in src:
        idx = src.find(old)
        end = src.find("</a>", idx) + 4
        new_tab = '\n    <a href="/panel-admin/guest-log/" class="admin-tab">🎲 مهمان‌ها</a>'
        src = src[:end] + new_tab + src[end:]
        write(tpl_path, src)
        print(f"  ✓ Tab added to {tpl_name}")

# ============================================================
# Migrations
# ============================================================
print("\n[Migrations] Running...")
for cmd in [
    [sys.executable, "manage.py", "makemigrations", "accounts", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd[1:])}")
    if r.returncode != 0 and r.stderr.strip():
        print(f"    ⚠ {r.stderr[:300]}")

# ============================================================
# TEST
# ============================================================
print("\n[TEST] Testing guest deletion flow")

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from accounts.models import GuestDeletionLog
User = get_user_model()

# Get count before
before_count = User.objects.filter(is_guest=True).count()
before_log = GuestDeletionLog.objects.count()

# Create test guest
test_guest = User.objects.create_user(
    username="__test_guest_del__", password="x"*10,
    alias="guest-test", is_active=True,
    has_chosen_avatar=True, has_completed_registration=True,
    is_guest=True,
)
print(f"  Created guest: {test_guest.username}")

# Login + logout
c = Client()
c.force_login(test_guest)
c.session["beta_unlocked"] = True
c.session.save()

r = c.get("/accounts/logout/", follow=False)
print(f"  GET /accounts/logout/ → {r.status_code}")

# Check guest was deleted
still_exists = User.objects.filter(username="__test_guest_del__").exists()
print(f"  Guest still exists in DB: {still_exists} ({'✗ BAD' if still_exists else '✓ DELETED'})")

# Check log was created
after_log = GuestDeletionLog.objects.count()
print(f"  Log count: {before_log} → {after_log} ({'✓ LOGGED' if after_log > before_log else '✗ NOT LOGGED'})")

# Check log details
log = GuestDeletionLog.objects.filter(username="__test_guest_del__").first()
if log:
    print(f"  ✓ Log entry: username={log.username}, alias={log.alias}")
    log.delete()  # cleanup

# Test non-guest logout (should NOT delete)
regular_user, created = User.objects.get_or_create(
    username="__test_regular__",
    defaults={"alias": "regular", "is_active": True, "has_chosen_avatar": True, "has_completed_registration": True, "is_guest": False}
)
if created:
    regular_user.set_password("x")
    regular_user.save()

c2 = Client()
c2.force_login(regular_user)
c2.session["beta_unlocked"] = True
c2.session.save()
c2.get("/accounts/logout/", follow=False)

still_exists = User.objects.filter(username="__test_regular__").exists()
print(f"  Regular user still exists after logout: {still_exists} ({'✓ KEPT' if still_exists else '✗ DELETED - BAD'})")

if created:
    regular_user.delete()

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
What changed:
  ✓ GuestDeletionLog model — stores deleted guests
  ✓ logout_view: if user.is_guest, logs then deletes user
  ✓ /panel-admin/guest-log/ — admin list of deleted guests
  ✓ 🎲 مهمان‌ها tab in admin panel

How it works:
  1. User logs in as guest
  2. User clicks "خروج" (logout)
  3. GuestDeletionLog created (username, alias, games, score)
  4. Guest account DELETED from DB
  5. Regular users logout normally (no deletion)

Admin panel:
  - New tab: 🎲 مهمان‌ها
  - Shows all deleted guests with:
    - Username, Alias, Public ID
    - Games played, Total score
    - Join date, Deletion date
  - Search by username or alias
  - Clear all logs button

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R
""")
