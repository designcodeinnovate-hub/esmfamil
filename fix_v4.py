#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re

ROOT = os.path.dirname(os.path.abspath(__file__))

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()

def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")

def backup(p):
    bak = p + ".bak"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) rooms.html - کامل بازنویسی
# ============================================================
print("\n[1/4] rooms.html")
p = os.path.join(ROOT, "game", "templates", "game", "rooms.html")
ROOMS_HTML = '''{% extends "base.html" %}
{% block title %}بازی‌ها{% endblock %}

{% block extra_css %}
<style>
  .page-head { margin-bottom: 20px; }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }
  .big-card {
    border-radius: 20px; padding: 20px; margin-bottom: 12px;
    text-decoration: none; color: #fff;
    display: flex; align-items: center; gap: 14px;
    position: relative; overflow: hidden;
    border: 1.5px solid; transition: all 0.22s;
  }
  .big-card:hover { transform: translateY(-3px); }
  .big-card:active { transform: scale(0.98); }
  .big-card.soon { cursor: default; opacity: 0.75; }
  .big-card.soon:hover { transform: none; }
  .big-card.bot    { background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.25), transparent 60%), linear-gradient(135deg, #2a1a0e, #1a0f1a); border-color: rgba(244,197,66,0.4); }
  .big-card.player { background: radial-gradient(circle at 100% 0%, rgba(59,130,246,0.25), transparent 60%), linear-gradient(135deg, #0a1a2a, #0f0f1e); border-color: rgba(59,130,246,0.4); }
  .big-card.group  { background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.3), transparent 60%), linear-gradient(135deg, #1a0f2e, #0f0f1e); border-color: rgba(139,92,246,0.4); }
  .big-card.tournament { background: radial-gradient(circle at 100% 0%, rgba(234,179,8,0.25), transparent 60%), linear-gradient(135deg, #2a1e0a, #1a0f1a); border-color: rgba(234,179,8,0.4); }
  .big-card.puzzle { background: radial-gradient(circle at 100% 0%, rgba(34,197,94,0.25), transparent 60%), linear-gradient(135deg, #0a2a1a, #0f0f1e); border-color: rgba(34,197,94,0.4); }
  .big-card.speed  { background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.25), transparent 60%), linear-gradient(135deg, #0a1e2a, #0f0f1e); border-color: rgba(6,182,212,0.4); }
  .big-card .bc-icon { font-size: 34px; width: 58px; height: 58px; border-radius: 16px; background: rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .big-card .bc-body { flex: 1; }
  .big-card .bc-title { font-size: 17px; font-weight: bold; margin-bottom: 4px; color: #fff; }
  .big-card .bc-desc { font-size: 12px; color: #cbd5e1; line-height: 1.5; }
  .big-card .bc-arrow { font-size: 20px; color: #94a3b8; }
  .soon-badge { position: absolute; top: 10px; left: 10px; background: rgba(234,179,8,0.95); color: #1a1a1a; font-size: 10px; font-weight: 900; padding: 3px 8px; border-radius: 6px; z-index: 2; }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <h1>🎮 <span>بازی‌ها</span></h1>
  </div>

  <a href="/game/quick/" class="big-card bot">
    <div class="bc-icon">⚡</div>
    <div class="bc-body">
      <div class="bc-title">بازی با بات</div>
      <div class="bc-desc">رقیب هوشمند، سه سطح سختی</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>

  <a href="/game/match/" class="big-card player">
    <div class="bc-icon">🌐</div>
    <div class="bc-body">
      <div class="bc-title">بازی با پلیر</div>
      <div class="bc-desc">رقابت آنی با یک حریف تصادفی</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>

  <a href="/game/rooms/manage/" class="big-card group">
    <div class="bc-icon">🚪</div>
    <div class="bc-body">
      <div class="bc-title">بازی گروهی</div>
      <div class="bc-desc">اتاق بساز یا به دوستانت بپیوند</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>

  <div class="big-card tournament soon" onclick="alert('🏆 تورنمنت هفتگی به زودی فعال می‌شود!')">
    <span class="soon-badge">به زودی</span>
    <div class="bc-icon">🏆</div>
    <div class="bc-body">
      <div class="bc-title">تورنمنت هفتگی</div>
      <div class="bc-desc">رقابت با بهترین‌ها، جوایز ویژه</div>
    </div>
    <div class="bc-arrow">←</div>
  </div>

  <div class="big-card puzzle soon" onclick="alert('🎯 بازی معما به زودی فعال می‌شود!')">
    <span class="soon-badge">به زودی</span>
    <div class="bc-icon">🎯</div>
    <div class="bc-body">
      <div class="bc-title">بازی معما</div>
      <div class="bc-desc">حدس کلمه از روی سرنخ</div>
    </div>
    <div class="bc-arrow">←</div>
  </div>

  <a href="/game/quick/bot/?mode=speed" class="big-card speed">
    <div class="bc-icon">⏱️</div>
    <div class="bc-body">
      <div class="bc-title">بازی سرعتی</div>
      <div class="bc-desc">مستقیم با حرف رندوم، فقط ۳۰ ثانیه!</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>
{% endblock %}
'''
backup(p)
write(p, ROOMS_HTML)

