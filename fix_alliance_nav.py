#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")
def backup(p):
    bak = p + ".bak8"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) alliance/views.py - home rewrite + edit view
# ============================================================
print("\n[1/6] alliance/views.py")
p = os.path.join(ROOT, "alliance", "views.py")
src = read(p)
changed = False

# Replace alliance_home
old_home_start = src.find("def alliance_home(request):")
if old_home_start > 0:
    dec_start = src.rfind("@login_required", 0, old_home_start)
    if dec_start < 0: dec_start = old_home_start
    # find next top-level def
    next_def = src.find("\n@login_required\ndef ", old_home_start)
    if next_def < 0: next_def = src.find("\n\ndef ", old_home_start)
    if next_def < 0: next_def = len(src)
    
    new_home = '''@login_required
def alliance_home(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    my_membership = AllianceMember.objects.filter(user=request.user).select_related("alliance").first()
    if my_membership:
        return redirect("alliance:detail", alliance_id=my_membership.alliance.id)

    query = (request.GET.get("q") or "").strip()
    alliances_qs = Alliance.objects.all().order_by("-created_at")
    if query:
        from django.db.models import Q
        alliances_qs = alliances_qs.filter(Q(name__icontains=query) | Q(tag__icontains=query))

    alliances_data = []
    for a in alliances_qs[:50]:
        count = a.member_count()
        alliances_data.append({
            "obj": a,
            "count": count,
            "is_full": count >= a.max_members,
            "has_password": bool(a.password),
            "leader_avatar": _avatar(a.leader),
        })

    return render(request, "alliance/home.html", {
        "alliances": alliances_data,
        "query": query,
        "active": "friends",
    })
'''
    src = src[:dec_start] + new_home + src[next_def:]
    changed = True
    print("  FIXED: alliance_home rewritten")

# Add edit view
if "def alliance_edit(request" in src:
    print("  SKIP: edit exists")
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
    src = src.rstrip() + "\n" + edit_view + "\n"
    changed = True
    print("  FIXED: alliance_edit added")

# Ensure django.db.models Q import at top for home
if "from django.db.models import Q" not in src.split("\n")[:20]:
    # Add inside the home function instead - already done
    pass

if changed:
    backup(p); write(p, src)

# ============================================================
# 2) alliance/urls.py - add edit route
# ============================================================
print("\n[2/6] alliance/urls.py")
p = os.path.join(ROOT, "alliance", "urls.py")
src = read(p)
if "alliance_edit" in src or "edit/" in src:
    print("  SKIP: edit route exists")
else:
    old = '    path("<int:alliance_id>/", views.alliance_detail, name="detail"),'
    new = old + '\n    path("<int:alliance_id>/edit/", views.alliance_edit, name="edit"),'
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: edit route added")
    else:
        print("  WARN: detail route not found")

# ============================================================
# 3) alliance/home.html - full rewrite
# ============================================================
print("\n[3/6] home.html")
p = os.path.join(ROOT, "alliance", "templates", "alliance", "home.html")

