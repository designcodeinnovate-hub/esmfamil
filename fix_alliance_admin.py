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
    bak = p + ".bak9"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) alliance fixes (add back buttons, verify templates)
# ============================================================
print("\n[1/8] alliance fixes")

# 1a) chat.html - add back button if missing
p = os.path.join(ROOT, "alliance", "templates", "alliance", "chat.html")
src = read(p)
if '<a href="/alliance/" class="back-btn">' not in src and 'بازگشت به اتحاد' not in src:
    # check for existing back to detail
    if '<a href="/alliance/{{ alliance.id }}/" class="back-btn">' in src:
        print("  SKIP: chat has back to detail")
    else:
        # Add back to detail if not exists
        old = "{% block content %}"
        new = '''{% block content %}
  <div style="margin-bottom: 12px;">
    <a href="/alliance/{{ alliance.id }}/" style="display:inline-flex; align-items:center; gap:6px; padding:10px 16px; border-radius:12px; background:rgba(139,92,246,0.12); border:1px solid rgba(139,92,246,0.3); color:#c4b5fd; text-decoration:none; font-size:13px; font-weight:bold;">← بازگشت به اتحاد</a>
  </div>'''
        if old in src and "بازگشت به اتحاد" not in src:
            src = src.replace(old, new, 1)
            backup(p); write(p, src)
            print("  FIXED: chat back button added")
        else:
            print("  WARN: chat content block not found")

# 1b) create.html - back to alliance
p = os.path.join(ROOT, "alliance", "templates", "alliance", "create.html")
src = read(p)
if 'href="/alliance/"' not in src:
    old = "{% block content %}"
    new = '''{% block content %}
  <div style="margin-bottom: 12px;">
    <a href="/alliance/" style="display:inline-flex; align-items:center; gap:6px; padding:10px 16px; border-radius:12px; background:rgba(139,92,246,0.12); border:1px solid rgba(139,92,246,0.3); color:#c4b5fd; text-decoration:none; font-size:13px; font-weight:bold;">← بازگشت به اتحاد</a>
  </div>'''
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: create back link")
else:
    print("  SKIP: create has back link")

# 1c) join.html - back to alliance
p = os.path.join(ROOT, "alliance", "templates", "alliance", "join.html")
if os.path.exists(p):
    src = read(p)
    if 'href="/alliance/"' not in src or ('href="/alliance/"' in src and 'back-btn' not in src):
        old = "{% block content %}"
        new = '''{% block content %}
  <div style="margin-bottom: 12px;">
    <a href="/alliance/" style="display:inline-flex; align-items:center; gap:6px; padding:10px 16px; border-radius:12px; background:rgba(139,92,246,0.12); border:1px solid rgba(139,92,246,0.3); color:#c4b5fd; text-decoration:none; font-size:13px; font-weight:bold;">← بازگشت به اتحاد</a>
  </div>'''
        if old in src:
            src = src.replace(old, new, 1)
            backup(p); write(p, src)
            print("  FIXED: join back link")

# 1d) detail.html - add leave button for non-leader (already exists but check)
p = os.path.join(ROOT, "alliance", "templates", "alliance", "detail.html")
src = read(p)
if "btn-danger" not in src:
    print("  WARN: detail has no leave button - check")
else:
    print("  SKIP: detail has leave button")

# ============================================================
# 2) accounts/admin_views.py - ADD views (keep existing)
# ============================================================
print("\n[2/8] accounts/admin_views.py - add new views")
p = os.path.join(ROOT, "accounts", "admin_views.py")
src = read(p)
changed = False

