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
# 1) alliance/models.py - password field
# ============================================================
print("\n[1/10] alliance/models.py")
p = os.path.join(ROOT, "alliance", "models.py")
src = read(p)

if "password = models.CharField" in src and "class Alliance(" in src[:src.find("password = models.CharField")]:
    print("  SKIP: password exists")
else:
    old = "    max_members = models.PositiveIntegerField(default=30)"
    new = '''    max_members = models.PositiveIntegerField(default=30)
    password = models.CharField(max_length=32, blank=True, default="")'''
    if old in src:
        backup(p); src = src.replace(old, new, 1); write(p, src)
        print("  FIXED: password field added")
    else:
        print("  WARN: max_members not found")

# ============================================================
# 2) alliance/views.py - join_alliance + password in create
# ============================================================
print("\n[2/10] alliance/views.py")
p = os.path.join(ROOT, "alliance", "views.py")
src = read(p)

# 2a) add join_alliance view
if "def join_alliance(request, alliance_id):" in src:
    print("  SKIP: join_alliance exists")
else:
    backup(p)
    new_view = '''

@login_required
def join_alliance(request, alliance_id):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    if AllianceMember.objects.filter(user=request.user).exists():
        messages.info(request, "شما الان عضو یک اتحاد هستید.")
        return redirect("social:friends_home")

    a = get_object_or_404(Alliance, id=alliance_id)

    if request.method != "POST":
        return redirect("social:friends_home")

    if a.password:
        entered = (request.POST.get("password") or "").strip()
        if entered != a.password:
            messages.error(request, "رمز اتحاد اشتباه است.")
            return redirect("social:friends_home")

    if a.member_count() >= a.max_members:
        messages.error(request, "این اتحاد پر شده است.")
        return redirect("social:friends_home")

    AllianceMember.objects.create(alliance=a, user=request.user, role="member")
    messages.success(request, f"به اتحاد «{a.name}» پیوستی!")
    return redirect("alliance:detail", alliance_id=a.id)
'''
    src = src.rstrip() + "\n" + new_view + "\n"
    write(p, src)
    print("  FIXED: join_alliance added")

# 2b) create with password (handle both cases)
src = read(p)
old_a = '''            try:
                max_members = int(request.POST.get("max_members") or 30)
            except (ValueError, TypeError):
                max_members = 30
            max_members = max(5, min(50, max_members))

            a = Alliance.objects.create(
                name=name, tag=tag, description=description,
                emblem=emblem or "🛡️", leader=request.user,
                max_members=max_members,
            )'''
new_a = '''            try:
                max_members = int(request.POST.get("max_members") or 30)
            except (ValueError, TypeError):
                max_members = 30
            max_members = max(5, min(50, max_members))
            password = (request.POST.get("password") or "").strip()[:32]

            a = Alliance.objects.create(
                name=name, tag=tag, description=description,
                emblem=emblem or "🛡️", leader=request.user,
                max_members=max_members, password=password,
            )'''
old_b = '''            a = Alliance.objects.create(
                name=name, tag=tag, description=description,
                emblem=emblem or "🛡️", leader=request.user,
            )'''
new_b = '''            try:
                max_members = int(request.POST.get("max_members") or 30)
            except (ValueError, TypeError):
                max_members = 30
            max_members = max(5, min(50, max_members))
            password = (request.POST.get("password") or "").strip()[:32]

            a = Alliance.objects.create(
                name=name, tag=tag, description=description,
                emblem=emblem or "🛡️", leader=request.user,
                max_members=max_members, password=password,
            )'''

if "password=password" in src:
    print("  SKIP: create has password")
elif old_a in src:
    backup(p); src = src.replace(old_a, new_a, 1); write(p, src)
    print("  FIXED (A): create with password")
elif old_b in src:
    backup(p); src = src.replace(old_b, new_b, 1); write(p, src)
    print("  FIXED (B): create with max_members + password")
