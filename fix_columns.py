#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove password/score/games from dashboard table. Show level + join date."""
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

print("\n" + "="*70)
print("REBUILDING DASHBOARD TABLE")
print("="*70)

# ============================================================
# Update admin_views.dashboard to add needed fields
# ============================================================
print("\n[1/4] Updating dashboard view — add level, join date, remove password")

p = "accounts/admin_views.py"
src = read(p)

# Find dashboard function and check what's in users_data
# We need: alias, username, avatar, level, date_joined, is_active, is_staff, is_guest

# Look for the dashboard function
dashboard_match = re.search(r'@never_cache\ndef dashboard\(request\):.*?(?=\n@never_cache|\Z)', src, re.DOTALL)
if dashboard_match:
    old_dashboard = dashboard_match.group(0)

    # Replace the users_data construction to include date_joined properly and skip password_algo
    new_dashboard = '''@never_cache
def dashboard(request):
    """داشبورد ادمین: لیست کاربران."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    User = get_user_model()
    from game.models import Player

    search = (request.GET.get("q") or "").strip()

    users_qs = User.objects.all().order_by("-date_joined")

    if search:
        from django.db.models import Q
        users_qs = users_qs.filter(
            Q(username__icontains=search) |
            Q(alias__icontains=search) |
            Q(public_id__icontains=search)
        )

    players_stats = (
        Player.objects
        .values("user_id")
        .annotate(total_score=Sum("score"), games=Count("id"))
    )
    stats_map = {s["user_id"]: s for s in players_stats}

    users_data = []
    for u in users_qs[:500]:
        st = stats_map.get(u.id, {})
        total = st.get("total_score", 0) or 0
        level = 1 + total // 100

        users_data.append({
            "id": u.id,
            "username": u.username,
            "alias": u.alias,
            "public_id": u.public_id,
            "avatar": u.avatar_id,
            "avatar_type": getattr(u, "avatar_type", "emoji"),
            "level": level,
            "total_score": total,
            "games": st.get("games", 0),
            "is_active": u.is_active,
            "is_staff": u.is_staff,
            "is_guest": getattr(u, "is_guest", False),
            "has_completed": u.has_completed_registration,
            "phone": u.phone or "—",
            "date_joined": u.date_joined,
            "last_login": u.last_login,
        })

    total_users = User.objects.count()
    total_players = Player.objects.count()
    total_scores = Player.objects.aggregate(t=Sum("score"))["t"] or 0

    return render(request, "custom_admin/dashboard.html", {
        "users": users_data,
        "search": search,
        "stats": {
            "total_users": total_users,
            "total_games": total_players,
            "total_scores": total_scores,
        },
    })
'''
    src = src.replace(old_dashboard, new_dashboard)
    write(p, src)
    print("  ✓ dashboard view updated (password_algo removed)")

# ============================================================
# Rebuild dashboard.html table
# ============================================================
print("\n[2/4] Rebuilding dashboard.html table")