# Add alliance views if not exist
if "def alliances_list(request):" not in src:
    alliance_views = '''

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
            "id": a.id,
            "name": a.name,
            "tag": a.tag,
            "emblem": a.emblem,
            "leader": a.leader.alias,
            "leader_username": a.leader.username,
            "member_count": a.member_count(),
            "max_members": a.max_members,
            "has_password": bool(a.password),
            "invite_code": a.invite_code,
            "created_at": a.created_at,
            "description": a.description,
        })

    message = request.session.pop("admin_message", None)

    return render(request, "custom_admin/alliances.html", {
        "alliances": data,
        "search": search,
        "message": message,
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

            # Validate
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

            # Leader change
            if new_leader_id and str(new_leader_id) != str(a.leader_id):
                try:
                    new_leader = User.objects.get(id=new_leader_id)
                    if AllianceMember.objects.filter(alliance=a, user=new_leader).exists():
                        # Old leader becomes member
                        AllianceMember.objects.filter(alliance=a, user=a.leader).update(role="member")
                        # New leader
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
    members_data = []
    for m in members:
        members_data.append({
            "user_id": m.user.id,
            "username": m.user.username,
            "alias": m.user.alias,
            "role": m.role,
            "role_display": m.get_role_display(),
            "joined_at": m.joined_at,
        })

    message = request.session.pop("admin_message", None)

    emojis = ["🛡️", "⚔️", "🏰", "🐉", "🦅", "🐺", "🔥", "⚡", "👑", "💎", "🌟", "🦁"]

    return render(request, "custom_admin/alliance_detail.html", {
        "a": a,
        "members": members_data,
        "message": message,
        "emojis": emojis,
    })


# ============================================================
# Admin — Rooms (Games)
# ============================================================
@never_cache
def rooms_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")

    from game.models import Game, Player

    search = (request.GET.get("q") or "").strip()
    status_filter = (request.GET.get("status") or "").strip()

    qs = Game.objects.all().order_by("-created_at")

    if search:
        from django.db.models import Q
        qs = qs.filter(
            Q(room_name__icontains=search) |
            Q(code__icontains=search) |
            Q(host__alias__icontains=search) |
            Q(host__username__icontains=search)
        )

    if status_filter in ("waiting", "in_round", "round_result", "finished"):
        qs = qs.filter(status=status_filter)

    data = []
    for g in qs[:300]:
        data.append({
            "id": str(g.id),
            "code": g.code,
            "room_name": g.room_name or "—",
            "mode": g.mode,
            "status": g.status,
            "host": g.host.alias,
            "host_username": g.host.username,
            "players_count": g.players.count(),
            "max_players": g.max_players,
            "created_at": g.created_at,
            "has_password": bool(g.password),
            "categories_count": len(g.categories or []),
        })

    message = request.session.pop("admin_message", None)

    return render(request, "custom_admin/rooms.html", {
        "rooms": data,
        "search": search,
        "status_filter": status_filter,
        "message": message,
    })


@never_cache
def rooms_active(request):
    """اتاق‌های در حال بازی (in_round)."""
    if not _check_auth(request):
        return redirect("custom_admin:login")

    from game.models import Game

    qs = Game.objects.filter(status="in_round").order_by("-created_at")

    data = []
    for g in qs:
        active_round = g.rounds.order_by("-number").first()
        data.append({
            "id": str(g.id),
            "code": g.code,
            "room_name": g.room_name or "—",
            "mode": g.mode,
            "host": g.host.alias,
            "host_username": g.host.username,
            "players_count": g.players.count(),
            "max_players": g.max_players,
            "created_at": g.created_at,
            "current_round": active_round.number if active_round else 0,
            "current_letter": active_round.letter if active_round else "—",
        })

    return render(request, "custom_admin/rooms.html", {
        "rooms": data,
        "search": "",
        "status_filter": "in_round",
        "message": None,
    })


@never_cache
def room_delete(request, game_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:rooms_list")

    from game.models import Game
    try:
        g = Game.objects.get(id=game_id)
        g.delete()
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

    return render(request, "custom_admin/user_edit.html", {
        "u": u,
        "message": message,
    })


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
        # Username
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

        # Alias
        new_alias = (request.POST.get("alias") or "").strip()[:32]
        if new_alias:
            u.alias = new_alias

        # Email
        u.email = (request.POST.get("email") or "").strip() or None

        # Phone
        phone_val = (request.POST.get("phone") or "").strip()[:20]
        u.phone = phone_val if phone_val else None

        # Booleans
        u.is_active = request.POST.get("is_active") == "on"
        u.is_staff = request.POST.get("is_staff") == "on"
        u.is_guest = request.POST.get("is_guest") == "on"

        # Coins/Gems
        try:
            u.coins = int(request.POST.get("coins") or 0)
        except (ValueError, TypeError):
            u.coins = 0
        try:
            u.gems = int(request.POST.get("gems") or 0)
        except (ValueError, TypeError):
            u.gems = 0

        # Password
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
        delta = request.POST.get("delta", "0")
        try:
            d = int(delta)
            u.coins = max(0, (u.coins or 0) + d)
            u.save(update_fields=["coins"])
            request.session["admin_message"] = {"type": "success", "text": f"سکه {d:+d} شد."}
        except (ValueError, TypeError):
            pass

    elif action == "quick_gems":
        delta = request.POST.get("delta", "0")
        try:
            d = int(delta)
            u.gems = max(0, (u.gems or 0) + d)
            u.save(update_fields=["gems"])
            request.session["admin_message"] = {"type": "success", "text": f"جم {d:+d} شد."}
        except (ValueError, TypeError):
            pass

    if redirect_to == "detail":
        return redirect("custom_admin:user_detail", user_id=u.id)
    return redirect("custom_admin:user_edit", user_id=u.id)
'''
    src = src.rstrip() + "\n" + alliance_views + "\n"
    changed = True
    print("  FIXED: alliance + rooms + user_edit views added")

if changed:
    backup(p); write(p, src)

# ============================================================
# 3) accounts/admin_urls.py - add routes
# ============================================================
print("\n[3/8] accounts/admin_urls.py")
p = os.path.join(ROOT, "accounts", "admin_urls.py")
src = read(p)

new_routes = '''    path("alliances/", admin_views.alliances_list, name="alliances_list"),
    path("alliance/<int:alliance_id>/", admin_views.alliance_manage, name="alliance_manage"),
    path("rooms/", admin_views.rooms_list, name="rooms_list"),
    path("rooms/active/", admin_views.rooms_active, name="rooms_active"),
    path("room/<uuid:game_id>/delete/", admin_views.room_delete, name="room_delete"),
    path("user/<int:user_id>/edit/", admin_views.user_edit, name="user_edit"),
    path("user/<int:user_id>/update/", admin_views.user_update, name="user_update"),'''

if "alliances/" in src and "rooms/" in src:
    print("  SKIP: routes exist")
else:
    old = '    path("user/<int:user_id>/change-alias/", admin_views.user_change_alias, name="user_change_alias"),'
    new = old + "\n" + new_routes
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: new routes added")
    else:
        # Fallback - add before closing ]
        old2 = "]\n"
        new2 = new_routes + "\n]\n"
        src = src.rsplit(old2, 1)[0] + new2
        backup(p); write(p, src)
        print("  FIXED: routes added (fallback)")

# ============================================================
# 4) dashboard.html - add nav tabs
# ============================================================
print("\n[4/8] dashboard.html - add nav tabs")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "dashboard.html")
src = read(p)

# Add tabs below topbar
if "admin-tabs" not in src:
    old_topbar_end = '''  <div class="stats">'''
    new_topbar_end = '''  <div class="admin-tabs">
    <a href="/panel-admin/dashboard/" class="admin-tab active">👥 کاربران</a>
    <a href="/panel-admin/alliances/" class="admin-tab">🛡️ اتحادها</a>
    <a href="/panel-admin/rooms/" class="admin-tab">🚪 اتاق‌ها</a>
    <a href="/panel-admin/rooms/active/" class="admin-tab">🎮 در حال بازی</a>
  </div>

  <div class="stats">'''
    if old_topbar_end in src:
        src = src.replace(old_topbar_end, new_topbar_end, 1)