else:
    print("  WARN: create block not found")

# ============================================================
# 3) alliance/urls.py - add join-id route
# ============================================================
print("\n[3/10] alliance/urls.py")
p = os.path.join(ROOT, "alliance", "urls.py")
src = read(p)

if "join-id" in src:
    print("  SKIP: route exists")
else:
    old = '    path("join/", views.join_by_code, name="join"),'
    new = old + '\n    path("join-id/<int:alliance_id>/", views.join_alliance, name="join_alliance"),'
    if old in src:
        backup(p); src = src.replace(old, new, 1); write(p, src)
        print("  FIXED: join-id route added")
    else:
        print("  WARN: join route not found")

# ============================================================
# 4) social/views.py - all_alliances in context
# ============================================================
print("\n[4/10] social/views.py")
p = os.path.join(ROOT, "social", "views.py")
src = read(p)

if "all_alliances" in src:
    print("  SKIP: all_alliances exists")
else:
    # Update import
    src = src.replace(
        "from alliance.models import AllianceMember, AllianceMessage",
        "from alliance.models import Alliance, AllianceMember, AllianceMessage"
    )
    if "from alliance.models import Alliance, AllianceMember" not in src:
        # no existing import line, add fresh one
        src = src.replace(
            "    from alliance.models import AllianceMember, AllianceMessage",
            "    from alliance.models import Alliance, AllianceMember, AllianceMessage"
        )

    # Add all_alliances after my_alliance construction
    old = '''            "last_message": last_msg.body if last_msg else "",
            "last_message_sender": last_msg.sender.alias if last_msg else "",
        }

    return render(request, "social/friends.html", {'''
    new = '''            "last_message": last_msg.body if last_msg else "",
            "last_message_sender": last_msg.sender.alias if last_msg else "",
        }

    # لیست اتحادهای قابل پیوستن (برای مودال)
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

    return render(request, "social/friends.html", {'''
    if old in src:
        src = src.replace(old, new, 1)
        src = src.replace(
            '        "my_alliance": my_alliance,\n        "active": "friends",',
            '        "my_alliance": my_alliance,\n        "all_alliances": all_alliances,\n        "active": "friends",',
            1,
        )
        backup(p); write(p, src)
        print("  FIXED: all_alliances passed")
    else:
        print("  WARN: my_alliance block not found")

# ============================================================
# 5) friends.html - modal + list + password prompt
# ============================================================
print("\n[5/10] friends.html")
p = os.path.join(ROOT, "social", "templates", "social", "friends.html")
src = read(p)

# 5a) Change alliance card else-branch to button
old_card = '''  {% else %}
    <a href="/alliance/" class="alliance-card">
      <div class="ac-icon">🛡️</div>
      <div class="ac-body">
        <div class="ac-title">اتحاد</div>
        <div class="ac-desc">با دوستات یه تیم بساز و با هم بازی کن</div>
      </div>
      <div class="ac-arrow">←</div>
    </a>
  {% endif %}'''
new_card = '''  {% else %}
    <button type="button" onclick="openAllianceModal()" class="alliance-card" style="width:100%; border:none; cursor:pointer; font-family:inherit; text-align:inherit; font-size:inherit;">
      <div class="ac-icon">🛡️</div>
      <div class="ac-body">
        <div class="ac-title">اتحاد</div>
        <div class="ac-desc">لیست اتحادها رو ببین یا خودت بساز</div>
      </div>
      <div class="ac-arrow">←</div>
    </button>
  {% endif %}'''

if 'onclick="openAllianceModal()"' in src:
    print("  SKIP: button exists")
elif old_card in src:
    src = src.replace(old_card, new_card, 1)
    print("  FIXED: card is button now")
else:
    print("  WARN: else-branch card not found")

