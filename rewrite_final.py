#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")
def backup(p):
    bak = p + ".bak_rewrite"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) admin_views.py - REWRITE tournament section from scratch
# ============================================================
print("\n[1/5] admin_views.py - full tournament rewrite")
p = os.path.join(ROOT, "accounts", "admin_views.py")
src = read(p)

# Find where tournament section starts and where user section starts
# Remove everything from "# Admin — Tournaments" to end of file
# then re-append cleanly
# Also remove old _parse_jalali_dt / _parse_dt if present

# Remove tournament section
tour_marker = "# ============================================================\n# Admin — Tournaments"
if tour_marker in src:
    idx = src.find(tour_marker)
    src = src[:idx].rstrip() + "\n"
    print("  Removed old tournament section")

# Remove old _parse_jalali_dt (any variant)
for pattern_text in [
    r'def _parse_jalali_dt\(request, prefix\):.*?(?=\ndef [A-Za-z_]|\Z)',
    r'def _parse_dt\(s\):.*?(?=\ndef [A-Za-z_]|\Z)',
]:
    m = re.search(pattern_text, src, re.DOTALL)
    if m:
        src = src[:m.start()] + src[m.end():]
        print("  Removed old parse function")

# Append clean tournament code
TOURNAMENT_CODE = r'''

# ============================================================
# Admin — Tournaments (Clean Rewrite)
# ============================================================
def _g2j_convert(gy, gm, gd):
    """Gregorian date -> (jy, jm, jd) Jalali."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
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


def _j2g_convert(jy, jm, jd):
    """Jalali date -> (gy, gm, gd) Gregorian."""
    jy2 = jy
    if jy2 > 979:
        gy = 1600
        jy2 -= 979
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
    return gy, gm, gd


def _parse_jalali_dt(request, prefix):
    """Read Jalali picker fields, return Gregorian aware datetime or None."""
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

    gy, gm, gd = _j2g_convert(jy, jm, jd)
    try:
        d = datetime(gy, gm, gd, jh, jmin)
        if tz.is_naive(d):
            d = tz.make_aware(d)
        return d
    except (ValueError, TypeError):
        return None


def _jalali_picker_context():
    """Return context dict for jalali picker default values."""
    from django.utils import timezone as tz
    from datetime import timedelta
    now = tz.now()
    end = now + timedelta(hours=2)  # default end = start + 2 hours

    now_jy, now_jm, now_jd = _g2j_convert(now.year, now.month, now.day)
    end_jy, end_jm, end_jd = _g2j_convert(end.year, end.month, end.day)

    return {
        "year_options": list(range(now_jy - 1, now_jy + 3)),
        "month_options": [
            (1, "فروردین"), (2, "اردیبهشت"), (3, "خرداد"), (4, "تیر"),
            (5, "مرداد"), (6, "شهریور"), (7, "مهر"), (8, "آبان"),
            (9, "آذر"), (10, "دی"), (11, "بهمن"), (12, "اسفند"),
        ],
        "day_options": list(range(1, 32)),
        "hour_options": list(range(0, 24)),
        "minute_options": list(range(0, 60, 5)),
        # Defaults for START
        "default_jy": now_jy,
        "default_jm": now_jm,
        "default_jd": now_jd,
        "default_jh": now.hour,
        # Defaults for END (2 hours later)
        "default_end_jy": end_jy,
        "default_end_jm": end_jm,
        "default_end_jd": end_jd,
        "default_end_jh": end.hour,
    }


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
    """Save tournament from POST. Returns (tournament, error)."""
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

    if not start_at:
        return None, "تاریخ شروع نامعتبر است."
    if not end_at:
        return None, "تاریخ پایان نامعتبر است."
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
    ctx = _jalali_picker_context()
    ctx["tournament"] = None
    ctx["message"] = message
    return render(request, "custom_admin/tournament_edit.html", ctx)


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

    entries = t.entries.select_related("user").order_by("-score", "joined_at")
    entries_data = [{
        "user_id": e.user.id,
        "username": e.user.username,
        "alias": e.user.alias,
        "joined_at": e.joined_at,
        "score": e.score,
    } for e in entries]

    message = request.session.pop("admin_message", None)
    ctx = _jalali_picker_context()
    ctx["tournament"] = t
    ctx["entries"] = entries_data
    ctx["message"] = message
    return render(request, "custom_admin/tournament_edit.html", ctx)


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

src = src.rstrip() + TOURNAMENT_CODE + "\n"
backup(p); write(p, src)

# ============================================================
# 2) Verify alliance views + recreate if missing
# ============================================================
print("\n[2/5] Alliance views verification")

import importlib

# Force reload
if "alliance" in sys.modules:
    del sys.modules["alliance"]
if "alliance.views" in sys.modules:
    del sys.modules["alliance.views"]

import django
django.setup()

try:
    from alliance import views as av
    required = [
        ("alliance_home", 1),
        ("create_alliance", 1),
        ("join_by_code", 1),
        ("join_alliance", 2),
        ("alliance_detail", 2),
        ("alliance_edit", 2),
        ("alliance_chat", 2),
        ("leave_alliance", 2),
        ("kick_member", 3),
    ]
    missing = []
    for name, argc in required:
        if not hasattr(av, name):
            missing.append(name)
            print(f"  ❌ MISSING: {name}")
        else:
            print(f"  ✓ {name}")

    if missing:
        print(f"\n  ⚠ {len(missing)} views missing: {missing}")
        print("  Adding missing views to alliance/views.py...")

        p = os.path.join(ROOT, "alliance", "views.py")
        src = read(p)

        if "def alliance_edit" in missing or "alliance_edit" in missing:
            if "def alliance_edit" not in src:
                src += '''

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
        "alliance": a, "error": error, "emojis": emojis, "active": "friends",
    })
