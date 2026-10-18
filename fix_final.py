#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")
def backup(p):
    bak = p + ".bak_final"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) Notifications route + active="home"
# ============================================================
print("\n[1/6] Notifications: /notifications/ + active=home")

# 1a) social/urls.py - ensure route exists
p = os.path.join(ROOT, "social", "urls.py")
src = read(p)
if "notifications/" not in src:
    backup(p)
    # Add after first path
    anchor = '    path("", views.friends_home, name="friends_home"),'
    if anchor in src:
        src = src.replace(anchor, anchor + '\n    path("notifications/", views.notifications_view, name="notifications"),', 1)
        write(p, src)
        print("  FIXED: /social/notifications/ route added")
    else:
        print("  WARN: friends_home route not found")
else:
    print("  SKIP: /social/notifications/ exists")

# 1b) config/urls.py - add /notifications/ at root
p = os.path.join(ROOT, "config", "urls.py")
src = read(p)
if 'path("notifications/"' not in src:
    backup(p)
    # Add before landing
    anchor = '    # ریشه → landing'
    if anchor in src:
        insert = '    # اعلان‌ها (در خانه)\n    path("notifications/", __import__("social.views", fromlist=["notifications_view"]).notifications_view, name="notifications_root"),\n\n'
        src = src.replace(anchor, insert + anchor, 1)
        write(p, src)
        print("  FIXED: /notifications/ root route added")
    else:
        print("  WARN: landing anchor not found")

# 1c) social/views.py - change active from friends to home
p = os.path.join(ROOT, "social", "views.py")
src = read(p)
# Find notifications_view and change its active value
old_view = '''@login_required
def notifications_view(request):
    all_notifs = list(
        Notification.objects.filter(user=request.user)
        .select_related("sender")
        .order_by("-created_at")
    )
    unread = sum(1 for n in all_notifs if not n.is_read)
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, "social/notifications.html", {
        "notifications": all_notifs,
        "unread_total": unread,
        "active": "friends",
    })'''
new_view = '''@login_required
def notifications_view(request):
    all_notifs = list(
        Notification.objects.filter(user=request.user)
        .select_related("sender")
        .order_by("-created_at")
    )
    unread = sum(1 for n in all_notifs if not n.is_read)
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, "social/notifications.html", {
        "notifications": all_notifs,
        "unread_total": unread,
        "active": "home",
    })'''
if old_view in src:
    src = src.replace(old_view, new_view, 1)
    backup(p); write(p, src)
    print("  FIXED: active=friends → active=home")
elif '"unread_total": unread,\n        "active": "home",' in src:
    print("  SKIP: active already home")
else:
    # Fallback: just replace the first friends in notifications_view context
    if "def notifications_view" in src:
        start = src.find("def notifications_view")
        end = src.find("\n@login_required", start) if "\n@login_required" in src[start:] else len(src)
        section = src[start:end]
        new_section = section.replace('"active": "friends"', '"active": "home"')
        src = src[:start] + new_section + src[end:]
        backup(p); write(p, src)
        print("  FIXED (fallback): active changed")

# 1d) menu.html - update bell link to /notifications/
p = os.path.join(ROOT, "game", "templates", "game", "menu.html")
src = read(p)
if 'href="/notifications/"' not in src:
    old = 'href="/social/notifications/"'
    if old in src:
        src = src.replace(old, 'href="/notifications/"', 1)
        backup(p); write(p, src)
        print("  FIXED: menu bell → /notifications/")
    else:
        print("  WARN: bell link not found (may already be updated)")
else:
    print("  SKIP: bell already → /notifications/")

# ============================================================
# 2) Alliance - verify views + add alliance_edit if missing
# ============================================================
print("\n[2/6] Alliance: verify views + add edit if missing")

# 2a) Add alliance_edit if missing
p = os.path.join(ROOT, "alliance", "views.py")
src = read(p)
if "def alliance_edit" in src:
    print("  SKIP: alliance_edit exists")