# ============================================================
# 2) game/views.py - speed direct mode
# ============================================================
print("\n[2/4] game/views.py")
p = os.path.join(ROOT, "game", "views.py")
src = read(p)

# Ensure mode vars exist
if 'is_speed = (mode == "speed")' not in src:
    old = '    if request.method == "POST":\n        difficulty = request.POST.get("difficulty", "medium")'
    new = '''    mode = request.GET.get("mode", "normal")
    is_speed = (mode == "speed")
    is_challenge = (mode == "challenge")

    if request.method == "POST":
        difficulty = request.POST.get("difficulty", "medium")'''
    if old in src:
        src = src.replace(old, new, 1)
        print("  FIXED: mode vars added")

# Add speed direct block
if "Direct speed mode" in src:
    print("  SKIP: speed direct exists")
else:
    marker = '    is_challenge = (mode == "challenge")'
    direct = '''

    # Direct speed mode - no setup, start immediately
    if is_speed and request.method == "GET":
        difficulty = "medium"
        selected = DEFAULT_CATEGORIES[:8]
        letter = bot_logic.bot_pick_letter(difficulty)
        game = Game.objects.create(
            host=request.user, status="in_round",
            categories=selected, mode="bot",
            difficulty=difficulty, letter_mode="random",
        )
        Player.objects.create(game=game, user=request.user)
        Round.objects.create(game=game, number=1, letter=letter, duration=30)
        return redirect("game:bot_play", game_id=game.id)'''
    if marker in src:
        src = src.replace(marker, marker + direct, 1)
        backup(p); write(p, src)
        print("  FIXED: speed direct mode added")
    else:
        print("  WARN: mode marker not found")

# ============================================================
# 3) social/views.py - full replacement of friends_home
# ============================================================
print("\n[3/4] social/views.py - friends_home")
p = os.path.join(ROOT, "social", "views.py")
src = read(p)

NEW_FRIENDS = '''@login_required
def friends_home(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    now = timezone.now()
    online_threshold = now - timedelta(minutes=5)

    User.objects.filter(id=request.user.id).update(last_seen=now)

    accepted = Friendship.objects.filter(
        Q(from_user=request.user, status="accepted") |
        Q(to_user=request.user, status="accepted")
    ).select_related("from_user", "to_user")

    friends = []
    for f in accepted:
        other = f.to_user if f.from_user_id == request.user.id else f.from_user
        is_online = other.last_seen and other.last_seen >= online_threshold
        stats = Player.objects.filter(user=other).aggregate(
            total_score=Sum('score'), games=Count('id')
        )
        total_score = stats['total_score'] or 0
        games = stats['games'] or 0
        level = 1 + total_score // 100
        friends.append({
            "user": other,
            "avatar": _avatar_of(other),
            "friendship_id": f.id,
            "is_online": is_online,
            "level": level,
            "total_score": total_score,
            "games": games,
        })

    incoming = Friendship.objects.filter(to_user=request.user, status="pending").select_related("from_user")
    incoming_list = [{"req": f, "from": f.from_user, "avatar": _avatar_of(f.from_user)} for f in incoming]

    outgoing = Friendship.objects.filter(from_user=request.user, status="pending").select_related("to_user")
    outgoing_list = [{"req": f, "to": f.to_user, "avatar": _avatar_of(f.to_user)} for f in outgoing]

    pending_invites = GameInvite.objects.filter(to_user=request.user, status="pending").select_related("from_user", "game")

    from alliance.models import Alliance, AllianceMember, AllianceMessage
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

    all_alliances = []
    if not my_alliance:
        for a in Alliance.objects.all().order_by("-created_at")[:30]:
            count = a.member_count()
            if count < a.max_members:
                all_alliances.append({
                    "id": a.id,
                    "name": a.name,
                    "emblem": a.emblem,
                    "tag": a.tag,
                    "member_count": count,
                    "max_members": a.max_members,
                    "has_password": bool(a.password),
                    "leader_avatar": _avatar_of(a.leader),
                })

    return render(request, "social/friends.html", {
        "friends": friends,
        "incoming": incoming_list,
        "outgoing": outgoing_list,
        "pending_invites": pending_invites,
        "my_alliance": my_alliance,
        "all_alliances": all_alliances,
        "active": "friends",
    })

'''

