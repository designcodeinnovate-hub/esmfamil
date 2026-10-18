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
    bak = p + ".bak4"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) menu.html - remove coin HUD (HTML + CSS)
# ============================================================
print("\n[1/3] menu.html - remove coin HUD")
p = os.path.join(ROOT, "game", "templates", "game", "menu.html")
src = read(p)
changed = False

# 1a) Remove HTML block
html_pat = re.compile(r'\s*<div class="coin-hud">.*?</div>\s*\n\s*</div>', re.DOTALL)
# Simpler: find the exact block
html_block = '''  <div class="coin-hud">
    <div class="hud-chip hud-coins">
      <div class="hud-circle">🪙</div>
      <span class="hud-num">{{ user.coins|default:0 }}</span>
      <span class="hud-lbl">سکه</span>
    </div>
    <div class="hud-chip hud-gems">
      <div class="hud-circle">💎</div>
      <span class="hud-num">{{ user.gems|default:0 }}</span>
      <span class="hud-lbl">جم</span>
    </div>
  </div>
'''
if html_block in src:
    src = src.replace(html_block, "", 1)
    changed = True
    print("  FIXED: coin HUD HTML removed")
else:
    # Try regex fallback
    m = re.search(r'<div class="coin-hud">.*?</div>\s*</div>\s*</div>', src, re.DOTALL)
    if m:
        src = src[:m.start()] + src[m.end():]
        changed = True
        print("  FIXED: coin HUD HTML removed (regex)")
    else:
        print("  WARN: coin HUD HTML not found")

# 1b) Remove CSS block
css_start = src.find("  .coin-hud {")
if css_start > 0:
    css_end_marker = "  .hud-lbl { font-size: 10px; opacity: 0.75; font-weight: bold; }"
    css_end = src.find(css_end_marker, css_start)
    if css_end > 0:
        css_end += len(css_end_marker)
        src = src[:css_start] + src[css_end:]
        changed = True
        print("  FIXED: coin HUD CSS removed")

if changed:
    backup(p); write(p, src)

# ============================================================
# 2) friends.html - remove modal (HTML + CSS) + password modal
# ============================================================
print("\n[2/3] friends.html - remove alliance modal")
p = os.path.join(ROOT, "social", "templates", "social", "friends.html")
src = read(p)
changed = False

# 2a) Remove modal HTML blocks
old_modal = '''  {% if not my_alliance %}
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

if old_modal in src:
    src = src.replace(old_modal, "", 1)
    changed = True
    print("  FIXED: modal HTML removed")
else:
    # Try regex - remove from "{% if not my_alliance %}" to matching "{% endif %}"
    pat = re.compile(
        r'\s*\{% if not my_alliance %\}\s*<!-- مودال لیست اتحادها -->.*?\{% endif %\}\s*',
        re.DOTALL
    )
    m = pat.search(src)
    if m:
        src = src[:m.start()] + src[m.end():]
        changed = True
        print("  FIXED: modal HTML removed (regex)")
    else:
        print("  WARN: modal HTML not found")

# 2b) Remove JS functions
old_js_start = "<script>\nfunction openAllianceModal()"
old_js_end = "})();\n</script>"
js_start = src.find(old_js_start)
if js_start > 0:
    js_end = src.find(old_js_end, js_start)
    if js_end > 0:
        js_end += len(old_js_end)
        src = src[:js_start] + src[js_end:]
        changed = True
        print("  FIXED: modal JS removed")

# 2c) Remove CSS block (from "/* ===== مودال لیست اتحادها ===== */" to end of password-modal)
css_start = src.find("/* ===== مودال لیست اتحادها ===== */")
if css_start > 0:
    # find end - last .alliance-password-modal closing brace
    end_marker = ".alliance-password-modal h3 { font-size: 18px; color: #c4b5fd; text-align: center; margin-bottom: 8px; }"
    css_end = src.find(end_marker, css_start)
    if css_end > 0:
        css_end += len(end_marker)
        src = src[:css_start] + src[css_end:]
        changed = True
        print("  FIXED: modal CSS removed")

# 2d) Convert alliance card button to plain link
old_card = '''  {% else %}
    <button type="button" onclick="openAllianceModal()" class="alliance-card">
      <div class="ac-icon">🛡️</div>
      <div class="ac-body">
        <div class="ac-title">اتحاد</div>
        <div class="ac-desc">لیست اتحادها رو ببین یا خودت بساز</div>
      </div>
      <div class="ac-arrow">←</div>
    </button>
  {% endif %}'''
new_card = '''  {% else %}
    <a href="/alliance/" class="alliance-card">
      <div class="ac-icon">🛡️</div>
      <div class="ac-body">
        <div class="ac-title">اتحاد</div>
        <div class="ac-desc">لیست اتحادها رو ببین یا خودت بساز</div>
      </div>
      <div class="ac-arrow">←</div>
    </a>
  {% endif %}'''

if old_card in src:
    src = src.replace(old_card, new_card, 1)
    changed = True
    print("  FIXED: card -> plain link to /alliance/")

if changed:
    backup(p); write(p, src)

# ============================================================
# 3) Verification
# ============================================================
print("\n[3/3] Verification")
menu_src = read(os.path.join(ROOT, "game", "templates", "game", "menu.html"))
friends_src = read(os.path.join(ROOT, "social", "templates", "social", "friends.html"))

print("  menu.html:")
print(f"    coin-hud present: {'coin-hud' in menu_src}")
print(f"    hud-chip present: {'hud-chip' in menu_src}")

print("  friends.html:")
print(f"    allianceModal present: {'allianceModal' in friends_src}")
print(f"    alliancePasswordModal present: {'alliancePasswordModal' in friends_src}")
print(f"    alliance-password-modal CSS present: {'.alliance-password-modal {' in friends_src}")
print(f"    openAllianceModal JS present: {'openAllianceModal' in friends_src}")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Removed:
  ✓ menu.html: coin/gem HUD (both HTML + CSS)
  ✓ friends.html: alliance modal (both HTML + CSS + JS)
  ✓ friends.html: alliance password modal
  ✓ friends.html: card converted back to plain link -> /alliance/

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R
""")