# 5b) Add CSS
if "id=\"allianceModal\"" not in src:
    css_start = src.find("{% block extra_css %}")
    if css_start >= 0:
        css_end = src.find("{% endblock %}", css_start)
        if css_end > 0:
            new_css = '''

  /* ===== مودال لیست اتحادها ===== */
  .alliance-modal {
    background: linear-gradient(135deg, rgba(30,41,59,0.98), rgba(15,23,42,0.98));
    border: 1.5px solid rgba(139,92,246,0.4);
    border-radius: 22px;
    width: 100%;
    max-width: 460px;
    max-height: 85vh;
    overflow-y: auto;
    padding: 26px 22px;
    position: relative;
    box-shadow: 0 25px 60px rgba(0,0,0,0.7);
  }
  .alliance-modal h2 { font-size: 20px; color: #c4b5fd; text-align: center; margin-bottom: 6px; }
  .alliance-modal .modal-sub { font-size: 12px; color: var(--muted); text-align: center; margin-bottom: 18px; }
  .create-alliance-btn {
    display: block; padding: 12px; border-radius: 12px;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: #fff; text-decoration: none; text-align: center;
    font-weight: bold; font-size: 14px; margin-bottom: 16px;
    box-shadow: 0 8px 20px rgba(34,197,94,0.3);
  }
  .alliance-item {
    display: flex; align-items: center; gap: 12px;
    padding: 12px; border-radius: 14px; margin-bottom: 8px;
    background: rgba(15,23,42,0.6); border: 1px solid var(--border);
  }
  .alliance-item .emblem {
    font-size: 26px; width: 46px; height: 46px; border-radius: 12px;
    background: linear-gradient(135deg, rgba(139,92,246,0.25), rgba(6,182,212,0.15));
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .alliance-item .info { flex: 1; min-width: 0; }
  .alliance-item .name { font-size: 14px; font-weight: bold; color: #fff; margin-bottom: 3px; display: flex; align-items: center; gap: 6px; }
  .alliance-item .tag { background: var(--gold); color: #1a1a1a; font-size: 9px; padding: 1px 6px; border-radius: 5px; font-family: monospace; font-weight: bold; }
  .alliance-item .meta { font-size: 11px; color: var(--muted); }
  .alliance-item .join-btn {
    padding: 8px 14px; background: linear-gradient(135deg, #8b5cf6, #6b4eff);
    color: #fff; border: none; border-radius: 10px; font-family: inherit;
    font-weight: bold; font-size: 12px; cursor: pointer;
    box-shadow: 0 4px 12px rgba(139,92,246,0.3); flex-shrink: 0;
  }
  .empty-alliances { text-align: center; padding: 30px 10px; color: var(--muted); font-size: 13px; }
  .alliance-password-modal {
    background: linear-gradient(135deg, rgba(30,41,59,0.98), rgba(15,23,42,0.98));
    border: 1.5px solid rgba(139,92,246,0.4);
    border-radius: 20px; padding: 24px; max-width: 360px; width: 100%; position: relative;
  }
  .alliance-password-modal h3 { font-size: 18px; color: #c4b5fd; text-align: center; margin-bottom: 8px; }'''
            src = src[:css_end] + new_css + src[css_end:]
            print("  FIXED: CSS added")

# 5c) Add modal HTML inside content block
if "id=\"allianceModal\"" not in src:
    content_start = src.find("{% block content %}")
    if content_start >= 0:
        content_end = src.find("{% endblock %}", content_start)
        if content_end > 0:
            modal_html = '''

  {% if not my_alliance %}
  <!-- مودال لیست اتحادها -->
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

  <!-- مودال رمز اتحاد -->
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
            src = src[:content_end] + modal_html + src[content_end:]
            print("  FIXED: modal HTML added")

# 5d) Add JS in extra_js
if "function openAllianceModal" not in src:
    last_endblock = src.rfind("{% endblock %}")
    if last_endblock > 0:
        js_code = '''

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
        src = src[:last_endblock] + js_code + src[last_endblock:]
        print("  FIXED: JS added")

backup(p)
write(p, src)

