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
# 1) game/templates/game/rooms.html - 5 کارت بازی
# ============================================================
print("\n[1/5] rooms.html - 5 game cards")
p = os.path.join(ROOT, "game", "templates", "game", "rooms.html")
src = read(p)

if "game-card speed" in src:
    print("  SKIP: 5 cards already exist")
else:
    backup(p)
    old_cards = '''  <a href="/game/quick/" class="big-card bot">
    <div class="bc-icon">⚡</div>
    <div class="bc-body">
      <div class="bc-title">بازی با بات</div>
      <div class="bc-desc">رقیب هوشمند، سه سطح سختی</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>

  <a href="/game/rooms/manage/" class="big-card room">
    <div class="bc-icon">🚪</div>
    <div class="bc-body">
      <div class="bc-title">اتاق‌های بازی</div>
      <div class="bc-desc">ساخت اتاق جدید یا پیوستن به دوستان</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>'''

    new_cards = '''  <a href="/game/quick/" class="big-card bot">
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
  </a>'''

    if old_cards in src:
        src = src.replace(old_cards, new_cards, 1)
        write(p, src)
        print("  FIXED: 5 cards added")
    else:
        print("  WARN: old cards block not found")

# ============================================================
# 2) game/views.py - bot_setup mode
# ============================================================
print("\n[2/5] game/views.py - bot_setup mode")
p = os.path.join(ROOT, "game", "views.py")
src = read(p)

if 'mode = request.GET.get("mode")' in src:
    print("  SKIP: mode already handled")
else:
    backup(p)
    old = '''    if request.method == "POST":
        difficulty = request.POST.get("difficulty", "medium")'''
    new = '''    mode = request.GET.get("mode", "normal")
    is_speed = (mode == "speed")
    is_challenge = (mode == "challenge")

    if request.method == "POST":
        difficulty = request.POST.get("difficulty", "medium")'''
    src = src.replace(old, new, 1)

    old = '''        base_time = {"easy": 150, "medium": 120, "hard": 90}[difficulty]'''
    new = '''        if is_speed:
            base_time = 30
        else:
            base_time = {"easy": 150, "medium": 120, "hard": 90}[difficulty]'''
    src = src.replace(old, new, 1)

    old = '''            letter = bot_logic.bot_pick_letter(difficulty)
        else:
            letter = bot_logic.bot_pick_letter(difficulty)'''
    new = '''            letter = bot_logic.bot_pick_letter(difficulty)
        else:
            if is_challenge:
                letter = random.choice(list("ثضظژذغ"))
            else:
                letter = bot_logic.bot_pick_letter(difficulty)'''
    src = src.replace(old, new, 1)

    write(p, src)
    print("  FIXED: bot_setup supports speed/challenge")

# ============================================================
# 3) alliance/views.py - max_members
# ============================================================
print("\n[3/5] alliance/views.py - max_members")
p = os.path.join(ROOT, "alliance", "views.py")
src = read(p)

if 'max_members = int(request.POST.get("max_members"' in src:
    print("  SKIP: max_members already handled")
else:
    backup(p)
    old = '''        elif Alliance.objects.filter(name=name).exists():
            error = "این نام قبلاً گرفته شده."
        else:
            a = Alliance.objects.create(
                name=name, tag=tag, description=description,
                emblem=emblem or "🛡️", leader=request.user,
            )'''
    new = '''        elif Alliance.objects.filter(name=name).exists():
            error = "این نام قبلاً گرفته شده."
        else:
            try:
                max_members = int(request.POST.get("max_members") or 30)
            except (ValueError, TypeError):
                max_members = 30
            max_members = max(5, min(50, max_members))

            a = Alliance.objects.create(
                name=name, tag=tag, description=description,
                emblem=emblem or "🛡️", leader=request.user,
                max_members=max_members,
            )'''
    if old in src:
        src = src.replace(old, new, 1)
        write(p, src)
        print("  FIXED: max_members added to create_alliance")
    else:
        print("  WARN: create_alliance block not found")

# ============================================================
# 4) alliance/templates/alliance/create.html - فیلد ظرفیت
# ============================================================
print("\n[4/5] create.html - capacity field")
p = os.path.join(ROOT, "alliance", "templates", "alliance", "create.html")
src = read(p)

if 'name="max_members"' in src:
    print("  SKIP: capacity field exists")
else:
    backup(p)
    old = '''      <label>توضیح (اختیاری)</label>
      <textarea name="description" maxlength="200" placeholder="چند خط درباره تیمت..."></textarea>'''
    new = '''      <label>توضیح (اختیاری)</label>
      <textarea name="description" maxlength="200" placeholder="چند خط درباره تیمت..."></textarea>

      <label>ظرفیت اعضا (۵ تا ۵۰)</label>
      <input type="number" name="max_members" min="5" max="50" value="30" style="width:100%; padding:12px 14px; border-radius:12px; border:1.5px solid var(--border); background:var(--bg); color:var(--text); font-size:15px; font-family:inherit; margin-bottom:12px;">'''
    src = src.replace(old, new, 1)
    write(p, src)
    print("  FIXED: capacity field added")

# ============================================================
# 5) alliance/templates/alliance/detail.html - نمایش ظرفیت + دکمه بازگشت
# ============================================================
print("\n[5/5] detail.html - capacity display + back button")
p = os.path.join(ROOT, "alliance", "templates", "alliance", "detail.html")
src = read(p)

if "member_count }} / {{ alliance.max_members" in src:
    print("  SKIP: capacity already displayed")
else:
    backup(p)
    old = '''    <div class="stat-box">
      <div class="stat-val">{{ member_count }}</div>
      <div class="stat-lbl">اعضا</div>
    </div>'''
    new = '''    <div class="stat-box">
      <div class="stat-val">{{ member_count }} / {{ alliance.max_members }}</div>
      <div class="stat-lbl">ظرفیت اعضا</div>
    </div>'''
    src = src.replace(old, new, 1)
    write(p, src)
    print("  FIXED: capacity displayed")

# دکمه بازگشت به اتحاد (برای create, join, chat)
for tpl_name in ["create.html", "join.html", "chat.html"]:
    tpl_path = os.path.join(ROOT, "alliance", "templates", "alliance", tpl_name)
    if not os.path.exists(tpl_path):
        continue
    t_src = read(tpl_path)
    if 'href="/alliance/"' in t_src and 'back-btn' in t_src:
        continue
    if tpl_name == "chat.html":
        old_back = '''    <a href="/alliance/{{ alliance.id }}/" class="back-btn"><span class="arrow-icon">→</span></a>'''
        if old_back not in t_src:
            continue
    # add simple back link at top of content if not exists
    if "{% block content %}" in t_src and 'href="/alliance/"' not in t_src:
        t_src = t_src.replace(
            "{% block content %}",
            '''{% block content %}
  <div style="margin-bottom:12px;">
    <a href="/alliance/" style="color:var(--muted); font-size:13px; text-decoration:none;">← بازگشت به اتحاد</a>
  </div>''',
            1
        )
        backup(tpl_path)
        write(tpl_path, t_src)
        print(f"  FIXED: back link in {tpl_name}")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Summary:
  1. rooms.html        -> 5 game cards: bot, player, group, speed, challenge
  2. game/views.py     -> bot_setup accepts ?mode=speed or ?mode=challenge
  3. alliance/views.py -> create_alliance reads max_members
  4. create.html       -> capacity input field (5-50)
  5. detail.html       -> shows capacity like "12 / 30"
  6. back links added to alliance sub-pages

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R
""")