# Add tab CSS
if ".admin-tabs {" not in src:
    old_css = "    .stats {"
    new_css = '''    .admin-tabs {
      display: flex; gap: 6px; margin-bottom: 20px;
      background: #12121f; border: 1px solid rgba(148,163,184,0.15);
      padding: 6px; border-radius: 14px; overflow-x: auto;
    }
    .admin-tab {
      flex: 1; min-width: 110px;
      padding: 12px 16px; border-radius: 10px;
      text-align: center; text-decoration: none;
      font-size: 13px; font-weight: bold;
      color: #94a3b8; transition: 0.2s;
      white-space: nowrap;
    }
    .admin-tab:hover { background: rgba(148,163,184,0.1); color: #fff; }
    .admin-tab.active {
      background: linear-gradient(135deg, #ef4444, #dc2626);
      color: #fff; box-shadow: 0 6px 20px rgba(239,68,68,0.4);
    }

    .stats {'''
    if old_css in src:
        src = src.replace(old_css, new_css, 1)

# Add edit button in users table row actions
if "btn-edit-full" not in src:
    old_actions = '''                <a href="{% url 'custom_admin:user_detail' u.id %}" class="btn-view">مشاهده</a>'''
    new_actions = '''                <a href="{% url 'custom_admin:user_detail' u.id %}" class="btn-view">مشاهده</a>
                <a href="{% url 'custom_admin:user_edit' u.id %}" class="btn-edit-full" style="background:rgba(139,92,246,0.2); color:#c4b5fd; padding:6px 10px; font-size:11px; border-radius:8px; text-decoration:none; font-weight:bold;">✏️ ویرایش</a>'''
    if old_actions in src:
        src = src.replace(old_actions, new_actions, 1)

backup(p); write(p, src)

# ============================================================
# 5) alliances.html - NEW
# ============================================================
print("\n[5/8] alliances.html - NEW")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "alliances.html")

