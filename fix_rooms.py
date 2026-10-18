#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Complete rooms diagnostic + fix."""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Check game/urls.py
# ============================================================
print("\n" + "="*70)
print("STEP 1: Check game/urls.py")
print("="*70)

urls_path = "game/urls.py"
if not os.path.exists(urls_path):
    print(f"  ❌ {urls_path} MISSING!")
    sys.exit(1)

urls_src = read(urls_path)
print(urls_src)

# ============================================================
# 2) Check views exist
# ============================================================
print("\n" + "="*70)
print("STEP 2: Check views functions")
print("="*70)

import django
django.setup()

try:
    from game import views as gv
    required = [
        "home", "rooms_list", "rooms_manage", "join_room",
        "room", "bot_setup", "bot_play", "bot_submit",
        "quick_play", "challenge_home",
    ]
    missing = []
    for fn in required:
        ok = hasattr(gv, fn)
        print(f"  {'✓' if ok else '✗'} game.views.{fn}")
        if not ok:
            missing.append(fn)

    if missing:
        print(f"\n  ❌ Missing: {missing}")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    missing = []

# ============================================================
# 3) Check templates
# ============================================================
print("\n" + "="*70)
print("STEP 3: Check templates")
print("="*70)

required_templates = [
    "game/templates/game/rooms.html",
    "game/templates/game/rooms_manage.html",
    "game/templates/game/room.html",
    "game/templates/game/room_password.html",
    "game/templates/game/bot_setup.html",
    "game/templates/game/bot_play.html",
    "game/templates/game/bot_result.html",
    "game/templates/game/menu.html",
    "game/templates/game/challenge.html",
    "game/templates/game/_tournament_card.html",
]

missing_templates = []
for tpl in required_templates:
    exists = os.path.exists(tpl)
    size = os.path.getsize(tpl) if exists else 0
    print(f"  {'✓' if exists else '✗'} {tpl} ({size} bytes)")
    if not exists or size < 100:
        missing_templates.append(tpl)

# ============================================================
# 4) Test HTTP access
# ============================================================
print("\n" + "="*70)
print("STEP 4: Test rooms URLs")
print("="*70)

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
User = get_user_model()

# Create test user
tu = User.objects.filter(username="__rooms_test__").first()
created = False
if not tu:
    tu = User.objects.create_user(
        username="__rooms_test__", password="x"*10,
        alias="rooms-test", is_active=True,
        has_chosen_avatar=True, has_completed_registration=True,
    )
    created = True

c = Client()
c.force_login(tu)
s = c.session
s["beta_unlocked"] = True
s.save()

rooms_urls = [
    ("/game/", "game:home"),
    ("/game/rooms/", "game:rooms"),
    ("/game/rooms/manage/", "game:rooms_manage"),
    ("/game/quick/", "game:quick_play"),
    ("/game/quick/bot/", "game:bot_setup"),
    ("/game/match/", "game:match_start"),
    ("/game/team/start/", "game:team_start"),
    ("/game/challenge/", "game:challenge"),
]

print("\n  Testing URLs:")
for url, name in rooms_urls:
    try:
        r = c.get(url, follow=False)
        status = r.status_code
        if status == 200:
            print(f"    ✓ {url:30s} → 200 ({name})")
        elif status in (301, 302):
            loc = r.get("Location", "")
            print(f"    → {url:30s} → {status} → {loc[:50]}")
        elif status == 500:
            print(f"    ❌ {url:30s} → 500 ERROR")
            # Get error content
            content = r.content.decode('utf-8', errors='ignore')
            # Extract error
            err_match = re.search(r'<title>(.*?)</title>', content)
            if err_match:
                print(f"       Title: {err_match.group(1)}")
            # Look for exception
            exc = re.search(r'<pre class="exception_value">(.*?)</pre>', content, re.DOTALL)
            if exc:
                print(f"       Error: {exc.group(1)[:200]}")
        else:
            print(f"    ⚠ {url:30s} → {status} ({name})")
    except Exception as e:
        print(f"    ❌ {url:30s} → {type(e).__name__}: {str(e)[:100]}")

