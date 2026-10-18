"""پنل ادمین سفارشی — فقط برای مدیر سیستم."""
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache


# ⚠️ فقط از اینجا قابل تغییر است — نه از دیتابیس
ADMIN_USERNAME = "admin74"
ADMIN_PASSWORD = "Amir2255ds"


def _check_auth(request):
    """آیا این نشست لاگین ادمین است؟"""
    return request.session.get("custom_admin_logged_in") is True


@never_cache
def admin_login(request):
    """صفحه ورود ادمین."""
    if _check_auth(request):
        return redirect("custom_admin:dashboard")

    error = None

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            request.session["custom_admin_logged_in"] = True
            request.session.set_expiry(60 * 60 * 8)
            return redirect("custom_admin:dashboard")
        else:
            error = "نام کاربری یا رمز عبور اشتباه است."

    return render(request, "custom_admin/login.html", {"error": error})


@never_cache
def admin_logout(request):
    request.session.pop("custom_admin_logged_in", None)
    return redirect("custom_admin:login")


@never_cache
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

@never_cache
def user_detail(request, user_id):
    """جزئیات یک کاربر."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("custom_admin:dashboard")

    from game.models import Player
    players = Player.objects.filter(user=u).select_related("game").order_by("-id")[:20]

    games_data = []
    for p in players:
        games_data.append({
            "game_id": p.game.id,
            "mode": p.game.mode,
            "score": p.score,
            "created_at": p.game.created_at,
            "status": p.game.status,
        })

    message = request.session.pop("admin_message", None)

    return render(request, "custom_admin/user_detail.html", {
        "u": u,
        "games": games_data,
        "message": message,
    })


@never_cache
def user_toggle_active(request, user_id):
    """فعال/غیرفعال کردن کاربر."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    if request.method != "POST":
        return redirect("custom_admin:dashboard")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
        u.is_active = not u.is_active
        u.save(update_fields=["is_active"])
    except User.DoesNotExist:
        pass

    return redirect("custom_admin:dashboard")


@never_cache
def user_delete(request, user_id):
    """حذف کاربر."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    if request.method != "POST":
        return redirect("custom_admin:dashboard")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
        u.delete()
    except User.DoesNotExist:
        pass

    return redirect("custom_admin:dashboard")


@never_cache
def user_reset_password(request, user_id):
    """تغییر پسورد کاربر توسط ادمین."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    if request.method != "POST":
        return redirect("custom_admin:dashboard")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("custom_admin:dashboard")

    new_password = (request.POST.get("new_password") or "").strip()

    if len(new_password) < 6:
        request.session["admin_message"] = {
            "type": "error",
            "text": "رمز جدید باید حداقل ۶ کاراکتر باشد."
        }
    else:
        u.set_password(new_password)
        u.save()
        request.session["admin_message"] = {
            "type": "success",
            "text": f"رمز کاربر {u.username} با موفقیت تغییر کرد."
        }

    return redirect("custom_admin:user_detail", user_id=u.id)