# ============================================================
# 6) create.html - password field
# ============================================================
print("\n[6/10] create.html")
p = os.path.join(ROOT, "alliance", "templates", "alliance", "create.html")
src = read(p)
if 'name="password"' in src:
    print("  SKIP: password field exists")
else:
    anchor = '<textarea name="description" maxlength="200" placeholder="چند خط درباره تیمت..."></textarea>'
    add = anchor + '''

      <label>رمز اتحاد (اختیاری)</label>
      <input type="password" name="password" maxlength="32" placeholder="خالی = بدون رمز" style="width:100%; padding:12px 14px; border-radius:12px; border:1.5px solid var(--border); background:var(--bg); color:var(--text); font-size:15px; font-family:inherit; margin-bottom:12px;">'''
    if anchor in src:
        backup(p); src = src.replace(anchor, add, 1); write(p, src)
        print("  FIXED: password field added")
    else:
        print("  WARN: description textarea not found")

# ============================================================
# 7) alliance/home.html - remove join-by-code button
# ============================================================
print("\n[7/10] alliance/home.html")
p = os.path.join(ROOT, "alliance", "templates", "alliance", "home.html")
src = read(p)
if 'href="/alliance/join/"' not in src:
    print("  SKIP: join-by-code already removed")
else:
    old = '''    <a href="/alliance/join/" class="action-card action-join">
      <div class="action-icon">🔑</div>
      <div class="action-title">ورود با کد</div>
      <div class="action-desc">کد ۶ حرفی دوستت</div>
    </a>'''
    if old in src:
        src = src.replace(old, '''    <a href="/social/" class="action-card action-join">
      <div class="action-icon">👥</div>
      <div class="action-title">پیوستن به اتحاد</div>
      <div class="action-desc">از صفحه دوستان اقدام کن</div>
    </a>''', 1)
        backup(p); write(p, src)
        print("  FIXED: join card -> go to friends")
    else:
        print("  WARN: join card not found")

# ============================================================
# 8) rooms.html - full rewrite with 7 cards
# ============================================================
print("\n[8/10] rooms.html (full rewrite)")
p = os.path.join(ROOT, "game", "templates", "game", "rooms.html")
ROOMS_HTML = '''{% extends "base.html" %}
{% block title %}بازی‌ها{% endblock %}

{% block extra_css %}
<style>
  .page-head { margin-bottom: 20px; }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }

  .big-card {
    border-radius: 20px; padding: 20px 20px; margin-bottom: 12px;
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
  .big-card.speed  { background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.25), transparent 60%), linear-gradient(135deg, #0a1e2a, #0f0f1e); border-color: rgba(6,182,212,0.4); }
  .big-card.challenge { background: radial-gradient(circle at 100% 0%, rgba(239,68,68,0.25), transparent 60%), linear-gradient(135deg, #2a0a0a, #1a0f1a); border-color: rgba(239,68,68,0.4); }
  .big-card.player { background: radial-gradient(circle at 100% 0%, rgba(59,130,246,0.25), transparent 60%), linear-gradient(135deg, #0a1a2a, #0f0f1e); border-color: rgba(59,130,246,0.4); }
  .big-card.group  { background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.3), transparent 60%), linear-gradient(135deg, #1a0f2e, #0f0f1e); border-color: rgba(139,92,246,0.4); }
  .big-card.tournament { background: radial-gradient(circle at 100% 0%, rgba(234,179,8,0.25), transparent 60%), linear-gradient(135deg, #2a1e0a, #1a0f1a); border-color: rgba(234,179,8,0.4); }
  .big-card.puzzle { background: radial-gradient(circle at 100% 0%, rgba(34,197,94,0.25), transparent 60%), linear-gradient(135deg, #0a2a1a, #0f0f1e); border-color: rgba(34,197,94,0.4); }

  .big-card .bc-icon {
    font-size: 34px; width: 58px; height: 58px;
    border-radius: 16px; background: rgba(255,255,255,0.08);
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .big-card .bc-body { flex: 1; }
  .big-card .bc-title { font-size: 17px; font-weight: bold; margin-bottom: 4px; color: #fff; }
  .big-card .bc-desc { font-size: 12px; color: #cbd5e1; line-height: 1.5; }
  .big-card .bc-arrow { font-size: 20px; color: #94a3b8; }

  .soon-badge {
    position: absolute; top: 10px; left: 10px;
    background: rgba(234,179,8,0.95); color: #1a1a1a;
    font-size: 10px; font-weight: 900;
    padding: 3px 8px; border-radius: 6px; z-index: 2;
  }
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

  <a href="/game/quick/bot/?mode=speed" class="big-card speed">
    <div class="bc-icon">⏱️</div>
    <div class="bc-body">
      <div class="bc-title">بازی سرعتی</div>
      <div class="bc-desc">فقط ۳۰ ثانیه فرصت داری!</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>

  <a href="/game/quick/bot/?mode=challenge" class="big-card challenge">
    <div class="bc-icon">🔥</div>
    <div class="bc-body">
      <div class="bc-title">بازی چالشی</div>
      <div class="bc-desc">فقط حروف سخت: ث، ض، ظ، ژ...</div>
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
{% endblock %}
'''
backup(p)
write(p, ROOMS_HTML)