# ============================================================
# 5) Find which URLs work and which don't
# ============================================================
print("\n" + "="*70)
print("STEP 5: Report")
print("="*70)

# Re-run tests to categorize
works = []
broken = []

for url, name in rooms_urls:
    try:
        r = c.get(url, follow=False)
        if r.status_code == 200:
            works.append((url, name))
        elif r.status_code == 500:
            broken.append((url, name, "500 error"))
        elif r.status_code == 404:
            broken.append((url, name, "404 not found"))
        # 302 is usually fine (redirect)
    except Exception as e:
        broken.append((url, name, str(type(e).__name__)))

print(f"\n  ✓ Working ({len(works)}):")
for url, name in works:
    print(f"    {url} ({name})")

if broken:
    print(f"\n  ❌ Broken ({len(broken)}):")
    for url, name, err in broken:
        print(f"    {url} → {err}")
else:
    print(f"\n  ✓ All URLs work!")

# ============================================================
# 6) Rebuild missing templates
# ============================================================
print("\n" + "="*70)
print("STEP 6: Rebuild missing templates")
print("="*70)

rebuilt = []

# rooms_manage.html (the list of rooms with search + create modal)
if not os.path.exists("game/templates/game/rooms_manage.html") or os.path.getsize("game/templates/game/rooms_manage.html") < 1000:
    print("\n  Rebuilding rooms_manage.html...")
    write("game/templates/game/rooms_manage.html", '''{% extends "base.html" %}
{% block title %}اتاق‌های بازی{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;gap:12px}
.head h1{font-size:22px;font-weight:bold}
.head h1 span{color:var(--gold)}
.create-btn{display:flex;align-items:center;gap:8px;padding:12px 20px;border-radius:14px;background:linear-gradient(135deg,#8b5cf6,#6b4eff);color:#fff;font-weight:bold;font-size:14px;border:none;font-family:inherit;cursor:pointer;box-shadow:0 8px 20px rgba(139,92,246,.4)}
.create-btn:hover{transform:translateY(-2px)}
.search{display:flex;gap:8px;margin-bottom:20px;background:var(--card);border:1.5px solid var(--border);border-radius:16px;padding:4px}
.search:focus-within{border-color:var(--purple)}
.search input{flex:1;padding:12px 16px;border-radius:12px;border:none;background:transparent;color:#fff;font-size:15px;font-family:inherit}
.search input:focus{outline:none}
.search button{padding:0 20px;border-radius:12px;background:linear-gradient(135deg,#06b6d4,#3b82f6);color:#fff;border:none;font-weight:bold;cursor:pointer;font-size:15px}
.empty{text-align:center;padding:60px 20px;background:var(--card);border:1.5px dashed var(--border);border-radius:20px}
.empty .ic{font-size:64px;margin-bottom:16px;display:block;opacity:.6}
.empty h3{font-size:18px;margin-bottom:8px;color:#fff}
.empty p{color:var(--muted);font-size:13px;margin-bottom:24px}
.empty button{padding:14px 32px;border-radius:14px;background:linear-gradient(135deg,#8b5cf6,#6b4eff);color:#fff;border:none;font-weight:bold;font-size:15px;font-family:inherit;cursor:pointer;box-shadow:0 8px 25px rgba(139,92,246,.4)}
.rooms-list{display:flex;flex-direction:column;gap:10px}
.room-card{display:flex;align-items:center;gap:14px;padding:16px;border-radius:16px;background:var(--card);border:1.5px solid var(--border);text-decoration:none;color:#fff;transition:.2s}
.room-card:hover{border-color:var(--purple);transform:translateX(-3px)}
.room-card.full{opacity:.5;pointer-events:none}
.room-card.member{border-color:rgba(34,197,94,.5);background:linear-gradient(135deg,rgba(34,197,94,.08),var(--card))}
.ri{width:52px;height:52px;border-radius:14px;background:linear-gradient(135deg,rgba(139,92,246,.25),rgba(6,182,212,.15));display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0;border:1px solid rgba(255,255,255,.1)}
.rinfo{flex:1;min-width:0}
.rname-row{display:flex;align-items:center;gap:6px;margin-bottom:4px}
.rname{font-size:16px;font-weight:bold;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rmeta{font-size:12px;color:var(--muted);display:flex;align-items:center;gap:8px}
.rmeta .host{color:var(--teal)}
.rbadge{padding:8px 14px;border-radius:10px;font-size:12px;font-weight:bold;background:rgba(139,92,246,.15);color:#c4b5fd;border:1px solid rgba(139,92,246,.3);flex-shrink:0}
.rbadge.full{background:rgba(239,68,68,.15);color:#fca5a5;border-color:rgba(239,68,68,.3)}
.rbadge.member{background:rgba(34,197,94,.15);color:#86efac;border-color:rgba(34,197,94,.3)}
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);backdrop-filter:blur(8px);z-index:1000;justify-content:center;align-items:center;padding:20px}
.modal-bg.active{display:flex}
.modal{background:linear-gradient(135deg,rgba(30,41,59,.98),rgba(15,23,42,.98));border:1.5px solid rgba(139,92,246,.4);border-radius:24px;width:100%;max-width:460px;max-height:90vh;overflow-y:auto;padding:28px 24px;position:relative;box-shadow:0 25px 60px rgba(0,0,0,.7)}
.modal::-webkit-scrollbar{width:6px}
.modal::-webkit-scrollbar-thumb{background:rgba(139,92,246,.4);border-radius:6px}
.mclose{position:absolute;top:16px;left:16px;width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.1);color:#fff;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center}
.mclose:hover{background:rgba(239,68,68,.3)}
.mtitle{font-size:22px;font-weight:900;text-align:center;margin-bottom:6px;background:linear-gradient(135deg,#c4b5fd,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.msub{font-size:12px;color:var(--muted);text-align:center;margin-bottom:22px}
.flabel{display:block;font-size:13px;color:#c4b5fd;margin:14px 0 8px;font-weight:bold}
.finput{width:100%;padding:14px 16px;border-radius:12px;border:1.5px solid var(--border);background:rgba(15,23,42,.8);color:#fff;font-size:15px;font-family:inherit;box-sizing:border-box}
.finput:focus{outline:none;border-color:var(--purple)}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.cats{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;max-height:180px;overflow-y:auto;padding:4px;margin-top:4px}
.cat-opt{padding:8px 4px;border-radius:8px;background:rgba(15,23,42,.6);border:1px solid var(--border);color:var(--muted);font-size:12px;text-align:center;cursor:pointer;user-select:none}
.cat-opt:hover{border-color:rgba(139,92,246,.4)}
.cat-opt.active{background:rgba(6,182,212,.2);border-color:var(--teal);color:#fff;font-weight:bold}
.bsubmit{width:100%;margin-top:22px;padding:16px;border:none;border-radius:14px;background:linear-gradient(135deg,#8b5cf6,#06b6d4);color:#fff;font-size:16px;font-weight:bold;font-family:inherit;cursor:pointer;box-shadow:0 10px 30px rgba(139,92,246,.4)}
.bsubmit:hover{transform:translateY(-2px)}
.err{background:rgba(239,68,68,.15);color:#fca5a5;border:1px solid rgba(239,68,68,.3);padding:12px 16px;border-radius:12px;font-size:13px;text-align:center;margin-bottom:16px}
</style>
{% endblock %}
{% block content %}
<div class="head">
  <h1>🚪 <span>اتاق‌های بازی</span></h1>
  <button class="create-btn" onclick="openCreateModal()">+ ساخت اتاق</button>
</div>

{% if error %}<div class="err">{{ error }}</div>{% endif %}

<form method="get" class="search">
  <input type="text" name="q" placeholder="جستجوی نام اتاق یا میزبان..." value="{{ query }}" autocomplete="off">
  <button type="submit">🔍</button>
</form>

{% if rooms %}
<div class="rooms-list">
  {% for r in rooms %}
  <a href="/game/rooms/join/{{ r.obj.code }}/" class="room-card {% if r.is_full %}full{% elif r.is_member %}member{% endif %}">
    <div class="ri">🚪</div>
    <div class="rinfo">
      <div class="rname-row">
        <div class="rname">{{ r.obj.room_name }}</div>
        {% if r.has_password %}<span>🔒</span>{% endif %}
      </div>
      <div class="rmeta">
        <span class="host">{{ r.host_avatar }} {{ r.obj.host.alias }}</span>
        <span>•</span>
        <span>{{ r.count }} / {{ r.obj.max_players }}</span>
      </div>
    </div>
    {% if r.is_full %}<span class="rbadge full">پر</span>
    {% elif r.is_member %}<span class="rbadge member">✓ عضو</span>
    {% else %}<span class="rbadge">ورود →</span>{% endif %}
  </a>
  {% endfor %}
</div>
{% elif query %}
<div class="empty">
  <span class="ic">🔍</span>
  <h3>نتیجه‌ای پیدا نشد</h3>
  <p>اتاقی با این مشخصات وجود ندارد.</p>
  <button onclick="openCreateModal()">ساخت اتاق جدید</button>
</div>
{% else %}
<div class="empty">
  <span class="ic">🎮</span>
  <h3>هنوز اتاقی نیست!</h3>
  <p>اولین نفری باش که یه اتاق می‌سازه</p>
  <button onclick="openCreateModal()">+ ساخت اولین اتاق</button>
</div>
{% endif %}

<div class="modal-bg" id="createModal">
  <div class="modal">
    <button class="mclose" onclick="closeCreateModal()">✕</button>
    <div class="mtitle">🏰 ساخت اتاق جدید</div>
    <div class="msub">تنظیمات اتاقت رو انتخاب کن</div>
    <form method="post" id="createForm">
      {% csrf_token %}
      <label class="flabel">📝 اسم اتاق</label>
      <input type="text" name="room_name" class="finput" placeholder="مثلاً: بازی دوستانه" maxlength="50" required>
      <div class="row2" style="margin-top:12px">
        <div>
          <label class="flabel">🔐 رمز (اختیاری)</label>
          <input type="text" name="password" class="finput" placeholder="خالی = بدون رمز" maxlength="32">
        </div>
        <div>
          <label class="flabel">👥 ظرفیت</label>
          <input type="number" name="max_players" class="finput" value="8" min="2" max="15">
        </div>
      </div>
      <label class="flabel">📋 دسته‌ها</label>
      <div class="cats" id="catsGrid">
        {% for c in categories %}
        <div class="cat-opt {% if forloop.counter <= 10 %}active{% endif %}" data-cat="{{ c }}">{{ c }}</div>
        {% endfor %}
      </div>
      <button type="submit" class="bsubmit">🚀 ساخت و ورود</button>
    </form>
  </div>
</div>
{% endblock %}
{% block extra_js %}
<script>
function openCreateModal(){ document.getElementById('createModal').classList.add('active'); document.body.style.overflow='hidden'; }
function closeCreateModal(){ document.getElementById('createModal').classList.remove('active'); document.body.style.overflow=''; }
document.getElementById('createModal').addEventListener('click', function(e){ if(e.target.id==='createModal') closeCreateModal(); });
document.querySelectorAll('.cat-opt').forEach(el => el.addEventListener('click', () => el.classList.toggle('active')));
document.getElementById('createForm').addEventListener('submit', function(e){
  document.querySelectorAll('input[name="categories"]').forEach(el => el.remove());
  const active = document.querySelectorAll('.cat-opt.active');
  if(active.length === 0){ e.preventDefault(); alert('حداقل یک دسته فعال باشد'); return; }
  active.forEach(cat => {
    const input = document.createElement('input');
    input.type = 'hidden'; input.name = 'categories'; input.value = cat.dataset.cat;
    e.target.appendChild(input);
  });
});
</script>
{% endblock %}
''')
    rebuilt.append("rooms_manage.html")

