#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()

def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")

def backup(p):
    bak = p + ".bak"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) social/views.py
# ============================================================
print("\n[1/6] social/views.py")
p = os.path.join(ROOT, "social", "views.py")
src = read(p)

if "my_alliance" in src and "# اتحاد کاربر" in src:
    print("  SKIP: already done")
else:
    old = '''    # دعوت‌نامه‌های بازی در انتظار
    pending_invites = GameInvite.objects.filter(to_user=request.user, status="pending").select_related("from_user", "game")

    return render(request, "social/friends.html", {
        "friends": friends,
        "incoming": incoming_list,
        "outgoing": outgoing_list,
        "pending_invites": pending_invites,
        "active": "friends",
    })'''
    new = '''    # دعوت‌نامه‌های بازی در انتظار
    pending_invites = GameInvite.objects.filter(to_user=request.user, status="pending").select_related("from_user", "game")

    # اتحاد کاربر
    from alliance.models import AllianceMember, AllianceMessage
    my_alliance = None
    membership = AllianceMember.objects.filter(user=request.user).select_related("alliance").first()
    if membership:
        a = membership.alliance
        last_msg = AllianceMessage.objects.filter(alliance=a).select_related("sender").order_by("-sent_at").first()
        my_alliance = {
            "id": a.id,
            "name": a.name,
            "emblem": a.emblem,
            "tag": a.tag,
            "member_count": a.member_count(),
            "max_members": a.max_members,
            "role": membership.role,
            "role_display": membership.get_role_display(),
            "last_message": last_msg.body if last_msg else "",
            "last_message_sender": last_msg.sender.alias if last_msg else "",
        }

    return render(request, "social/friends.html", {
        "friends": friends,
        "incoming": incoming_list,
        "outgoing": outgoing_list,
        "pending_invites": pending_invites,
        "my_alliance": my_alliance,
        "active": "friends",
    })'''
    if old in src:
        backup(p); src = src.replace(old, new, 1); write(p, src)
        print("  FIXED: my_alliance passed to context")
    else:
        print("  WARN: friends_home return block not found")

# ============================================================
# 2) social/templates/social/friends.html - CSS + card
# ============================================================
print("\n[2/6] friends.html - CSS")
p = os.path.join(ROOT, "social", "templates", "social", "friends.html")
src = read(p)

if ".alliance-card.member {" in src:
    print("  SKIP: CSS already added")
else:
    anchor = "  .ac-arrow { font-size: 20px; color: #c4b5fd; }"
    add_css = anchor + '''

  .alliance-card.member {
    background: radial-gradient(circle at 100% 0%, rgba(34,197,94,0.3), transparent 60%),
                linear-gradient(135deg, #0a1f0f, #0f1e15);
    border-color: rgba(34,197,94,0.55);
    box-shadow: 0 8px 25px rgba(34,197,94,0.2);
  }
  .alliance-card.member:hover {
    border-color: rgba(34,197,94,0.9);
    box-shadow: 0 15px 35px rgba(34,197,94,0.4);
  }
  .alliance-card.member .ac-title { color: #86efac; }
  .alliance-card.member .ac-arrow { color: #86efac; }
  .alliance-card.member .ac-icon {
    background: linear-gradient(135deg, rgba(34,197,94,0.35), rgba(6,182,212,0.15));
    border-color: rgba(34,197,94,0.4);
  }
  .ac-tag {
    font-size: 10px;
    color: #1a1a1a;
    background: var(--gold);
    padding: 2px 8px;
    border-radius: 6px;
    margin-right: 6px;
    font-family: monospace;
    font-weight: bold;
    vertical-align: middle;
  }
  .ac-last {
    color: #86efac;
    font-size: 11px;
    margin-top: 3px;
    display: block;
    opacity: 0.9;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }'''
    if anchor in src:
        backup(p); src = src.replace(anchor, add_css, 1); write(p, src)
        print("  FIXED: member CSS added")
    else:
        print("  WARN: ac-arrow anchor not found")

# card replacement
print("\n[3/6] friends.html - card content")
src = read(p)
old_card = '''  <!-- کارت اتحاد -->
  <a href="/alliance/" class="alliance-card">
    <div class="ac-icon">🛡️</div>
    <div class="ac-body">
      <div class="ac-title">اتحاد</div>
      <div class="ac-desc">با دوستات یه تیم بساز و با هم بازی کن</div>
    </div>
    <div class="ac-arrow">←</div>
  </a>'''

