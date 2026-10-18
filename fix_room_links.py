#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find and fix broken room links in templates."""
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
# 1) Test ALL room-related flows with follow=True
# ============================================================
print("\n" + "="*70)
print("STEP 1: Test room flows (with redirects followed)")
print("="*70)

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
User = get_user_model()

tu = User.objects.filter(username="__room_diag__").first()
created = False
if not tu:
    tu = User.objects.create_user(
        username="__room_diag__", password="x"*10,
        alias="room-test", is_active=True,
        has_chosen_avatar=True, has_completed_registration=True,
    )
    created = True

c = Client()
c.force_login(tu)
c.session["beta_unlocked"] = True
c.session.save()

def test_url(url, follow=False):
    try:
        r = c.get(url, follow=follow)
        return r.status_code, r.redirect_chain if follow and hasattr(r, 'redirect_chain') else None
    except Exception as e:
        return f"EXC: {type(e).__name__}: {str(e)[:50]}", None

# Test the flows the user would follow
print("\n  Flow 1: user clicks 'بازی‌ها' in nav")
print(f"    /game/rooms/                    → {test_url('/game/rooms/')}")

print("\n  Flow 2: user clicks 'اتاق‌ها' in nav")
print(f"    /game/rooms/manage/             → {test_url('/game/rooms/manage/')}")

print("\n  Flow 3: user clicks 'ساخت اتاق' (opens modal - no navigation)")
print("    (this is JS-only, no URL to test)")

print("\n  Flow 4: user submits create room form (POST)")
try:
    r = c.post('/game/rooms/manage/', {
        'room_name': '__test_room__',
        'password': '',
        'max_players': '8',
        'categories': ['اسم', 'فامیل', 'میوه'],
    }, follow=True)
    print(f"    POST → {r.status_code}, chain: {r.redirect_chain if hasattr(r, 'redirect_chain') else 'N/A'}")

    # Get the created room
    from game.models import Game
    test_game = Game.objects.filter(room_name='__test_room__').first()
    if test_game:
        print(f"    ✓ Room created: code={test_game.code}")

        print("\n  Flow 5: user clicks 'join' on their room")
        print(f"    /game/rooms/join/{test_game.code}/   → {test_url(f'/game/rooms/join/{test_game.code}/')}")

        print("\n  Flow 6: user is redirected to room page")
        print(f"    /game/room/{test_game.code}/        → {test_url(f'/game/room/{test_game.code}/')}")

        # Cleanup
        test_game.delete()
        print(f"    ✓ Cleaned up")
    else:
        print(f"    ❌ Room was NOT created")
except Exception as e:
    print(f"    ❌ POST failed: {e}")

print("\n  Flow 7: user clicks 'بازی با پلیر'")
status, chain = test_url('/game/match/', follow=True)
print(f"    /game/match/ (follow) → {status}")
if chain:
    print(f"    redirect chain: {chain}")

print("\n  Flow 8: user clicks 'بازی گروهی'")
status, chain = test_url('/game/team/start/', follow=True)
print(f"    /game/team/start/ (follow) → {status}")
if chain:
    print(f"    redirect chain: {chain}")

# ============================================================
# 2) Check what links exist in the actual templates
# ============================================================
print("\n" + "="*70)
print("STEP 2: What links exist in templates?")
print("="*70)

templates_to_check = {
    "menu.html": "game/templates/game/menu.html",
    "rooms.html": "game/templates/game/rooms.html",
    "rooms_manage.html": "game/templates/game/rooms_manage.html",
    "base.html (nav)": "templates/base.html",
}

for name, path in templates_to_check.items():
    if not os.path.exists(path):
        print(f"\n  ✗ {name}: FILE NOT FOUND")
        continue

    src = read(path)
    hrefs = re.findall(r'href="([^"]+)"', src)
    unique = sorted(set(h for h in hrefs if not h.startswith('#') and 'javascript' not in h))

    print(f"\n  {name}:")
    for h in unique[:15]:
        print(f"    {h}")

# ============================================================
# 3) Check base.html bottom nav specifically
# ============================================================
print("\n" + "="*70)
print("STEP 3: Bottom nav links")
print("="*70)

base_src = read("templates/base.html")
nav_match = re.search(r'<nav class="bottom-nav">(.*?)</nav>', base_src, re.DOTALL)

if nav_match:
    nav = nav_match.group(1)
    links = re.findall(r'<a\s+href="([^"]+)"[^>]*>.*?<span[^>]*>([^<]*)</span>', nav, re.DOTALL)
    for href, label in links:
        label_clean = label.strip()
        # Check if route works
        status, _ = test_url(href)
        mark = "✓" if status in (200, 301, 302) else "✗"
        print(f"  {mark} {label_clean:12s} → {href:30s} ({status})")