# rooms.html (list of game modes)
if not os.path.exists("game/templates/game/rooms.html") or os.path.getsize("game/templates/game/rooms.html") < 500:
    print("  Rebuilding rooms.html...")
    write("game/templates/game/rooms.html", '''{% extends "base.html" %}
{% block title %}بازی‌ها{% endblock %}
{% block extra_css %}
<style>
.head{margin-bottom:20px}
.head h1{font-size:22px;font-weight:bold}
.head h1 span{color:var(--gold)}
.big{display:flex;align-items:center;gap:14px;padding:20px;border-radius:20px;text-decoration:none;color:#fff;margin-bottom:12px;border:1.5px solid;transition:.2s;position:relative;overflow:hidden}
.big:hover{transform:translateY(-3px)}
.big:active{transform:scale(.98)}
.big.soon{cursor:default;opacity:.75}
.big.bot{background:radial-gradient(circle at 100% 0%,rgba(244,197,66,.25),transparent 60%),linear-gradient(135deg,#2a1a0e,#1a0f1a);border-color:rgba(244,197,66,.4)}
.big.player{background:radial-gradient(circle at 100% 0%,rgba(59,130,246,.25),transparent 60%),linear-gradient(135deg,#0a1a2a,#0f0f1e);border-color:rgba(59,130,246,.4)}
.big.group{background:radial-gradient(circle at 100% 0%,rgba(139,92,246,.3),transparent 60%),linear-gradient(135deg,#1a0f2e,#0f0f1e);border-color:rgba(139,92,246,.4)}
.big.challenge{background:radial-gradient(circle at 100% 0%,rgba(239,68,68,.3),transparent 60%),linear-gradient(135deg,#2a0a0a,#0f0f1e);border-color:rgba(239,68,68,.5)}
.big.speed{background:radial-gradient(circle at 100% 0%,rgba(6,182,212,.25),transparent 60%),linear-gradient(135deg,#0a1e2a,#0f0f1e);border-color:rgba(6,182,212,.4)}
.big.puzzle{background:radial-gradient(circle at 100% 0%,rgba(34,197,94,.25),transparent 60%),linear-gradient(135deg,#0a2a1a,#0f0f1e);border-color:rgba(34,197,94,.4)}
.bic{font-size:34px;width:58px;height:58px;border-radius:16px;background:rgba(255,255,255,.08);display:flex;align-items:center;justify-content:center;flex-shrink:0}
.bbody{flex:1}
.btitle{font-size:17px;font-weight:bold;margin-bottom:4px;color:#fff}
.bdesc{font-size:12px;color:#cbd5e1;line-height:1.5}
.barrow{font-size:20px;color:#94a3b8}
.soon-badge{position:absolute;top:10px;left:10px;background:rgba(234,179,8,.95);color:#1a1a1a;font-size:10px;font-weight:900;padding:3px 8px;border-radius:6px;z-index:2}
</style>
{% endblock %}
{% block content %}
<div class="head"><h1>🎮 <span>بازی‌ها</span></h1></div>

<a href="/game/quick/" class="big bot">
  <div class="bic">⚡</div>
  <div class="bbody"><div class="btitle">بازی با بات</div><div class="bdesc">رقیب هوشمند، سه سطح سختی</div></div>
  <div class="barrow">←</div>
</a>

<a href="/game/match/" class="big player">
  <div class="bic">🌐</div>
  <div class="bbody"><div class="btitle">بازی با پلیر</div><div class="bdesc">رقابت آنی با یک حریف تصادفی</div></div>
  <div class="barrow">←</div>
</a>

<a href="/game/team/start/" class="big group">
  <div class="bic">👥</div>
  <div class="bbody"><div class="btitle">بازی گروهی</div><div class="bdesc">۴ نفره · دو تیم ۲ نفره · ۳ راند</div></div>
  <div class="barrow">←</div>
</a>

<a href="/game/challenge/" class="big challenge">
  <div class="bic">⚔️</div>
  <div class="bbody"><div class="btitle">چالش</div><div class="bdesc">تورنمنت هفتگی، مسابقه روزانه و ساعتی</div></div>
  <div class="barrow">←</div>
</a>

<a href="/game/quick/bot/?mode=speed" class="big speed">
  <div class="bic">⏱️</div>
  <div class="bbody"><div class="btitle">بازی سرعتی</div><div class="bdesc">مستقیم با حرف رندوم، فقط ۲۰ ثانیه!</div></div>
  <div class="barrow">←</div>
</a>

<div class="big puzzle soon" onclick="alert('🎯 بازی معما به زودی فعال می‌شود!')">
  <span class="soon-badge">به زودی</span>
  <div class="bic">🎯</div>
  <div class="bbody"><div class="btitle">بازی معما</div><div class="bdesc">حدس کلمه از روی سرنخ</div></div>
  <div class="barrow">←</div>
</div>
{% endblock %}
''')
    rebuilt.append("rooms.html")