HOME_HTML = '''{% extends "base.html" %}
{% block title %}اتحاد{% endblock %}

{% block extra_css %}
<style>
  .hero-card {
    padding: 26px 22px;
    background:
      radial-gradient(circle at 100% 0%, rgba(139,92,246,0.4), transparent 55%),
      radial-gradient(circle at 0% 100%, rgba(236,72,153,0.2), transparent 55%),
      linear-gradient(135deg, #1a0f2e, #170a24, #0f0f1e);
    border: 2px solid rgba(139,92,246,0.55);
    border-radius: 24px;
    margin-bottom: 18px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 15px 40px rgba(139,92,246,0.25);
  }
  .hero-card .icon { font-size: 56px; margin-bottom: 8px; filter: drop-shadow(0 0 20px rgba(167,139,250,0.6)); }
  .hero-card h1 {
    font-size: 22px; font-weight: 900; margin-bottom: 8px;
    background: linear-gradient(135deg, #e9d5ff, #a78bfa, #ec4899);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .hero-card p { color: var(--muted); font-size: 13px; line-height: 1.7; margin-bottom: 18px; }

  .create-btn {
    display: flex; align-items: center; justify-content: center; gap: 10px;
    padding: 16px 24px; border-radius: 16px;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: #fff; text-decoration: none; font-weight: 900; font-size: 16px;
    box-shadow: 0 10px 30px rgba(34,197,94,0.4);
    transition: 0.2s;
  }
  .create-btn:hover { transform: translateY(-2px); box-shadow: 0 14px 35px rgba(34,197,94,0.6); }
  .create-btn .plus { font-size: 22px; font-weight: 900; }

  .search-bar {
    display: flex; gap: 8px;
    background: var(--card); border: 1.5px solid var(--border);
    border-radius: 16px; padding: 4px;
    margin-bottom: 18px;
    transition: 0.2s;
  }
  .search-bar:focus-within { border-color: var(--purple); box-shadow: 0 0 20px rgba(139,92,246,0.15); }
  .search-bar input {
    flex: 1; padding: 12px 16px; border-radius: 12px;
    border: none; background: transparent; color: #fff;
    font-size: 15px; font-family: inherit;
  }
  .search-bar input:focus { outline: none; }
  .search-bar button {
    padding: 0 20px; border-radius: 12px;
    background: linear-gradient(135deg, #8b5cf6, #6b4eff);
    color: #fff; border: none; font-weight: bold;
    font-family: inherit; cursor: pointer; font-size: 15px;
  }

  .section-title {
    font-size: 15px; color: var(--gold);
    font-weight: bold; margin: 8px 0 14px;
    display: flex; align-items: center; gap: 8px;
  }
  .section-title .count {
    background: rgba(244,197,66,0.15);
    padding: 3px 10px; border-radius: 8px;
    font-size: 11px; font-family: monospace;
  }

  .alliance-list { display: flex; flex-direction: column; gap: 10px; }

  .alliance-card {
    display: flex; align-items: center; gap: 14px;
    padding: 16px;
    background: var(--card);
    border: 1.5px solid var(--border);
    border-radius: 18px;
    transition: 0.2s;
    position: relative;
  }
  .alliance-card:hover { border-color: rgba(139,92,246,0.6); transform: translateX(-3px); }
  .alliance-card.is-full { opacity: 0.6; }
  .alliance-card.is-full:hover { transform: none; }

  .alliance-emblem {
    width: 56px; height: 56px; flex-shrink: 0;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(139,92,246,0.3), rgba(6,182,212,0.15));
    border: 1px solid rgba(255,255,255,0.12);
    display: flex; align-items: center; justify-content: center;
    font-size: 30px;
  }
  .alliance-info { flex: 1; min-width: 0; }
  .alliance-name-row {
    display: flex; align-items: center; gap: 6px;
    margin-bottom: 4px;
  }
  .alliance-name { font-size: 15px; font-weight: bold; color: #fff;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .alliance-tag {
    background: var(--gold); color: #1a1a1a;
    padding: 2px 8px; border-radius: 6px;
    font-size: 9px; font-weight: 900;
    font-family: monospace;
  }
  .alliance-meta { font-size: 11.5px; color: var(--muted); display: flex; align-items: center; gap: 6px; }
  .alliance-meta .dot { opacity: 0.5; }
  .alliance-meta .lock { font-size: 13px; }

  .join-btn {
    padding: 10px 16px; border-radius: 12px;
    background: linear-gradient(135deg, #8b5cf6, #6b4eff);
    color: #fff; border: none; font-family: inherit;
    font-weight: bold; font-size: 13px; cursor: pointer;
    box-shadow: 0 6px 15px rgba(139,92,246,0.35);
    transition: 0.2s; flex-shrink: 0;
  }
  .join-btn:hover { transform: scale(1.05); }
  .join-btn.full { background: rgba(148,163,184,0.2); box-shadow: none; cursor: not-allowed; }

  .empty-state {
    text-align: center; padding: 50px 20px;
    background: var(--card);
    border: 1.5px dashed var(--border);
    border-radius: 20px;
  }
  .empty-state .icon { font-size: 60px; margin-bottom: 14px; display: block; opacity: 0.5; }
  .empty-state h3 { font-size: 17px; margin-bottom: 8px; }
  .empty-state p { color: var(--muted); font-size: 13px; margin-bottom: 20px; line-height: 1.6; }

  /* password modal */
  .pass-modal-bg {
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.85); backdrop-filter: blur(8px);
    z-index: 1000; align-items: center; justify-content: center;
    padding: 20px;
  }
  .pass-modal-bg.active { display: flex; animation: fadeIn 0.25s; }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  .pass-modal {
    background: linear-gradient(135deg, rgba(30,41,59,0.98), rgba(15,23,42,0.98));
    border: 1.5px solid rgba(139,92,246,0.5);
    border-radius: 22px;
    padding: 26px 22px;
    max-width: 380px; width: 100%;
    text-align: center;
    box-shadow: 0 25px 60px rgba(0,0,0,0.7);
    animation: slideUp 0.3s ease-out;
  }
  @keyframes slideUp { from { transform: translateY(30px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
  .pass-modal .icon { font-size: 48px; margin-bottom: 10px; }
  .pass-modal h3 { font-size: 18px; color: #c4b5fd; margin-bottom: 6px; }
  .pass-modal p { font-size: 12px; color: var(--muted); margin-bottom: 16px; line-height: 1.6; }
  .pass-modal input {
    width: 100%; padding: 14px; border-radius: 12px;
    border: 1.5px solid var(--border); background: var(--bg); color: #fff;
    font-size: 16px; font-family: monospace; text-align: center;
    letter-spacing: 3px; margin-bottom: 14px; box-sizing: border-box;
  }
  .pass-modal input:focus { outline: none; border-color: var(--purple); }
  .pass-modal-actions { display: flex; gap: 8px; }
  .pass-modal-actions button {
    flex: 1; padding: 12px; border-radius: 12px;
    font-family: inherit; font-weight: bold; font-size: 14px;
    cursor: pointer; border: none;
  }
  .btn-join { background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; }
  .btn-cancel { background: rgba(148,163,184,0.2); color: #fff; }
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
            <form method="post" action="/alliance/join-id/{{ a.obj.id }}/" style="display:inline;">
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

  <!-- Password modal -->
  <div class="pass-modal-bg" id="passModal">
    <div class="pass-modal">
      <div class="icon">🔐</div>
      <h3>رمز اتحاد</h3>
      <p>اتحاد <b id="passAllianceName"></b> رمز دارد.<br>رمز را وارد کن.</p>
      <form method="post" id="passForm">
        {% csrf_token %}
        <input type="password" name="password" placeholder="رمز" required autofocus autocomplete="off">
        <div class="pass-modal-actions">
          <button type="submit" class="btn-join">ورود</button>
          <button type="button" class="btn-cancel" onclick="closePassModal()">انصراف</button>
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
  document.getElementById('passModal').addEventListener('click', function(e) {
    if (e.target.id === 'passModal') closePassModal();
  });
</script>
{% endblock %}
'''
backup(p); write(p, HOME_HTML)