start_marker = 'def friends_home(request):'
start_idx = src.find(start_marker)
if start_idx == -1:
    print("  WARN: friends_home not found")
else:
    dec_start = src.rfind('@login_required', 0, start_idx)
    if dec_start == -1: dec_start = start_idx
    next_func = src.find('\n@login_required\ndef ', start_idx + 50)
    if next_func == -1: next_func = src.find('\ndef ', start_idx + 50)
    if next_func == -1: next_func = len(src)

    src = src[:dec_start] + NEW_FRIENDS + src[next_func:]
    backup(p); write(p, src)
    print("  FIXED: friends_home replaced")

# ============================================================
# 4) friends.html - surgical fixes
# ============================================================
print("\n[4/4] friends.html")
p = os.path.join(ROOT, "social", "templates", "social", "friends.html")
src = read(p)
orig = src
backup(p)

# 4a) CSS
if ".alliance-card.member {" not in src:
    css_end = src.find("{% endblock %}", src.find("{% block extra_css %}"))
    if css_end > 0:
        CSS = '''
  /* ===== کارت اتحاد ===== */
  .alliance-card {
    display: flex; align-items: center; gap: 14px;
    padding: 16px 18px;
    background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.25), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #0f0f1e);
    border: 1.5px solid rgba(139,92,246,0.4);
    border-radius: 18px; text-decoration: none; color: #fff;
    margin-bottom: 16px; transition: all 0.22s;
    box-shadow: 0 8px 25px rgba(139,92,246,0.15);
    cursor: pointer; width: 100%; font-family: inherit; font-size: inherit;
    text-align: inherit;
  }
  .alliance-card:hover { transform: translateY(-3px); border-color: rgba(139,92,246,0.8); box-shadow: 0 15px 35px rgba(139,92,246,0.3); }
  .alliance-card.member {
    background: radial-gradient(circle at 100% 0%, rgba(34,197,94,0.3), transparent 60%),
                linear-gradient(135deg, #0a1f0f, #0f1e15);
    border-color: rgba(34,197,94,0.55); box-shadow: 0 8px 25px rgba(34,197,94,0.2);
  }
  .alliance-card.member:hover { border-color: rgba(34,197,94,0.9); box-shadow: 0 15px 35px rgba(34,197,94,0.4); }
  .ac-icon { font-size: 32px; width: 54px; height: 54px; border-radius: 16px; background: linear-gradient(135deg, rgba(139,92,246,0.3), rgba(6,182,212,0.15)); display: flex; align-items: center; justify-content: center; flex-shrink: 0; border: 1px solid rgba(255,255,255,0.1); }
  .alliance-card.member .ac-icon { background: linear-gradient(135deg, rgba(34,197,94,0.35), rgba(6,182,212,0.15)); border-color: rgba(34,197,94,0.4); }
  .ac-body { flex: 1; text-align: right; min-width: 0; }
  .ac-title { font-size: 16px; font-weight: bold; margin-bottom: 3px; color: #c4b5fd; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  .alliance-card.member .ac-title { color: #86efac; }
  .ac-desc { font-size: 12px; color: var(--muted); }
  .alliance-card.member .ac-desc { color: #86efac; opacity: 0.9; }
  .ac-arrow { font-size: 20px; color: #c4b5fd; }
  .alliance-card.member .ac-arrow { color: #86efac; }
  .ac-tag { font-size: 10px; color: #1a1a1a; background: var(--gold); padding: 2px 8px; border-radius: 6px; font-family: monospace; font-weight: bold; }
  .ac-last { color: #86efac; font-size: 11px; margin-top: 3px; display: block; opacity: 0.9; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .alliance-modal { background: linear-gradient(135deg, rgba(30,41,59,0.98), rgba(15,23,42,0.98)); border: 1.5px solid rgba(139,92,246,0.4); border-radius: 22px; width: 100%; max-width: 460px; max-height: 85vh; overflow-y: auto; padding: 26px 22px; position: relative; box-shadow: 0 25px 60px rgba(0,0,0,0.7); }
  .alliance-modal h2 { font-size: 20px; color: #c4b5fd; text-align: center; margin-bottom: 6px; }
  .alliance-modal .modal-sub { font-size: 12px; color: var(--muted); text-align: center; margin-bottom: 18px; }
  .create-alliance-btn { display: block; padding: 12px; border-radius: 12px; background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; text-decoration: none; text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 16px; box-shadow: 0 8px 20px rgba(34,197,94,0.3); }
  .alliance-item { display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 14px; margin-bottom: 8px; background: rgba(15,23,42,0.6); border: 1px solid var(--border); }
  .alliance-item .emblem { font-size: 26px; width: 46px; height: 46px; border-radius: 12px; background: linear-gradient(135deg, rgba(139,92,246,0.25), rgba(6,182,212,0.15)); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .alliance-item .info { flex: 1; min-width: 0; }
  .alliance-item .name { font-size: 14px; font-weight: bold; color: #fff; margin-bottom: 3px; display: flex; align-items: center; gap: 6px; }
  .alliance-item .tag { background: var(--gold); color: #1a1a1a; font-size: 9px; padding: 1px 6px; border-radius: 5px; font-family: monospace; font-weight: bold; }
  .alliance-item .meta { font-size: 11px; color: var(--muted); }
  .alliance-item .join-btn { padding: 8px 14px; background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; border: none; border-radius: 10px; font-family: inherit; font-weight: bold; font-size: 12px; cursor: pointer; box-shadow: 0 4px 12px rgba(139,92,246,0.3); flex-shrink: 0; }
  .empty-alliances { text-align: center; padding: 30px 10px; color: var(--muted); font-size: 13px; }
  .alliance-password-modal { background: linear-gradient(135deg, rgba(30,41,59,0.98), rgba(15,23,42,0.98)); border: 1.5px solid rgba(139,92,246,0.4); border-radius: 20px; padding: 24px; max-width: 360px; width: 100%; position: relative; }
  .alliance-password-modal h3 { font-size: 18px; color: #c4b5fd; text-align: center; margin-bottom: 8px; }
'''
        src = src[:css_end] + CSS + src[css_end:]
        print("  FIXED: CSS added")

