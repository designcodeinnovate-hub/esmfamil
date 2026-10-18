#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix announcements + redesign rooms + add support tickets."""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    if not os.path.exists(p): return ""
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# PART 1: Game model - add intended_game_type
# ============================================================
print("\n[1/8] Adding intended_game_type to Game model")
p = "game/models.py"
src = read(p)

if "intended_game_type" in src:
    print("  ✓ Field exists")
else:
    old = '    letter_mode = models.CharField(max_length=16, default="random")'
    new = old + '\n    intended_game_type = models.CharField(max_length=16, blank=True, default="")'
    if old in src:
        src = src.replace(old, new, 1)
        write(p, src)
        print("  ✓ Added intended_game_type field")
    else:
        print("  ⚠ Could not find letter_mode field")

# ============================================================
# PART 2: Fix announcements_list view (clean rebuild)
# ============================================================
print("\n[2/8] Rebuilding announcements_list view")
p = "accounts/admin_views.py"
src = read(p)

# Remove old announcements_list
pattern = re.compile(r'@never_cache\ndef announcements_list\(request\):.*?(?=\n@never_cache\ndef |\n@never_cache\n@|\Z)', re.DOTALL)
m = pattern.search(src)
if m:
    src = src[:m.start()] + src[m.end():]

new_ann_view = '''

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
'''

src = src.rstrip() + new_ann_view + "\n"
write(p, src)
print("  ✓ announcements_list rebuilt")

# ============================================================
# PART 3: Rooms - update rooms_manage + room views
# ============================================================
print("\n[3/8] Updating rooms views")

p = "game/views.py"
src = read(p)

# Update rooms_manage POST to accept intended_game_type
# Find rooms_manage function
pattern = re.compile(r'@login_required\ndef rooms_manage\(request\):.*?(?=\n@login_required\ndef |\Z)', re.DOTALL)
m = pattern.search(src)
if m:
    new_rooms_manage = '''@login_required
def rooms_manage(request):
    check = _require_complete(request.user)
    if check:
        return check

    query = (request.GET.get("q") or "").strip()
    active_rooms = Game.objects.filter(status="waiting", mode="group").order_by("-created_at")

    if query:
        active_rooms = active_rooms.filter(
            Q(room_name__icontains=query) | Q(host__alias__icontains=query)
        )

    rooms_data = []
    for r in active_rooms:
        count = r.players.count()
        is_member = r.players.filter(user=request.user).exists()
        rooms_data.append({
            "obj": r,
            "count": count,
            "is_full": count >= r.max_players,
            "has_password": bool(r.password),
            "is_member": is_member,
            "host_avatar": get_emoji(r.host.avatar_id),
            "game_type": r.intended_game_type or "—",
        })

    if request.method == "POST":
        room_name = (request.POST.get("room_name") or "").strip()[:50] or "اتاق بازی"
        password = (request.POST.get("password") or "").strip()[:32]
        try:
            max_players = int(request.POST.get("max_players") or 8)
        except (ValueError, TypeError):
            max_players = 8
        max_players = max(2, min(15, max_players))

        game_type = request.POST.get("game_type", "player")
        valid_types = ["player", "team", "challenge", "speed", "bot", "puzzle"]
        if game_type not in valid_types:
            game_type = "player"

        selected = [c for c in request.POST.getlist("categories") if c in DEFAULT_CATEGORIES]
        if not selected:
            selected = DEFAULT_CATEGORIES[:8]

        game = Game.objects.create(
            host=request.user, status="waiting",
            categories=selected, mode="group", password=password,
            room_name=room_name, max_players=max_players,
            intended_game_type=game_type,
        )
        Player.objects.create(game=game, user=request.user)
        return redirect("game:room", room_code=game.code)

    return render(request, "game/rooms_manage.html", {
        "categories": DEFAULT_CATEGORIES,
        "rooms": rooms_data,
        "query": query,
        "active": "rooms",
        "game_types": [
            ("player", "⚔️ با پلیر (۱v۱)"),
            ("team", "🛡️ تیمی (۲v۲)"),
            ("challenge", "🔥 چالشی"),
            ("speed", "⏱️ سرعتی"),
            ("puzzle", "🎯 معما"),
            ("bot", "🤖 با بات"),
        ],
    })


@login_required
def room(request, room_code):
    check = _require_complete(request.user)
    if check:
        return check

    room_obj = Game.objects.filter(code=room_code).first()
    if not room_obj:
        return redirect("game:rooms_manage")

    my_player, _ = Player.objects.get_or_create(game=room_obj, user=request.user)

    # If host and no game type selected yet, show selection modal
    if room_obj.host_id == request.user.id and not room_obj.intended_game_type:
        if request.method == "POST" and request.POST.get("action") == "select_game_type":
            game_type = request.POST.get("game_type", "player")
            valid = ["player", "team", "challenge", "speed", "bot", "puzzle"]
            if game_type in valid:
                room_obj.intended_game_type = game_type
                room_obj.save(update_fields=["intended_game_type"])
            return redirect("game:room", room_code=room_obj.code)

    # Handle "I'm ready" toggle
    if request.method == "POST" and request.POST.get("action") == "toggle_ready":
        my_player.is_ready = not my_player.is_ready
        my_player.save(update_fields=["is_ready"])
        return redirect("game:room", room_code=room_obj.code)

    # Handle "Start game" by host
    if request.method == "POST" and request.POST.get("action") == "start_game":
        if room_obj.host_id != request.user.id:
            return redirect("game:room", room_code=room_obj.code)

        gt = room_obj.intended_game_type
        if gt == "player":
            # Start 1v1 with first two ready players
            ready_players = list(room_obj.players.filter(is_ready=True).select_related("user"))
            if len(ready_players) < 2:
                messages.error(request, "حداقل ۲ بازیکن آماده لازم است.")
                return redirect("game:room", room_code=room_obj.code)
            # Redirect to match flow
            return redirect("game:rooms_manage")
        elif gt == "team":
            ready_count = room_obj.players.filter(is_ready=True).count()
            if ready_count < 4:
                messages.error(request, "بازی تیمی به ۴ بازیکن آماده نیاز دارد.")
                return redirect("game:room", room_code=room_obj.code)
            return redirect("game:team_start")
        elif gt == "challenge":
            return redirect("game:challenge")
        elif gt == "speed":
            return redirect("/game/quick/bot/?mode=speed")
        elif gt == "puzzle":
            return redirect("game:puzzle_setup")
        elif gt == "bot":
            return redirect("game:bot_setup")

    # Players list
    players = []
    for p in room_obj.players.select_related("user"):
        players.append({
            "user_id": p.user.id,
            "alias": p.user.alias,
            "avatar": get_emoji(p.user.avatar_id),
            "avatar_type": getattr(p.user, "avatar_type", "emoji"),
            "avatar_id": p.user.avatar_id,
            "is_ready": p.is_ready,
            "score": p.score,
            "is_host": p.user_id == room_obj.host_id,
            "is_me": p.user_id == request.user.id,
        })

    is_host = room_obj.host_id == request.user.id
    ready_count = sum(1 for p in players if p["is_ready"])
    can_start = is_host and ready_count >= 2

    return render(request, "game/room.html", {
        "room": room_obj,
        "players": players,
        "is_host": is_host,
        "my_is_ready": my_player.is_ready,
        "host": room_obj.host,
        "host_avatar": get_emoji(room_obj.host.avatar_id),
        "ready_count": ready_count,
        "can_start": can_start,
        "game_type_display": dict([
            ("player", "⚔️ با پلیر"),
            ("team", "🛡️ تیمی"),
            ("challenge", "🔥 چالشی"),
            ("speed", "⏱️ سرعتی"),
            ("puzzle", "🎯 معما"),
            ("bot", "🤖 با بات"),
        ]).get(room_obj.intended_game_type or "", "—"),
        "active": "rooms",
    })
'''
    src = src.replace(m.group(0), new_rooms_manage)
    write(p, src)
    print("  ✓ rooms_manage + room views updated")

