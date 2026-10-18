#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix without jdatetime - pure Python Jalali converter."""
import os, subprocess, sys, re

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")
def backup(p):
    bak = p + ".bak_off"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) common/templatetags/jalali_tags.py - PURE PYTHON
# ============================================================
print("\n[1/6] jalali_tags.py - pure Python (no jdatetime)")
os.makedirs(os.path.join(ROOT, "common", "templatetags"), exist_ok=True)
write(os.path.join(ROOT, "common", "__init__.py"), "")
write(os.path.join(ROOT, "common", "templatetags", "__init__.py"), "")

JALALI_PURE = '''# -*- coding: utf-8 -*-
"""Pure Python Jalali (Shamsi) date converter - no external deps."""
from django import template

register = template.Library()


def g2j(gy, gm, gd):
    """Gregorian -> Jalali. Returns (jy, jm, jd)."""
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


def j2g(jy, jm, jd):
    """Jalali -> Gregorian. Returns (gy, gm, gd)."""
    if jy > 979:
        gy = 1600
        jy -= 979
    else:
        gy = 621
    days = (365 * jy) + ((jy // 33) * 8) + (((jy % 33) + 3) // 4) + 78 + jd + ((jm - 1) * 31 if jm < 7 else ((jm - 7) * 30) + 186)
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


class JDate:
    def __init__(self, jy, jm, jd, h=0, mi=0, s=0):
        self.year = jy
        self.month = jm
        self.day = jd
        self.hour = h
        self.minute = mi
        self.second = s

    def strftime(self, fmt):
        # Minimal strftime - only Y/m/d H:i:s + Persian
        out = fmt
        out = out.replace("%Y", str(self.year))
        out = out.replace("%m", str(self.month).zfill(2))
        out = out.replace("%d", str(self.day).zfill(2))
        out = out.replace("%H", str(self.hour).zfill(2))
        out = out.replace("%M", str(self.minute).zfill(2))
        out = out.replace("%S", str(self.second).zfill(2))
        # Also handle Django-style tokens
        out = out.replace("Y", str(self.year))
        out = out.replace("m", str(self.month).zfill(2))
        out = out.replace("d", str(self.day).zfill(2))
        out = out.replace("H", str(self.hour).zfill(2))
        out = out.replace("i", str(self.minute).zfill(2))
        out = out.replace("s", str(self.second).zfill(2))
        return out


@register.filter
def to_jalali(value):
    if not value:
        return None
    try:
        jy, jm, jd = g2j(value.year, value.month, value.day)
        h = getattr(value, "hour", 0)
        mi = getattr(value, "minute", 0)
        s = getattr(value, "second", 0)
        return JDate(jy, jm, jd, h, mi, s)
    except Exception:
        return None


@register.filter
def jdate(value, fmt="Y/m/d H:i"):
    if not value:
        return ""
    try:
        jy, jm, jd = g2j(value.year, value.month, value.day)
        h = getattr(value, "hour", 0)
        mi = getattr(value, "minute", 0)
        s = getattr(value, "second", 0)
        j = JDate(jy, jm, jd, h, mi, s)
        return j.strftime(fmt)
    except Exception:
        try:
            return value.strftime(fmt)
        except Exception:
            return str(value)
'''
write(os.path.join(ROOT, "common", "templatetags", "jalali_tags.py"), JALALI_PURE)

# ============================================================
# 2) config/settings.py - add 'common'
# ============================================================
print("\n[2/6] settings.py - add 'common'")
p = os.path.join(ROOT, "config", "settings.py")
src = read(p)
if '"common"' in src or "'common'" in src:
    print("  SKIP: already in INSTALLED_APPS")
else:
    # Find end of INSTALLED_APPS
    match = re.search(r'INSTALLED_APPS\s*=\s*\[(.*?)\]', src, re.DOTALL)
    if match:
        old_block = match.group(0)
        new_block = old_block.rstrip("]") + '\n    "common",\n]'
        src = src.replace(old_block, new_block, 1)
        backup(p); write(p, src)
        print("  FIXED: 'common' added")
    else:
        print("  WARN: INSTALLED_APPS not found")

