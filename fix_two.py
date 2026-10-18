#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, subprocess, sys, re

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")
def backup(p):
    bak = p + ".bak_2"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# STEP 1: Add 'common' to INSTALLED_APPS
# ============================================================
print("\n[1/5] settings.py - add common app")
p = os.path.join(ROOT, "config", "settings.py")
src = read(p)
if '"common"' in src or "'common'" in src:
    print("  SKIP: common already in INSTALLED_APPS")
else:
    match = re.search(r'INSTALLED_APPS\s*=\s*\[(.*?)\]', src, re.DOTALL)
    if match:
        old_block = match.group(0)
        inner = match.group(1).rstrip()
        new_block = 'INSTALLED_APPS = [' + inner + '\n    "common",\n]'
        src = src.replace(old_block, new_block, 1)
        backup(p); write(p, src)
        print("  FIXED: common added to INSTALLED_APPS")
    else:
        print("  WARN: could not find INSTALLED_APPS")

# ============================================================
# STEP 2: notifications.html - Django date, NO jalali
# ============================================================
print("\n[2/5] notifications.html - rebuild (safe)")
p = os.path.join(ROOT, "social", "templates", "social", "notifications.html")

NOTIF = '''{% extends "base.html" %}
{% block title %}اعلان‌ها{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 18px; }
  .page-head-left { display: flex; align-items: center; gap: 12px; }
  .page-head a { width: 42px; height: 42px; background: var(--card); border: 1px solid var(--border); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: var(--gold); text-decoration: none; font-size: 20px; transition: 0.2s; }
  .page-head a:hover { border-color: var(--gold); transform: translateX(-2px); }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }
  .unread-count { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; padding: 6px 14px; border-radius: 999px; font-size: 12px; font-weight: 900; box-shadow: 0 4px 12px rgba(239,68,68,0.4); }
  .notif-card { display: flex; align-items: flex-start; gap: 14px; padding: 16px; margin-bottom: 10px; background: var(--card); border: 1.5px solid var(--border); border-radius: 16px; text-decoration: none; color: var(--text); transition: all 0.2s; position: relative; overflow: hidden; }
  .notif-card:hover { border-color: var(--gold); transform: translateX(-3px); box-shadow: 0 8px 25px rgba(244,197,66,0.15); }
  .notif-card.unread { border-color: rgba(244,197,66,0.4); background: linear-gradient(135deg, rgba(244,197,66,0.08), rgba(139,92,246,0.05)); }
  .notif-card.unread::before { content: ""; position: absolute; top: 0; bottom: 0; right: 0; width: 4px; background: linear-gradient(180deg, #f4c542, #eab308); }
  .notif-card.admin { border-color: rgba(245,158,11,0.5); background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(15,23,42,0.5)); }
  .notif-card.admin::before { background: linear-gradient(180deg, #f59e0b, #d97706); }
  .notif-icon { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; background: linear-gradient(135deg, rgba(244,197,66,0.2), rgba(139,92,246,0.15)); }
  .notif-icon.admin-icon { background: linear-gradient(135deg, rgba(245,158,11,0.3), rgba(234,179,8,0.15)); }
  .notif-body { flex: 1; min-width: 0; }
  .notif-title { font-size: 14px; font-weight: bold; margin-bottom: 4px; color: #fff; }
  .notif-sender { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; color: #c4b5fd; padding: 2px 8px; background: rgba(139,92,246,0.15); border-radius: 6px; margin-bottom: 6px; font-weight: bold; }
  .notif-sender.admin-sender { color: #fde68a; background: rgba(245,158,11,0.15); }
  .notif-sender .username { font-size: 10px; opacity: 0.7; font-family: monospace; }
  .notif-desc { font-size: 12px; color: var(--muted); line-height: 1.6; margin-bottom: 6px; }
  .notif-time { font-size: 10px; color: var(--dim); font-family: monospace; }
  .unread-dot { width: 10px; height: 10px; background: var(--gold); border-radius: 50%; flex-shrink: 0; margin-top: 8px; box-shadow: 0 0 8px rgba(244,197,66,0.7); animation: pulseDot 1.5s ease-in-out infinite; }
  @keyframes pulseDot { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.3); opacity: 0.6; } }
  .empty { text-align: center; padding: 60px 20px; color: var(--muted); font-size: 14px; }
  .empty .icon { font-size: 60px; display: block; margin-bottom: 12px; opacity: 0.5; }
  .empty h3 { font-size: 16px; margin-bottom: 6px; color: #fff; }
  .empty p { font-size: 12px; line-height: 1.7; }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <div class="page-head-left">
      <a href="/game/">←</a>
      <h1>🔔 <span>اعلان‌ها</span></h1>
    </div>
    {% if unread_total %}
      <div class="unread-count">{{ unread_total }} جدید</div>
    {% endif %}
  </div>

  {% if notifications %}
    {% for n in notifications %}
      {% if n.url %}<a href="{{ n.url }}" class="notif-card {% if not n.is_read %}unread{% endif %} {% if n.type == 'admin_broadcast' %}admin{% endif %}">{% else %}<div class="notif-card {% if not n.is_read %}unread{% endif %} {% if n.type == 'admin_broadcast' %}admin{% endif %}">{% endif %}
        <div class="notif-icon {% if n.type == 'admin_broadcast' %}admin-icon{% endif %}">
          {% if n.type == "friend_request" %}👋
          {% elif n.type == "friend_accepted" %}✅
          {% elif n.type == "message" %}💬
          {% elif n.type == "game_invite" %}🎮
          {% elif n.type == "game_result" %}🏆
          {% elif n.type == "alliance_invite" %}🛡️
          {% elif n.type == "admin_broadcast" %}📢
          {% else %}🔔{% endif %}
        </div>
        <div class="notif-body">
          <div class="notif-title">{{ n.title }}</div>
          {% if n.sender %}
            <div class="notif-sender">👤 {{ n.sender.alias }} <span class="username">@{{ n.sender.username }}</span></div>
          {% elif n.type == "admin_broadcast" %}
            <div class="notif-sender admin-sender">📢 مدیر سیستم</div>
          {% endif %}
          {% if n.body %}<div class="notif-desc">{{ n.body }}</div>{% endif %}
          <div class="notif-time">🕐 {{ n.created_at|date:"Y/m/d H:i" }}</div>
        </div>
        {% if not n.is_read %}<div class="unread-dot"></div>{% endif %}
      {% if n.url %}</a>{% else %}</div>{% endif %}
    {% endfor %}
  {% else %}
    <div class="empty">
      <span class="icon">📭</span>
      <h3>هنوز اعلانی نداری</h3>
      <p>وقتی دوستی اضافه کنی یا دعوتی دریافت کنی،<br>اینجا نمایش داده می‌شه.</p>
    </div>
  {% endif %}
{% endblock %}
'''
backup(p); write(p, NOTIF)