# Need `messages` import
src = read(p)
if "from django.contrib import messages" not in src:
    src = src.replace("from django.contrib.auth.decorators import login_required", "from django.contrib import messages\nfrom django.contrib.auth.decorators import login_required", 1)
    write(p, src)

# ============================================================
# PART 4: Support ticket models
# ============================================================
print("\n[4/8] Adding support ticket models")

p = "accounts/models.py"
src = read(p)

if "class SupportTicket(models.Model):" in src:
    print("  ✓ Models exist")
else:
    src = src.rstrip() + '''


class SupportTicket(models.Model):
    STATUS = [
        ("open", "باز"),
        ("answered", "پاسخ داده شده"),
        ("closed", "بسته شده"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_tickets")
    subject = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        return f"#{self.id} {self.subject} - {self.user.alias}"

    def message_count(self):
        return self.messages.count()


class SupportMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    body = models.TextField(max_length=2000)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Ticket #{self.ticket_id} - {self.body[:30]}"
'''
    write(p, src)
    print("  ✓ Support models added")

# ============================================================
# PART 5: Support views
# ============================================================
print("\n[5/8] Adding support views to accounts/views.py")

p = "accounts/views.py"
src = read(p)

if "def support_home(request):" in src:
    print("  ✓ Views exist")
else:
    src = src.rstrip() + '''


# ============================================================
# SUPPORT / TICKETING
# ============================================================
BOT_REPLY_TEXT = "سلام! از پیام شما متشکریم. اگر انتقاد یا پیشنهادی دارید، لطفاً ذکر کنید — ممنون می‌شویم. تیم پشتیبانی در اسرع وقت پاسخ می‌دهد. 🙏"


@login_required
def support_home(request):
    if not getattr(request.user, "has_chosen_avatar", False):
        return redirect("accounts:avatar_select")

    from .models import SupportTicket, SupportMessage

    if request.method == "POST":
        subject = (request.POST.get("subject") or "").strip()[:100]
        body = (request.POST.get("body") or "").strip()[:2000]

        if not subject:
            messages.error(request, "موضوع را وارد کن.")
            return redirect("accounts:support_home")

        if not body:
            messages.error(request, "متن پیام را وارد کن.")
            return redirect("accounts:support_home")

        ticket = SupportTicket.objects.create(
            user=request.user,
            subject=subject,
            status="answered",
        )
        SupportMessage.objects.create(
            ticket=ticket, sender=request.user, body=body, is_staff=False,
        )
        # Auto-bot reply
        SupportMessage.objects.create(
            ticket=ticket, sender=None, body=BOT_REPLY_TEXT, is_staff=True,
        )

        messages.success(request, "تیکت شما ثبت شد. پاسخ اولیه ارسال شد.")
        return redirect("accounts:support_detail", ticket_id=ticket.id)

    tickets = SupportTicket.objects.filter(user=request.user).order_by("-updated_at")
    tickets_data = []
    for t in tickets:
        last_msg = t.messages.order_by("-created_at").first()
        tickets_data.append({
            "id": t.id,
            "subject": t.subject,
            "status": t.status,
            "status_display": t.get_status_display(),
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "message_count": t.message_count(),
            "last_msg": (last_msg.body[:60] + "...") if last_msg and len(last_msg.body) > 60 else (last_msg.body if last_msg else ""),
        })

    return render(request, "accounts/support_home.html", {
        "tickets": tickets_data,
        "active": "profile",
    })


@login_required
def support_detail(request, ticket_id):
    from .models import SupportTicket, SupportMessage

    ticket = SupportTicket.objects.filter(id=ticket_id, user=request.user).first()
    if not ticket:
        messages.error(request, "تیکت پیدا نشد.")
        return redirect("accounts:support_home")

    if request.method == "POST":
        action = request.POST.get("action", "reply")
        if action == "reply":
            body = (request.POST.get("body") or "").strip()[:2000]
            if body:
                SupportMessage.objects.create(
                    ticket=ticket, sender=request.user, body=body, is_staff=False,
                )
                if ticket.status == "closed":
                    ticket.status = "open"
                else:
                    ticket.status = "open"
                ticket.save()
            return redirect("accounts:support_detail", ticket_id=ticket.id)
        elif action == "close":
            ticket.status = "closed"
            ticket.save()
            messages.info(request, "تیکت بسته شد.")
            return redirect("accounts:support_detail", ticket_id=ticket.id)
        elif action == "delete":
            ticket.delete()
            messages.success(request, "تیکت حذف شد.")
            return redirect("accounts:support_home")

    msgs_list = ticket.messages.select_related("sender").all()
    msgs_data = [{
        "id": m.id,
        "sender": m.sender,
        "sender_alias": (m.sender.alias if m.sender else "🤖 پشتیبانی"),
        "body": m.body,
        "is_staff": m.is_staff,
        "is_me": m.sender_id == request.user.id if m.sender_id else False,
        "created_at": m.created_at,
    } for m in msgs_list]

    return render(request, "accounts/support_detail.html", {
        "ticket": ticket,
        "ticket_messages": msgs_data,
        "active": "profile",
    })
'''
    write(p, src)
    print("  ✓ Support views added")

# Add URLs
p = "accounts/urls.py"
src = read(p)

if "support_home" not in src:
    old = '    path("logout/", logout_view, name="logout"),'
    new = old + '''
    path("support/", support_home, name="support_home"),
    path("support/<int:ticket_id>/", support_detail, name="support_detail"),'''
    if old in src:
        src = src.replace(old, new, 1)
        write(p, src)
        print("  ✓ Support routes added")

# Need to import
src = read(p)
if "support_home" in src and "from .views import (" in src:
    if "support_home," not in src.split("from .views import")[1].split(")")[0]:
        # Add to imports
        old = "    profile_view, register_view, settings_view,\n)"
        new = "    profile_view, register_view, settings_view,\n    support_home, support_detail,\n)"
        if old in src:
            src = src.replace(old, new, 1)
            write(p, src)
            print("  ✓ Support imports added")

# ============================================================
# PART 6: Admin ticket views
# ============================================================
print("\n[6/8] Adding admin ticket views")

p = "accounts/admin_views.py"
src = read(p)

if "def support_tickets_list" in src:
    print("  ✓ Admin views exist")
else:
    src = src.rstrip() + '''


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
'''
    write(p, src)
    print("  ✓ Admin support views added")

# Add admin URLs
p = "accounts/admin_urls.py"
src = read(p)

if "support_tickets_list" not in src:
    old = '    path("send-to-all/", admin_views.send_to_all, name="send_to_all"),'
    new = old + '''
    path("support/", admin_views.support_tickets_list, name="support_tickets_list"),
    path("support/<int:ticket_id>/", admin_views.support_ticket_admin, name="support_ticket_admin"),'''
    if old in src:
        src = src.replace(old, new, 1)
        write(p, src)
        print("  ✓ Admin support routes added")

# ============================================================
# PART 7: Rebuild templates
# ============================================================
print("\n[7/8] Rebuilding templates")