# ============================================================
# 4) alliance/edit.html - new file
# ============================================================
print("\n[4/6] edit.html (new)")
p = os.path.join(ROOT, "alliance", "templates", "alliance", "edit.html")

EDIT_HTML = '''{% extends "base.html" %}
{% block title %}ویرایش اتحاد{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }
  .error-msg {
    background: rgba(239,68,68,0.15); color: #fca5a5;
    border: 1px solid rgba(239,68,68,0.35);
    padding: 12px 16px; border-radius: 12px;
    margin-bottom: 14px; font-size: 13px; text-align: right;
  }
  .box { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 22px; margin-bottom: 14px; }
  .box h3 { font-size: 14px; color: var(--gold); margin-bottom: 16px; }
  label { display: block; color: var(--muted); font-size: 13px; margin: 12px 0 6px; }
  input[type=text], input[type=password], input[type=number], textarea {
    width: 100%; padding: 12px 14px; border-radius: 12px;
    border: 1.5px solid var(--border); background: var(--bg);
    color: var(--text); font-size: 15px; font-family: inherit;
    box-sizing: border-box;
  }
  textarea { resize: vertical; min-height: 70px; }
  input:focus, textarea:focus { outline: none; border-color: var(--purple); }
  .emojis { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
  .emoji-opt {
    padding: 12px 0; text-align: center; font-size: 26px;
    background: var(--bg); border: 2px solid transparent;
    border-radius: 12px; cursor: pointer; transition: 0.15s;
  }
  .emoji-opt:hover { border-color: var(--gold); }
  .emoji-opt input { display: none; }
  .emoji-opt:has(input:checked) {
    border-color: var(--gold);
    background: linear-gradient(135deg, rgba(244,197,66,0.25), rgba(139,92,246,0.15));
    box-shadow: 0 0 20px rgba(244,197,66,0.35);
  }
  button.save {
    width: 100%; margin-top: 16px; padding: 16px;
    border: none; border-radius: 14px;
    font-size: 16px; font-weight: bold;
    font-family: inherit; cursor: pointer;
    color: #fff;
    background: linear-gradient(135deg, #8b5cf6, #6b4eff);
    box-shadow: 0 10px 30px rgba(139,92,246,0.4);
    transition: 0.2s;
  }
  button.save:hover { transform: translateY(-2px); }
  .current-info {
    background: rgba(139,92,246,0.08);
    border: 1px dashed rgba(139,92,246,0.3);
    border-radius: 12px; padding: 12px 14px;
    margin-bottom: 14px;
    font-size: 12px; color: var(--muted);
  }
  .current-info b { color: var(--purple); }
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
      <div class="current-info">
        <b>راهنما:</b> رهبر می‌تونه نام، تگ، توضیح، ظرفیت و رمز رو تغییر بده.
      </div>

      <h3>📝 اطلاعات اتحاد</h3>
      <label>نام اتحاد</label>
      <input type="text" name="name" maxlength="40" required value="{{ alliance.name }}">

      <label>تگ (اختیاری)</label>
      <input type="text" name="tag" maxlength="8" value="{{ alliance.tag }}" placeholder="مثلاً IRN">

      <label>توضیح</label>
      <textarea name="description" maxlength="200" placeholder="درباره اتحاد...">{{ alliance.description }}</textarea>
    </div>

    <div class="box">
      <h3>⚙️ تنظیمات</h3>

      <label>ظرفیت اعضا (۵ تا ۵۰)</label>
      <input type="number" name="max_members" min="5" max="50" value="{{ alliance.max_members }}">

      <label>رمز اتحاد (اختیاری — خالی = بدون رمز)</label>
      <input type="password" name="password" maxlength="32" value="{{ alliance.password }}" placeholder="خالی = بدون رمز">
    </div>

    <button type="submit" class="save">💾 ذخیره تغییرات</button>
  </form>
{% endblock %}
'''
backup(p); write(p, EDIT_HTML)