if rebuilt:
    print(f"\n  ✓ Rebuilt: {', '.join(rebuilt)}")
else:
    print("  ✓ All templates exist and are large enough")

# ============================================================
# 7) Fix bottom nav in base.html
# ============================================================
print("\n" + "="*70)
print("STEP 7: Fix bottom nav")
print("="*70)

base = read("templates/base.html")

# Check nav
if 'href="/game/rooms/manage/"' in base:
    print("  ✓ Bottom nav has /game/rooms/manage/")
elif 'href="/game/rooms/"' in base and 'href="/game/rooms/manage/"' not in base:
    print("  ⚠ Bottom nav has /game/rooms/ but not /game/rooms/manage/")
    # Replace
    base = base.replace(
        '<a href="/game/rooms/" class="nav-link {% if active == \'games\' %}active{% endif %}">\n    <span class="nav-icon">🚪</span>\n    <span>اتاق‌ها</span>',
        '<a href="/game/rooms/manage/" class="nav-link {% if active == \'rooms\' %}active{% endif %}">\n    <span class="nav-icon">🚪</span>\n    <span>اتاق‌ها</span>'
    )
    write("templates/base.html", base)
    print("  ✓ Fixed")

# ============================================================
# 8) Test again after fixes
# ============================================================
print("\n" + "="*70)
print("STEP 8: Final test")
print("="*70)

for url, name in rooms_urls:
    try:
        r = c.get(url, follow=False)
        if r.status_code == 200:
            print(f"  ✓ {url:30s} → 200")
        elif r.status_code == 500:
            print(f"  ❌ {url:30s} → 500")
        elif r.status_code == 404:
            print(f"  ❌ {url:30s} → 404")
        else:
            print(f"  → {url:30s} → {r.status_code}")
    except Exception as e:
        print(f"  ❌ {url:30s} → {type(e).__name__}")

# Cleanup
if created:
    tu.delete()

# Django check
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("\n  ✓ Django check PASSED")
else:
    print(f"\n  ⚠ Errors: {r.stderr[:500]}")

print("\n" + "="*70)
print("DONE")
print("="*70)
print("""
Summary:
  - Checked game/urls.py routes
  - Checked all view functions
  - Checked all templates
  - Tested all URLs with HTTP client
  - Rebuilt any missing/broken templates
  - Fixed bottom nav link

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)

Test each:
  /game/                  → menu (bot button + all games)
  /game/rooms/            → list of game modes
  /game/rooms/manage/     → list of active rooms + create button
  /game/quick/bot/        → bot setup
""")