@never_cache
def user_change_alias(request, user_id):
    """تغییر نام نمایشی کاربر توسط ادمین."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    if request.method != "POST":
        return redirect("custom_admin:dashboard")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("custom_admin:dashboard")

    new_alias = (request.POST.get("new_alias") or "").strip()[:32]

    if len(new_alias) < 2:
        request.session["admin_message"] = {
            "type": "error",
            "text": "نام نمایشی باید حداقل ۲ کاراکتر باشد."
        }
    else:
        u.alias = new_alias
        u.save(update_fields=["alias"])
        request.session["admin_message"] = {
            "type": "success",
            "text": f"نام نمایشی به «{new_alias}» تغییر کرد."
        }

    return redirect("custom_admin:user_detail", user_id=u.id)

# ============================================================
# Admin — Alliances
# ============================================================
@never_cache
def alliances_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    from alliance.models import Alliance
    search = (request.GET.get("q") or "").strip()
    qs = Alliance.objects.all().order_by("-created_at")
    if search:
        from django.db.models import Q
        qs = qs.filter(Q(name__icontains=search) | Q(tag__icontains=search) | Q(invite_code__icontains=search))
    data = []
    for a in qs:
        data.append({
            "id": a.id, "name": a.name, "tag": a.tag, "emblem": a.emblem,
            "leader": a.leader.alias, "leader_username": a.leader.username,
            "member_count": a.member_count(), "max_members": a.max_members,
            "has_password": bool(a.password), "invite_code": a.invite_code,
            "created_at": a.created_at, "description": a.description,
        })
    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/alliances.html", {
        "alliances": data, "search": search, "message": message,
    })


@never_cache
def alliance_manage(request, alliance_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    from alliance.models import Alliance, AllianceMember
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        a = Alliance.objects.get(id=alliance_id)
    except Alliance.DoesNotExist:
        return redirect("custom_admin:alliances_list")

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "update":
            name = (request.POST.get("name") or "").strip()[:40]
            tag = (request.POST.get("tag") or "").strip().upper()[:8]
            description = (request.POST.get("description") or "").strip()[:200]
            emblem = (request.POST.get("emblem") or "🛡️").strip()[:4]
            password = (request.POST.get("password") or "").strip()[:32]
            try:
                max_members = int(request.POST.get("max_members") or 30)
            except (ValueError, TypeError):
                max_members = 30
            max_members = max(5, min(100, max_members))
            new_leader_id = request.POST.get("leader_id") or ""

            if not name or len(name) < 3:
                request.session["admin_message"] = {"type": "error", "text": "نام باید حداقل ۳ حرف باشد."}
                return redirect("custom_admin:alliance_manage", alliance_id=a.id)
            if Alliance.objects.filter(name=name).exclude(id=a.id).exists():
                request.session["admin_message"] = {"type": "error", "text": "این نام قبلاً استفاده شده."}
                return redirect("custom_admin:alliance_manage", alliance_id=a.id)

            a.name = name
            a.tag = tag
            a.description = description
            a.emblem = emblem
            a.password = password
            a.max_members = max_members

            if new_leader_id and str(new_leader_id) != str(a.leader_id):
                try:
                    new_leader = User.objects.get(id=new_leader_id)
                    if AllianceMember.objects.filter(alliance=a, user=new_leader).exists():
                        AllianceMember.objects.filter(alliance=a, user=a.leader).update(role="member")
                        AllianceMember.objects.filter(alliance=a, user=new_leader).update(role="leader")
                        a.leader = new_leader
                except User.DoesNotExist:
                    pass
            a.save()
            request.session["admin_message"] = {"type": "success", "text": "اتحاد با موفقیت به‌روزرسانی شد."}
            return redirect("custom_admin:alliance_manage", alliance_id=a.id)

        elif action == "delete":
            a.delete()
            request.session["admin_message"] = {"type": "success", "text": "اتحاد حذف شد."}
            return redirect("custom_admin:alliances_list")

        elif action == "kick_member":
            user_id = request.POST.get("user_id")
            AllianceMember.objects.filter(alliance=a, user_id=user_id).exclude(role="leader").delete()
            return redirect("custom_admin:alliance_manage", alliance_id=a.id)

    members = AllianceMember.objects.filter(alliance=a).select_related("user")
    members_data = [{
        "user_id": m.user.id, "username": m.user.username, "alias": m.user.alias,
        "role": m.role, "role_display": m.get_role_display(), "joined_at": m.joined_at,
    } for m in members]
    message = request.session.pop("admin_message", None)
    emojis = ["🛡️", "⚔️", "🏰", "🐉", "🦅", "🐺", "🔥", "⚡", "👑", "💎", "🌟", "🦁"]
    return render(request, "custom_admin/alliance_detail.html", {
        "a": a, "members": members_data, "message": message, "emojis": emojis,
    })


# ============================================================
# Admin — Rooms (Games)
# ============================================================


@never_cache
def room_delete(request, game_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:rooms_list")
    from game.models import Game
    try:
        Game.objects.get(id=game_id).delete()
        request.session["admin_message"] = {"type": "success", "text": "اتاق حذف شد."}
    except Game.DoesNotExist:
        pass
    return redirect("custom_admin:rooms_list")


# ============================================================
# Admin — Full User Edit
# ============================================================
@never_cache
def user_edit(request, user_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("custom_admin:dashboard")
    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/user_edit.html", {"u": u, "message": message})


@never_cache
def user_update(request, user_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:user_edit", user_id=user_id)
    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("custom_admin:dashboard")

    action = request.POST.get("action", "update")
    redirect_to = request.POST.get("redirect_to", "edit")

    if action == "update":
        new_username = (request.POST.get("username") or "").strip().lower()
        if new_username and new_username != u.username:
            if len(new_username) < 3 or len(new_username) > 32:
                request.session["admin_message"] = {"type": "error", "text": "username باید ۳ تا ۳۲ حرف باشد."}
                return redirect("custom_admin:user_edit", user_id=u.id)
            if not all(c.isalnum() or c == "_" for c in new_username):
                request.session["admin_message"] = {"type": "error", "text": "username فقط حروف/اعداد/_."}
                return redirect("custom_admin:user_edit", user_id=u.id)
            if User.objects.filter(username=new_username).exclude(id=u.id).exists():
                request.session["admin_message"] = {"type": "error", "text": "این username قبلاً استفاده شده."}
                return redirect("custom_admin:user_edit", user_id=u.id)
            u.username = new_username

        new_alias = (request.POST.get("alias") or "").strip()[:32]
        if new_alias:
            u.alias = new_alias
        u.email = (request.POST.get("email") or "").strip() or None
        phone_val = (request.POST.get("phone") or "").strip()[:20]
        u.phone = phone_val if phone_val else None
        u.is_active = request.POST.get("is_active") == "on"
        u.is_staff = request.POST.get("is_staff") == "on"
        u.is_guest = request.POST.get("is_guest") == "on"
        try:
            u.coins = int(request.POST.get("coins") or 0)
        except (ValueError, TypeError):
            u.coins = 0
        try:
            u.gems = int(request.POST.get("gems") or 0)
        except (ValueError, TypeError):
            u.gems = 0

        new_password = (request.POST.get("password") or "").strip()
        if new_password:
            if len(new_password) < 6:
                request.session["admin_message"] = {"type": "error", "text": "پسورد باید حداقل ۶ کاراکتر."}
                return redirect("custom_admin:user_edit", user_id=u.id)
            u.set_password(new_password)

        try:
            u.save()
            request.session["admin_message"] = {"type": "success", "text": "کاربر با موفقیت به‌روزرسانی شد."}
        except Exception as e:
            request.session["admin_message"] = {"type": "error", "text": f"خطا: {str(e)[:100]}"}

    elif action == "quick_coins":
        try:
            d = int(request.POST.get("delta") or 0)
            u.coins = max(0, (u.coins or 0) + d)
            u.save(update_fields=["coins"])
            request.session["admin_message"] = {"type": "success", "text": f"سکه {d:+d} شد."}
        except (ValueError, TypeError):
            pass

    elif action == "quick_gems":
        try:
            d = int(request.POST.get("delta") or 0)
            u.gems = max(0, (u.gems or 0) + d)
            u.save(update_fields=["gems"])
            request.session["admin_message"] = {"type": "success", "text": f"جم {d:+d} شد."}
        except (ValueError, TypeError):
            pass

    if redirect_to == "detail":
        return redirect("custom_admin:user_detail", user_id=u.id)
    return redirect("custom_admin:user_edit", user_id=u.id)

# ============================================================
# Admin — Announcements (broadcast to all users)
# ============================================================

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

@never_cache
def user_toggle_staff(request, user_id):
    """ارتقا/حذف ادمینی کاربر."""
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:dashboard")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("custom_admin:dashboard")

    action = request.POST.get("action", "toggle")
    if action == "promote":
        u.is_staff = True
        u.save(update_fields=["is_staff"])
        request.session["admin_message"] = {"type": "success", "text": f"@{u.username} به ادمین ارتقا یافت."}
    elif action == "demote":
        u.is_staff = False
        u.save(update_fields=["is_staff"])
        request.session["admin_message"] = {"type": "success", "text": f"@{u.username} از ادمینی خارج شد."}
    else:
        u.is_staff = not u.is_staff
        u.save(update_fields=["is_staff"])
        request.session["admin_message"] = {"type": "success", "text": f"وضعیت ادمین @{u.username}: {'فعال' if u.is_staff else 'غیرفعال'}."}

    redirect_to = request.POST.get("redirect_to", "dashboard")
    if redirect_to == "edit":
        return redirect("custom_admin:user_edit", user_id=u.id)
    elif redirect_to == "detail":
        return redirect("custom_admin:user_detail", user_id=u.id)
    return redirect("custom_admin:dashboard")



# ============================================================
# Admin — Shop Items
# ============================================================
@never_cache
def shop_items_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    from accounts.models import ShopItem
    items = ShopItem.objects.all().order_by("-created_at")
    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/shop_items.html", {"items": items, "message": message})


@never_cache
def shop_item_create(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:shop_items_list")
    from accounts.models import ShopItem
    try:
        item = ShopItem(
            name=(request.POST.get("name") or "").strip()[:60],
            description=(request.POST.get("description") or "").strip()[:200],
            icon=(request.POST.get("icon") or "🎁").strip()[:8],
            category=request.POST.get("category", "cosmetic"),
            price_coins=int(request.POST.get("price_coins") or 0),
            price_gems=int(request.POST.get("price_gems") or 0),
            reward_type=(request.POST.get("reward_type") or "").strip()[:20],
            reward_value=int(request.POST.get("reward_value") or 0),
            reward_min=int(request.POST.get("reward_min") or 0),
            reward_max=int(request.POST.get("reward_max") or 0),
            sort_order=int(request.POST.get("sort_order") or 0),
        )
        stock = (request.POST.get("stock") or "").strip()
        if stock:
            item.stock = int(stock)
        item.save()
        request.session["admin_message"] = {"type": "success", "text": f"آیتم {item.name} ساخته شد."}
    except (ValueError, TypeError) as e:
        request.session["admin_message"] = {"type": "error", "text": f"خطا: {e}"}
    return redirect("custom_admin:shop_items_list")


@never_cache
def shop_item_toggle(request, item_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:shop_items_list")
    from accounts.models import ShopItem
    try:
        item = ShopItem.objects.get(id=item_id)
        item.is_active = not item.is_active
        item.save(update_fields=["is_active"])
        request.session["admin_message"] = {"type": "success", "text": f"وضعیت {item.name} تغییر کرد."}
    except ShopItem.DoesNotExist:
        pass
    return redirect("custom_admin:shop_items_list")


@never_cache
def shop_item_delete(request, item_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:shop_items_list")
    from accounts.models import ShopItem
    try:
        ShopItem.objects.get(id=item_id).delete()
        request.session["admin_message"] = {"type": "success", "text": "آیتم حذف شد."}
    except ShopItem.DoesNotExist:
        pass
    return redirect("custom_admin:shop_items_list")

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

# ============================================================
# Admin — Send reward/coins to all users
# ============================================================
@never_cache
def send_to_all(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")

    from django.contrib.auth import get_user_model
    from django.db.models import F
    from social.models import Notification
    User = get_user_model()

    message = request.session.pop("admin_message", None)

    if request.method == "POST":
        action = request.POST.get("action", "send")
        if action == "send":
            try:
                coins = int(request.POST.get("coins") or 0)
                gems = int(request.POST.get("gems") or 0)
            except (ValueError, TypeError):
                coins = 0
                gems = 0
            note = (request.POST.get("note") or "").strip()[:200]

            if coins == 0 and gems == 0:
                request.session["admin_message"] = {"type": "error", "text": "حداقل یکی از مقادیر باید بیشتر از صفر باشد."}
                return redirect("custom_admin:send_to_all")

            # Bulk update
            if coins != 0 or gems != 0:
                try:
                    User.objects.all().update(
                        coins=F("coins") + coins,
                        gems=F("gems") + gems,
                    )
                except Exception as e:
                    request.session["admin_message"] = {"type": "error", "text": f"خطا: {e}"}
                    return redirect("custom_admin:send_to_all")

            # Send notification to all users
            if note:
                sender = User.objects.filter(is_staff=True).first()
                uids = User.objects.values_list("id", flat=True)
                batch = []
                for uid in uids.iterator(chunk_size=1000):
                    batch.append(Notification(
                        user_id=uid,
                        type="admin_broadcast",
                        title="🎁 جایزه ویژه!",
                        body=note,
                        url="/accounts/shop/",
                        is_read=False,
                        sender=sender,
                    ))
                    if len(batch) >= 500:
                        Notification.objects.bulk_create(batch)
                        batch = []
                if batch:
                    Notification.objects.bulk_create(batch)

            total = User.objects.count()
            request.session["admin_message"] = {
                "type": "success",
                "text": f"✅ به {total} کاربر داده شد (سکه: {coins:+d}، جم: {gems:+d}).",
            }
            return redirect("custom_admin:send_to_all")

        elif action == "reset_all":
            try:
                User.objects.all().update(coins=0, gems=0)
                request.session["admin_message"] = {"type": "success", "text": "همه سکه/جم‌ها صفر شدند."}
            except Exception as e:
                request.session["admin_message"] = {"type": "error", "text": f"خطا: {e}"}
            return redirect("custom_admin:send_to_all")

    total_users = User.objects.count()
    return render(request, "custom_admin/send_to_all.html", {
        "message": message,
        "total_users": total_users,
    })

# ============================================================
# Admin — Rooms (with categorization + live game info)
# ============================================================
def _room_to_dict(g):
    """Convert Game to dict with all needed info."""
    players = []
    for p in g.players.select_related("user").all():
        players.append({
            "alias": p.user.alias,
            "username": p.user.username,
            "avatar": p.user.avatar_id,
            "score": p.score,
            "ready": p.is_ready,
            "team": p.team,
            "stopped": p.stopped_round,
        })

    active_round = g.rounds.order_by("-number").first()

    # Match description
    match_desc = ""
    if g.mode == "match" and len(players) >= 2:
        match_desc = f"⚔️ {players[0]['alias']} vs {players[1]['alias']}"
    elif g.mode == "team":
        team_a = [p["alias"] for p in players if p["team"] == "A"]
        team_b = [p["alias"] for p in players if p["team"] == "B"]
        a_str = " + ".join(team_a) if team_a else "?"
        b_str = " + ".join(team_b) if team_b else "?"
        match_desc = f"🔵 {a_str} vs 🔴 {b_str}"
    elif g.mode == "bot":
        match_desc = f"🤖 {g.host.alias} vs Bot"
    elif g.mode == "puzzle":
        match_desc = f"🎯 {g.host.alias} (معما)"
    elif g.mode == "group" and len(players) >= 1:
        names = " + ".join(p["alias"] for p in players[:3])
        if len(players) > 3:
            names += f" +{len(players) - 3}"
        match_desc = f"👥 {names}"

    return {
        "obj": g,
        "code": g.code,
        "room_name": g.room_name or "—",
        "mode": g.mode,
        "status": g.status,
        "host": g.host.alias,
        "host_username": g.host.username,
        "players": players,
        "player_count": len(players),
        "max_players": g.max_players,
        "created_at": g.created_at,
        "current_round": active_round.number if active_round else 0,
        "current_letter": active_round.letter if active_round else "—",
        "match_desc": match_desc,
    }


@never_cache
def rooms_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")

    from game.models import Game

    all_rooms = Game.objects.all().order_by("-created_at")

    # Group by status
    in_round = [_room_to_dict(g) for g in all_rooms.filter(status="in_round")[:50]]
    round_result = [_room_to_dict(g) for g in all_rooms.filter(status="round_result")[:30]]
    waiting = [_room_to_dict(g) for g in all_rooms.filter(status="waiting")[:50]]
    finished = [_room_to_dict(g) for g in all_rooms.filter(status="finished")[:50]]

    message = request.session.pop("admin_message", None)

    return render(request, "custom_admin/rooms.html", {
        "in_round": in_round,
        "round_result": round_result,
        "waiting": waiting,
        "finished": finished,
        "count_in_round": all_rooms.filter(status="in_round").count(),
        "count_round_result": all_rooms.filter(status="round_result").count(),
        "count_waiting": all_rooms.filter(status="waiting").count(),
        "count_finished": all_rooms.filter(status="finished").count(),
        "count_total": all_rooms.count(),
        "message": message,
    })


@never_cache
def rooms_active(request):
    """Redirect to main rooms page (everything is there)."""
    return redirect("custom_admin:rooms_list")

@never_cache
def user_notify_toggle_read(request, user_id, notif_id):
    """Toggle read/unread for a single notification."""
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:user_notify", user_id=user_id)

    from social.models import Notification
    try:
        n = Notification.objects.get(id=notif_id, user_id=user_id)
        n.is_read = not n.is_read
        n.save(update_fields=["is_read"])
        status = "خوانده شد" if n.is_read else "نخوانده شد"
        request.session["admin_message"] = {"type": "success", "text": f"اعلان {status}."}
    except Notification.DoesNotExist:
        request.session["admin_message"] = {"type": "error", "text": "اعلان پیدا نشد."}

    return redirect("custom_admin:user_notify", user_id=user_id)


@never_cache
def announcement_toggle_read(request):
    """Toggle read/unread for a broadcast announcement for ALL users."""
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:announcements_list")

    from social.models import Notification

    title = (request.POST.get("title") or "").strip()
    body = (request.POST.get("body") or "").strip()
    url = (request.POST.get("url") or "").strip()
    mark_as = request.POST.get("mark_as", "read")

    if title:
        qs = Notification.objects.filter(type="admin_broadcast", title=title)
        if body:
            qs = qs.filter(body=body)
        if url:
            qs = qs.filter(url=url)

        if mark_as == "read":
            n = qs.update(is_read=True)
            request.session["admin_message"] = {"type": "success", "text": f"{n} اعلان به «خوانده شد» تغییر یافت."}
        elif mark_as == "unread":
            n = qs.update(is_read=False)
            request.session["admin_message"] = {"type": "success", "text": f"{n} اعلان به «نخوانده» تغییر یافت."}

    return redirect("custom_admin:announcements_list")

@never_cache
def announcements_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")

    from social.models import Notification, NotificationRead
    from django.contrib.auth import get_user_model
    from django.db.models import Count, Q
    User = get_user_model()

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "send_all":
            title = (request.POST.get("title") or "").strip()[:100]
            body = (request.POST.get("body") or "").strip()[:300]
            url = (request.POST.get("url") or "").strip()[:200]

            if not title:
                request.session["admin_message"] = {"type": "error", "text": "عنوان الزامی است."}
                return redirect("custom_admin:announcements_list")

            sender = User.objects.filter(is_staff=True).first()
            uids = list(User.objects.values_list("id", flat=True))
            total = 0

            # Create notifications one by one for each user
            for uid in uids:
                Notification.objects.create(
                    user_id=uid,
                    type="admin_broadcast",
                    title=title,
                    body=body,
                    url=url,
                    is_read=False,
                    sender=sender,
                )
                total += 1

            request.session["admin_message"] = {
                "type": "success",
                "text": f"اعلان برای {total} کاربر ارسال شد."
            }
            return redirect("custom_admin:announcements_list")

    # GET — show history
    qs = Notification.objects.filter(type="admin_broadcast").order_by("-created_at")

    seen = set()
    data = []
    for n in qs.iterator(chunk_size=200):
        key = (n.title, n.body or "", n.url or "")
        if key in seen:
            continue
        seen.add(key)

        notif_qs = Notification.objects.filter(
            type="admin_broadcast",
            title=n.title,
            body=n.body or "",
            url=n.url or "",
        )
        total = notif_qs.count()
        read_count = notif_qs.filter(is_read=True).count()
        unread_count = total - read_count

        # Get reader names from NotificationRead
        notif_ids = list(notif_qs.values_list("id", flat=True))
        readers_data = []
        seen_users = set()
        for r in NotificationRead.objects.filter(notification_id__in=notif_ids).select_related("user").order_by("-read_at")[:100]:
            if r.user_id in seen_users:
                continue
            seen_users.add(r.user_id)
            readers_data.append({
                "username": r.user.username,
                "alias": r.user.alias or r.user.username,
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


# ============================================================
# Admin — Support Tickets
# ============================================================
@never_cache
def support_tickets_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    from accounts.models import SupportTicket
    status_filter = (request.GET.get("status") or "").strip()
    qs = SupportTicket.objects.all().select_related("user").order_by("-updated_at")
    if status_filter in ("open", "answered", "closed"):
        qs = qs.filter(status=status_filter)

    data = []
    for t in qs[:200]:
        last_msg = t.messages.order_by("-created_at").first()
        data.append({
            "id": t.id,
            "subject": t.subject,
            "status": t.status,
            "status_display": t.get_status_display(),
            "user_alias": t.user.alias or t.user.username,
            "username": t.user.username,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "message_count": t.message_count(),
            "last_msg": (last_msg.body[:80] + "...") if last_msg and len(last_msg.body) > 80 else (last_msg.body if last_msg else "—"),
        })

    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/support_tickets.html", {
        "tickets": data,
        "status_filter": status_filter,
        "message": message,
        "count_open": SupportTicket.objects.filter(status="open").count(),
        "count_answered": SupportTicket.objects.filter(status="answered").count(),
        "count_closed": SupportTicket.objects.filter(status="closed").count(),
        "count_total": SupportTicket.objects.count(),
    })


@never_cache
def support_ticket_admin(request, ticket_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    from accounts.models import SupportTicket, SupportMessage
    from django.contrib.auth import get_user_model
    User = get_user_model()

    ticket = SupportTicket.objects.filter(id=ticket_id).select_related("user").first()
    if not ticket:
        return redirect("custom_admin:support_tickets_list")

    if request.method == "POST":
        action = request.POST.get("action", "reply")
        if action == "reply":
            body = (request.POST.get("body") or "").strip()[:2000]
            if body:
                admin_user = User.objects.filter(is_staff=True).first()
                SupportMessage.objects.create(
                    ticket=ticket, sender=admin_user, body=body, is_staff=True,
                )
                ticket.status = "answered"
                ticket.save()
                request.session["admin_message"] = {"type": "success", "text": "پاسخ ارسال شد."}
            return redirect("custom_admin:support_ticket_admin", ticket_id=ticket.id)
        elif action == "close":
            ticket.status = "closed"
            ticket.save()
            request.session["admin_message"] = {"type": "success", "text": "تیکت بسته شد."}
            return redirect("custom_admin:support_ticket_admin", ticket_id=ticket.id)
        elif action == "reopen":
            ticket.status = "open"
            ticket.save()
            return redirect("custom_admin:support_ticket_admin", ticket_id=ticket.id)
        elif action == "delete":
            ticket.delete()
            request.session["admin_message"] = {"type": "success", "text": "تیکت حذف شد."}
            return redirect("custom_admin:support_tickets_list")

    msgs_data = [{
        "id": m.id,
        "sender_alias": (m.sender.alias if m.sender else "🤖 پشتیبانی"),
        "body": m.body,
        "is_staff": m.is_staff,
        "created_at": m.created_at,
    } for m in ticket.messages.select_related("sender").all()]

    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/support_ticket_detail.html", {
        "ticket": ticket,
        "ticket_messages": msgs_data,
        "message": message,
    })