# ============================================================
# 5) alliance/detail.html - polish (add edit button + better capacity)
# ============================================================
print("\n[5/6] detail.html - add edit button for leader")
p = os.path.join(ROOT, "alliance", "templates", "alliance", "detail.html")
src = read(p)

# Add edit button next to chat button for leader
old_actions = '''  <div style="display:flex; gap:10px; margin-bottom:20px;">
    <a href="/alliance/{{ alliance.id }}/chat/" style="flex:1; text-align:center; background:linear-gradient(135deg, #06b6d4, #3b82f6); color:#fff; padding:14px; border-radius:14px; text-decoration:none; font-weight:bold; font-size:15px; box-shadow:0 8px 20px rgba(6,182,212,0.3);">💬 چت گروهی</a>
    <form method="post" action="/alliance/{{ alliance.id }}/leave/" style="flex:1;" onsubmit="return confirm('{% if my_role == 'leader' %}اتحاد منحل شود؟{% else %}از اتحاد خارج شوی؟{% endif %}');">
      {% csrf_token %}
      <button type="submit" class="btn-danger" style="height:100%;">{% if my_role == 'leader' %}🗑️ حذف{% else %}🚪 خروج{% endif %}</button>
    </form>
  </div>'''

new_actions = '''  <div style="display:flex; gap:10px; margin-bottom:20px; flex-wrap:wrap;">
    <a href="/alliance/{{ alliance.id }}/chat/" style="flex:1; min-width:140px; text-align:center; background:linear-gradient(135deg, #06b6d4, #3b82f6); color:#fff; padding:14px; border-radius:14px; text-decoration:none; font-weight:bold; font-size:15px; box-shadow:0 8px 20px rgba(6,182,212,0.3);">💬 چت گروهی</a>
    {% if my_role == 'leader' %}
      <a href="/alliance/{{ alliance.id }}/edit/" style="flex:1; min-width:140px; text-align:center; background:linear-gradient(135deg, #8b5cf6, #6b4eff); color:#fff; padding:14px; border-radius:14px; text-decoration:none; font-weight:bold; font-size:15px; box-shadow:0 8px 20px rgba(139,92,246,0.3);">✏️ ویرایش</a>
    {% endif %}
    <form method="post" action="/alliance/{{ alliance.id }}/leave/" style="flex:1; min-width:140px;" onsubmit="return confirm('{% if my_role == 'leader' %}اتحاد منحل شود؟{% else %}از اتحاد خارج شوی؟{% endif %}');">
      {% csrf_token %}
      <button type="submit" class="btn-danger" style="height:100%; width:100%;">{% if my_role == 'leader' %}🗑️ حذف{% else %}🚪 خروج{% endif %}</button>
    </form>
  </div>'''