# 4b) Card - force rewrite
if "{% if my_alliance %}" not in src or "ac-last" not in src:
    # Find and replace the whole alliance card section
    card_start = -1
    for marker in ["<!-- کارت اتحاد -->", "{# کارت اتحاد #}", 'class="alliance-card"']:
        idx = src.find(marker)
        if idx > 0:
            card_start = idx
            if marker == 'class="alliance-card"':
                comment_start = src.rfind('<!--', 0, idx)
                if comment_start > 0:
                    card_start = comment_start
            break

    if card_start > 0:
        end_marker = None
        for m in ['{% for inv in pending_invites', '<!-- بنر', '{# بنر', '{% if incoming %}', '<!-- درخواست']:
            i = src.find(m, card_start + 50)
            if i > 0 and (end_marker is None or i < end_marker):
                end_marker = i
        if end_marker:
            NEW_CARD = '''<!-- کارت اتحاد -->
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
    <button type="button" onclick="openAllianceModal()" class="alliance-card">
      <div class="ac-icon">🛡️</div>
      <div class="ac-body">
        <div class="ac-title">اتحاد</div>
        <div class="ac-desc">لیست اتحادها رو ببین یا خودت بساز</div>
      </div>
      <div class="ac-arrow">←</div>
    </button>
  {% endif %}

  '''
            src = src[:card_start] + NEW_CARD + src[end_marker:]
            print("  FIXED: card replaced")
    else:
        print("  WARN: card not found")