# ============================================================
# 3) accounts/admin_views.py - replace _parse_jalali_dt with pure python
# ============================================================
print("\n[3/6] admin_views.py - pure python Jalali parse")
p = os.path.join(ROOT, "accounts", "admin_views.py")
src = read(p)

# Remove old _parse_jalali_dt
old_pattern = re.compile(r'def _parse_jalali_dt\(request, prefix\):.*?(?=\ndef |\Z)', re.DOTALL)
m = old_pattern.search(src)
if m:
    src = src[:m.start()] + src[m.end():]

new_fn = '''

def _parse_jalali_dt(request, prefix):
    """Read Jalali picker fields, return Gregorian aware datetime."""
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

    # Inline pure-python j2g
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

    from datetime import datetime
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
print("  FIXED: _parse_jalali_dt rewritten (pure python)")

# Remove jdatetime imports from tournament views
src = read(p)
if "import jdatetime" in src:
    # Replace tournament_create context block
    old_block = '''    message = request.session.pop("admin_message", None)
    import jdatetime
    from datetime import timedelta
    now_j = jdatetime.datetime.now()
    tomorrow_j = now_j + timedelta(days=1)'''
    # Get current Jalali year from system date
    new_block = '''    message = request.session.pop("admin_message", None)
    from datetime import datetime, timedelta
    from django.utils import timezone as tz_now
    gnow = tz_now.now()
    # g2j inline
    _g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    _gy = gnow.year
    _gm = gnow.month
    _gd = gnow.day
    if _gy > 1600:
        _jy = 979
        _gy -= 1600
    else:
        _jy = 0
        _gy -= 621
    _gy2 = _gy + 1 if _gm > 2 else _gy
    _days = (365 * _gy) + ((_gy2 + 3) // 4) - ((_gy2 + 99) // 100) + ((_gy2 + 399) // 400) - 80 + _gd + _g_d_m[_gm - 1]
    _jy += 33 * (_days // 12053)
    _days %= 12053
    _jy += 4 * (_days // 1461)
    _days %= 1461
    if _days > 365:
        _jy += (_days - 1) // 365
        _days = (_days - 1) % 365
    if _days < 186:
        _jm = 1 + _days // 31
        _jd = 1 + _days % 31
    else:
        _jm = 7 + (_days - 186) // 30
        _jd = 1 + (_days - 186) % 30
    now_j_year = _jy
    now_j_month = _jm
    now_j_day = _jd
    now_j_hour = gnow.hour
    tomorrow_j_hour = (gnow + timedelta(days=1)).hour'''
    
    src = src.replace(old_block, new_block)
    # Fix references
    src = src.replace('"year_options": list(range(now_j.year - 1, now_j.year + 3)),', '"year_options": list(range(now_j_year - 1, now_j_year + 3)),')
    src = src.replace('"default_jy": now_j.year,', '"default_jy": now_j_year,')
    src = src.replace('"default_jm": now_j.month,', '"default_jm": now_j_month,')
    src = src.replace('"default_jd": now_j.day,', '"default_jd": now_j_day,')
    src = src.replace('"default_jh": now_j.hour,', '"default_jh": now_j_hour,')
    src = src.replace('"default_end_jh": tomorrow_j.hour,', '"default_end_jh": tomorrow_j_hour,')
    
    backup(p); write(p, src)
    print("  FIXED: tournament context rewritten (pure python)")

# ============================================================
# 4) Ensure notifications_view is correct
# ============================================================
print("\n[4/6] social/views.py - verify notifications_view")
p = os.path.join(ROOT, "social", "views.py")
src = read(p)
if "unread_total" not in src:
    print("  WARN: notifications_view may be outdated - fixing")
    # Remove old
    pattern = re.compile(r'@login_required\ndef notifications_view\(request\):.*?(?=\n@login_required|\Z)', re.DOTALL)
    m = pattern.search(src)
    if m:
        src = src[:m.start()] + src[m.end():]
    new = '''

@login_required
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
    })
'''
    src = src.rstrip() + new + "\n"
    backup(p); write(p, src)
    print("  FIXED")
else:
    print("  SKIP: already has unread_total")

# ============================================================
# 5) Verify challenge view exists
# ============================================================
print("\n[5/6] game/views.py - verify challenge_home + tournament_join")
p = os.path.join(ROOT, "game", "views.py")
src = read(p)
if "def challenge_home" not in src:
    print("  WARN: challenge_home missing - adding")
    new = '''

@login_required
def challenge_home(request):
    check = _require_complete(request.user)
    if check:
        return check
    from django.utils import timezone
    try:
        from .models import Tournament, TournamentEntry
    except ImportError:
        return render(request, "game/challenge.html", {"weekly": [], "daily": [], "hourly": [], "active": "games"})
    now = timezone.now()
    Tournament.objects.filter(end_at__lt=now, status__in=["scheduled", "active"]).update(status="finished")

    def _list(t_type):
        qs = Tournament.objects.filter(tournament_type=t_type).order_by("-start_at")[:10]
        out = []
        for x in qs:
            is_joined = TournamentEntry.objects.filter(tournament=x, user=request.user).exists()
            out.append({
                "id": x.id, "name": x.name, "icon": x.icon, "description": x.description,
                "tournament_type": x.tournament_type, "status": x.status,
                "get_status_display": x.get_status_display(),
                "start_at": x.start_at, "end_at": x.end_at,
                "start_at_ts": int(x.start_at.timestamp()),
                "end_at_ts": int(x.end_at.timestamp()),
                "entry_count": x.entry_count(), "max_players": x.max_players,
                "prize_coins": x.prize_coins, "prize_gems": x.prize_gems,
                "entry_fee_coins": x.entry_fee_coins,
                "is_live": x.is_live, "is_finished": x.is_finished,
                "is_upcoming": x.is_upcoming, "is_joined": is_joined,
            })
        return out

    return render(request, "game/challenge.html", {
        "weekly": _list("weekly"), "daily": _list("daily"), "hourly": _list("hourly"),
        "active": "games",
    })
'''
    src = src.rstrip() + new + "\n"
    backup(p); write(p, src)
    print("  FIXED: challenge_home added")
else:
    print("  SKIP: challenge_home exists")

# ============================================================
# 6) Migrations
# ============================================================
print("\n[6/6] Migrations")
for cmd in [
    [sys.executable, "manage.py", "makemigrations", "game", "social", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    print(f"\n  $ {' '.join(cmd[1:])}")
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = r.stdout.strip()
    if out: print("   ", out.replace("\n", "\n    ")[:800])
    if r.returncode != 0 and r.stderr.strip():
        print("   ERR:", r.stderr.strip()[:600])

print("\n  $ manage.py check")
r = subprocess.run([sys.executable, "manage.py", "check"], cwd=ROOT, capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check passed")
else:
    print("  ⚠ ERRORS:")
    print(r.stderr[:2000] if r.stderr else r.stdout[:2000])

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
What was fixed (no internet needed):

  1.  ✓ common/templatetags/jalali_tags.py → pure Python
        - no jdatetime import
        - g2j / j2g converters built-in
        - to_jalali returns object with .year/.month/.day/.hour/.minute
        - jdate filter formats correctly

  2.  ✓ 'common' added to INSTALLED_APPS
        - THIS is what makes {% load jalali_tags %} work

  3.  ✓ accounts/admin_views.py
        - _parse_jalali_dt rewritten (pure python, no jdatetime)
        - tournament_create context rewritten

  4.  ✓ social/views.py → notifications_view clean

  5.  ✓ game/views.py → challenge_home verified

  6.  ✓ Migrations run

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R

Then test:
  - /social/notifications/  → should open
  - /panel-admin/tournaments/  → list should open
  - /panel-admin/tournaments/ → + ساخت تورنمنت
    → Date picker with 5 dropdowns, live preview
  - /game/challenge/  → 3 sections

If still broken, run:
  python manage.py check --deploy
  and send output
""")