if old_actions in src:
    src = src.replace(old_actions, new_actions, 1)
    print("  FIXED: edit button added")
else:
    print("  WARN: action buttons block not found")

# Ensure capacity bar is added near member count
if "capacity-bar" not in src:
    # Add capacity bar in hero after invite-box
    old_hero_end = '''    <div style="font-size:10px; color:var(--dim); margin-top:6px;">برای کپی کلیک کنید</div>
  </div>'''
    new_hero_end = '''    <div style="font-size:10px; color:var(--dim); margin-top:6px;">برای کپی کلیک کنید</div>

    <div style="margin-top: 16px;">
      <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--muted); margin-bottom:6px;">
        <span>ظرفیت اعضا</span>
        <span style="font-family:monospace;">{{ member_count }} / {{ alliance.max_members }}</span>
      </div>
      <div style="height:8px; background:rgba(148,163,184,0.15); border-radius:8px; overflow:hidden;">
        <div style="height:100%; width:{% widthratio member_count alliance.max_members 100 %}%; background:linear-gradient(90deg,#8b5cf6,#06b6d4); border-radius:8px; transition:width 0.5s; box-shadow:0 0 10px rgba(139,92,246,0.5);"></div>
      </div>
    </div>
  </div>'''
    if old_hero_end in src:
        src = src.replace(old_hero_end, new_hero_end, 1)
        print("  FIXED: capacity bar added")
    else:
        print("  WARN: hero end not found")

# Add back button to /alliance/ in header if not exists
if '<a href="/alliance/" class="back-btn">' not in src and 'href="/alliance/"' not in src:
    old_back = '''  <div class="page-head">
    <a href="/alliance/" class="back-btn"><span class="arrow-icon">→</span></a>
  </div>'''
    # Already there? check
    if old_back in src:
        print("  SKIP: back button exists")

backup(p); write(p, src)

# ============================================================
# 6) base.html - smooth bottom nav
# ============================================================
print("\n[6/6] base.html - smooth nav + loading bar")
p = os.path.join(ROOT, "templates", "base.html")
src = read(p)
changed = False

# Add page loader at start of body
if 'id="pageLoader"' not in src:
    old_body = "<body>\n"
    new_body = '''<body>

<div class="page-loader" id="pageLoader"></div>
'''
    if old_body in src:
        src = src.replace(old_body, new_body, 1)
        changed = True
        print("  FIXED: page loader added")

# Add CSS for loader + smooth nav
if ".page-loader {" not in src:
    css_anchor = "    .container {"
    new_css = '''    /* ===== Page loader ===== */
    .page-loader {
      position: fixed;
      top: 0; left: 0;
      height: 3px;
      width: 0;
      background: linear-gradient(90deg, #f4c542, #8b5cf6, #06b6d4);
      z-index: 9999;
      transition: width 0.3s ease-out, opacity 0.3s;
      box-shadow: 0 0 12px rgba(244,197,66,0.6);
      pointer-events: none;
    }
    .page-loader.loading {
      width: 85%;
      transition: width 3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .container {'''
    if css_anchor in src:
        src = src.replace(css_anchor, new_css, 1)
        changed = True
        print("  FIXED: loader CSS added")