# 4c) Modal
if 'id="allianceModal"' not in src:
    content_start = src.find("{% block content %}")
    content_end = src.find("{% endblock %}", content_start) if content_start > 0 else -1
    if content_end > 0:
        MODAL = '''
  {% if not my_alliance %}
  <div class="modal-overlay" id="allianceModal">
    <div class="alliance-modal">
      <button type="button" class="modal-close" onclick="closeAllianceModal()">✕</button>
      <h2>🛡️ لیست اتحادها</h2>
      <p class="modal-sub">یکی رو انتخاب کن یا خودت بساز</p>
      <a href="/alliance/create/" class="create-alliance-btn">+ ساخت اتحاد جدید</a>
      <div class="alliance-list">
        {% for a in all_alliances %}
        <div class="alliance-item">
          <div class="emblem">{{ a.emblem }}</div>
          <div class="info">
            <div class="name">
              {{ a.name }}
              {% if a.tag %}<span class="tag">{{ a.tag }}</span>{% endif %}
              {% if a.has_password %}<span style="font-size:12px;">🔒</span>{% endif %}
            </div>
            <div class="meta">{{ a.leader_avatar }} · {{ a.member_count }} / {{ a.max_members }} عضو</div>
          </div>
          {% if a.has_password %}
            <button type="button" class="join-btn" onclick="openPasswordModal({{ a.id }})">🔐 ورود</button>
          {% else %}
            <form method="post" action="/alliance/join-id/{{ a.id }}/" style="display:inline;">
              {% csrf_token %}
              <button type="submit" class="join-btn">ورود</button>
            </form>
          {% endif %}
        </div>
        {% empty %}
        <div class="empty-alliances">هنوز اتحادی ساخته نشده. اولین نفر باش!</div>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="modal-overlay" id="alliancePasswordModal">
    <div class="alliance-password-modal">
      <h3>🔐 رمز اتحاد</h3>
      <p style="color: var(--muted); font-size: 12px; margin-bottom: 14px;">این اتحاد رمز دارد. رمز را وارد کن.</p>
      <form method="post" id="alliancePasswordForm">
        {% csrf_token %}
        <input type="password" name="password" placeholder="رمز اتحاد" required autofocus
               style="width:100%; padding:12px; border-radius:10px; border:1.5px solid var(--border); background:var(--bg); color:#fff; font-family:inherit; margin-bottom:12px; box-sizing:border-box;">
        <div style="display:flex; gap:8px;">
          <button type="submit" class="join-btn" style="flex:1; padding:12px;">ورود</button>
          <button type="button" onclick="closePasswordModal()" style="flex:1; padding:12px; background:rgba(148,163,184,0.2); color:#fff; border:none; border-radius:10px; font-family:inherit; cursor:pointer; font-weight:bold;">انصراف</button>
        </div>
      </form>
    </div>
  </div>
  {% endif %}
'''
        src = src[:content_end] + MODAL + src[content_end:]
        print("  FIXED: modal HTML added")

# 4d) JS
if "function openAllianceModal" not in src:
    last_end = src.rfind("{% endblock %}")
    if last_end > 0:
        JS = '''
<script>
function openAllianceModal() {
  var m = document.getElementById('allianceModal');
  if (m) { m.classList.add('active'); document.body.style.overflow = 'hidden'; }
  if (window.soundClick) window.soundClick();
}
function closeAllianceModal() {
  var m = document.getElementById('allianceModal');
  if (m) { m.classList.remove('active'); document.body.style.overflow = ''; }
}
function openPasswordModal(allianceId) {
  var form = document.getElementById('alliancePasswordForm');
  if (form) { form.action = '/alliance/join-id/' + allianceId + '/'; }
  var m = document.getElementById('alliancePasswordModal');
  if (m) {
    m.classList.add('active');
    setTimeout(function() { var inp = form.querySelector('input[name="password"]'); if (inp) inp.focus(); }, 100);
  }
}
function closePasswordModal() {
  var m = document.getElementById('alliancePasswordModal');
  if (m) m.classList.remove('active');
}
(function() {
  var am = document.getElementById('allianceModal');
  if (am) am.addEventListener('click', function(e) { if (e.target.id === 'allianceModal') closeAllianceModal(); });
  var pm = document.getElementById('alliancePasswordModal');
  if (pm) pm.addEventListener('click', function(e) { if (e.target.id === 'alliancePasswordModal') closePasswordModal(); });
})();
</script>
'''
        src = src[:last_end] + JS + src[last_end:]
        print("  FIXED: JS added")

if src != orig:
    write(p, src)

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Summary:
  1.  rooms.html: new order = bot, player, group, tournament(soon), puzzle(soon), speed
  2.  Challenge game removed
  3.  Speed mode: direct entry, random letter, 30s timer
  4.  friends_home: rebuilt with my_alliance + all_alliances
  5.  friends.html: alliance card + modal + password prompt

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R
""")