# ============================================================
# 4) Check menu.html for what buttons actually link to
# ============================================================
print("\n" + "="*70)
print("STEP 4: Menu buttons")
print("="*70)

menu_src = read("game/templates/game/menu.html")

# Find all <a> links
links = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>', menu_src)
print(f"\n  Found {len(links)} links in menu.html:")
for link in sorted(set(links)):
    if link.startswith('#') or 'javascript' in link:
        continue
    status, _ = test_url(link)
    mark = "✓" if status == 200 else ("→" if status in (301,302) else "✗")
    print(f"  {mark} {link:30s} ({status})")

# ============================================================
# 5) If any link is broken, FIX it
# ============================================================
print("\n" + "="*70)
print("STEP 5: Fix any issues found")
print("="*70)

# 5a) Ensure menu has ALL game links
menu_src = read("game/templates/game/menu.html")
menu_changes = 0

# Check for the "همه بازی‌ها" or bot card
if "/game/rooms/" not in menu_src and "/game/quick/" not in menu_src:
    print("  ⚠ menu.html has NO game links!")
    menu_changes += 1

# 5b) Ensure rooms.html has ALL game mode links
rooms_src = read("game/templates/game/rooms.html")
required_links = {
    "/game/quick/": "بازی با بات",
    "/game/match/": "بازی با پلیر",
    "/game/team/start/": "بازی گروهی",
    "/game/challenge/": "چالش",
    "/game/quick/bot/?mode=speed": "بازی سرعتی",
}

missing = []
for link, name in required_links.items():
    if link not in rooms_src:
        missing.append((link, name))
        print(f"  ⚠ rooms.html missing: {name} ({link})")

if missing:
    print(f"\n  → Rebuilding rooms.html with all links...")
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
    print("  ✓ Rebuilt rooms.html with all 6 game links")

# 5c) Check rooms_manage.html has proper form action
if os.path.exists("game/templates/game/rooms_manage.html"):
    manage_src = read("game/templates/game/rooms_manage.html")
    # The form should POST to the same URL (which is correct)
    if 'method="post"' not in manage_src:
        print("  ⚠ rooms_manage.html missing form POST")

# 5d) Rebuild rooms_manage.html with working create + join
print("\n  → Ensuring rooms_manage.html is complete...")
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
.mclose{position:absolute;top:16px;left:16px;width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.1);color:#fff;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center;border:none}
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
    <form method="post" action="/game/rooms/manage/" id="createForm">
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
print("  ✓ Rebuilt rooms_manage.html")

# ============================================================
# 6) Verify all links now work
# ============================================================
print("\n" + "="*70)
print("STEP 6: Final verification")
print("="*70)

# Re-run the flows
print("\n  Critical URLs:")
test_urls = [
    "/game/",
    "/game/rooms/",
    "/game/rooms/manage/",
    "/game/quick/",
    "/game/quick/bot/",
    "/game/match/",
    "/game/team/start/",
    "/game/challenge/",
]

for url in test_urls:
    status, _ = test_url(url, follow=False)
    if status == 200:
        print(f"    ✓ {url:30s} → 200")
    elif status in (301, 302):
        print(f"    → {url:30s} → {status} (redirect)")
    else:
        print(f"    ❌ {url:30s} → {status}")

# POST create room test
print("\n  POST create room test:")
try:
    r = c.post('/game/rooms/manage/', {
        'room_name': '__final_test__',
        'password': '',
        'max_players': '8',
        'categories': ['اسم', 'فامیل', 'میوه'],
    }, follow=False)

    print(f"    POST status: {r.status_code}")
    if r.status_code == 302:
        loc = r.get("Location", "")
        print(f"    → redirects to: {loc}")

        # Follow the redirect
        r2 = c.get(loc, follow=False)
        print(f"    → {loc} → {r2.status_code}")

        if r2.status_code == 200:
            print(f"    ✓ Room page works!")

    from game.models import Game
    test_game = Game.objects.filter(room_name='__final_test__').first()
    if test_game:
        test_game.delete()
        print(f"    ✓ Cleaned up")
except Exception as e:
    print(f"    ❌ {e}")

# Cleanup user
if created:
    tu.delete()

# Django check
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("\n  ✓ Django check PASSED")
else:
    print(f"\n  ⚠ {r.stderr[:400]}")

print("\n" + "="*70)
print("DONE")
print("="*70)
print("""
If everything is ✓ above, try the browser:

  1. pkill -9 -f "manage.py runserver"
  2. python manage.py runserver
  3. Ctrl+Shift+R (hard refresh)
  4. Open /game/rooms/manage/
  5. Click "+ ساخت اتاق" → modal should open
  6. Fill in name → click "ساخت و ورود"
  7. Should redirect to /game/room/<code>/

If modal doesn't open:
  → F12 Console → check for JS errors
  → Send screenshot or error message

If POST fails:
  → F12 Network tab → see the POST response
""")