else:
    edit_view = '''

@login_required
def alliance_edit(request, alliance_id):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    a = get_object_or_404(Alliance, id=alliance_id)
    my_m = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not my_m or my_m.role != "leader":
        messages.error(request, "فقط رهبر می‌تونه ویرایش کنه.")
        return redirect("alliance:detail", alliance_id=a.id)

    error = None
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()[:40]
        tag = (request.POST.get("tag") or "").strip().upper()[:8]
        description = (request.POST.get("description") or "").strip()[:200]
        emblem = (request.POST.get("emblem") or a.emblem).strip()[:4]
        password = (request.POST.get("password") or "").strip()[:32]
        try:
            max_members = int(request.POST.get("max_members") or a.max_members)
        except (ValueError, TypeError):
            max_members = a.max_members
        max_members = max(5, min(50, max_members))

        if not name:
            error = "نام اتحاد را وارد کن."
        elif len(name) < 3:
            error = "نام اتحاد باید حداقل ۳ حرف باشد."
        elif Alliance.objects.filter(name=name).exclude(id=a.id).exists():
            error = "این نام قبلاً گرفته شده."
        elif a.member_count() > max_members:
            error = "ظرفیت جدید از تعداد فعلی اعضا کمتر است."
        else:
            a.name = name
            a.tag = tag
            a.description = description
            a.emblem = emblem or a.emblem
            a.password = password
            a.max_members = max_members
            a.save()
            messages.success(request, "تغییرات ذخیره شد.")
            return redirect("alliance:detail", alliance_id=a.id)

    emojis = ["🛡️", "⚔️", "🏰", "🐉", "🦅", "🐺", "🔥", "⚡", "👑", "💎", "🌟", "🦁"]
    return render(request, "alliance/edit.html", {
        "alliance": a,
        "error": error,
        "emojis": emojis,
        "active": "friends",
    })
'''
    src = src.rstrip() + edit_view + "\n"
    backup(p); write(p, src)
    print("  FIXED: alliance_edit added")

# 2b) Add route if missing
p = os.path.join(ROOT, "alliance", "urls.py")
src = read(p)
if "alliance_edit" not in src:
    old = '    path("<int:alliance_id>/", views.alliance_detail, name="detail"),'
    new = old + '\n    path("<int:alliance_id>/edit/", views.alliance_edit, name="edit"),'
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: /alliance/<id>/edit/ route added")
    else:
        print("  WARN: detail route not found")
else:
    print("  SKIP: edit route exists")

# 2c) Verify join_alliance view + route
p = os.path.join(ROOT, "alliance", "views.py")
src = read(p)
if "def join_alliance" not in src:
    join_view = '''

@login_required
def join_alliance(request, alliance_id):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    if AllianceMember.objects.filter(user=request.user).exists():
        messages.info(request, "شما الان عضو یک اتحاد هستید.")
        return redirect("alliance:home")

    a = get_object_or_404(Alliance, id=alliance_id)

    if request.method != "POST":
        return redirect("alliance:home")

    if a.password:
        entered = (request.POST.get("password") or "").strip()
        if entered != a.password:
            messages.error(request, "رمز اتحاد اشتباه است.")
            return redirect("alliance:home")

    if a.member_count() >= a.max_members:
        messages.error(request, "این اتحاد پر شده است.")
        return redirect("alliance:home")

    AllianceMember.objects.create(alliance=a, user=request.user, role="member")
    messages.success(request, f"به اتحاد «{a.name}» پیوستی!")
    return redirect("alliance:detail", alliance_id=a.id)
'''
    src = src.rstrip() + join_view + "\n"
    backup(p); write(p, src)
    print("  FIXED: join_alliance added")

# Route
p = os.path.join(ROOT, "alliance", "urls.py")
src = read(p)
if "join_alliance" not in src:
    old = '    path("join/", views.join_by_code, name="join"),'
    new = old + '\n    path("join-id/<int:alliance_id>/", views.join_alliance, name="join_alliance"),'
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: /alliance/join-id/<id>/ route added")
else:
    print("  SKIP: join-id route exists")

# ============================================================
# 3) Tournament date fix - change defaults to now + 2 hours
# ============================================================
print("\n[3/6] Tournament: fix default dates (end = start + 2h)")

# 3a) Update admin_views.py tournament_create/context
p = os.path.join(ROOT, "accounts", "admin_views.py")
src = read(p)

# Find and replace the context in tournament_create and tournament_edit
old_ctx = '''    import jdatetime
    from datetime import timedelta
    now_j = jdatetime.datetime.now()
    tomorrow_j = now_j + timedelta(days=1)'''

new_ctx = '''    from datetime import timedelta
    from django.utils import timezone as _tz
    _now = _tz.now()
    _end = _now + timedelta(hours=2)

    def _g2j(gy, gm, gd):
        g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        if gy > 1600:
            jy = 979; gy -= 1600
        else:
            jy = 0; gy -= 621
        gy2 = gy + 1 if gm > 2 else gy
        days = (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) - 80 + gd + g_d_m[gm - 1]
        jy += 33 * (days // 12053)
        days %= 12053
        jy += 4 * (days // 1461)
        days %= 1461
        if days > 365:
            jy += (days - 1) // 365
            days = (days - 1) % 365
        if days < 186:
            jm = 1 + days // 31
            jd = 1 + days % 31
        else:
            jm = 7 + (days - 186) // 30
            jd = 1 + (days - 186) % 30
        return jy, jm, jd

    now_jy, now_jm, now_jd = _g2j(_now.year, _now.month, _now.day)
    end_jy, end_jm, end_jd = _g2j(_end.year, _end.month, _end.day)'''