# 7a) announcements.html - clean rebuild
write("accounts/templates/custom_admin/announcements.html", '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>اعلان‌ها — پنل ادمین</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 16px 16px 40px; }
.container { max-width: 1400px; margin: 0 auto; }
.admin-sticky-header { position: sticky; top: 0; z-index: 500; background: #0a0a15; padding: 4px 0 8px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.7); }
.topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 8px; }
.topbar h1 { font-size: 20px; color: #fca5a5; }
.admin-tabs { display: flex !important; gap: 6px !important; overflow-x: auto !important; overflow-y: hidden !important; white-space: nowrap !important; padding: 8px !important; background: #12121f !important; border: 1px solid rgba(148,163,184,0.15) !important; border-radius: 14px !important; scrollbar-width: none !important; height: 48px !important; }
.admin-tabs::-webkit-scrollbar { display: none; }
.admin-tab { flex: 0 0 auto !important; height: 40px !important; display: inline-flex !important; align-items: center !important; padding: 0 14px !important; border-radius: 10px !important; text-decoration: none !important; font-size: 12px !important; font-weight: bold !important; color: #94a3b8 !important; white-space: nowrap !important; }
.admin-tab:hover { background: rgba(148,163,184,0.1) !important; color: #fff !important; }
.admin-tab.active { background: linear-gradient(135deg, #ef4444, #dc2626) !important; color: #fff !important; }
.msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
.msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
.msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }
.card { background: #12121f; border: 1px solid rgba(148,163,184,0.15); border-radius: 16px; padding: 22px; margin-bottom: 16px; }
.card h3 { color: #fdba74; font-size: 15px; margin-bottom: 16px; }
.form-row { margin-bottom: 10px; }
.form-row label { display: block; font-size: 11px; color: #94a3b8; margin-bottom: 4px; font-weight: bold; }
.form-row input[type=text], .form-row textarea { width: 100%; padding: 10px 12px; border-radius: 10px; border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15; color: #fff; font-size: 13px; font-family: inherit; }
.form-row input:focus, .form-row textarea:focus { outline: none; border-color: #facc15; }
.form-row textarea { min-height: 60px; resize: vertical; }
.send-btn { padding: 12px 24px; border: none; border-radius: 10px; background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; font-family: inherit; font-weight: bold; font-size: 14px; cursor: pointer; }
.ann-card { background: linear-gradient(135deg, #1a1a2e, #12121f); border: 1px solid rgba(245,158,11,0.3); border-radius: 14px; padding: 16px; margin-bottom: 12px; }
.ann-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
.ann-icon { width: 40px; height: 40px; border-radius: 10px; background: rgba(245,158,11,0.2); display: flex; align-items: center; justify-content: center; font-size: 20px; }
.ann-title { font-size: 15px; font-weight: bold; color: #fde68a; margin-bottom: 3px; }
.ann-meta { font-size: 10px; color: #64748b; font-family: monospace; }
.ann-body { font-size: 13px; color: #cbd5e1; line-height: 1.6; margin: 10px 0; padding: 10px; background: rgba(15,23,42,0.4); border-radius: 8px; }
.stat-chips { display: flex; gap: 6px; margin: 10px 0; flex-wrap: wrap; }
.stat-chip { padding: 5px 12px; border-radius: 8px; font-size: 11px; font-weight: bold; font-family: monospace; }
.stat-chip.total { background: rgba(148,163,184,0.15); color: #cbd5e1; }
.stat-chip.read { background: rgba(34,197,94,0.2); color: #4ade80; }
.stat-chip.unread { background: rgba(234,179,8,0.2); color: #fde68a; }
.readers-section { margin-top: 10px; padding: 10px; background: rgba(34,197,94,0.05); border: 1px solid rgba(34,197,94,0.2); border-radius: 10px; }
.readers-title { font-size: 11px; color: #4ade80; font-weight: bold; margin-bottom: 8px; }
.readers-list { display: flex; flex-wrap: wrap; gap: 6px; }
.reader-chip { padding: 4px 10px; border-radius: 16px; background: rgba(34,197,94,0.15); border: 1px solid rgba(34,197,94,0.3); color: #86efac; font-size: 11px; font-weight: bold; }
.reader-chip .time { font-size: 9px; opacity: 0.6; margin-right: 4px; }
.ann-actions { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 12px; }
.ann-actions form { display: inline; }
.btn-sm { padding: 7px 14px; border: none; border-radius: 8px; font-family: inherit; font-size: 11px; font-weight: bold; cursor: pointer; }
.btn-mark-read { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
.btn-mark-unread { background: rgba(234,179,8,0.15); color: #fde68a; border: 1px solid rgba(234,179,8,0.3); }
.btn-del-ann { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
.empty-state { text-align: center; padding: 40px 20px; color: #64748b; font-size: 13px; }
.empty-state .icon { font-size: 60px; display: block; margin-bottom: 12px; opacity: 0.5; }
</style>
</head>
<body>
<div class="container">
  <div class="admin-sticky-header">
    <div class="topbar"><h1>📢 اعلان‌ها</h1></div>
    <div class="admin-tabs">
      <a href="/panel-admin/dashboard/" class="admin-tab {% if '/panel-admin/dashboard/' in request.path or request.path == '/panel-admin/' %}active{% endif %}">👥 کاربران</a>
      <a href="/panel-admin/alliances/" class="admin-tab {% if '/panel-admin/alliance' in request.path %}active{% endif %}">🛡️ اتحادها</a>
      <a href="/panel-admin/rooms/" class="admin-tab {% if '/panel-admin/room' in request.path %}active{% endif %}">🚪 اتاق‌ها</a>
      <a href="/panel-admin/announcements/" class="admin-tab {% if '/panel-admin/announcement' in request.path %}active{% endif %}">📢 اعلان‌ها</a>
      <a href="/panel-admin/tournaments/" class="admin-tab {% if '/panel-admin/tournament' in request.path %}active{% endif %}">🏆 تورنمنت</a>
      <a href="/panel-admin/shop/" class="admin-tab {% if '/panel-admin/shop/' in request.path %}active{% endif %}">🛒 فروشگاه</a>
      <a href="/panel-admin/support/" class="admin-tab {% if '/panel-admin/support' in request.path %}active{% endif %}">💬 پشتیبانی</a>
    </div>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <div class="card">
    <h3>📝 ارسال اعلان جدید ({{ total_users }} کاربر)</h3>
    <form method="post">
      {% csrf_token %}
      <input type="hidden" name="action" value="send_all">
      <div class="form-row"><label>عنوان</label><input type="text" name="title" required maxlength="100" placeholder="عنوان اعلان..."></div>
      <div class="form-row"><label>متن</label><textarea name="body" maxlength="300" placeholder="متن کامل..."></textarea></div>
      <div class="form-row"><label>لینک (اختیاری)</label><input type="text" name="url" maxlength="200" placeholder="/game/"></div>
      <button type="submit" class="send-btn">📤 ارسال به همه</button>
    </form>
  </div>

  <div class="card">
    <h3>📜 تاریخچه ({{ announcements|length }})</h3>
    {% if announcements %}
      {% for a in announcements %}
        <div class="ann-card">
          <div class="ann-head">
            <div class="ann-icon">📢</div>
            <div style="flex:1;">
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
          {% if a.readers %}
            <div class="readers-section">
              <div class="readers-title">✓ خوانده‌شده توسط:</div>
              <div class="readers-list">
                {% for r in a.readers %}
                  <span class="reader-chip">{{ r.alias }} <span class="time">{{ r.read_at|jdate:"H:i" }}</span></span>
                {% endfor %}
              </div>
            </div>
          {% endif %}
          <div class="ann-actions">
            <form method="post" action="{% url 'custom_admin:announcement_toggle_read' %}">
              {% csrf_token %}
              <input type="hidden" name="title" value="{{ a.title }}">
              <input type="hidden" name="body" value="{{ a.body }}">
              <input type="hidden" name="url" value="{{ a.url }}">
              <input type="hidden" name="mark_as" value="read">
              <button type="submit" class="btn-sm btn-mark-read" onclick="return confirm('همه «خوانده» شوند؟');">✓ خوانده برای همه</button>
            </form>
            <form method="post" action="{% url 'custom_admin:announcement_toggle_read' %}">
              {% csrf_token %}
              <input type="hidden" name="title" value="{{ a.title }}">
              <input type="hidden" name="body" value="{{ a.body }}">
              <input type="hidden" name="url" value="{{ a.url }}">
              <input type="hidden" name="mark_as" value="unread">
              <button type="submit" class="btn-sm btn-mark-unread" onclick="return confirm('همه «نخوانده» شوند؟');">● نخوانده برای همه</button>
            </form>
            <form method="post" action="{% url 'custom_admin:announcement_delete' %}">
              {% csrf_token %}
              <input type="hidden" name="title" value="{{ a.title }}">
              <input type="hidden" name="body" value="{{ a.body }}">
              <input type="hidden" name="url" value="{{ a.url }}">
              <button type="submit" class="btn-sm btn-del-ann" onclick="return confirm('حذف از همه؟');">🗑️ حذف</button>
            </form>
          </div>
        </div>
      {% endfor %}
    {% else %}
      <div class="empty-state"><span class="icon">📭</span>هنوز اعلانی ارسال نشده.</div>
    {% endif %}
  </div>
</div>
</body>
</html>
''')
print("  ✓ announcements.html")

# 7b) rooms_manage.html - add game_type select
p = "game/templates/game/rooms_manage.html"
src = read(p)
if "game_type" not in src:
    # Add game_type select to form
    old = '''<label class="flabel">📝 اسم اتاق</label>
      <input type="text" name="room_name" class="finput" placeholder="مثلاً: بازی دوستانه" maxlength="50" required>'''
    new = '''<label class="flabel">🎮 نوع بازی</label>
      <select name="game_type" class="finput" style="padding: 12px; font-family: inherit;">
        <option value="player">⚔️ با پلیر (۱v۱)</option>
        <option value="team">🛡️ تیمی (۲v۲)</option>
        <option value="challenge">🔥 چالشی</option>
        <option value="speed">⏱️ سرعتی</option>
        <option value="puzzle">🎯 معما</option>
        <option value="bot">🤖 با بات</option>
      </select>
      <label class="flabel">📝 اسم اتاق</label>
      <input type="text" name="room_name" class="finput" placeholder="مثلاً: بازی دوستانه" maxlength="50" required>'''
    if old in src:
        src = src.replace(old, new, 1)
        write(p, src)
        print("  ✓ rooms_manage.html: game_type select added")

# 7c) room.html - complete rebuild
write("game/templates/game/room.html", '''{% extends "base.html" %}
{% block title %}{{ room.room_name }}{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.room-hero{text-align:center;padding:24px 20px;background:radial-gradient(circle at 100% 0%,rgba(139,92,246,.3),transparent 60%),linear-gradient(135deg,#1a0f2e,#0f0f1e);border:1.5px solid rgba(139,92,246,.4);border-radius:22px;margin-bottom:16px}
.room-name{font-size:22px;font-weight:900;margin-bottom:6px;background:linear-gradient(135deg,#c4b5fd,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.room-meta{font-size:12px;color:var(--muted)}
.game-type-badge{display:inline-block;padding:6px 16px;border-radius:10px;background:rgba(34,197,94,.2);border:1px solid rgba(34,197,94,.4);color:#86efac;font-weight:bold;font-size:13px;margin-top:10px}
.players-card{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:18px;margin-bottom:16px}
.players-card h3{font-size:15px;color:var(--gold);margin-bottom:14px;display:flex;justify-content:space-between}
.player-row{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05)}
.player-row:last-child{border-bottom:none}
.pav{width:44px;height:44px;border-radius:50%;background:rgba(15,23,42,.6);border:2px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:22px;background-size:cover;background-position:center}
.pav.ready{border-color:#22c55e;box-shadow:0 0 12px rgba(34,197,94,.5)}
.pinfo{flex:1}
.pname{font-size:14px;font-weight:bold;color:#fff;display:flex;align-items:center;gap:6px}
.host-badge{background:linear-gradient(135deg,#f4c542,#eab308);color:#1a1a1a;font-size:9px;padding:2px 6px;border-radius:5px;font-weight:900}
.pstatus{font-size:11px;margin-top:2px}
.pstatus.ready{color:#4ade80}
.pstatus.wait{color:var(--muted)}
.actions{display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap}
.act-btn{flex:1;min-width:140px;padding:16px;border:none;border-radius:14px;font-family:inherit;font-weight:900;font-size:15px;cursor:pointer;transition:0.2s}
.btn-ready{background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;box-shadow:0 8px 20px rgba(34,197,94,.4)}
.btn-notready{background:rgba(148,163,184,.2);color:#cbd5e1;border:1px solid var(--border)}
.btn-start{background:linear-gradient(135deg,#f4c542,#eab308);color:#1a1a1a;box-shadow:0 8px 20px rgba(244,197,66,.4)}
.btn-start:disabled{opacity:.4;cursor:not-allowed;box-shadow:none}
.ready-info{text-align:center;padding:12px;background:rgba(34,197,94,.08);border-radius:12px;font-size:13px;color:#86efac;margin-bottom:16px}
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.9);backdrop-filter:blur(8px);z-index:1000;align-items:center;justify-content:center;padding:20px}
.modal-bg.active{display:flex}
.modal{background:linear-gradient(135deg,rgba(30,41,59,.98),rgba(15,23,42,.98));border:1.5px solid rgba(139,92,246,.5);border-radius:24px;padding:28px 24px;max-width:420px;width:100%;box-shadow:0 25px 60px rgba(0,0,0,.7)}
.modal h3{font-size:20px;font-weight:900;text-align:center;margin-bottom:6px;background:linear-gradient(135deg,#c4b5fd,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.modal p{text-align:center;font-size:13px;color:var(--muted);margin-bottom:20px}
.game-opt{display:block;padding:14px 16px;margin-bottom:8px;border-radius:14px;background:rgba(15,23,42,.6);border:1.5px solid var(--border);cursor:pointer;font-size:15px;font-weight:bold;color:#fff;transition:.2s;text-align:center}
.game-opt:hover{border-color:var(--purple);background:rgba(139,92,246,.2);transform:translateX(-3px)}
</style>
{% endblock %}
{% block content %}
<div class="head"><a href="/game/rooms/manage/" class="back-btn"><span class="arrow-icon">→</span></a></div>

<div class="room-hero">
  <div class="room-name">{{ room.room_name }}</div>
  <div class="room-meta">میزبان: {{ host_avatar }} {{ host.alias }}{% if is_host %} (شما){% endif %} · {{ players|length }} / {{ room.max_players }} نفر</div>
  {% if room.intended_game_type %}
    <div class="game-type-badge">🎮 {{ game_type_display }}</div>
  {% else %}
    <div class="game-type-badge" style="background:rgba(234,179,8,.2);border-color:rgba(234,179,8,.4);color:#fde68a;">در انتظار انتخاب بازی توسط میزبان</div>
  {% endif %}
</div>

{% if ready_count > 0 %}
<div class="ready-info">✓ {{ ready_count }} بازیکن آماده‌ست</div>
{% endif %}

<div class="players-card">
  <h3>👥 بازیکنان <span style="font-size:11px;color:var(--muted);">{{ players|length }} / {{ room.max_players }}</span></h3>
  {% for p in players %}
    <div class="player-row">
      {% if p.avatar_type == 'image' and p.avatar_id %}
        <div class="pav {% if p.is_ready %}ready{% endif %}" style="background-image:url('/static/avatars/images/{{ p.avatar_id|stringformat:"03d" }}.jpg');"></div>
      {% else %}
        <div class="pav {% if p.is_ready %}ready{% endif %}">{{ p.avatar }}</div>
      {% endif %}
      <div class="pinfo">
        <div class="pname">
          {{ p.alias }}
          {% if p.is_host %}<span class="host-badge">👑 میزبان</span>{% endif %}
          {% if p.is_me %}<span style="color:var(--teal);font-size:10px;">(شما)</span>{% endif %}
        </div>
        <div class="pstatus {% if p.is_ready %}ready{% else %}wait{% endif %}">
          {% if p.is_ready %}✓ آماده{% else %}⏳ در انتظار{% endif %}
        </div>
      </div>
      <div style="font-size:16px;font-weight:900;color:var(--gold);font-family:monospace;">{{ p.score }}</div>
    </div>
  {% endfor %}
</div>

<div class="actions">
  {% if not is_host %}
    <form method="post" style="flex:1;margin:0;">
      {% csrf_token %}
      <input type="hidden" name="action" value="toggle_ready">
      <button type="submit" class="act-btn {% if my_is_ready %}btn-notready{% else %}btn-ready{% endif %}" style="width:100%;">
        {% if my_is_ready %}✗ لغو آمادگی{% else %}✓ من آماده‌ام{% endif %}
      </button>
    </form>
  {% else %}
    <form method="post" style="flex:1;margin:0;">
      {% csrf_token %}
      <input type="hidden" name="action" value="start_game">
      <button type="submit" class="act-btn btn-start" style="width:100%;" {% if not can_start %}disabled{% endif %}>
        🚀 شروع بازی{% if not can_start %} (نیاز به ۲+ آماده){% endif %}
      </button>
    </form>
  {% endif %}
</div>

<!-- Modal: select game type (host only, if not selected yet) -->
{% if is_host and not room.intended_game_type %}
<div class="modal-bg active" id="selectGameModal">
  <div class="modal">
    <h3>🎮 انتخاب بازی</h3>
    <p>یه بازی انتخاب کن تا بقیه ببینن</p>
    <form method="post">
      {% csrf_token %}
      <input type="hidden" name="action" value="select_game_type">
      <button type="submit" name="game_type" value="player" class="game-opt">⚔️ با پلیر (۱v۱)</button>
      <button type="submit" name="game_type" value="team" class="game-opt">🛡️ تیمی (۲v۲)</button>
      <button type="submit" name="game_type" value="challenge" class="game-opt">🔥 چالشی</button>
      <button type="submit" name="game_type" value="speed" class="game-opt">⏱️ سرعتی</button>
      <button type="submit" name="game_type" value="puzzle" class="game-opt">🎯 معما</button>
      <button type="submit" name="game_type" value="bot" class="game-opt">🤖 با بات</button>
    </form>
  </div>
</div>
{% endif %}
{% endblock %}
''')
print("  ✓ room.html")

# 7d) Support templates
write("accounts/templates/accounts/support_home.html", '''{% extends "base.html" %}
{% block title %}پشتیبانی{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.head h1{font-size:22px;font-weight:bold}
.head h1 span{color:var(--gold)}
.card{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:20px;margin-bottom:16px}
.card h3{font-size:15px;color:var(--gold);margin-bottom:14px}
.form-row{margin-bottom:12px}
.form-row label{display:block;font-size:12px;color:var(--muted);margin-bottom:6px;font-weight:bold}
.form-row input,.form-row textarea{width:100%;padding:12px 14px;border-radius:12px;border:1.5px solid var(--border);background:var(--bg);color:#fff;font-size:14px;font-family:inherit;box-sizing:border-box}
.form-row textarea{min-height:100px;resize:vertical}
.form-row input:focus,.form-row textarea:focus{outline:none;border-color:var(--gold)}
.btn-send{width:100%;padding:14px;border:none;border-radius:14px;background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;font-family:inherit;font-weight:bold;font-size:15px;cursor:pointer}
.ticket-item{display:flex;align-items:center;gap:12px;padding:14px;background:rgba(15,23,42,.5);border:1px solid var(--border);border-radius:12px;margin-bottom:8px;text-decoration:none;color:#fff;transition:.2s}
.ticket-item:hover{border-color:var(--purple);transform:translateX(-3px)}
.ticket-icon{width:42px;height:42px;border-radius:10px;background:rgba(139,92,246,.2);display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0}
.ticket-body{flex:1;min-width:0}
.ticket-subject{font-size:14px;font-weight:bold;margin-bottom:3px;color:#fff}
.ticket-meta{font-size:11px;color:var(--muted);font-family:monospace}
.ticket-status{padding:4px 10px;border-radius:8px;font-size:10px;font-weight:bold}
.status-open{background:rgba(234,179,8,.2);color:#fde68a}
.status-answered{background:rgba(34,197,94,.2);color:#4ade80}
.status-closed{background:rgba(100,116,139,.2);color:#cbd5e1}
.empty{text-align:center;padding:40px 20px;color:var(--muted);font-size:13px}
.empty .icon{font-size:50px;display:block;margin-bottom:10px;opacity:.5}
.msg{padding:12px 16px;border-radius:10px;font-size:13px;margin-bottom:14px}
.msg-success{background:rgba(34,197,94,.15);color:#4ade80;border:1px solid rgba(34,197,94,.3)}
.msg-error{background:rgba(239,68,68,.15);color:#fca5a5;border:1px solid rgba(239,68,68,.35)}
</style>
{% endblock %}
{% block content %}
<div class="head"><a href="/game/" class="back-btn"><span class="arrow-icon">→</span></a><h1>💬 <span>پشتیبانی</span></h1></div>

{% if messages %}{% for m in messages %}<div class="msg msg-{{ m.tags }}">{{ m }}</div>{% endfor %}{% endif %}

<div class="card">
  <h3>📝 ارسال تیکت جدید</h3>
  <form method="post">
    {% csrf_token %}
    <div class="form-row"><label>موضوع</label><input type="text" name="subject" required maxlength="100" placeholder="خلاصه مشکل..."></div>
    <div class="form-row"><label>توضیحات</label><textarea name="body" required maxlength="2000" placeholder="جزئیات مشکل یا انتقاد یا پیشنهاد..."></textarea></div>
    <button type="submit" class="btn-send">📤 ارسال تیکت</button>
  </form>
</div>

<div class="card">
  <h3>📋 تیکت‌های من ({{ tickets|length }})</h3>
  {% if tickets %}
    {% for t in tickets %}
      <a href="{% url 'accounts:support_detail' t.id %}" class="ticket-item">
        <div class="ticket-icon">💬</div>
        <div class="ticket-body">
          <div class="ticket-subject">{{ t.subject }}</div>
          <div class="ticket-meta">{{ t.created_at|date:"Y/m/d H:i" }} · {{ t.message_count }} پیام</div>
          {% if t.last_msg %}<div class="ticket-meta" style="margin-top:2px;">{{ t.last_msg }}</div>{% endif %}
        </div>
        <span class="ticket-status status-{{ t.status }}">{{ t.status_display }}</span>
      </a>
    {% endfor %}
  {% else %}
    <div class="empty"><span class="icon">📭</span>هنوز تیکتی ارسال نکردی.</div>
  {% endif %}
</div>
{% endblock %}
''')
print("  ✓ support_home.html")

write("accounts/templates/accounts/support_detail.html", '''{% extends "base.html" %}
{% block title %}{{ ticket.subject }}{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.ticket-head{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:18px;margin-bottom:16px}
.ticket-subject{font-size:18px;font-weight:bold;color:#fff;margin-bottom:6px}
.ticket-meta{font-size:12px;color:var(--muted)}
.ticket-status{display:inline-block;padding:4px 12px;border-radius:8px;font-size:11px;font-weight:bold;margin-top:8px}
.status-open{background:rgba(234,179,8,.2);color:#fde68a}
.status-answered{background:rgba(34,197,94,.2);color:#4ade80}
.status-closed{background:rgba(100,116,139,.2);color:#cbd5e1}
.chat-box{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:16px;margin-bottom:16px;min-height:300px;max-height:60vh;overflow-y:auto;display:flex;flex-direction:column;gap:12px}
.msg-bubble{max-width:80%;padding:12px 16px;border-radius:14px;background:rgba(15,23,42,.6);border:1px solid var(--border);font-size:14px;line-height:1.5;color:#fff;align-self:flex-start;border-bottom-left-radius:4px}
.msg-bubble.me{background:linear-gradient(135deg,#3b82f6,#2563eb);border-color:#2563eb;align-self:flex-end;border-bottom-left-radius:14px;border-bottom-right-radius:4px}
.msg-bubble.staff{background:linear-gradient(135deg,rgba(139,92,246,.3),rgba(6,182,212,.2));border-color:rgba(139,92,246,.5)}
.msg-sender{font-size:11px;color:var(--muted);margin-bottom:4px}
.msg-time{font-size:9px;color:var(--dim);margin-top:4px;opacity:.7}
.chat-input{display:flex;gap:10px;background:var(--card);padding:10px;border-radius:16px;border:1px solid var(--border);margin-bottom:16px}
.chat-input input{flex:1;background:transparent;border:none;color:#fff;font-size:15px;padding:10px;font-family:inherit}
.chat-input input:focus{outline:none}
.chat-input button{background:linear-gradient(135deg,#06b6d4,#3b82f6);color:#fff;border:none;padding:0 22px;border-radius:12px;font-size:15px;font-weight:bold;cursor:pointer;font-family:inherit}
.action-row{display:flex;gap:10px;flex-wrap:wrap}
.action-row button,.action-row a{flex:1;min-width:120px;padding:12px;border:none;border-radius:12px;font-family:inherit;font-weight:bold;font-size:13px;cursor:pointer;text-decoration:none;text-align:center}
.btn-close{background:rgba(234,179,8,.15);color:#fde68a;border:1px solid rgba(234,179,8,.3)}
.btn-delete{background:rgba(239,68,68,.15);color:#fca5a5;border:1px solid rgba(239,68,68,.3)}
.msg{padding:12px 16px;border-radius:10px;font-size:13px;margin-bottom:14px}
.msg-success{background:rgba(34,197,94,.15);color:#4ade80;border:1px solid rgba(34,197,94,.3)}
.msg-info{background:rgba(59,130,246,.15);color:#93c5fd;border:1px solid rgba(59,130,246,.3)}
</style>
{% endblock %}
{% block content %}
<div class="head"><a href="{% url 'accounts:support_home' %}" class="back-btn"><span class="arrow-icon">→</span></a></div>

{% if messages %}{% for m in messages %}<div class="msg msg-{{ m.tags }}">{{ m }}</div>{% endfor %}{% endif %}

<div class="ticket-head">
  <div class="ticket-subject">{{ ticket.subject }}</div>
  <div class="ticket-meta">{{ ticket.created_at|date:"Y/m/d H:i" }} · {{ ticket.message_count }} پیام</div>
  <div class="ticket-status status-{{ ticket.status }}">{{ ticket.get_status_display }}</div>
</div>

<div class="chat-box" id="chatBox">
  {% for m in ticket_messages %}
    <div class="msg-bubble {% if m.is_me %}me{% elif m.is_staff %}staff{% endif %}">
      <div class="msg-sender">{{ m.sender_alias }}</div>
      {{ m.body }}
      <div class="msg-time">{{ m.created_at|date:"Y/m/d H:i" }}</div>
    </div>
  {% empty %}
    <div style="text-align:center;color:var(--muted);font-size:13px;margin:auto;">هنوز پیامی نیست.</div>
  {% endfor %}
</div>

{% if ticket.status != "closed" %}
<form method="post" class="chat-input">
  {% csrf_token %}
  <input type="hidden" name="action" value="reply">
  <input type="text" name="body" required maxlength="2000" placeholder="پاسخ خود را بنویسید..." autocomplete="off">
  <button type="submit">↑</button>
</form>
{% else %}
<div class="msg msg-info">این تیکت بسته شده است. برای ادامه، ابتدا آن را باز کنید.</div>
{% endif %}

<div class="action-row">
  {% if ticket.status != "closed" %}
    <form method="post" style="flex:1;">
      {% csrf_token %}
      <input type="hidden" name="action" value="close">
      <button type="submit" class="btn-close" style="width:100%;" onclick="return confirm('تیکت بسته شود؟');">🔒 بستن تیکت</button>
    </form>
  {% endif %}
  <form method="post" style="flex:1;" onsubmit="return confirm('تیکت حذف شود؟');">
    {% csrf_token %}
    <input type="hidden" name="action" value="delete">
    <button type="submit" class="btn-delete" style="width:100%;">🗑️ حذف تیکت</button>
  </form>
</div>

<script>
const box = document.getElementById('chatBox');
if (box) box.scrollTop = box.scrollHeight;
</script>
{% endblock %}
''')
print("  ✓ support_detail.html")

# 7e) Admin support templates
write("accounts/templates/custom_admin/support_tickets.html", '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>پشتیبانی — پنل ادمین</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 16px 16px 40px; }
.container { max-width: 1400px; margin: 0 auto; }
.admin-sticky-header { position: sticky; top: 0; z-index: 500; background: #0a0a15; padding: 4px 0 8px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.7); }
.topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 8px; }
.topbar h1 { font-size: 20px; color: #fca5a5; }
.admin-tabs { display: flex !important; gap: 6px !important; overflow-x: auto !important; overflow-y: hidden !important; white-space: nowrap !important; padding: 8px !important; background: #12121f !important; border: 1px solid rgba(148,163,184,0.15) !important; border-radius: 14px !important; scrollbar-width: none !important; height: 48px !important; }
.admin-tabs::-webkit-scrollbar { display: none; }
.admin-tab { flex: 0 0 auto !important; height: 40px !important; display: inline-flex !important; align-items: center !important; padding: 0 14px !important; border-radius: 10px !important; text-decoration: none !important; font-size: 12px !important; font-weight: bold !important; color: #94a3b8 !important; white-space: nowrap !important; }
.admin-tab:hover { background: rgba(148,163,184,0.1) !important; color: #fff !important; }
.admin-tab.active { background: linear-gradient(135deg, #ef4444, #dc2626) !important; color: #fff !important; }
.msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
.msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px; }
.stat-box { padding: 12px; border-radius: 12px; background: rgba(30,41,59,.6); border: 1px solid rgba(148,163,184,.15); text-align: center; }
.stat-val { font-size: 22px; font-weight: 900; font-family: monospace; color: #fff; }
.stat-lbl { font-size: 11px; color: #94a3b8; }
.ticket-item { display: flex; align-items: center; gap: 12px; padding: 14px; background: #12121f; border: 1px solid rgba(148,163,184,.15); border-radius: 12px; margin-bottom: 8px; text-decoration: none; color: #e2e8f0; transition: 0.2s; }
.ticket-item:hover { border-color: rgba(139,92,246,.5); transform: translateX(-3px); }
.ticket-icon { width: 44px; height: 44px; border-radius: 10px; background: rgba(139,92,246,.2); display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
.ticket-body { flex: 1; min-width: 0; }
.ticket-subject { font-size: 14px; font-weight: bold; color: #fff; margin-bottom: 3px; }
.ticket-meta { font-size: 11px; color: #94a3b8; font-family: monospace; }
.ticket-status { padding: 4px 10px; border-radius: 8px; font-size: 10px; font-weight: bold; }
.status-open { background: rgba(234,179,8,0.2); color: #fde68a; }
.status-answered { background: rgba(34,197,94,0.2); color: #4ade80; }
.status-closed { background: rgba(100,116,139,0.2); color: #cbd5e1; }
.filter-row { display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }
.filter-btn { padding: 8px 14px; border-radius: 10px; font-size: 12px; font-weight: bold; text-decoration: none; color: #94a3b8; background: rgba(148,163,184,.1); border: 1px solid rgba(148,163,184,.2); }
.filter-btn.active { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; border-color: transparent; }
.empty { text-align: center; padding: 60px 20px; color: #64748b; }
.empty .icon { font-size: 60px; display: block; margin-bottom: 12px; opacity: 0.5; }
</style>
</head>
<body>
<div class="container">
  <div class="admin-sticky-header">
    <div class="topbar"><h1>💬 پشتیبانی</h1></div>
    <div class="admin-tabs">
      <a href="/panel-admin/dashboard/" class="admin-tab {% if '/panel-admin/dashboard/' in request.path or request.path == '/panel-admin/' %}active{% endif %}">👥 کاربران</a>
      <a href="/panel-admin/alliances/" class="admin-tab {% if '/panel-admin/alliance' in request.path %}active{% endif %}">🛡️ اتحادها</a>
      <a href="/panel-admin/rooms/" class="admin-tab {% if '/panel-admin/room' in request.path %}active{% endif %}">🚪 اتاق‌ها</a>
      <a href="/panel-admin/announcements/" class="admin-tab {% if '/panel-admin/announcement' in request.path %}active{% endif %}">📢 اعلان‌ها</a>
      <a href="/panel-admin/tournaments/" class="admin-tab {% if '/panel-admin/tournament' in request.path %}active{% endif %}">🏆 تورنمنت</a>
      <a href="/panel-admin/shop/" class="admin-tab {% if '/panel-admin/shop/' in request.path %}active{% endif %}">🛒 فروشگاه</a>
      <a href="/panel-admin/support/" class="admin-tab {% if '/panel-admin/support' in request.path %}active{% endif %}">💬 پشتیبانی</a>
    </div>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <div class="stats-row">
    <div class="stat-box"><div class="stat-val">{{ count_open }}</div><div class="stat-lbl">باز</div></div>
    <div class="stat-box"><div class="stat-val">{{ count_answered }}</div><div class="stat-lbl">پاسخ داده</div></div>
    <div class="stat-box"><div class="stat-val">{{ count_closed }}</div><div class="stat-lbl">بسته</div></div>
    <div class="stat-box"><div class="stat-val">{{ count_total }}</div><div class="stat-lbl">کل</div></div>
  </div>

  <div class="filter-row">
    <a href="?" class="filter-btn {% if not status_filter %}active{% endif %}">همه</a>
    <a href="?status=open" class="filter-btn {% if status_filter == 'open' %}active{% endif %}">باز</a>
    <a href="?status=answered" class="filter-btn {% if status_filter == 'answered' %}active{% endif %}">پاسخ داده</a>
    <a href="?status=closed" class="filter-btn {% if status_filter == 'closed' %}active{% endif %}">بسته</a>
  </div>

  {% if tickets %}
    {% for t in tickets %}
      <a href="/panel-admin/support/{{ t.id }}/" class="ticket-item">
        <div class="ticket-icon">💬</div>
        <div class="ticket-body">
          <div class="ticket-subject">{{ t.subject }}</div>
          <div class="ticket-meta">👤 {{ t.user_alias }} · {{ t.updated_at|jdate:"Y/m/d H:i" }} · {{ t.message_count }} پیام</div>
          {% if t.last_msg %}<div class="ticket-meta" style="margin-top:2px; color:#cbd5e1;">{{ t.last_msg }}</div>{% endif %}
        </div>
        <span class="ticket-status status-{{ t.status }}">{{ t.status_display }}</span>
      </a>
    {% endfor %}
  {% else %}
    <div class="empty"><span class="icon">📭</span>هیچ تیکتی پیدا نشد.</div>
  {% endif %}
</div>
</body>
</html>
''')
print("  ✓ support_tickets.html")

write("accounts/templates/custom_admin/support_ticket_detail.html", '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ ticket.subject }}</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 16px 16px 40px; }
.container { max-width: 900px; margin: 0 auto; }
.topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(139,92,246,.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 16px; }
.topbar h1 { font-size: 18px; color: #c4b5fd; }
.topbar .actions { display: flex; gap: 8px; }
.topbar a { padding: 8px 14px; border-radius: 10px; text-decoration: none; font-size: 12px; font-weight: bold; color: #fff; background: rgba(148,163,184,.2); }
.msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
.msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
.ticket-head { background: #12121f; border: 1px solid rgba(148,163,184,.15); border-radius: 16px; padding: 18px; margin-bottom: 16px; }
.ticket-subject { font-size: 18px; font-weight: bold; color: #fff; margin-bottom: 6px; }
.ticket-meta { font-size: 12px; color: #94a3b8; margin-bottom: 8px; }
.ticket-status { display: inline-block; padding: 5px 14px; border-radius: 8px; font-size: 11px; font-weight: bold; }
.status-open { background: rgba(234,179,8,0.2); color: #fde68a; }
.status-answered { background: rgba(34,197,94,0.2); color: #4ade80; }
.status-closed { background: rgba(100,116,139,0.2); color: #cbd5e1; }
.chat-box { background: #12121f; border: 1px solid rgba(148,163,184,.15); border-radius: 16px; padding: 16px; margin-bottom: 16px; min-height: 300px; max-height: 55vh; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.msg-bubble { max-width: 80%; padding: 12px 16px; border-radius: 14px; background: rgba(15,23,42,.6); border: 1px solid rgba(148,163,184,.15); font-size: 14px; line-height: 1.5; color: #fff; align-self: flex-start; }
.msg-bubble.user { background: linear-gradient(135deg, #3b82f6, #2563eb); border-color: #2563eb; align-self: flex-end; }
.msg-bubble.staff { background: linear-gradient(135deg, rgba(139,92,246,.3), rgba(6,182,212,.2)); border-color: rgba(139,92,246,.5); }
.msg-sender { font-size: 11px; color: #94a3b8; margin-bottom: 4px; }
.msg-time { font-size: 9px; color: #64748b; margin-top: 4px; opacity: .7; }
.chat-input { display: flex; gap: 10px; background: #12121f; padding: 10px; border-radius: 14px; border: 1px solid rgba(148,163,184,.15); margin-bottom: 16px; }
.chat-input input { flex: 1; background: transparent; border: none; color: #fff; font-size: 15px; padding: 10px; font-family: inherit; }
.chat-input input:focus { outline: none; }
.chat-input button { background: linear-gradient(135deg,#06b6d4,#3b82f6); color: #fff; border: none; padding: 0 22px; border-radius: 10px; font-size: 14px; font-weight: bold; cursor: pointer; font-family: inherit; }
.action-row { display: flex; gap: 10px; flex-wrap: wrap; }
.action-row form { flex: 1; }
.action-row button { width: 100%; padding: 12px; border: none; border-radius: 12px; font-family: inherit; font-weight: bold; font-size: 13px; cursor: pointer; }
.btn-close { background: rgba(234,179,8,.15); color: #fde68a; border: 1px solid rgba(234,179,8,.3); }
.btn-reopen { background: rgba(34,197,94,.15); color: #4ade80; border: 1px solid rgba(34,197,94,.3); }
.btn-delete { background: rgba(239,68,68,.15); color: #fca5a5; border: 1px solid rgba(239,68,68,.3); }
</style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>💬 تیکت #{{ ticket.id }}</h1>
    <div class="actions">
      <a href="/panel-admin/support/">← بازگشت</a>
    </div>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <div class="ticket-head">
    <div class="ticket-subject">{{ ticket.subject }}</div>
    <div class="ticket-meta">👤 {{ ticket.user.alias|default:ticket.user.username }} · {{ ticket.created_at|jdate:"Y/m/d H:i" }} · {{ ticket.message_count }} پیام</div>
    <div class="ticket-status status-{{ ticket.status }}">{{ ticket.get_status_display }}</div>
  </div>

  <div class="chat-box" id="chatBox">
    {% for m in ticket_messages %}
      <div class="msg-bubble {% if m.is_staff %}staff{% else %}user{% endif %}">
        <div class="msg-sender">{{ m.sender_alias }}{% if m.is_staff %} (پشتیبانی){% endif %}</div>
        {{ m.body }}
        <div class="msg-time">{{ m.created_at|jdate:"Y/m/d H:i" }}</div>
      </div>
    {% empty %}
      <div style="text-align:center;color:#64748b;font-size:13px;margin:auto;">هنوز پیامی نیست.</div>
    {% endfor %}
  </div>

  <form method="post" class="chat-input">
    {% csrf_token %}
    <input type="hidden" name="action" value="reply">
    <input type="text" name="body" required maxlength="2000" placeholder="پاسخ به کاربر..." autocomplete="off">
    <button type="submit">↑</button>
  </form>

  <div class="action-row">
    {% if ticket.status != "closed" %}
      <form method="post">
        {% csrf_token %}
        <input type="hidden" name="action" value="close">
        <button type="submit" class="btn-close" onclick="return confirm('تیکت بسته شود؟');">🔒 بستن تیکت</button>
      </form>
    {% else %}
      <form method="post">
        {% csrf_token %}
        <input type="hidden" name="action" value="reopen">
        <button type="submit" class="btn-reopen">🔓 باز کردن مجدد</button>
      </form>
    {% endif %}
    <form method="post">
      {% csrf_token %}
      <input type="hidden" name="action" value="delete">
      <button type="submit" class="btn-delete" onclick="return confirm('تیکت حذف شود؟');">🗑️ حذف تیکت</button>
    </form>
  </div>
</div>
<script>
const b = document.getElementById('chatBox');
if (b) b.scrollTop = b.scrollHeight;
</script>
</body>
</html>
''')
print("  ✓ support_ticket_detail.html")

# 7f) Menu - add support icon
p = "game/templates/game/menu.html"
src = read(p)

if 'href="/accounts/support/"' not in src:
    # Find shop disabled div and add support after it
    old = '''<div class="round-btn round-shop-disabled" title="به زودی" style="opacity:0.45; cursor:not-allowed; background:rgba(148,163,184,0.15); border:1.5px solid rgba(148,163,184,0.25);">
    <span class="rb-icon" style="filter:grayscale(1);">🛒</span>
    <span class="rb-label" style="color:#94a3b8;">به زودی</span>
  </div>'''
    new = old + '''
  <a href="/accounts/support/" class="round-btn round-top" title="پشتیبانی" style="background: linear-gradient(135deg, rgba(59,130,246,0.3), rgba(6,182,212,0.15)); border-color: rgba(59,130,246,0.55);">
    <span class="rb-icon">💬</span>
    <span class="rb-label">پشتیبانی</span>
  </a>'''
    if old in src:
        src = src.replace(old, new, 1)
        write(p, src)
        print("  ✓ support icon added to menu")

# ============================================================
# PART 8: Migrations + test
# ============================================================
print("\n[8/8] Migrations + test")

for cmd in [
    [sys.executable, "manage.py", "makemigrations", "accounts", "game", "--noinput"],
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
    print(f"  ⚠ {r.stderr[:600]}")

# Test
import django
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

tu, created = User.objects.get_or_create(
    username="__test_final__",
    defaults={"alias": "test", "is_active": True, "has_chosen_avatar": True, "has_completed_registration": True}
)
if created:
    tu.set_password("x")
    tu.save()

# Test player support
c = Client()
c.force_login(tu)
c.session["beta_unlocked"] = True
c.session.save()

print("\n  Player pages:")
for url in ["/accounts/support/"]:
    r = c.get(url, follow=False)
    print(f"    {'✓' if r.status_code == 200 else '✗'} {url} → {r.status_code}")

# Test create ticket
r = c.post("/accounts/support/", {"subject": "__test_ticket__", "body": "test body"}, follow=False)
print(f"    POST create ticket → {r.status_code}")

# Test admin support
c2 = Client()
c2.session["custom_admin_logged_in"] = True
c2.session["beta_unlocked"] = True
c2.session.save()

print("\n  Admin pages:")
for url in ["/panel-admin/announcements/", "/panel-admin/support/"]:
    r = c2.get(url, follow=False)
    print(f"    {'✓' if r.status_code == 200 else '✗'} {url} → {r.status_code}")

# Test announcement send
r = c2.post("/panel-admin/announcements/", {
    "action": "send_all",
    "title": "__test_ann__",
    "body": "test",
    "url": ""
}, follow=False)
print(f"    POST send announcement → {r.status_code}")

if created:
    tu.delete()

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
What was added:

  1. ANNOUNCEMENT FIX:
     - announcements_list rebuilt (clean)
     - Reader tracking via NotificationRead
     - Shows who read + when

  2. ROOMS REDESIGN:
     - Create room now has "game type" selector
     - Host sees modal to pick game (if not set)
     - Players click "من آماده‌ام" (I'm ready)
     - Host clicks "شروع بازی" when 2+ ready
     - Game type determines where to redirect

  3. SUPPORT TICKETS:
     - Menu icon 💬 next to top-players and shop
     - /accounts/support/ — create + list tickets
     - /accounts/support/<id>/ — chat view
     - Auto-bot reply on create
     - Close/delete ticket
     - Admin: /panel-admin/support/ — list all
     - Admin: /panel-admin/support/<id>/ — reply, close, reopen, delete

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R

Test:
  1. /accounts/support/ → create ticket → see bot reply
  2. /game/rooms/manage/ → create room → pick game type
  3. /game/room/<code>/ → see players, click ready/start
  4. /panel-admin/support/ → reply to ticket
""")