# ============================================================
# 9) base.html - flash messages
# ============================================================
print("\n[9/10] base.html - flash messages")
p = os.path.join(ROOT, "templates", "base.html")
src = read(p)

if "flash-messages" in src:
    print("  SKIP: flash messages exist")
else:
    old = '''<div class="container">
{% block content %}{% endblock %}
</div>'''
    new = '''<div class="container">
{% if messages %}
<div class="flash-messages">
  {% for m in messages %}
    <div class="flash-msg flash-{{ m.tags }}">{{ m }}</div>
  {% endfor %}
</div>
{% endif %}
{% block content %}{% endblock %}
</div>'''
    if old in src:
        css_anchor = "    .container {"
        css_add = '''    .flash-messages { margin-bottom: 14px; }
    .flash-msg {
      padding: 12px 16px; border-radius: 12px; margin-bottom: 8px;
      font-size: 13px; text-align: right; line-height: 1.6;
    }
    .flash-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .flash-error   { background: rgba(239,68,68,0.15);  color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }
    .flash-info    { background: rgba(59,130,246,0.15); color: #93c5fd; border: 1px solid rgba(59,130,246,0.3); }
    .flash-warning { background: rgba(234,179,8,0.15);  color: #fde68a; border: 1px solid rgba(234,179,8,0.35); }
    .container {'''
        if css_anchor in src:
            src = src.replace(css_anchor, css_add, 1)
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: flash messages added")
    else:
        print("  WARN: container block not found")

# ============================================================
# 10) Run migrations
# ============================================================
print("\n[10/10] Running migrations...")
import subprocess, sys
for cmd in [
    [sys.executable, "manage.py", "makemigrations", "alliance", "--verbosity=1"],
    [sys.executable, "manage.py", "migrate", "--verbosity=1"],
]:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd[1:])}")
    if r.stdout.strip(): print("   ", r.stdout.strip().replace("\n", "\n    "))
    if r.returncode != 0 and r.stderr.strip():
        print("   STDERR:", r.stderr.strip())

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Summary:
  1.  Alliance.password field + migration
  2.  join_alliance view (checks password)
  3.  /alliance/join-id/<id>/ route
  4.  all_alliances passed to friends context
  5.  friends.html: card opens modal with list + password prompt
  6.  create.html: password field
  7.  alliance/home.html: join-by-code removed, redirects to friends
  8.  rooms.html: 7 cards (5 active + 2 soon: tournament, puzzle)
  9.  base.html: flash messages display
  10. Migrations applied

Next:
  Ctrl+C (stop server)
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R
""")