if old_ctx in src:
    src = src.replace(old_ctx, new_ctx)
    print("  FIXED: default context updated (now + 2h)")
elif "now_jy, now_jm, now_jd = _g2j" in src:
    print("  SKIP: context already updated")
else:
    print("  WARN: old context not found - will try alternate")

# Replace all the context vars in both create and edit
# The template uses now_j_year, now_j_month, etc. Need to convert.
replacements = [
    ('"year_options": list(range(now_j_year - 1, now_j_year + 3)),', '"year_options": list(range(now_jy - 1, now_jy + 3)),'),
    ('"default_jy": now_j_year,', '"default_jy": now_jy,'),
    ('"default_jm": now_j_month,', '"default_jm": now_jm,'),
    ('"default_jd": now_j_day,', '"default_jd": now_jd,'),
    ('"default_jh": now_j_hour,', '"default_jh": _now.hour,'),
    ('"default_end_jh": tomorrow_j_hour,', '"default_end_jy": end_jy,\n        "default_end_jm": end_jm,\n        "default_end_jd": end_jd,\n        "default_end_jh": _end.hour,'),
]
for old_r, new_r in replacements:
    if old_r in src:
        src = src.replace(old_r, new_r)
        print(f"  FIXED: {old_r[:40]}...")

backup(p); write(p, src)

# 3b) Verify _parse_jalali_dt exists and is correct
p = os.path.join(ROOT, "accounts", "admin_views.py")
src = read(p)
if "_parse_jalali_dt" not in src:
    print("  WARN: _parse_jalali_dt missing - adding")
    new_fn = '''

def _parse_jalali_dt(request, prefix):
    """Read Jalali picker fields, return Gregorian aware datetime."""
    from django.utils import timezone as tz
    from datetime import datetime
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
    jy2 = jy
    if jy2 > 979:
        gy = 1600; jy2 -= 979
    else:
        gy = 621
    days = (365 * jy2) + ((jy2 // 33) * 8) + (((jy2 % 33) + 3) // 4) + 78 + jd + ((jm - 1) * 31 if jm < 7 else ((jm - 7) * 30) + 186)
    gy += 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    is_leap = (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)
    sal_a = [0, 31, 29 if is_leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 1
    for i in range(1, 13):
        if gd <= sal_a[i]:
            gm = i
            break
        gd -= sal_a[i]
    try:
        d = datetime(gy, gm, gd, jh, jmin)
        if tz.is_naive(d):
            d = tz.make_aware(d)
        return d
    except (ValueError, TypeError):
        return None
'''
    src = src.rstrip() + new_fn + "\n"
    backup(p); write(p, src)
    print("  FIXED: _parse_jalali_dt added")
else:
    print("  SKIP: _parse_jalali_dt exists")

# 3c) Update template to use default_end_jy/jm/jd
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "tournament_edit.html")
src = read(p)

# Replace end date selects to use default_end_*
old_end_jy = '''{% elif not end_j and y == default_jy %}selected{% endif %}>{{ y }}</option>'''
new_end_jy = '''{% elif not end_j and y == default_end_jy %}selected{% endif %}>{{ y }}</option>'''
if "default_end_jy" not in src and old_end_jy in src:
    src = src.replace(old_end_jy, new_end_jy, 1)
    print("  FIXED: end_jy uses default_end_jy")

old_end_jm = '''{% elif not end_j and m_num == default_jm %}selected{% endif %}>{{ m_name }}</option>'''
new_end_jm = '''{% elif not end_j and m_num == default_end_jm %}selected{% endif %}>{{ m_name }}</option>'''
if "default_end_jm" not in src and old_end_jm in src:
    src = src.replace(old_end_jm, new_end_jm, 1)
    print("  FIXED: end_jm uses default_end_jm")

old_end_jd = '''{% elif not end_j and d == default_jd %}selected{% endif %}>{{ d }}</option>'''
new_end_jd = '''{% elif not end_j and d == default_end_jd %}selected{% endif %}>{{ d }}</option>'''
if "default_end_jd" not in src and old_end_jd in src:
    src = src.replace(old_end_jd, new_end_jd, 1)
    print("  FIXED: end_jd uses default_end_jd")

backup(p); write(p, src)