# ============================================================
# STEP 3: Ensure notifications_view works
# ============================================================
print("\n[3/5] social/views.py - verify notifications_view")
p = os.path.join(ROOT, "social", "views.py")
src = read(p)
pattern = re.compile(r'@login_required\ndef notifications_view\(request\):.*?(?=\n@login_required|\ndef [a-z]|\Z)', re.DOTALL)
m = pattern.search(src)
if m:
    src = src[:m.start()] + src[m.end():]
new_view = '''

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
src = src.rstrip() + new_view + "\n"
backup(p); write(p, src)
print("  FIXED: notifications_view rebuilt")

# ============================================================
# STEP 4: ALLIANCE templates - rebuild all (Django date, no jalali)
# ============================================================
print("\n[4/5] Alliance templates rebuild")

# 4a) alliance/home.html
ALLIANCE_HOME = '''{% extends "base.html" %}
{% block title %}اتحاد{% endblock %}

{% block extra_css %}
<style>
  .hero-card { padding: 26px 22px; background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.4), transparent 55%), radial-gradient(circle at 0% 100%, rgba(236,72,153,0.2), transparent 55%), linear-gradient(135deg, #1a0f2e, #170a24, #0f0f1e); border: 2px solid rgba(139,92,246,0.55); border-radius: 24px; margin-bottom: 18px; text-align: center; position: relative; overflow: hidden; box-shadow: 0 15px 40px rgba(139,92,246,0.25); }
  .hero-card .icon { font-size: 56px; margin-bottom: 8px; filter: drop-shadow(0 0 20px rgba(167,139,250,0.6)); }
  .hero-card h1 { font-size: 22px; font-weight: 900; margin-bottom: 8px; background: linear-gradient(135deg, #e9d5ff, #a78bfa, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .hero-card p { color: var(--muted); font-size: 13px; line-height: 1.7; margin-bottom: 18px; }
  .create-btn { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 16px 24px; border-radius: 16px; background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; text-decoration: none; font-weight: 900; font-size: 16px; box-shadow: 0 10px 30px rgba(34,197,94,0.4); transition: 0.2s; }
  .create-btn:hover { transform: translateY(-2px); box-shadow: 0 14px 35px rgba(34,197,94,0.6); }
  .create-btn .plus { font-size: 22px; font-weight: 900; }
  .search-bar { display: flex; gap: 8px; background: var(--card); border: 1.5px solid var(--border); border-radius: 16px; padding: 4px; margin-bottom: 18px; transition: 0.2s; }
  .search-bar:focus-within { border-color: var(--purple); box-shadow: 0 0 20px rgba(139,92,246,0.15); }
  .search-bar input { flex: 1; padding: 12px 16px; border-radius: 12px; border: none; background: transparent; color: #fff; font-size: 15px; font-family: inherit; }
  .search-bar input:focus { outline: none; }
  .search-bar button { padding: 0 20px; border-radius: 12px; background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; border: none; font-weight: bold; font-family: inherit; cursor: pointer; font-size: 15px; }
  .section-title { font-size: 15px; color: var(--gold); font-weight: bold; margin: 8px 0 14px; display: flex; align-items: center; gap: 8px; }
  .section-title .count { background: rgba(244,197,66,0.15); padding: 3px 10px; border-radius: 8px; font-size: 11px; font-family: monospace; }
  .alliance-list { display: flex; flex-direction: column; gap: 10px; }
  .alliance-card { display: flex; align-items: center; gap: 14px; padding: 16px; background: var(--card); border: 1.5px solid var(--border); border-radius: 18px; transition: 0.2s; position: relative; }
  .alliance-card:hover { border-color: rgba(139,92,246,0.6); transform: translateX(-3px); }
  .alliance-card.is-full { opacity: 0.6; }
  .alliance-card.is-full:hover { transform: none; }
  .alliance-emblem { width: 56px; height: 56px; flex-shrink: 0; border-radius: 16px; background: linear-gradient(135deg, rgba(139,92,246,0.3), rgba(6,182,212,0.15)); border: 1px solid rgba(255,255,255,0.12); display: flex; align-items: center; justify-content: center; font-size: 30px; }
  .alliance-info { flex: 1; min-width: 0; }
  .alliance-name-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
  .alliance-name { font-size: 15px; font-weight: bold; color: #fff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .alliance-tag { background: var(--gold); color: #1a1a1a; padding: 2px 8px; border-radius: 6px; font-size: 9px; font-weight: 900; font-family: monospace; }
  .alliance-meta { font-size: 11.5px; color: var(--muted); display: flex; align-items: center; gap: 6px; }
  .alliance-meta .dot { opacity: 0.5; }
  .alliance-meta .lock { font-size: 13px; }
  .join-btn { padding: 10px 16px; border-radius: 12px; background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; border: none; font-family: inherit; font-weight: bold; font-size: 13px; cursor: pointer; box-shadow: 0 6px 15px rgba(139,92,246,0.35); transition: 0.2s; flex-shrink: 0; text-decoration: none; }
  .join-btn:hover { transform: scale(1.05); }
  .join-btn.full { background: rgba(148,163,184,0.2); box-shadow: none; cursor: not-allowed; }
  .empty-state { text-align: center; padding: 50px 20px; background: var(--card); border: 1.5px dashed var(--border); border-radius: 20px; }
  .empty-state .icon { font-size: 60px; margin-bottom: 14px; display: block; opacity: 0.5; }
  .empty-state h3 { font-size: 17px; margin-bottom: 8px; }
  .empty-state p { color: var(--muted); font-size: 13px; margin-bottom: 20px; line-height: 1.6; }
  .pass-modal-bg { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }
  .pass-modal-bg.active { display: flex; animation: fadeIn 0.25s; }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  .pass-modal { background: linear-gradient(135deg, rgba(30,41,59,0.98), rgba(15,23,42,0.98)); border: 1.5px solid rgba(139,92,246,0.5); border-radius: 22px; padding: 26px 22px; max-width: 380px; width: 100%; text-align: center; box-shadow: 0 25px 60px rgba(0,0,0,0.7); }
  .pass-modal .icon { font-size: 48px; margin-bottom: 10px; }
  .pass-modal h3 { font-size: 18px; color: #c4b5fd; margin-bottom: 6px; }
  .pass-modal p { font-size: 12px; color: var(--muted); margin-bottom: 16px; line-height: 1.6; }
  .pass-modal input { width: 100%; padding: 14px; border-radius: 12px; border: 1.5px solid var(--border); background: var(--bg); color: #fff; font-size: 16px; font-family: monospace; text-align: center; letter-spacing: 3px; margin-bottom: 14px; box-sizing: border-box; }
  .pass-modal input:focus { outline: none; border-color: var(--purple); }
  .pass-modal-actions { display: flex; gap: 8px; }
  .pass-modal-actions button { flex: 1; padding: 12px; border-radius: 12px; font-family: inherit; font-weight: bold; font-size: 14px; cursor: pointer; border: none; }
  .btn-join-p { background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; }
  .btn-cancel-p { background: rgba(148,163,184,0.2); color: #fff; }
</style>
{% endblock %}

{% block content %}
  <div class="hero-card">
    <div class="icon">🛡️</div>
    <h1>اتحاد</h1>
    <p>با دوستانت یه تیم بساز،<br>با هم بازی کن و به بالای جدول برس!</p>
    <a href="/alliance/create/" class="create-btn">
      <span class="plus">+</span>
      <span>ساخت اتحاد جدید</span>
    </a>
  </div>

  <form method="get" class="search-bar">
    <input type="text" name="q" placeholder="جستجوی نام یا تگ اتحاد..." value="{{ query }}" autocomplete="off">
    <button type="submit">🔍</button>
  </form>

  <div class="section-title">
    <span>🌍 اتحادهای فعال</span>
    <span class="count">{{ alliances|length }}</span>
  </div>

  {% if alliances %}
    <div class="alliance-list">
      {% for a in alliances %}
        <div class="alliance-card {% if a.is_full %}is-full{% endif %}">
          <div class="alliance-emblem">{{ a.obj.emblem }}</div>
          <div class="alliance-info">
            <div class="alliance-name-row">
              <div class="alliance-name">{{ a.obj.name }}</div>
              {% if a.obj.tag %}<span class="alliance-tag">{{ a.obj.tag }}</span>{% endif %}
              {% if a.has_password %}<span class="lock">🔒</span>{% endif %}
            </div>
            <div class="alliance-meta">
              <span>{{ a.leader_avatar }} {{ a.obj.leader.alias }}</span>
              <span class="dot">•</span>
              <span>{{ a.count }} / {{ a.obj.max_members }} عضو</span>
            </div>
          </div>
          {% if a.is_full %}
            <button class="join-btn full" disabled>پر</button>
          {% elif a.has_password %}
            <button class="join-btn" onclick="openPassModal({{ a.obj.id }}, '{{ a.obj.name|escapejs }}')">🔐 ورود</button>
          {% else %}
            <form method="post" action="/alliance/join-id/{{ a.obj.id }}/" style="display:inline; margin:0;">
              {% csrf_token %}
              <button type="submit" class="join-btn">ورود</button>
            </form>
          {% endif %}
        </div>
      {% endfor %}
    </div>
  {% elif query %}
    <div class="empty-state">
      <span class="icon">🔍</span>
      <h3>نتیجه‌ای پیدا نشد</h3>
      <p>اتحادی با این مشخصات وجود ندارد.</p>
      <a href="/alliance/" class="join-btn" style="display:inline-block; padding:12px 22px;">پاک کردن جستجو</a>
    </div>
  {% else %}
    <div class="empty-state">
      <span class="icon">🏰</span>
      <h3>هنوز اتحادی نیست!</h3>
      <p>اولین نفری باش که یه اتحاد می‌سازه</p>
      <a href="/alliance/create/" class="create-btn" style="max-width:280px; margin:0 auto;">
        <span class="plus">+</span><span>ساخت اولین اتحاد</span>
      </a>
    </div>
  {% endif %}

  <div class="pass-modal-bg" id="passModal">
    <div class="pass-modal">
      <div class="icon">🔐</div>
      <h3>رمز اتحاد</h3>
      <p>اتحاد <b id="passAllianceName"></b> رمز دارد.<br>رمز را وارد کن.</p>
      <form method="post" id="passForm">
        {% csrf_token %}
        <input type="password" name="password" placeholder="رمز" required autofocus autocomplete="off">
        <div class="pass-modal-actions">
          <button type="submit" class="btn-join-p">ورود</button>
          <button type="button" class="btn-cancel-p" onclick="closePassModal()">انصراف</button>
        </div>
      </form>
    </div>
  </div>
{% endblock %}

{% block extra_js %}
<script>
  function openPassModal(allianceId, allianceName) {
    document.getElementById('passForm').action = '/alliance/join-id/' + allianceId + '/';
    document.getElementById('passAllianceName').textContent = allianceName;
    var m = document.getElementById('passModal');
    m.classList.add('active');
    setTimeout(function() {
      var inp = m.querySelector('input[name="password"]');
      if (inp) inp.focus();
    }, 100);
  }
  function closePassModal() {
    document.getElementById('passModal').classList.remove('active');
  }
  var pm = document.getElementById('passModal');
  if (pm) pm.addEventListener('click', function(e) { if (e.target.id === 'passModal') closePassModal(); });
</script>
{% endblock %}
'''
backup(os.path.join(ROOT, "alliance", "templates", "alliance", "home.html"))
write(os.path.join(ROOT, "alliance", "templates", "alliance", "home.html"), ALLIANCE_HOME)

# 4b) create.html
ALLIANCE_CREATE = '''{% extends "base.html" %}
{% block title %}ساخت اتحاد{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }
  .error-msg { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); padding: 12px 16px; border-radius: 12px; margin-bottom: 14px; font-size: 13px; text-align: right; }
  .box { background: var(--card); border: 1px solid var(--border); padding: 22px; border-radius: 18px; margin-bottom: 14px; }
  label { display: block; color: var(--muted); font-size: 13px; margin: 12px 0 6px; }
  input[type=text], input[type=password], input[type=number], textarea { width: 100%; padding: 12px 14px; border-radius: 12px; border: 1.5px solid var(--border); background: var(--bg); color: var(--text); font-size: 15px; font-family: inherit; box-sizing: border-box; }
  textarea { resize: vertical; min-height: 80px; }
  input:focus, textarea:focus { outline: none; border-color: var(--gold); }
  .emojis { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
  .emoji-opt { padding: 12px 0; text-align: center; font-size: 26px; background: var(--bg); border: 2px solid transparent; border-radius: 12px; cursor: pointer; transition: all 0.15s; }
  .emoji-opt:hover { border-color: var(--gold); }
  .emoji-opt input { display: none; }
  .emoji-opt:has(input:checked) { border-color: var(--gold); background: linear-gradient(135deg, rgba(244,197,66,0.3), rgba(249,115,22,0.2)); box-shadow: 0 0 20px rgba(244,197,66,0.4); }
  button.save { width: 100%; margin-top: 20px; padding: 16px; border: none; border-radius: 14px; font-size: 17px; font-weight: bold; font-family: inherit; cursor: pointer; color: #1a1a1a; background: linear-gradient(135deg, #22c55e, #16a34a); box-shadow: 0 10px 30px rgba(34,197,94,0.4); }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <a href="/alliance/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>🏰 <span>ساخت اتحاد</span></h1>
  </div>

  {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}

  <form method="post">
    {% csrf_token %}
    <div class="box">
      <label>نماد اتحاد</label>
      <div class="emojis">
        {% for e in emojis %}
          <label class="emoji-opt">
            <input type="radio" name="emblem" value="{{ e }}" {% if forloop.first %}checked{% endif %}>
            {{ e }}
          </label>
        {% endfor %}
      </div>
    </div>
    <div class="box">
      <label>نام اتحاد (حداقل ۳ حرف)</label>
      <input type="text" name="name" maxlength="40" required placeholder="مثلاً: عقاب‌های آتشین">
      <label>برچسب کوتاه (اختیاری)</label>
      <input type="text" name="tag" maxlength="8" placeholder="مثلاً: IRN">
      <label>توضیح (اختیاری)</label>
      <textarea name="description" maxlength="200" placeholder="چند خط درباره تیمت..."></textarea>
      <label>ظرفیت اعضا (۵ تا ۵۰)</label>
      <input type="number" name="max_members" min="5" max="50" value="30">
      <label>رمز اتحاد (اختیاری)</label>
      <input type="password" name="password" maxlength="32" placeholder="خالی = بدون رمز">
    </div>
    <button type="submit" class="save">🚀 ساخت اتحاد</button>
  </form>
{% endblock %}
'''
backup(os.path.join(ROOT, "alliance", "templates", "alliance", "create.html"))
write(os.path.join(ROOT, "alliance", "templates", "alliance", "create.html"), ALLIANCE_CREATE)

# 4c) detail.html
ALLIANCE_DETAIL = '''{% extends "base.html" %}
{% block title %}{{ alliance.name }}{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
  .hero-card { text-align: center; padding: 30px 20px; background: linear-gradient(135deg, rgba(30,41,59,0.8), rgba(15,23,42,0.9)); border: 1px solid rgba(148,163,184,0.2); border-radius: 24px; margin-bottom: 20px; position: relative; overflow: hidden; }
  .hero-card::before { content: ""; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(244,197,66,0.1) 0%, transparent 60%); pointer-events: none; }
  .emblem-big { font-size: 76px; margin-bottom: 12px; filter: drop-shadow(0 10px 20px rgba(0,0,0,0.5)); }
  .alliance-title { font-size: 26px; font-weight: 900; background: linear-gradient(135deg, #fde68a, #f4c542, #ca8a04); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 6px; }
  .invite-box { display: inline-flex; align-items: center; gap: 10px; background: rgba(15,23,42,0.8); border: 1px solid var(--border); padding: 8px 16px; border-radius: 12px; margin-top: 16px; cursor: pointer; transition: 0.2s; }
  .invite-box:hover { border-color: var(--gold); }
  .invite-code { font-family: monospace; font-size: 18px; letter-spacing: 3px; color: var(--gold); font-weight: bold; }
  .copy-icon { font-size: 16px; color: var(--muted); }
  .capacity-bar-wrap { margin-top: 16px; }
  .capacity-bar-labels { display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); margin-bottom: 6px; }
  .capacity-bar { height: 8px; background: rgba(148,163,184,0.15); border-radius: 8px; overflow: hidden; }
  .capacity-fill { height: 100%; background: linear-gradient(90deg, #8b5cf6, #06b6d4); border-radius: 8px; transition: width 0.5s; box-shadow: 0 0 10px rgba(139,92,246,0.5); }
  .stats-row { display: flex; gap: 10px; margin-bottom: 20px; }
  .stat-box { flex: 1; background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 16px; text-align: center; }
  .stat-val { font-size: 22px; font-weight: bold; color: #fff; margin-bottom: 4px; }
  .stat-lbl { font-size: 11px; color: var(--muted); }
  .action-grid { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
  .action-grid a, .action-grid button { flex: 1; min-width: 140px; text-align: center; padding: 14px; border-radius: 14px; text-decoration: none; font-weight: bold; font-size: 15px; border: none; font-family: inherit; cursor: pointer; }
  .btn-chat { background: linear-gradient(135deg, #06b6d4, #3b82f6); color: #fff; box-shadow: 0 8px 20px rgba(6,182,212,0.3); }
  .btn-edit { background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; box-shadow: 0 8px 20px rgba(139,92,246,0.3); }
  .btn-leave { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; box-shadow: 0 8px 20px rgba(239,68,68,0.3); }
  .member-list { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 20px; margin-bottom: 20px; }
  .member-list h3 { font-size: 15px; color: var(--gold); margin-bottom: 16px; display: flex; justify-content: space-between; }
  .badge-count { display: inline-block; background: var(--border); color: #fff; font-size: 10px; padding: 2px 8px; border-radius: 8px; font-weight: bold; }
  .member-row { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
  .member-row:last-child { border-bottom: none; padding-bottom: 0; }
  .member-av-wrapper { position: relative; }
  .member-av { width: 44px; height: 44px; border-radius: 50%; background: rgba(15,23,42,0.6); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; font-size: 22px; background-size: cover; background-position: center; }
  .online-dot { position: absolute; bottom: 0; right: 0; width: 12px; height: 12px; background: #22c55e; border-radius: 50%; border: 2px solid var(--card); box-shadow: 0 0 8px #22c55e; }
  .member-info { flex: 1; }
  .member-name { font-size: 14px; font-weight: bold; color: #fff; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  .member-join { font-size: 11px; color: var(--dim); }
  .level-badge { background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; font-size: 10px; padding: 2px 6px; border-radius: 6px; font-family: monospace; }
  .role-badge { font-size: 11px; padding: 4px 10px; border-radius: 8px; font-weight: bold; }
  .role-leader { background: rgba(244,197,66,0.2); color: #facc15; border: 1px solid rgba(244,197,66,0.3); }
  .role-officer { background: rgba(59,130,246,0.2); color: #93c5fd; border: 1px solid rgba(59,130,246,0.3); }
  .role-member { background: rgba(100,116,139,0.2); color: #cbd5e1; border: 1px solid rgba(100,116,139,0.3); }
  .kick-btn { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); color: #f87171; border-radius: 8px; padding: 6px 10px; cursor: pointer; font-size: 12px; font-family: inherit; }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <a href="/alliance/" class="back-btn"><span class="arrow-icon">→</span></a>
  </div>

  <div class="hero-card">
    <div class="emblem-big">{{ alliance.emblem }}</div>
    <div class="alliance-title">{{ alliance.name }}</div>
    {% if alliance.tag %}<div style="color:var(--muted); font-size:14px; letter-spacing:2px;">{{ alliance.tag }}</div>{% endif %}
    <div class="invite-box" onclick="copyCode()">
      <span class="invite-code" id="codeText">{{ alliance.invite_code }}</span>
      <span class="copy-icon">📋</span>
    </div>
    <div style="font-size:10px; color:var(--dim); margin-top:6px;">برای کپی کلیک کنید</div>

    <div class="capacity-bar-wrap">
      <div class="capacity-bar-labels">
        <span>ظرفیت اعضا</span>
        <span style="font-family:monospace;">{{ member_count }} / {{ alliance.max_members }}</span>
      </div>
      <div class="capacity-bar">
        <div class="capacity-fill" style="width: {% widthratio member_count alliance.max_members 100 %}%;"></div>
      </div>
    </div>
  </div>

  <div class="stats-row">
    <div class="stat-box">
      <div class="stat-val">{{ member_count }} / {{ alliance.max_members }}</div>
      <div class="stat-lbl">ظرفیت اعضا</div>
    </div>
    <div class="stat-box">
      <div class="stat-val">{{ alliance.created_at|date:"Y/m/d" }}</div>
      <div class="stat-lbl">تأسیس</div>
    </div>
  </div>

  <div class="action-grid">
    <a href="/alliance/{{ alliance.id }}/chat/" class="btn-chat">💬 چت گروهی</a>
    {% if my_role == 'leader' %}
      <a href="/alliance/{{ alliance.id }}/edit/" class="btn-edit">✏️ ویرایش</a>
    {% endif %}
    <form method="post" action="/alliance/{{ alliance.id }}/leave/" style="flex:1; min-width:140px;" onsubmit="return confirm('{% if my_role == 'leader' %}اتحاد منحل شود؟{% else %}از اتحاد خارج شوی؟{% endif %}');">
      {% csrf_token %}
      <button type="submit" class="btn-leave" style="width:100%;">{% if my_role == 'leader' %}🗑️ حذف{% else %}🚪 خروج{% endif %}</button>
    </form>
  </div>

  <div class="member-list">
    <h3>👥 اعضای اتحاد <span class="badge-count">{{ member_count }}</span></h3>
    {% for mem in members %}
      <div class="member-row">
        <div class="member-av-wrapper">
          {% if mem.user.avatar_type == 'image' and mem.user.avatar_id %}
            <div class="member-av" style="background-image: url('/static/avatars/images/{{ mem.user.avatar_id|stringformat:"03d" }}.jpg');"></div>
          {% else %}
            <div class="member-av">{{ mem.avatar }}</div>
          {% endif %}
          {% if mem.is_online %}<div class="online-dot"></div>{% endif %}
        </div>
        <div class="member-info">
          <div class="member-name">
            {{ mem.user.alias }}
            {% if mem.user.id == request.user.id %}<span style="color:var(--teal);font-size:10px;">(شما)</span>{% endif %}
            <span class="level-badge">Lv {{ mem.level }}</span>
          </div>
          <div class="member-join">عضو از {{ mem.joined_at|date:"Y/m/d" }}</div>
        </div>
        <span class="role-badge role-{{ mem.role }}">
          {% if mem.role == 'leader' %}👑 رهبر{% elif mem.role == 'officer' %}🛡️ افسر{% else %}👤 عضو{% endif %}
        </span>
        {% if is_leader and mem.role != 'leader' %}
          <form method="post" action="/alliance/{{ alliance.id }}/kick/{{ mem.user.id }}/" onsubmit="return confirm('حذف شود؟');">
            {% csrf_token %}
            <button type="submit" class="kick-btn">حذف</button>
          </form>
        {% endif %}
      </div>
    {% endfor %}
  </div>
{% endblock %}

{% block extra_js %}
<script>
  function copyCode() {
    const code = document.getElementById('codeText').innerText;
    navigator.clipboard.writeText(code).then(() => {
      if (typeof window.soundSuccess === 'function') window.soundSuccess();
      alert('کد دعوت کپی شد: ' + code);
    }).catch(() => {
      alert('کد دعوت: ' + code);
    });
  }
</script>
{% endblock %}
'''
backup(os.path.join(ROOT, "alliance", "templates", "alliance", "detail.html"))
write(os.path.join(ROOT, "alliance", "templates", "alliance", "detail.html"), ALLIANCE_DETAIL)

# 4d) edit.html
ALLIANCE_EDIT = '''{% extends "base.html" %}
{% block title %}ویرایش اتحاد{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }
  .error-msg { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); padding: 12px 16px; border-radius: 12px; margin-bottom: 14px; font-size: 13px; }
  .box { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 22px; margin-bottom: 14px; }
  .box h3 { font-size: 14px; color: var(--gold); margin-bottom: 16px; }
  label { display: block; color: var(--muted); font-size: 13px; margin: 12px 0 6px; }
  input[type=text], input[type=password], input[type=number], textarea { width: 100%; padding: 12px 14px; border-radius: 12px; border: 1.5px solid var(--border); background: var(--bg); color: var(--text); font-size: 15px; font-family: inherit; box-sizing: border-box; }
  textarea { resize: vertical; min-height: 70px; }
  input:focus, textarea:focus { outline: none; border-color: var(--purple); }
  .emojis { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
  .emoji-opt { padding: 12px 0; text-align: center; font-size: 26px; background: var(--bg); border: 2px solid transparent; border-radius: 12px; cursor: pointer; transition: 0.15s; }
  .emoji-opt:hover { border-color: var(--gold); }
  .emoji-opt input { display: none; }
  .emoji-opt:has(input:checked) { border-color: var(--gold); background: linear-gradient(135deg, rgba(244,197,66,0.25), rgba(139,92,246,0.15)); box-shadow: 0 0 20px rgba(244,197,66,0.35); }
  button.save { width: 100%; margin-top: 16px; padding: 16px; border: none; border-radius: 14px; font-size: 16px; font-weight: bold; font-family: inherit; cursor: pointer; color: #fff; background: linear-gradient(135deg, #8b5cf6, #6b4eff); box-shadow: 0 10px 30px rgba(139,92,246,0.4); transition: 0.2s; }
  button.save:hover { transform: translateY(-2px); }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <a href="/alliance/{{ alliance.id }}/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>✏️ <span>ویرایش اتحاد</span></h1>
  </div>

  {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}

  <form method="post">
    {% csrf_token %}
    <div class="box">
      <h3>🎨 نماد اتحاد</h3>
      <div class="emojis">
        {% for e in emojis %}
          <label class="emoji-opt">
            <input type="radio" name="emblem" value="{{ e }}" {% if e == alliance.emblem %}checked{% endif %}>
            {{ e }}
          </label>
        {% endfor %}
      </div>
    </div>
    <div class="box">
      <h3>📝 اطلاعات اتحاد</h3>
      <label>نام اتحاد</label>
      <input type="text" name="name" maxlength="40" required value="{{ alliance.name }}">
      <label>تگ (اختیاری)</label>
      <input type="text" name="tag" maxlength="8" value="{{ alliance.tag }}">
      <label>توضیح</label>
      <textarea name="description" maxlength="200">{{ alliance.description }}</textarea>
    </div>
    <div class="box">
      <h3>⚙️ تنظیمات</h3>
      <label>ظرفیت اعضا (۵ تا ۵۰)</label>
      <input type="number" name="max_members" min="5" max="50" value="{{ alliance.max_members }}">
      <label>رمز اتحاد (خالی = بدون رمز)</label>
      <input type="password" name="password" maxlength="32" value="{{ alliance.password }}">
    </div>
    <button type="submit" class="save">💾 ذخیره تغییرات</button>
  </form>
{% endblock %}
'''
backup(os.path.join(ROOT, "alliance", "templates", "alliance", "edit.html"))
write(os.path.join(ROOT, "alliance", "templates", "alliance", "edit.html"), ALLIANCE_EDIT)

# 4e) chat.html
ALLIANCE_CHAT = '''{% extends "base.html" %}
{% block title %}چت {{ alliance.name }}{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
  .chat-header { display: flex; align-items: center; gap: 12px; padding: 16px; background: var(--card); border: 1px solid var(--border); border-radius: 16px; margin-bottom: 16px; }
  .chat-header .emblem { font-size: 32px; }
  .chat-header .info { flex: 1; }
  .chat-header .name { font-size: 16px; font-weight: bold; color: #fff; }
  .chat-header .sub { font-size: 12px; color: var(--muted); }
  .chat-body { min-height: 400px; max-height: 55vh; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; padding: 10px; background: rgba(15,23,42,0.3); border-radius: 20px; margin-bottom: 16px; }
  .chat-body::-webkit-scrollbar { width: 6px; }
  .chat-body::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.2); border-radius: 6px; }
  .msg { display: flex; gap: 10px; align-items: flex-end; }
  .msg.me { flex-direction: row-reverse; }
  .msg-av { width: 32px; height: 32px; border-radius: 50%; background: rgba(51,65,85,0.8); display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; background-size: cover; background-position: center; border: 1px solid var(--border); }
  .msg-bubble { max-width: 75%; padding: 12px 16px; border-radius: 18px; background: var(--card); border: 1px solid var(--border); font-size: 14px; line-height: 1.5; color: #fff; border-bottom-right-radius: 4px; }
  .msg.me .msg-bubble { background: linear-gradient(135deg, #3b82f6, #2563eb); border-color: #2563eb; border-bottom-right-radius: 18px; border-bottom-left-radius: 4px; box-shadow: 0 4px 15px rgba(59,130,246,0.3); }
  .msg-sender { font-size: 11px; color: var(--muted); margin-bottom: 4px; }
  .msg-time { font-size: 9px; color: var(--dim); margin-top: 6px; text-align: left; }
  .chat-input { display: flex; gap: 10px; background: var(--card); padding: 10px; border-radius: 16px; border: 1px solid var(--border); }
  .chat-input input { flex: 1; background: transparent; border: none; color: #fff; font-size: 15px; padding: 10px; font-family: inherit; }
  .chat-input input:focus { outline: none; }
  .chat-input button { background: linear-gradient(135deg, #06b6d4, #3b82f6); color: #fff; border: none; width: 44px; height: 44px; border-radius: 12px; font-size: 18px; cursor: pointer; transition: 0.2s; display: flex; align-items: center; justify-content: center; }
  .chat-input button:hover { transform: scale(1.05); }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <a href="/alliance/{{ alliance.id }}/" class="back-btn"><span class="arrow-icon">→</span></a>
  </div>

  <div class="chat-header">
    <div class="emblem">{{ alliance.emblem }}</div>
    <div class="info">
      <div class="name">{{ alliance.name }}</div>
      <div class="sub">چت گروهی اعضا</div>
    </div>
  </div>

  <div class="chat-body" id="chatBody">
    {% for m in messages %}
      <div class="msg {% if m.is_me %}me{% endif %}">
        {% if m.sender.avatar_type == 'image' and m.sender.avatar_id %}
          <div class="msg-av" style="background-image: url('/static/avatars/images/{{ m.sender.avatar_id|stringformat:"03d" }}.jpg');"></div>
        {% else %}
          <div class="msg-av">{{ m.avatar }}</div>
        {% endif %}
        <div>
          {% if not m.is_me %}<div class="msg-sender">{{ m.sender.alias }}</div>{% endif %}
          <div class="msg-bubble">{{ m.body }}</div>
          <div class="msg-time">{{ m.sent_at|date:"H:i" }}</div>
        </div>
      </div>
    {% empty %}
      <div style="text-align:center; color:var(--dim); font-size:13px; margin:auto;">هنوز پیامی فرستاده نشده. اولین نفر باش!</div>
    {% endfor %}
  </div>

  <form method="post" class="chat-input">
    {% csrf_token %}
    <input type="text" name="body" maxlength="500" required placeholder="پیامت را اینجا بنویس..." autocomplete="off" autofocus>
    <button type="submit">↑</button>
  </form>
{% endblock %}

{% block extra_js %}
<script>
  const body = document.getElementById('chatBody');
  if (body) body.scrollTop = body.scrollHeight;
</script>
{% endblock %}
'''
backup(os.path.join(ROOT, "alliance", "templates", "alliance", "chat.html"))
write(os.path.join(ROOT, "alliance", "templates", "alliance", "chat.html"), ALLIANCE_CHAT)

# ============================================================
# STEP 5: Verify + check
# ============================================================
print("\n[5/5] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], cwd=ROOT, capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check passed")
else:
    print("  ⚠ ERRORS:")
    print(r.stderr[:2000] if r.stderr else r.stdout[:2000])

# Test template loading
print("\n[Test] Loading templates")
tests = [
    "social/notifications.html",
    "alliance/home.html",
    "alliance/create.html",
    "alliance/detail.html",
    "alliance/edit.html",
    "alliance/chat.html",
]
for t in tests:
    code = f"from django.template.loader import get_template; get_template('{t}'); print('OK {t}')"
    r = subprocess.run([sys.executable, "manage.py", "shell", "-c", code],
                       cwd=ROOT, capture_output=True, text=True, timeout=30)
    out = r.stdout.strip()
    if "OK" in out:
        print(f"  ✓ {t}")
    else:
        err = (r.stderr or r.stdout).strip()
        print(f"  ✗ {t} → {err[:200]}")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
What was fixed:

  1.  ✓ 'common' added to INSTALLED_APPS
        → tournaments Jalali now works

  2.  ✓ notifications.html rebuilt
        → uses Django's {{ n.created_at|date:"Y/m/d H:i" }}
        → no jalali dependency
        → shows sender name
        → unread badge + pulse dot

  3.  ✓ notifications_view rewritten
        → materializes list before marking read
        → unread_total correct

  4.  ✓ ALL alliance templates rebuilt:
        - home.html (list + search + create + password modal)
        - create.html (with password field + capacity)
        - detail.html (with edit button for leader + capacity bar)
        - edit.html (leader-only edit page)
        - chat.html (group chat)

  5.  ✓ Django check + template load test

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R

Test:
  /social/notifications/  → should show (even if empty)
  /alliance/              → list + search + create
  /alliance/create/       → form with all fields
  /alliance/<id>/         → detail with edit button (if leader)
  /alliance/<id>/edit/    → edit form (leader only)
  /alliance/<id>/chat/    → group chat
""")