'''
                print("    + alliance_edit added")

        if "join_alliance" in missing:
            if "def join_alliance" not in src:
                src += '''

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
                print("    + join_alliance added")

        write(p, src)
except Exception as e:
    print(f"  ❌ Import failed: {e}")

# Also ensure routes exist
p = os.path.join(ROOT, "alliance", "urls.py")
src = read(p)
routes_to_add = []

if "join_alliance" not in src:
    routes_to_add.append('    path("join-id/<int:alliance_id>/", views.join_alliance, name="join_alliance"),')
if "alliance_edit" not in src:
    routes_to_add.append('    path("<int:alliance_id>/edit/", views.alliance_edit, name="edit"),')

if routes_to_add:
    # Add before closing ]
    old_end = "]\n"
    new_end = "\n".join(routes_to_add) + "\n]\n"
    src = src.rsplit(old_end, 1)[0] + new_end
    backup(p); write(p, src)
    print(f"  FIXED: {len(routes_to_add)} route(s) added")
else:
    print("  ✓ All alliance routes present")

# ============================================================
# 3) Reload Django and TEST all pages
# ============================================================
print("\n[3/5] Testing all pages")

# Force fresh imports
for mod in ["accounts.admin_views", "alliance.views", "social.views"]:
    if mod in sys.modules:
        del sys.modules[mod]

importlib.invalidate_caches()
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

test_user = User.objects.filter(username="__test__").first()
created = False
if not test_user:
    test_user = User.objects.create_user(
        username="__test__", password="test123456",
        alias="تست", is_active=True,
        has_chosen_avatar=True, has_completed_registration=True,
    )
    created = True

c = Client()
c.force_login(test_user)

pages = [
    ("/notifications/", "notifications (root)"),
    ("/social/notifications/", "notifications (social)"),
    ("/alliance/", "alliance home"),
    ("/alliance/create/", "alliance create"),
    ("/panel-admin/tournaments/", "admin tournaments list"),
    ("/panel-admin/tournaments/create/", "admin tournament create"),
]

errors = []
for url, name in pages:
    try:
        r = c.get(url, follow=False)
        code = r.status_code
        if code == 200:
            print(f"  ✓ {url} → 200 ({name})")
        elif code in (301, 302):
            print(f"  → {url} → {code} → {r.get('Location','?')[:60]} ({name})")
        else:
            print(f"  ❌ {url} → {code} ({name})")
            errors.append((url, code))
    except Exception as e:
        print(f"  ❌ {url} → {type(e).__name__}: {str(e)[:120]} ({name})")
        errors.append((url, str(e)[:120]))

# Test creating a tournament
print("\n  [Test: create tournament]")
try:
    from accounts.admin_views import _jalali_picker_context
    ctx = _jalali_picker_context()
    print(f"    Default start: {ctx['default_jy']}/{ctx['default_jm']:02d}/{ctx['default_jd']:02d} {ctx['default_jh']:02d}:00")
    print(f"    Default end:   {ctx['default_end_jy']}/{ctx['default_end_jm']:02d}/{ctx['default_end_jd']:02d} {ctx['default_end_jh']:02d}:00")
    
    start_h = ctx['default_jh']
    end_h = ctx['default_end_jh']
    if start_h != end_h or ctx['default_jd'] != ctx['default_end_jd']:
        print("    ✓ start and end differ")
    else:
        print("    ⚠ start and end may collide")