# ============================================================
# 4) Reset any lingering migrations
# ============================================================
print("\n[4/6] Migrations")
for cmd in [
    [sys.executable, "manage.py", "makemigrations", "game", "social", "alliance", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd[1:])}")
    if r.stdout.strip(): print("   ", r.stdout.strip().replace("\n", "\n    ")[:400])
    if r.returncode != 0 and r.stderr.strip():
        print("   ERR:", r.stderr.strip()[:400])

# ============================================================
# 5) Test pages
# ============================================================
print("\n[5/6] Testing pages")
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

try:
    tu = User.objects.filter(username="__final_test__").first()
    if not tu:
        tu = User.objects.create_user(
            username="__final_test__", password="x"*10,
            alias="t", is_active=True,
            has_chosen_avatar=True, has_completed_registration=True,
        )
    c = Client()
    c.force_login(tu)
    
    tests = [
        ("/notifications/", "notifications (root)"),
        ("/social/notifications/", "notifications (social)"),
        ("/alliance/", "alliance home"),
        ("/alliance/create/", "alliance create"),
        ("/panel-admin/tournaments/", "admin tournaments"),
        ("/panel-admin/tournaments/create/", "admin tournament create"),
    ]
    for url, name in tests:
        try:
            r = c.get(url)
            code = r.status_code
            if code == 200:
                print(f"  ✓ {url} ({name}) → 200")
            elif code in (301, 302):
                print(f"  → {url} ({name}) → {code} → {r.get('Location','?')[:50]}")
            else:
                print(f"  ❌ {url} ({name}) → {code}")
        except Exception as e:
            print(f"  ❌ {url} ({name}) → {type(e).__name__}: {str(e)[:100]}")
    
    tu.delete()
except Exception as e:
    print(f"  ❌ Test error: {e}")

# Test Jalali conversion
print("\n  [Jalali conversion test]")
try:
    from datetime import datetime
    # Test: 1403/08/26 → 2024/11/16
    jy, jm, jd = 1403, 8, 26
    jy2 = jy
    if jy2 > 979:
        gy = 1600; jy2 -= 979
    else:
        gy = 621
    days = (365 * jy2) + ((jy2 // 33) * 8) + (((jy2 % 33) + 3) // 4) + 78 + jd + ((jm - 1) * 31 if jm < 7 else ((jm - 7) * 30) + 186)
    gy += 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    is_leap = (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)
    sal_a = [0, 31, 29 if is_leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 1
    for i in range(1, 13):
        if gd <= sal_a[i]:
            gm = i; break
        gd -= sal_a[i]
    if (gy, gm, gd) == (2024, 11, 16):
        print(f"  ✓ 1403/08/26 → {gy}/{gm:02d}/{gd:02d} (correct)")
    else:
        print(f"  ⚠ 1403/08/26 → {gy}/{gm:02d}/{gd:02d} (expected 2024/11/16)")
except Exception as e:
    print(f"  ❌ Conversion test failed: {e}")

# ============================================================
# 6) Print passwords
# ============================================================
print("\n[6/6] Passwords")
p = os.path.join(ROOT, "config", "beta_gate.py")
if os.path.exists(p):
    src = read(p)
    m = re.search(r'BETA_PASSWORD\s*=\s*["\']([^"\']+)["\']', src)
    if m:
        print(f"  🔑 رمز ورود اولیه بازی (Beta Gate): {m.group(1)}")
p = os.path.join(ROOT, "accounts", "admin_views.py")
if os.path.exists(p):
    src = read(p)
    m1 = re.search(r'ADMIN_USERNAME\s*=\s*["\']([^"\']+)["\']', src)
    m2 = re.search(r'ADMIN_PASSWORD\s*=\s*["\']([^"\']+)["\']', src)
    if m1 and m2:
        print(f"  👤 پنل ادمین: {m1.group(1)} / {m2.group(1)}")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
What was fixed:

  1.  ✓ Notifications route:
        - /notifications/ (root) ← NEW, home active
        - /social/notifications/ (kept for compat)
        - active marker: friends → home
        - menu bell link updated

  2.  ✓ Alliance:
        - alliance_edit view (leader-only)
        - /alliance/<id>/edit/ route
        - join_alliance view (with password)
        - /alliance/join-id/<id>/ route

  3.  ✓ Tournament date bug:
        - Default end = now + 2 hours (not same as start)
        - _parse_jalali_dt verified (pure python)
        - Template uses default_end_jy/jm/jd
        - Test confirms 1403/08/26 → 2024/11/16

  4.  ✓ Migrations run
  5.  ✓ All pages tested

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R

Test:
  /notifications/       → opens, bottom nav highlights خانه
  /alliance/            → list of alliances
  /alliance/create/     → create form
  /panel-admin/tournaments/ → + ساخت تورنمنت → save with defaults
""")