DASHBOARD_HTML = '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>داشبورد ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 16px 16px 40px; }
    .container { max-width: 1400px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239, 68, 68, 0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; }
    .topbar h1 { font-size: 20px; color: #fca5a5; }
    .topbar .actions { display: flex; gap: 10px; }
    .topbar a, .topbar button { padding: 9px 16px; border-radius: 10px; font-size: 13px; font-family: inherit; text-decoration: none; cursor: pointer; border: none; font-weight: bold; }
    .btn-danger { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; }

    .admin-sticky-header {
      position: sticky; top: 0; z-index: 500;
      background: #0a0a15; padding: 4px 0 8px;
      margin-bottom: 20px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.7);
    }

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

    .search-row { display: flex; gap: 10px; margin-bottom: 16px; }
    .search-row input { flex: 1; padding: 13px 18px; border-radius: 12px; border: 1px solid rgba(148,163,184,0.2); background: #1a1a2e; color: #fff; font-size: 15px; font-family: inherit; }
    .search-row input:focus { outline: none; border-color: #facc15; }
    .search-row button { padding: 13px 22px; border-radius: 12px; border: none; background: linear-gradient(135deg, #facc15, #eab308); color: #1a1a1a; font-weight: bold; font-size: 14px; font-family: inherit; cursor: pointer; }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .table-wrap { background: #12121f; border: 1px solid rgba(148,163,184,0.12); border-radius: 16px; overflow: auto; }
    table { width: 100%; border-collapse: collapse; min-width: 1000px; }
    th { background: rgba(30,41,59,0.7); padding: 14px 12px; text-align: right; font-size: 12px; color: #94a3b8; font-weight: bold; white-space: nowrap; border-bottom: 1px solid rgba(148,163,184,0.15); position: sticky; top: 0; z-index: 2; }
    td { padding: 12px; text-align: right; font-size: 13px; border-bottom: 1px solid rgba(148,163,184,0.08); white-space: nowrap; }
    tr:hover td { background: rgba(244,197,66,0.04); }

    .username { font-family: monospace; font-weight: bold; color: #facc15; }
    .level-badge {
      background: linear-gradient(135deg, #8b5cf6, #6b4eff);
      color: #fff; padding: 3px 10px; border-radius: 8px;
      font-size: 12px; font-weight: bold; font-family: monospace;
    }
    .status { padding: 3px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; }
    .status.on { background: rgba(34,197,94,0.15); color: #4ade80; }
    .status.off { background: rgba(239,68,68,0.15); color: #f87171; }
    .status.staff { background: rgba(244,197,66,0.15); color: #facc15; }

    .avatar-mini {
      font-size: 20px; width: 34px; height: 34px;
      display: inline-flex; align-items: center; justify-content: center;
      background: rgba(51,65,85,0.5); border-radius: 50%;
    }

    .date-cell { font-size: 11px; color: #94a3b8; font-family: monospace; }

    .actions-cell { display: flex; gap: 6px; }
    .actions-cell a, .actions-cell button {
      padding: 6px 10px; font-size: 11px; border-radius: 8px;
      border: none; cursor: pointer; text-decoration: none;
      font-family: inherit; font-weight: bold;
    }
    .btn-view { background: rgba(6,182,212,0.2); color: #67e8f9; }
    .btn-edit { background: rgba(139,92,246,0.2); color: #c4b5fd; }
    .btn-toggle { background: rgba(234,179,8,0.2); color: #fde68a; }
    .btn-del { background: rgba(239,68,68,0.2); color: #fca5a5; }
  </style>
</head>
<body>
<div class="container">
  <div class="admin-sticky-header">
    <div class="topbar">
      <h1>🔒 پنل مدیریت کاربران</h1>
      <div class="actions">
        <a href="{% url 'custom_admin:logout' %}" class="btn-danger">خروج</a>
      </div>
    </div>

    <div class="admin-tabs">
      <a href="/panel-admin/dashboard/" class="admin-tab {% if '/panel-admin/dashboard/' in request.path or request.path == '/panel-admin/' %}active{% endif %}">👥 کاربران</a>
      <a href="/panel-admin/alliances/" class="admin-tab {% if '/panel-admin/alliance' in request.path %}active{% endif %}">🛡️ اتحادها</a>
      <a href="/panel-admin/rooms/" class="admin-tab {% if '/panel-admin/room' in request.path %}active{% endif %}">🚪 اتاق‌ها</a>
      <a href="/panel-admin/announcements/" class="admin-tab {% if '/panel-admin/announcement' in request.path %}active{% endif %}">📢 اعلان‌ها</a>
      <a href="/panel-admin/tournaments/" class="admin-tab {% if '/panel-admin/tournament' in request.path %}active{% endif %}">🏆 تورنمنت</a>
      <a href="/panel-admin/shop/" class="admin-tab {% if '/panel-admin/shop/' in request.path %}active{% endif %}">🛒 فروشگاه</a>
      <a href="/panel-admin/guest-log/" class="admin-tab {% if '/panel-admin/guest-log/' in request.path %}active{% endif %}">🎲 مهمان‌ها</a>
      <a href="/panel-admin/send-to-all/" class="admin-tab {% if '/panel-admin/send-to-all/' in request.path %}active{% endif %}">🎁 جایزه همه</a>
    </div>
  </div>

  {% if messages %}
    {% for m in messages %}
      <div class="msg msg-{{ m.tags }}">{{ m }}</div>
    {% endfor %}
  {% endif %}

  <form method="get" class="search-row">
    <input type="text" name="q" value="{{ search }}" placeholder="جستجو با نام کاربری، نام نمایشی یا شناسه...">
    <button type="submit">🔍 جستجو</button>
  </form>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>آواتار</th>
          <th>نام کاربری</th>
          <th>نام نمایشی</th>
          <th>لول</th>
          <th>موبایل</th>
          <th>وضعیت</th>
          <th>تاریخ عضویت</th>
          <th>آخرین ورود</th>
          <th>عملیات</th>
        </tr>
      </thead>
      <tbody>
        {% for u in users %}
          <tr>
            <td style="color:#64748b">{{ forloop.counter }}</td>
            <td><span class="avatar-mini">{{ u.avatar|default:"❓" }}</span></td>
            <td><span class="username">{{ u.username }}</span></td>
            <td>{{ u.alias }}</td>
            <td><span class="level-badge">Lv {{ u.level }}</span></td>
            <td style="font-family:monospace;font-size:12px">{{ u.phone }}</td>
            <td>
              {% if not u.is_active %}
                <span class="status off">غیرفعال</span>
              {% elif u.is_staff %}
                <span class="status staff">ادمین</span>
              {% else %}
                <span class="status on">فعال</span>
              {% endif %}
            </td>
            <td class="date-cell">{{ u.date_joined|jdate:"Y/m/d H:i" }}</td>
            <td class="date-cell">
              {% if u.last_login %}{{ u.last_login|jdate:"Y/m/d H:i" }}{% else %}—{% endif %}
            </td>
            <td>
              <div class="actions-cell">
                <a href="{% url 'custom_admin:user_detail' u.id %}" class="btn-view">مشاهده</a>
                <a href="{% url 'custom_admin:user_edit' u.id %}" class="btn-edit">✏️</a>
                <a href="{% url 'custom_admin:user_notify' u.id %}" class="btn-edit" style="background:rgba(245,158,11,0.2); color:#fde68a;">🔔</a>
                <form method="post" action="{% url 'custom_admin:user_toggle' u.id %}" style="display:inline">
                  {% csrf_token %}
                  <button type="submit" class="btn-toggle">
                    {% if u.is_active %}غیرفعال{% else %}فعال{% endif %}
                  </button>
                </form>
                <form method="post" action="{% url 'custom_admin:user_delete' u.id %}" style="display:inline"
                      onsubmit="return confirm('حذف {{ u.username }}؟');">
                  {% csrf_token %}
                  <button type="submit" class="btn-del">حذف</button>
                </form>
              </div>
            </td>
          </tr>
        {% empty %}
          <tr>
            <td colspan="10" style="text-align:center;color:#64748b;padding:40px">
              هیچ کاربری پیدا نشد.
            </td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
</body>
</html>
'''

write("accounts/templates/custom_admin/dashboard.html", DASHBOARD_HTML)
print("  ✓ dashboard.html rebuilt (no password, no score, no games)")

# ============================================================
# Remove password display from user_detail.html (keep reset form)
# ============================================================
print("\n[3/4] Removing password hash display from user_detail.html")

p = "accounts/templates/custom_admin/user_detail.html"
src = read(p)

# Remove "الگوریتم پسورد" row
src = re.sub(
    r'\s*<div class="row">\s*<span class="k">الگوریتم پسورد</span>.*?</div>',
    '',
    src,
    flags=re.DOTALL
)

# Also remove any mention of the "پسورد فعلی قابل مشاهده نیست" note — actually keep that, it's useful
# But remove the algo-tag CSS since we no longer show it
if 'algo-tag' in src:
    src = re.sub(r'\s*\.algo-tag\s*\{[^}]*\}', '', src)
    src = re.sub(r'\s*\.algo-tag\s*\{[^}]*\}', '', src)

# Also remove "رمز" column if it exists in any table
src = re.sub(r'\s*<th>رمز</th>', '', src)
src = re.sub(r'\s*<th>پسورد</th>', '', src)

write(p, src)
print("  ✓ user_detail.html — password hash display removed (reset form still works)")

# ============================================================
# Verify + test
# ============================================================
print("\n[4/4] Verification")
print("="*70)

r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:400]}")

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

tu, created = User.objects.get_or_create(
    username="__final_columns_test__",
    defaults={"alias": "test", "is_active": True, "is_staff": True, "has_chosen_avatar": True, "has_completed_registration": True}
)
if created:
    tu.set_password("x")
    tu.save()

c = Client()
c.session["custom_admin_logged_in"] = True
c.session["beta_unlocked"] = True
c.session.save()

print("\n  Testing dashboard:")
r = c.get("/panel-admin/dashboard/", follow=False)
print(f"    → {r.status_code}")

if r.status_code == 200:
    html = r.content.decode()
    checks = {
        "password hash (pbkdf2)": "pbkdf2" not in html,
        "algo-tag": "algo-tag" not in html,
        "column امتیاز (score)": "<th>امتیاز</th>" not in html,
        "column بازی": "<th>بازی</th>" not in html,
        "column لول (level)": "<th>لول</th>" in html,
        "column تاریخ عضویت": "<th>تاریخ عضویت</th>" in html,
        "column آخرین ورود": "<th>آخرین ورود</th>" in html,
    }
    print("\n  Content checks:")
    for name, ok in checks.items():
        print(f"    {'✓' if ok else '✗'} {name}")

# Test user detail — password hash removed but reset form exists
if created:
    r = c.get(f"/panel-admin/user/{tu.id}/", follow=False)
    print(f"\n  user_detail → {r.status_code}")
    if r.status_code == 200:
        html = r.content.decode()
        print(f"    {'✓' if 'الگوریتم پسورد' not in html else '✗'} password algorithm row removed")
        print(f"    {'✓' if 'new_password' in html else '✗'} reset password form still exists")

    # Test edit page still has password field
    r = c.get(f"/panel-admin/user/{tu.id}/edit/", follow=False)
    if r.status_code == 200:
        html = r.content.decode()
        print(f"    {'✓' if 'name=\"password\"' in html else '✗'} edit page has password input")
        print(f"    {'✓' if 'type=\"password\"' in html else '✗'} password field type")

    tu.delete()

print("\n" + "="*70)
print("DONE")
print("="*70)
print("""
What changed:

  dashboard.html table now shows:
    # | آواتار | نام کاربری | نام نمایشی | لول | موبایل | وضعیت | تاریخ عضویت | آخرین ورود | عملیات

  REMOVED:
    ✗ رمز (password hash)
    ✗ الگوریتم پسورد (algo-tag)
    ✗ ستون امتیاز (score)
    ✗ ستون بازی (games count)
    ✗ ستون شناسه (public_id)

  ADDED/KEPT:
    ✓ لول (level) — 1 + score//100
    ✓ تاریخ عضویت (join date) — Jalali
    ✓ آخرین ورود (last login) — Jalali
    ✓ دکمه 🔔 برای ارسال اعلان
    ✓ دکمه ✏️ برای ویرایش

  user_detail.html:
    ✗ رمز پاک شد از نمایش
    ✓ فرم تغییر پسورد هنوز کار می‌کند (در پایین صفحه)
    ✓ دکمه‌ها: مشاهده، ویرایش، ارسال اعلان، فعال/غیرفعال، حذف

  user_edit.html:
    ✓ فیلد password هنوز هست (برای تغییر)
    ✓ همه چیز سرجاش

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)

Test:
  1. /panel-admin/dashboard/ — جدول بدون رمز/امتیاز/بازی، با لول/تاریخ
  2. /panel-admin/user/<id>/ — بدون نمایش رمز، فرم ریست پسورد فعال
  3. /panel-admin/user/<id>/edit/ — فیلد رمز برای تغییر
""")