new_card = '''  <!-- کارت اتحاد -->
  {% if my_alliance %}
    <a href="/alliance/" class="alliance-card member">
      <div class="ac-icon">{{ my_alliance.emblem }}</div>
      <div class="ac-body">
        <div class="ac-title">
          {{ my_alliance.name }}
          {% if my_alliance.tag %}<span class="ac-tag">{{ my_alliance.tag }}</span>{% endif %}
        </div>
        <div class="ac-desc">
          {{ my_alliance.member_count }} / {{ my_alliance.max_members }} عضو · {{ my_alliance.role_display }}
          {% if my_alliance.last_message %}
            <span class="ac-last">💬 {{ my_alliance.last_message_sender }}: {{ my_alliance.last_message|truncatechars:40 }}</span>
          {% else %}
            <span class="ac-last" style="color:#64748b;">💬 هنوز پیامی نیست</span>
          {% endif %}
        </div>
      </div>
      <div class="ac-arrow">←</div>
    </a>
  {% else %}
    <a href="/alliance/" class="alliance-card">
      <div class="ac-icon">🛡️</div>
      <div class="ac-body">
        <div class="ac-title">اتحاد</div>
        <div class="ac-desc">با دوستات یه تیم بساز و با هم بازی کن</div>
      </div>
      <div class="ac-arrow">←</div>
    </a>
  {% endif %}'''

if "{% if my_alliance %}" in src:
    print("  SKIP: card already dynamic")
elif old_card in src:
    src = src.replace(old_card, new_card, 1)
    write(p, src)
    print("  FIXED: card is dynamic now")
else:
    print("  WARN: static card not found")

# ============================================================
# 4) game/views.py - leave_room
# ============================================================
print("\n[4/6] game/views.py - leave_room")
p = os.path.join(ROOT, "game", "views.py")
src = read(p)

if "def leave_room" in src:
    print("  SKIP: already exists")
else:
    leave_view = '''

@login_required
def leave_room(request, room_code):
    check = _require_complete(request.user)
    if check:
        return check

    if request.method != "POST":
        return redirect("game:room", room_code=room_code)

    room_obj = Game.objects.filter(code=room_code).first()
    if not room_obj:
        return redirect("game:rooms_manage")

    is_host = room_obj.host_id == request.user.id

    if is_host:
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"game_{room_obj.id}",
                {"type": "ev.room_closed"}
            )
        except Exception:
            pass
        room_obj.players.all().delete()
        room_obj.delete()
    else:
        room_obj.players.filter(user=request.user).delete()

    return redirect("game:rooms_manage")
'''
    src = src.rstrip() + "\n" + leave_view + "\n"
    backup(p); write(p, src)
    print("  FIXED: leave_room added")

# ============================================================
# 5) game/urls.py
# ============================================================
print("\n[5/6] game/urls.py")
p = os.path.join(ROOT, "game", "urls.py")
src = read(p)

if "leave_room" in src:
    print("  SKIP: route already exists")
else:
    old = '    path("rooms/join/<str:room_code>/", views.join_room, name="join_room"),'
    new = old + '\n    path("rooms/leave/<str:room_code>/", views.leave_room, name="leave_room"),'
    if old in src:
        backup(p); src = src.replace(old, new, 1); write(p, src)
        print("  FIXED: route added")
    else:
        print("  WARN: join_room route not found")

# ============================================================
# 6) game/consumers.py - room_closed event
# ============================================================
print("\n[6/6] game/consumers.py")
p = os.path.join(ROOT, "game", "consumers.py")
src = read(p)

if "ev_room_closed" in src:
    print("  SKIP: already exists")
else:
    add = '''
    async def ev_room_closed(self, event):
        await self.send_json({"type": "room_closed"})
'''
    marker = "    async def ev_chat_msg(self, event):"
    if marker in src:
        src = src.replace(marker, add + "\n" + marker, 1)
        backup(p); write(p, src)
        print("  FIXED: ev_room_closed added")
    else:
        src = src.rstrip() + "\n" + add + "\n"
        backup(p); write(p, src)
        print("  FIXED: ev_room_closed added (at end)")

# ============================================================
# 7) room.html - leave button + JS
# ============================================================
print("\n[7/6] room.html - leave button")
p = os.path.join(ROOT, "game", "templates", "game", "room.html")
src = read(p)