# Improve nav animations
if ".bottom-nav a.active .nav-icon {\n      animation:" not in src and "navBounce" not in src:
    old_active = "    .bottom-nav a.active .nav-icon {\n      filter: none;\n      opacity: 1;\n      transform: scale(1.12) translateY(-1px);\n    }"
    new_active = '''    .bottom-nav a.active .nav-icon {
      filter: none;
      opacity: 1;
      transform: scale(1.12) translateY(-1px);
      animation: navBounce 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    }
    @keyframes navBounce {
      0%   { transform: scale(1) translateY(0); }
      40%  { transform: scale(1.28) translateY(-7px); }
      70%  { transform: scale(0.92) translateY(2px); }
      100% { transform: scale(1.12) translateY(-1px); }
    }'''
    if old_active in src:
        src = src.replace(old_active, new_active, 1)
        changed = True
        print("  FIXED: navBounce animation")

# Slide-in active indicator
if "activeSlide" not in src:
    old_active_bar = '    .bottom-nav a.active::before {\n      content: "";\n      position: absolute;\n      top: 0; left: 30%; right: 30%;\n      height: 3px;\n      background: linear-gradient(90deg, transparent, var(--gold), transparent);\n      border-radius: 0 0 4px 4px;\n    }'
    new_active_bar = '''    .bottom-nav a.active::before {
      content: "";
      position: absolute;
      top: 0; left: 30%; right: 30%;
      height: 3px;
      background: linear-gradient(90deg, transparent, var(--gold), transparent);
      border-radius: 0 0 4px 4px;
      animation: activeSlide 0.35s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 0 10px rgba(244,197,66,0.6);
    }
    @keyframes activeSlide {
      from { left: 50%; right: 50%; opacity: 0; }
      to   { left: 30%; right: 30%; opacity: 1; }
    }'''
    if old_active_bar in src:
        src = src.replace(old_active_bar, new_active_bar, 1)
        changed = True
        print("  FIXED: activeSlide animation")

# JS for loading bar + vibration
if "pageLoader.classList.add" not in src:
    js_anchor = "window.applySettingsNow = function(key, value) {"
    js_add = '''// ============================================================
// Bottom nav smooth transition
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  const loader = document.getElementById('pageLoader');
  if (!loader) return;

  // Reset on page load
  loader.classList.remove('loading');
  loader.style.width = '0';
  loader.style.opacity = '0';

  // On nav link click
  document.querySelectorAll('.bottom-nav a').forEach(link => {
    link.addEventListener('click', (e) => {
      const href = link.getAttribute('href');
      const current = window.location.pathname;
      if (!href || href === current) return;
      // If it's the same page, don't intercept
      if (href === current || href === current + '/') return;

      if (navigator.vibrate) {
        try { navigator.vibrate(12); } catch(e) {}
      }

      loader.style.opacity = '1';
      loader.classList.add('loading');

      // Fade out container
      document.querySelectorAll('.container').forEach(c => {
        c.style.transition = 'opacity 0.25s';
        c.style.opacity = '0.7';
      });

      // Let it proceed normally
    });
  });
});

// Reset loader if page comes back from bfcache
window.addEventListener('pageshow', (e) => {
  const loader = document.getElementById('pageLoader');
  if (loader) {
    loader.classList.remove('loading');
    loader.style.width = '0';
    loader.style.opacity = '0';
  }
  document.querySelectorAll('.container').forEach(c => {
    c.style.opacity = '1';
  });
});

window.applySettingsNow = function(key, value) {'''
    if js_anchor in src:
        src = src.replace(js_anchor, js_add, 1)
        changed = True
        print("  FIXED: loader JS added")

if changed:
    backup(p); write(p, src)

# ============================================================
# Final summary
# ============================================================
print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
What's new:

ALLIANCE:
  1. home.html - full rewrite: hero + create button + search + list of all alliances
  2. home.html - password modal for locked alliances
  3. edit.html - NEW: leader can edit name, tag, emblem, description, capacity, password
  4. alliance_edit view + route
  5. detail.html - edit button (for leader) + capacity bar
  6. alliance_home view - active = "friends" (correct tab highlight)
  7. search by name or tag

BOTTOM NAV:
  1. Top loading bar (3px gradient) - animates on nav click
  2. Vibration feedback on tap (12ms)
  3. navBounce - icon bounces when active
  4. activeSlide - indicator bar slides in from center
  5. Smooth opacity fade during navigation
  6. bfcache reset - clean state when back button

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R
""")