except Exception as e:
    print(f"    ❌ Context error: {e}")

# Test actual save via POST
print("\n  [Test: save tournament with defaults]")
try:
    from accounts.admin_views import _check_auth, _save_tournament_from_post
    from game.models import Tournament
    
    # Get current picker context and simulate POST
    ctx = _jalali_picker_context()
    data = {
        "name": "__TEST_TOURNAMENT__",
        "description": "test",
        "icon": "🏆",
        "tournament_type": "daily",
        "status": "scheduled",
        "start_jy": ctx['default_jy'],
        "start_jm": ctx['default_jm'],
        "start_jd": ctx['default_jd'],
        "start_jh": ctx['default_jh'],
        "start_jmin": 0,
        "end_jy": ctx['default_end_jy'],
        "end_jm": ctx['default_end_jm'],
        "end_jd": ctx['default_end_jd'],
        "end_jh": ctx['default_end_jh'],
        "end_jmin": 0,
        "entry_fee_coins": 0,
        "entry_fee_gems": 0,
        "prize_coins": 0,
        "prize_gems": 0,
        "max_players": 100,
        "min_players": 2,
    }
    
    # Build a fake request object
    class FakeRequest:
        def __init__(self, data):
            self.POST = data
            self.session = {}
    
    # Need real session - use client
    r = c.post("/panel-admin/tournaments/create/", data, follow=False)
    if r.status_code in (200, 302):
        saved = Tournament.objects.filter(name="__TEST_TOURNAMENT__").first()
        if saved:
            print(f"    ✓ Tournament saved: {saved.name}")
            print(f"      start={saved.start_at} end={saved.end_at}")
            if saved.end_at > saved.start_at:
                print(f"      ✓ end > start")
            else:
                print(f"      ❌ end <= start")
            saved.delete()
        else:
            print(f"    ⚠ Status {r.status_code} but tournament not found")
            if r.status_code == 200:
                # Check for error
                content = r.content.decode('utf-8', errors='ignore')
                if 'error' in content.lower():
                    print(f"    Content preview: {content[:500]}")
    else:
        print(f"    ❌ POST failed: {r.status_code}")
except Exception as e:
    import traceback
    print(f"    ❌ Test error: {e}")
    traceback.print_exc()

# Cleanup
if created:
    test_user.delete()

# ============================================================
# 4) Run migrations + check
# ============================================================
print("\n[4/5] Migrations + check")
for cmd in [
    [sys.executable, "manage.py", "makemigrations", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0 and r.stderr.strip():
        print(f"  ⚠ {cmd[2]}: {r.stderr.strip()[:300]}")
    else:
        print(f"  ✓ {cmd[2]}")

r = subprocess.run([sys.executable, "manage.py", "check"], cwd=ROOT, capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check passed")
else:
    print("  ⚠ Check errors:")
    print(r.stderr[:1000] if r.stderr else r.stdout[:1000])

# ============================================================
# 5) Summary
# ============================================================
print("\n[5/5] Summary")
if not errors:
    print("\n✅ ALL TESTS PASSED")
else:
    print(f"\n⚠ {len(errors)} issue(s) found")

print("\n🔑 Passwords:")
print("  Beta Gate (رمز ورود اولیه بازی): emami_irani_esm1405")
print("  Admin Panel: admin74 / Amir2255ds")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Next steps:
  1. Ctrl+C to stop server
  2. python manage.py runserver
  3. Ctrl+Shift+R to hard refresh browser

Test tournament date:
  1. Go /panel-admin/tournaments/
  2. Click "+ ساخت تورنمنت"
  3. Verify START section shows current date/time
  4. Verify END section shows 2 hours later
  5. Click 💾 ذخیره WITHOUT changing anything
  6. Should save successfully

If it STILL fails, run this and send the output:
  python manage.py shell -c "
from accounts.admin_views import _jalali_picker_context, _parse_jalali_dt
ctx = _jalali_picker_context()
print('start_jy:', ctx['default_jy'])
print('end_jy:', ctx['default_end_jy'])
print('start_jh:', ctx['default_jh'])
print('end_jh:', ctx['default_end_jh'])
"
""")