# 7a) CSS for leave button
if ".leave-btn {" not in src:
    anchor = "  .empty-chat { text-align: center; color: var(--dim); font-size: 12px;\n    margin: auto; padding: 30px 0; }"
    add_css = anchor + '''

  .room-topbar { display: flex; justify-content: flex-start; margin-bottom: 12px; }
  .leave-btn { display: inline-flex; align-items: center; gap: 6px; padding: 10px 16px;
    border-radius: 12px; background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.3); color: #fca5a5;
    font-size: 13px; font-weight: bold; font-family: inherit; cursor: pointer; transition: 0.2s; }
  .leave-btn:hover { background: rgba(239,68,68,0.3); border-color: #ef4444; color: #fff; }'''
    if anchor in src:
        src = src.replace(anchor, add_css, 1)
        print("  FIXED: leave CSS added")
    else:
        print("  WARN: empty-chat anchor not found")
else:
    print("  SKIP: leave CSS exists")

# 7b) Insert leave button before room-header
old_header_start = '''{% block content %}
  <div class="room-header">'''
new_header_start = '''{% block content %}
  <div class="room-topbar">
    <button class="leave-btn" onclick="leaveRoom()">← خروج از اتاق</button>
  </div>

  <div class="room-header">'''

if 'onclick="leaveRoom()"' in src:
    print("  SKIP: button exists")
elif old_header_start in src:
    src = src.replace(old_header_start, new_header_start, 1)
    print("  FIXED: button added")
else:
    print("  WARN: header block not found")

# 7c) Add leaveRoom JS function
js_anchor = '  $("chatForm").onsubmit = (e) => {'
js_add = '''  function leaveRoom() {
    const playerCount = {{ players|length }};
    const isHost = {% if is_host %}true{% else %}false{% endif %};

    let msg;
    if (isHost && playerCount > 1) {
      msg = "⚠️ هشدار!\\n\\nشما میزبان این اتاق هستید.\\nبا خارج شدن شما، اتاق بسته می‌شود و همه " + (playerCount - 1) + " بازیکن دیگر هم خارج می‌شوند.\\n\\nمطمئنی؟";
    } else if (isHost) {
      msg = "با خارج شدن شما، اتاق بسته می‌شود.\\n\\nمطمئنی؟";
    } else {
      msg = "از اتاق خارج می‌شوی؟";
    }

    if (!confirm(msg)) return;

    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/game/rooms/leave/{{ room.code }}/';
    const csrf = document.createElement('input');
    csrf.type = 'hidden';
    csrf.name = 'csrfmiddlewaretoken';
    csrf.value = '{{ csrf_token }}';
    form.appendChild(csrf);
    document.body.appendChild(form);
    form.submit();
  }

  $("chatForm").onsubmit = (e) => {'''

if "function leaveRoom()" in src:
    print("  SKIP: leaveRoom JS exists")
elif js_anchor in src:
    src = src.replace(js_anchor, js_add, 1)
    print("  FIXED: leaveRoom JS added")
else:
    print("  WARN: chatForm JS anchor not found")

# 7d) Add room_closed handler
old_ws = '''    else if (msg.type === "round_start") alert(`بازی شروع شد! حرف: ${msg.letter}`);'''
new_ws = '''    else if (msg.type === "round_start") alert(`بازی شروع شد! حرف: ${msg.letter}`);
    else if (msg.type === "room_closed") {
      alert("اتاق توسط میزبان بسته شد.");
      window.location.href = "/game/rooms/manage/";
    }'''

if "room_closed" in src:
    print("  SKIP: room_closed handler exists")
elif old_ws in src:
    src = src.replace(old_ws, new_ws, 1)
    print("  FIXED: room_closed handler added")
else:
    print("  WARN: ws.onmessage anchor not found")

write(p, src)

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Changes applied:
  1. social/views.py       -> my_alliance passed to friends page
  2. friends.html (CSS)    -> member variant (green) + tag badge + last message
  3. friends.html (card)   -> dynamic: shows alliance info if member
  4. game/views.py         -> leave_room view added
  5. game/urls.py          -> /game/rooms/leave/<code>/ route
  6. game/consumers.py     -> ev_room_closed handler
  7. room.html             -> leave button + confirm + room_closed listener

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R
""")