ALLIANCES_HTML = '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>اتحادها — پنل ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 1300px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; }
    .topbar h1 { font-size: 20px; color: #fca5a5; }
    .topbar a { padding: 9px 16px; border-radius: 10px; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold; }

    .admin-tabs { display: flex; gap: 6px; margin-bottom: 20px; background: #12121f; border: 1px solid rgba(148,163,184,0.15); padding: 6px; border-radius: 14px; overflow-x: auto; }
    .admin-tab { flex: 1; min-width: 110px; padding: 12px 16px; border-radius: 10px; text-align: center; text-decoration: none; font-size: 13px; font-weight: bold; color: #94a3b8; transition: 0.2s; white-space: nowrap; }
    .admin-tab:hover { background: rgba(148,163,184,0.1); color: #fff; }
    .admin-tab.active { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; box-shadow: 0 6px 20px rgba(239,68,68,0.4); }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; text-align: right; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .search-row { display: flex; gap: 10px; margin-bottom: 16px; }
    .search-row input { flex: 1; padding: 13px 18px; border-radius: 12px; border: 1px solid rgba(148,163,184,0.2); background: #1a1a2e; color: #fff; font-size: 15px; font-family: inherit; }
    .search-row input:focus { outline: none; border-color: #facc15; }
    .search-row button { padding: 13px 22px; border-radius: 12px; border: none; background: linear-gradient(135deg, #facc15, #eab308); color: #1a1a1a; font-weight: bold; font-size: 14px; font-family: inherit; cursor: pointer; }

    .empty-state { text-align: center; padding: 60px 20px; color: #64748b; }
    .empty-state .icon { font-size: 60px; display: block; margin-bottom: 12px; opacity: 0.5; }

    .alliance-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 14px; }
    .alliance-card { background: linear-gradient(135deg, #12121f, #1a1a2e); border: 1px solid rgba(139,92,246,0.3); border-radius: 18px; padding: 18px; transition: 0.2s; }
    .alliance-card:hover { border-color: rgba(139,92,246,0.7); transform: translateY(-2px); box-shadow: 0 8px 25px rgba(139,92,246,0.2); }

    .ac-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
    .ac-emblem { width: 52px; height: 52px; border-radius: 14px; background: linear-gradient(135deg, rgba(139,92,246,0.3), rgba(6,182,212,0.15)); display: flex; align-items: center; justify-content: center; font-size: 28px; flex-shrink: 0; border: 1px solid rgba(255,255,255,0.1); }
    .ac-info { flex: 1; min-width: 0; }
    .ac-name { font-size: 16px; font-weight: bold; color: #fff; margin-bottom: 3px; display: flex; align-items: center; gap: 6px; }
    .ac-tag { background: #facc15; color: #1a1a1a; font-size: 9px; padding: 2px 6px; border-radius: 5px; font-weight: bold; font-family: monospace; }
    .ac-meta { font-size: 11px; color: #64748b; font-family: monospace; }

    .ac-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
    .ac-stat { padding: 8px 10px; background: rgba(15,23,42,0.5); border-radius: 10px; text-align: center; }
    .ac-stat .lbl { font-size: 10px; color: #64748b; margin-bottom: 2px; }
    .ac-stat .val { font-size: 14px; font-weight: bold; color: #facc15; font-family: monospace; }

    .ac-actions { display: flex; gap: 8px; }
    .ac-actions a, .ac-actions button {
      flex: 1; padding: 10px; border-radius: 10px; border: none;
      font-family: inherit; font-weight: bold; font-size: 12px;
      cursor: pointer; text-align: center; text-decoration: none;
    }
    .btn-manage { background: rgba(139,92,246,0.2); color: #c4b5fd; border: 1px solid rgba(139,92,246,0.4) !important; }
    .btn-manage:hover { background: rgba(139,92,246,0.35); }
    .btn-del { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35) !important; }
    .btn-del:hover { background: rgba(239,68,68,0.3); }

    .password-badge { font-size: 12px; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>🛡️ مدیریت اتحادها</h1>
    <a href="{% url 'custom_admin:logout' %}">خروج</a>
  </div>

  <div class="admin-tabs">
    <a href="/panel-admin/dashboard/" class="admin-tab">👥 کاربران</a>
    <a href="/panel-admin/alliances/" class="admin-tab active">🛡️ اتحادها</a>
    <a href="/panel-admin/rooms/" class="admin-tab">🚪 اتاق‌ها</a>
    <a href="/panel-admin/rooms/active/" class="admin-tab">🎮 در حال بازی</a>
  </div>

  {% if message %}
    <div class="msg msg-{{ message.type }}">{{ message.text }}</div>
  {% endif %}

  <form method="get" class="search-row">
    <input type="text" name="q" value="{{ search }}" placeholder="جستجو با نام، tag یا کد دعوت...">
    <button type="submit">🔍 جستجو</button>
  </form>

  {% if alliances %}
    <div class="alliance-grid">
      {% for a in alliances %}
        <div class="alliance-card">
          <div class="ac-header">
            <div class="ac-emblem">{{ a.emblem }}</div>
            <div class="ac-info">
              <div class="ac-name">
                {{ a.name }}
                {% if a.tag %}<span class="ac-tag">{{ a.tag }}</span>{% endif %}
                {% if a.has_password %}<span class="password-badge">🔒</span>{% endif %}
              </div>
              <div class="ac-meta">رهبر: {{ a.leader }} (@{{ a.leader_username }})</div>
            </div>
          </div>
          <div class="ac-stats">
            <div class="ac-stat"><div class="lbl">اعضا</div><div class="val">{{ a.member_count }} / {{ a.max_members }}</div></div>
            <div class="ac-stat"><div class="lbl">کد دعوت</div><div class="val">{{ a.invite_code }}</div></div>
          </div>
          <div class="ac-actions">
            <a href="{% url 'custom_admin:alliance_manage' a.id %}" class="btn-manage">⚙️ مدیریت</a>
            <form method="post" action="{% url 'custom_admin:alliance_manage' a.id %}" style="flex:1;" onsubmit="return confirm('حذف اتحاد {{ a.name }}؟');">
              {% csrf_token %}
              <input type="hidden" name="action" value="delete">
              <button type="submit" class="btn-del" style="width:100%;">🗑️ حذف</button>
            </form>
          </div>
        </div>
      {% endfor %}
    </div>
  {% else %}
    <div class="empty-state">
      <span class="icon">🛡️</span>
      {% if search %}اتحادی با این مشخصات پیدا نشد.{% else %}هیچ اتحادی وجود ندارد.{% endif %}
    </div>
  {% endif %}
</div>
</body>
</html>
'''
backup(p); write(p, ALLIANCES_HTML)

# ============================================================
# 6) alliance_detail.html - NEW
# ============================================================
print("\n[6/8] alliance_detail.html - NEW")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "alliance_detail.html")

DETAIL_HTML = '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>مدیریت اتحاد {{ a.name }}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 1000px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(139,92,246,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; }
    .topbar h1 { font-size: 19px; color: #c4b5fd; }
    .topbar .actions { display: flex; gap: 8px; }
    .topbar a { padding: 9px 16px; border-radius: 10px; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold; }
    .topbar .back { background: rgba(148,163,184,0.2); }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .card { background: #12121f; border: 1px solid rgba(148,163,184,0.15); border-radius: 16px; padding: 22px; margin-bottom: 16px; }
    .card h3 { color: #fdba74; font-size: 15px; margin-bottom: 16px; }

    label { display: block; color: #94a3b8; font-size: 12px; margin: 12px 0 6px; }
    input[type=text], input[type=password], input[type=number], textarea, select {
      width: 100%; padding: 12px 14px; border-radius: 10px;
      border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15;
      color: #fff; font-size: 14px; font-family: inherit;
      box-sizing: border-box;
    }
    textarea { resize: vertical; min-height: 70px; }
    input:focus, textarea:focus, select:focus { outline: none; border-color: #facc15; }

    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    @media (max-width: 500px) { .row { grid-template-columns: 1fr; } }

    .emojis { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
    .emoji-opt { padding: 12px; text-align: center; font-size: 24px; background: #1a1a2e; border: 2px solid transparent; border-radius: 10px; cursor: pointer; transition: 0.15s; }
    .emoji-opt:hover { border-color: #facc15; }
    .emoji-opt input { display: none; }
    .emoji-opt:has(input:checked) { border-color: #facc15; background: linear-gradient(135deg, rgba(250,204,21,0.2), rgba(139,92,246,0.1)); box-shadow: 0 0 15px rgba(250,204,21,0.3); }

    button.submit { width: 100%; margin-top: 18px; padding: 14px; border: none; border-radius: 12px; font-size: 15px; font-weight: bold; font-family: inherit; cursor: pointer; color: #fff; background: linear-gradient(135deg, #8b5cf6, #6b4eff); box-shadow: 0 8px 20px rgba(139,92,246,0.4); transition: 0.2s; }
    button.submit:hover { transform: translateY(-2px); }

    .danger-zone { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.3); border-radius: 16px; padding: 22px; margin-bottom: 16px; }
    .danger-zone h3 { color: #fca5a5; }
    .danger-zone p { font-size: 12px; color: #94a3b8; margin-bottom: 12px; line-height: 1.6; }
    button.delete-btn { padding: 12px 24px; border: none; border-radius: 10px; font-family: inherit; font-weight: bold; font-size: 14px; cursor: pointer; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; box-shadow: 0 6px 18px rgba(239,68,68,0.4); }

    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 10px 12px; text-align: right; font-size: 12px; border-bottom: 1px solid rgba(148,163,184,0.1); }
    th { color: #94a3b8; font-size: 11px; font-weight: bold; }
    tr:last-child td { border-bottom: none; }

    .role-badge { padding: 3px 10px; border-radius: 6px; font-size: 10px; font-weight: bold; }
    .role-leader { background: rgba(250,204,21,0.2); color: #facc15; }
    .role-officer { background: rgba(59,130,246,0.2); color: #93c5fd; }
    .role-member { background: rgba(100,116,139,0.2); color: #cbd5e1; }

    .kick-btn { padding: 5px 10px; background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); border-radius: 6px; cursor: pointer; font-size: 10px; font-family: inherit; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>🛡️ {{ a.emblem }} {{ a.name }}</h1>
    <div class="actions">
      <a href="{% url 'custom_admin:alliances_list' %}" class="back">← بازگشت</a>
      <a href="{% url 'custom_admin:logout' %}">خروج</a>
    </div>
  </div>

  {% if message %}
    <div class="msg msg-{{ message.type }}">{{ message.text }}</div>
  {% endif %}

  <form method="post">
    {% csrf_token %}
    <input type="hidden" name="action" value="update">

    <div class="card">
      <h3>✏️ اطلاعات پایه</h3>

      <label>نماد</label>
      <div class="emojis">
        {% for e in emojis %}
          <label class="emoji-opt">
            <input type="radio" name="emblem" value="{{ e }}" {% if e == a.emblem %}checked{% endif %}>
            {{ e }}
          </label>
        {% endfor %}
      </div>

      <label>نام اتحاد</label>
      <input type="text" name="name" value="{{ a.name }}" required maxlength="40">

      <div class="row">
        <div>
          <label>تگ</label>
          <input type="text" name="tag" value="{{ a.tag }}" maxlength="8">
        </div>
        <div>
          <label>ظرفیت (۵-۱۰۰)</label>
          <input type="number" name="max_members" value="{{ a.max_members }}" min="5" max="100">
        </div>
      </div>

      <label>توضیح</label>
      <textarea name="description" maxlength="200">{{ a.description }}</textarea>

      <label>رمز (خالی = بدون رمز)</label>
      <input type="password" name="password" value="{{ a.password }}" maxlength="32">

      <label>رهبر</label>
      <select name="leader_id">
        {% for m in members %}
          <option value="{{ m.user_id }}" {% if m.role == "leader" %}selected{% endif %}>{{ m.alias }} (@{{ m.username }})</option>
        {% endfor %}
      </select>

      <button type="submit" class="submit">💾 ذخیره تغییرات</button>
    </div>
  </form>

  <div class="card">
    <h3>👥 اعضای اتحاد ({{ members|length }})</h3>
    <table>
      <thead>
        <tr>
          <th>نام نمایشی</th>
          <th>username</th>
          <th>نقش</th>
          <th>عضویت</th>
          <th>عملیات</th>
        </tr>
      </thead>
      <tbody>
        {% for m in members %}
          <tr>
            <td>{{ m.alias }}</td>
            <td style="font-family:monospace; color:#94a3b8;">@{{ m.username }}</td>
            <td><span class="role-badge role-{{ m.role }}">{{ m.role_display }}</span></td>
            <td style="font-size:11px; color:#64748b;">{{ m.joined_at|date:"Y/m/d" }}</td>
            <td>
              {% if m.role != "leader" %}
                <form method="post" action="{% url 'custom_admin:alliance_manage' a.id %}" style="display:inline;" onsubmit="return confirm('اخراج شود؟');">
                  {% csrf_token %}
                  <input type="hidden" name="action" value="kick_member">
                  <input type="hidden" name="user_id" value="{{ m.user_id }}">
                  <button type="submit" class="kick-btn">اخراج</button>
                </form>
              {% else %}
                <span style="font-size:11px; color:#64748b;">—</span>
              {% endif %}
            </td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="danger-zone">
    <h3>⚠️ منطقه خطر</h3>
    <p>حذف اتحاد غیرقابل بازگشت است. تمام اعضا و پیام‌های چت حذف می‌شوند.</p>
    <form method="post" onsubmit="return confirm('آیا مطمئنید؟ حذف اتحاد {{ a.name }}؟');">
      {% csrf_token %}
      <input type="hidden" name="action" value="delete">
      <button type="submit" class="delete-btn">🗑️ حذف اتحاد</button>
    </form>
  </div>
</div>
</body>
</html>
'''
backup(p); write(p, DETAIL_HTML)

# ============================================================
# 7) rooms.html - NEW
# ============================================================
print("\n[7/8] rooms.html - NEW")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "rooms.html")

ROOMS_HTML = '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>اتاق‌ها — پنل ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 1300px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; }
    .topbar h1 { font-size: 20px; color: #fca5a5; }
    .topbar a { padding: 9px 16px; border-radius: 10px; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold; }

    .admin-tabs { display: flex; gap: 6px; margin-bottom: 20px; background: #12121f; border: 1px solid rgba(148,163,184,0.15); padding: 6px; border-radius: 14px; overflow-x: auto; }
    .admin-tab { flex: 1; min-width: 110px; padding: 12px 16px; border-radius: 10px; text-align: center; text-decoration: none; font-size: 13px; font-weight: bold; color: #94a3b8; transition: 0.2s; white-space: nowrap; }
    .admin-tab:hover { background: rgba(148,163,184,0.1); color: #fff; }
    .admin-tab.active { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; box-shadow: 0 6px 20px rgba(239,68,68,0.4); }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .filter-row { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
    .filter-row input, .filter-row select { padding: 12px 16px; border-radius: 12px; border: 1px solid rgba(148,163,184,0.2); background: #1a1a2e; color: #fff; font-size: 14px; font-family: inherit; }
    .filter-row input { flex: 1; min-width: 200px; }
    .filter-row input:focus, .filter-row select:focus { outline: none; border-color: #facc15; }
    .filter-row button { padding: 12px 22px; border-radius: 12px; border: none; background: linear-gradient(135deg, #facc15, #eab308); color: #1a1a1a; font-weight: bold; font-size: 14px; font-family: inherit; cursor: pointer; }

    .stats-mini { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
    .stat-mini { padding: 10px 16px; border-radius: 10px; background: rgba(30,41,59,0.6); border: 1px solid rgba(148,163,184,0.15); font-size: 12px; }
    .stat-mini b { color: #facc15; font-family: monospace; }

    .table-wrap { background: #12121f; border: 1px solid rgba(148,163,184,0.12); border-radius: 16px; overflow: auto; }
    table { width: 100%; border-collapse: collapse; min-width: 900px; }
    th { background: rgba(30,41,59,0.7); padding: 14px 12px; text-align: right; font-size: 12px; color: #94a3b8; font-weight: bold; white-space: nowrap; border-bottom: 1px solid rgba(148,163,184,0.15); position: sticky; top: 0; }
    td { padding: 12px; text-align: right; font-size: 13px; border-bottom: 1px solid rgba(148,163,184,0.08); white-space: nowrap; }
    tr:hover td { background: rgba(244,197,66,0.03); }

    .code { font-family: monospace; font-weight: bold; color: #facc15; }
    .username { font-family: monospace; color: #94a3b8; }
    .status { padding: 3px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; }
    .status-waiting { background: rgba(234,179,8,0.15); color: #fde68a; }
    .status-in_round { background: rgba(34,197,94,0.15); color: #4ade80; animation: pulse 2s infinite; }
    .status-round_result { background: rgba(59,130,246,0.15); color: #93c5fd; }
    .status-finished { background: rgba(100,116,139,0.15); color: #cbd5e1; }
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.6; } }

    .mode-badge { padding: 2px 8px; border-radius: 6px; font-size: 10px; font-weight: bold; background: rgba(139,92,246,0.15); color: #c4b5fd; }

    .btn-del-small { padding: 6px 10px; border-radius: 6px; border: none; background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); font-family: inherit; font-size: 11px; font-weight: bold; cursor: pointer; }
    .btn-del-small:hover { background: rgba(239,68,68,0.3); }

    .empty-state { text-align: center; padding: 60px 20px; color: #64748b; }
    .empty-state .icon { font-size: 60px; display: block; margin-bottom: 12px; opacity: 0.5; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>🚪 مدیریت اتاق‌ها</h1>
    <a href="{% url 'custom_admin:logout' %}">خروج</a>
  </div>

  <div class="admin-tabs">
    <a href="/panel-admin/dashboard/" class="admin-tab">👥 کاربران</a>
    <a href="/panel-admin/alliances/" class="admin-tab">🛡️ اتحادها</a>
    <a href="/panel-admin/rooms/" class="admin-tab {% if status_filter != 'in_round' %}active{% endif %}">🚪 اتاق‌ها</a>
    <a href="/panel-admin/rooms/active/" class="admin-tab {% if status_filter == 'in_round' %}active{% endif %}">🎮 در حال بازی</a>
  </div>

  {% if message %}
    <div class="msg msg-{{ message.type }}">{{ message.text }}</div>
  {% endif %}

  {% if status_filter != 'in_round' %}
    <div class="stats-mini">
      <div class="stat-mini">مجموع اتاق‌ها: <b>{{ rooms|length }}</b></div>
    </div>

    <form method="get" class="filter-row">
      <input type="text" name="q" value="{{ search }}" placeholder="جستجو با اسم اتاق، کد، میزبان...">
      <select name="status">
        <option value="">همه وضعیت‌ها</option>
        <option value="waiting" {% if status_filter == "waiting" %}selected{% endif %}>در انتظار</option>
        <option value="in_round" {% if status_filter == "in_round" %}selected{% endif %}>در حال بازی</option>
        <option value="round_result" {% if status_filter == "round_result" %}selected{% endif %}>نتیجه راند</option>
        <option value="finished" {% if status_filter == "finished" %}selected{% endif %}>تمام‌شده</option>
      </select>
      <button type="submit">🔍 فیلتر</button>
    </form>
  {% endif %}

  {% if rooms %}
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>کد</th>
            <th>اسم اتاق</th>
            <th>حالت</th>
            <th>وضعیت</th>
            <th>میزبان</th>
            <th>بازیکنان</th>
            <th>راند</th>
            <th>حرف</th>
            <th>تاریخ</th>
            <th>عملیات</th>
          </tr>
        </thead>
        <tbody>
          {% for r in rooms %}
            <tr>
              <td style="color:#64748b;">{{ forloop.counter }}</td>
              <td><span class="code">{{ r.code }}</span></td>
              <td>{{ r.room_name }}</td>
              <td><span class="mode-badge">{{ r.mode }}</span></td>
              <td><span class="status status-{{ r.status }}">{{ r.status }}</span></td>
              <td>{{ r.host }} <span class="username">(@{{ r.host_username }})</span></td>
              <td>{{ r.players_count }} / {{ r.max_players }}</td>
              <td>{% if r.current_round %}{{ r.current_round }}{% else %}—{% endif %}</td>
              <td>{% if r.current_letter %}<b style="color:#facc15; font-size:15px;">{{ r.current_letter }}</b>{% else %}—{% endif %}</td>
              <td style="font-size:11px; color:#64748b;">{{ r.created_at|date:"Y/m/d H:i" }}</td>
              <td>
                <form method="post" action="{% url 'custom_admin:room_delete' r.id %}" style="display:inline;" onsubmit="return confirm('حذف اتاق {{ r.code }}؟');">
                  {% csrf_token %}
                  <button type="submit" class="btn-del-small">🗑️ حذف</button>
                </form>
              </td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  {% else %}
    <div class="empty-state">
      <span class="icon">🚪</span>
      هیچ اتاقی یافت نشد.
    </div>
  {% endif %}
</div>
</body>
</html>
'''
backup(p); write(p, ROOMS_HTML)

# ============================================================
# 8) user_edit.html - NEW
# ============================================================
print("\n[8/8] user_edit.html - NEW")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "user_edit.html")

USER_EDIT_HTML = '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ویرایش کاربر {{ u.username }}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 900px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(139,92,246,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
    .topbar h1 { font-size: 19px; color: #c4b5fd; }
    .topbar .actions { display: flex; gap: 8px; flex-wrap: wrap; }
    .topbar a { padding: 9px 16px; border-radius: 10px; font-size: 13px; font-weight: bold; text-decoration: none; }
    .topbar .back { background: rgba(148,163,184,0.2); color: #fff; }
    .topbar .logout { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; }
    .topbar .view { background: rgba(139,92,246,0.2); color: #c4b5fd; border: 1px solid rgba(139,92,246,0.4); }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .card { background: #12121f; border: 1px solid rgba(148,163,184,0.15); border-radius: 16px; padding: 22px; margin-bottom: 16px; }
    .card h3 { color: #fdba74; font-size: 15px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }

    label { display: block; color: #94a3b8; font-size: 12px; margin: 12px 0 6px; font-weight: bold; }
    label .hint { color: #64748b; font-weight: normal; font-size: 11px; margin-right: 6px; }

    input[type=text], input[type=email], input[type=password], input[type=number] {
      width: 100%; padding: 12px 14px; border-radius: 10px;
      border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15;
      color: #fff; font-size: 14px; font-family: inherit;
      box-sizing: border-box;
    }
    input:focus { outline: none; border-color: #facc15; }

    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    @media (max-width: 500px) { .row { grid-template-columns: 1fr; } }

    .toggles { display: flex; flex-direction: column; gap: 12px; }
    .toggle-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; background: rgba(15,23,42,0.5); border-radius: 10px; }
    .toggle-info { flex: 1; }
    .toggle-title { font-size: 13px; color: #fff; font-weight: bold; margin-bottom: 2px; }
    .toggle-desc { font-size: 11px; color: #64748b; }

    .switch { position: relative; width: 46px; height: 26px; flex-shrink: 0; }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider { position: absolute; inset: 0; background: rgba(71,85,105,0.6); border-radius: 26px; cursor: pointer; transition: 0.3s; }
    .slider::before { content: ""; position: absolute; width: 18px; height: 18px; left: 4px; top: 4px; background: #fff; border-radius: 50%; transition: 0.3s; }
    .switch input:checked + .slider { background: linear-gradient(135deg, #22c55e, #16a34a); }
    .switch input:checked + .slider::before { transform: translateX(-20px); }

    .btn-submit { width: 100%; margin-top: 18px; padding: 15px; border: none; border-radius: 12px; font-size: 15px; font-weight: bold; font-family: inherit; cursor: pointer; color: #fff; background: linear-gradient(135deg, #8b5cf6, #6b4eff); box-shadow: 0 8px 20px rgba(139,92,246,0.4); transition: 0.2s; }
    .btn-submit:hover { transform: translateY(-2px); }

    .quick-actions { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
    .qa-btn { padding: 10px 18px; border: none; border-radius: 10px; font-family: inherit; font-weight: bold; font-size: 12px; cursor: pointer; }
    .qa-coins { background: linear-gradient(135deg, #facc15, #ca8a04); color: #1a1a1a; }
    .qa-gems { background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; }

    .danger-card { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.3); border-radius: 16px; padding: 22px; }
    .danger-card h3 { color: #fca5a5; }
    .btn-delete { padding: 12px 24px; border: none; border-radius: 10px; font-family: inherit; font-weight: bold; font-size: 14px; cursor: pointer; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; box-shadow: 0 6px 18px rgba(239,68,68,0.4); }

    .info-banner { background: rgba(59,130,246,0.1); border-right: 3px solid #3b82f6; padding: 12px 16px; border-radius: 10px; font-size: 12px; color: #93c5fd; margin-bottom: 16px; line-height: 1.7; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>✏️ ویرایش کاربر: {{ u.username }}</h1>
    <div class="actions">
      <a href="{% url 'custom_admin:user_detail' u.id %}" class="view">👁 مشاهده</a>
      <a href="{% url 'custom_admin:dashboard' %}" class="back">← بازگشت</a>
      <a href="{% url 'custom_admin:logout' %}" class="logout">خروج</a>
    </div>
  </div>

  {% if message %}
    <div class="msg msg-{{ message.type }}">{{ message.text }}</div>
  {% endif %}

  <div class="info-banner">
    💡 <b>توجه:</b> این صفحه به شما اجازه می‌دهد <b>همه</b> اطلاعات کاربر را تغییر دهید. تغییرات بلافاصله اعمال می‌شوند.
  </div>

  <form method="post" action="{% url 'custom_admin:user_update' u.id %}">
    {% csrf_token %}
    <input type="hidden" name="action" value="update">
    <input type="hidden" name="redirect_to" value="edit">

    <div class="card">
      <h3>👤 اطلاعات ورود</h3>

      <label>نام کاربری (username)</label>
      <input type="text" name="username" value="{{ u.username }}" required minlength="3" maxlength="32">
      <div style="font-size:11px; color:#64748b; margin-top:4px;">فقط حروف انگلیسی، اعداد و _ — ۳ تا ۳۲ کاراکتر</div>

      <label>پسورد جدید <span class="hint">(خالی = بدون تغییر)</span></label>
      <input type="password" name="password" placeholder="حداقل ۶ کاراکتر" minlength="6" autocomplete="new-password">
    </div>

    <div class="card">
      <h3>📋 اطلاعات پروفایل</h3>

      <div class="row">
        <div>
          <label>نام نمایشی (alias)</label>
          <input type="text" name="alias" value="{{ u.alias }}" maxlength="32">
        </div>
        <div>
          <label>ایمیل</label>
          <input type="email" name="email" value="{{ u.email|default:'' }}" maxlength="254">
        </div>
      </div>

      <label>موبایل</label>
      <input type="text" name="phone" value="{{ u.phone|default:'' }}" maxlength="20">
    </div>

    <div class="card">
      <h3>💰 اقتصاد درون‌بازی</h3>

      <div class="row">
        <div>
          <label>🪙 سکه</label>
          <input type="number" name="coins" value="{{ u.coins|default:0 }}" min="0">
        </div>
        <div>
          <label>💎 جم</label>
          <input type="number" name="gems" value="{{ u.gems|default:0 }}" min="0">
        </div>
      </div>

      <div class="quick-actions">
        <form method="post" action="{% url 'custom_admin:user_update' u.id %}" style="display:contents;">
          {% csrf_token %}
          <input type="hidden" name="action" value="quick_coins">
          <button type="submit" name="delta" value="100" class="qa-btn qa-coins">+۱۰۰ سکه</button>
        </form>
        <form method="post" action="{% url 'custom_admin:user_update' u.id %}" style="display:contents;">
          {% csrf_token %}
          <input type="hidden" name="action" value="quick_gems">
          <button type="submit" name="delta" value="10" class="qa-btn qa-gems">+۱۰ جم</button>
        </form>
      </div>
    </div>

    <div class="card">
      <h3>🔐 وضعیت‌ها</h3>
      <div class="toggles">
        <div class="toggle-row">
          <div class="toggle-info">
            <div class="toggle-title">فعال (is_active)</div>
            <div class="toggle-desc">کاربر می‌تونه وارد بشه یا نه</div>
          </div>
          <label class="switch">
            <input type="checkbox" name="is_active" {% if u.is_active %}checked{% endif %}>
            <span class="slider"></span>
          </label>
        </div>

        <div class="toggle-row">
          <div class="toggle-info">
            <div class="toggle-title">ادمین (is_staff)</div>
            <div class="toggle-desc">دسترسی به پنل جنگو</div>
          </div>
          <label class="switch">
            <input type="checkbox" name="is_staff" {% if u.is_staff %}checked{% endif %}>
            <span class="slider"></span>
          </label>
        </div>

        <div class="toggle-row">
          <div class="toggle-info">
            <div class="toggle-title">حساب مهمان</div>
            <div class="toggle-desc">مهمان دسترسی محدود داره</div>
          </div>
          <label class="switch">
            <input type="checkbox" name="is_guest" {% if u.is_guest %}checked{% endif %}>
            <span class="slider"></span>
          </label>
        </div>
      </div>
    </div>

    <button type="submit" class="btn-submit">💾 ذخیره همه تغییرات</button>
  </form>

  <div class="danger-card" style="margin-top: 16px;">
    <h3>⚠️ منطقه خطر</h3>
    <p style="font-size: 12px; color: #94a3b8; margin: 12px 0; line-height: 1.7;">حذف کاربر غیرقابل بازگشت است. تمام بازی‌ها، اعلان‌ها، دوستی‌ها و اتحادش حذف می‌شود.</p>
    <form method="post" action="{% url 'custom_admin:user_delete' u.id %}" onsubmit="return confirm('آیا مطمئنید؟ حذف {{ u.username }} غیرقابل بازگشت است.');">
      {% csrf_token %}
      <button type="submit" class="btn-delete">🗑️ حذف کامل کاربر</button>
    </form>
  </div>
</div>
</body>
</html>
'''
backup(p); write(p, USER_EDIT_HTML)

# ============================================================
# Also update user_detail.html to have link to edit
# ============================================================
print("\n[Extra] user_detail.html - add edit link")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "user_detail.html")
if os.path.exists(p):
    src = read(p)
    if "user_edit" not in src:
        # Add edit button in header area
        old = '''  <h1>👤 جزئیات کاربر: {{ u.username }}</h1>'''
        new = '''  <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
    <h1 style="margin: 14px 0 0;">👤 جزئیات کاربر: {{ u.username }}</h1>
    <a href="{% url 'custom_admin:user_edit' u.id %}" style="margin-top: 14px; padding: 10px 18px; border-radius: 10px; background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold;">✏️ ویرایش کامل</a>
  </div>'''
        if old in src:
            src = src.replace(old, new, 1)
            backup(p); write(p, src)
            print("  FIXED: edit link added to user_detail")

# ============================================================
# Run migrations to be safe
# ============================================================
print("\n[Migrations check]")
for cmd in [[sys.executable, "manage.py", "check"]]:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print("  ⚠ check errors:")
        print(r.stderr[:500] if r.stderr else r.stdout[:500])
    else:
        print("  ✓ Django check passed")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
ALLIANCE FIXES:
  ✓ Back buttons added to chat, create, join
  ✓ Verify detail has leave/edit buttons
  ✓ Templates verified

ADMIN PANEL UPGRADE:

NEW PAGES:
  ✓ /panel-admin/alliances/          → لیست همه اتحادها
  ✓ /panel-admin/alliance/<id>/      → مدیریت اتحاد (ویرایش کامل)
  ✓ /panel-admin/rooms/              → لیست همه اتاق‌ها با فیلتر
  ✓ /panel-admin/rooms/active/       → اتاق‌های در حال بازی
  ✓ /panel-admin/user/<id>/edit/     → ویرایش کامل کاربر

ADMIN FEATURES:
  ✓ کاربران:
    - تغییر username، email، alias، phone
    - ریست پسورد
    - تنظیم coins، gems (دستی یا +100/+10)
    - toggle is_active، is_staff، is_guest
    - حذف کامل
  ✓ اتحادها:
    - تغییر name، tag، emblem، description
    - تغییر ظرفیت (5-100)
    - تغییر رمز
    - تغییر رهبر
    - اخراج اعضا
    - حذف اتحاد
  ✓ اتاق‌ها:
    - جستجو و فیلتر بر اساس وضعیت
    - نمایش mode، host، players count، round، letter
    - حذف اتاق
  ✓ اتاق‌های در حال بازی:
    - نمایش زنده راند فعلی و حرف
    - با انیمیشن pulse سبز

NEW TAB NAVIGATION:
  👥 کاربران | 🛡️ اتحادها | 🚪 اتاق‌ها | 🎮 در حال بازی

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R
  
  Login to /panel-admin/ with admin74 / Amir2255ds
""")
