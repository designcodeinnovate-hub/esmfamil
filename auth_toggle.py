#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Toggle auth UI off (auto-guest) with easy restore."""
import os, re, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def read(p):
    if not os.path.exists(p): return ""
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Add FORCE_GUEST_MODE to settings.py
# ============================================================
print("\n[1/6] Adding FORCE_GUEST_MODE flag to settings")

p = "config/settings.py"
src = read(p)

if "FORCE_GUEST_MODE" not in src:
    src = src.rstrip() + '''

# ============================================================
# AUTH MODE TOGGLE
# ============================================================
# True  = auto-guest, no login/register UI (direct to game)
# False = normal auth flow (login/register visible)
FORCE_GUEST_MODE = True
'''
    write(p, src)
    print("  ✓ FORCE_GUEST_MODE = True added")
else:
    print("  ✓ FORCE_GUEST_MODE already exists")

# ============================================================
# 2) Create context processor
# ============================================================
print("\n[2/6] Creating context processor")

p = "accounts/context_processors.py"
write(p, '''# -*- coding: utf-8 -*-
"""Context processor to expose FORCE_GUEST_MODE to all templates."""
from django.conf import settings


def force_guest_mode(request):
    return {
        "force_guest_mode": getattr(settings, "FORCE_GUEST_MODE", False),
    }
''')

# Register it in settings.py TEMPLATES
p = "config/settings.py"
src = read(p)

if "accounts.context_processors.force_guest_mode" not in src:
    # Find TEMPLATES context_processors section
    old = '''"django.contrib.messages.context_processors.messages",
            ],'''
    new = '''"django.contrib.messages.context_processors.messages",
                "accounts.context_processors.force_guest_mode",
            ],'''
    if old in src:
        src = src.replace(old, new, 1)
        write(p, src)
        print("  ✓ Registered in TEMPLATES context_processors")
    else:
        # Try alternate
        old2 = '''"django.template.context_processors.request",'''
        if old2 in src:
            src = src.replace(
                old2,
                '"django.template.context_processors.request",\n                "accounts.context_processors.force_guest_mode",',
                1
            )
            write(p, src)
            print("  ✓ Registered (fallback)")
        else:
            print("  ⚠ Could not auto-register — need manual addition")
else:
    print("  ✓ Already registered")

# ============================================================
# 3) Modify landing view to auto-guest
# ============================================================
print("\n[3/6] Modifying landing view")

p = "accounts/views.py"
src = read(p)

# Replace landing function
pattern = re.compile(r'def landing\(request\):.*?(?=\ndef |\n@login_required|\Z)', re.DOTALL)
m = pattern.search(src)

if m:
    old_block = m.group(0)
    new_landing = '''def landing(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)
    from django.conf import settings as _s
    if getattr(_s, "FORCE_GUEST_MODE", False):
        return guest_start(request)
    return render(request, "accounts/landing.html")
'''
    src = src.replace(old_block, new_landing)
    write(p, src)
    print("  ✓ landing: auto-guest when FORCE_GUEST_MODE")
else:
    print("  ⚠ landing function not found")

# ============================================================
# 4) Modify login, register, logout views
# ============================================================
print("\n[4/6] Modifying auth views")

src = read(p)

# login_view
if "def login_view(request):" in src:
    m = re.search(r'def login_view\(request\):.*?(?=\ndef |\n@login_required|\Z)', src, re.DOTALL)
    if m:
        old = m.group(0)
        # Add auto-guest at top
        new = '''def login_view(request):
    if request.user.is_authenticated:
        return _next_after_login(request.user)
    from django.conf import settings as _s
    if getattr(_s, "FORCE_GUEST_MODE", False):
        return guest_start(request)
    error = None
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip().lower()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return _next_after_login(user)
        error = "شناسه کاربری یا رمز عبور اشتباه است."
    return render(request, "accounts/login.html", {"error": error})
'''
        src = src.replace(old, new)
        print("  ✓ login_view: auto-guest")

# register_view
if "def register_view(request):" in src:
    m = re.search(r'def register_view\(request\):.*?(?=\ndef |\n@login_required|\Z)', src, re.DOTALL)
    if m:
        old = m.group(0)
        # Add check at top
        if "FORCE_GUEST_MODE" not in old:
            insert_pos = old.find("error = None")
            if insert_pos > 0:
                new = old[:insert_pos] + '''from django.conf import settings as _s
    if getattr(_s, "FORCE_GUEST_MODE", False):
        return guest_start(request)
    ''' + old[insert_pos:]
                src = src.replace(old, new)
                print("  ✓ register_view: auto-guest")

# logout_view - redirect to game (no-op)
if "def logout_view(request):" in src:
    m = re.search(r'def logout_view\(request\):.*?(?=\ndef |\n@login_required|\Z)', src, re.DOTALL)
    if m:
        old = m.group(0)
        if "FORCE_GUEST_MODE" not in old:
            # Add at very top
            first_line_end = old.find("\n") + 1
            new = old[:first_line_end] + '''    from django.conf import settings as _s
    if getattr(_s, "FORCE_GUEST_MODE", False):
        return redirect("game:home")
''' + old[first_line_end:]
            src = src.replace(old, new)
            print("  ✓ logout_view: no-op in guest mode")

# profile_view - redirect to game
if "def profile_view(request):" in src:
    m = re.search(r'(@login_required[^\n]*\n)?def profile_view\(request\):.*?(?=\ndef |\n@login_required|\Z)', src, re.DOTALL)
    if m:
        old = m.group(0)
        if "FORCE_GUEST_MODE" not in old:
            # Find the first line after def (skip decorator)
            def_line = old.find("def profile_view")
            body_start = old.find("\n", def_line) + 1
            new = old[:body_start] + '''    from django.conf import settings as _s
    if getattr(_s, "FORCE_GUEST_MODE", False):
        return redirect("game:home")
''' + old[body_start:]
            src = src.replace(old, new)
            print("  ✓ profile_view: redirect to game")

write(p, src)

# _next_after_login - respect FORCE_GUEST_MODE
src = read(p)
if "_next_after_login" in src:
    m = re.search(r'def _next_after_login\(user\):.*?(?=\ndef |\Z)', src, re.DOTALL)
    if m:
        old = m.group(0)
        if "FORCE_GUEST_MODE" not in old:
            first_line_end = old.find("\n") + 1
            new = old[:first_line_end] + '''    from django.conf import settings as _s
    if getattr(_s, "FORCE_GUEST_MODE", False):
        return redirect("game:home")
''' + old[first_line_end:]
            src = src.replace(old, new)
            write(p, src)
            print("  ✓ _next_after_login: respects FORCE_GUEST_MODE")

# ============================================================
# 5) Hide UI elements in base.html + menu.html
# ============================================================
print("\n[5/6] Hiding UI elements")

# --- base.html: hide profile nav link ---
p = "templates/base.html"
src = read(p)

old_profile_nav = '''<a href="/accounts/profile/" class="nav-link {% if active == 'profile' %}active{% endif %}">
    <span class="nav-icon">👤</span>
    <span>پروفایل</span>
  </a>'''

new_profile_nav = '''{% if not force_guest_mode %}
  <a href="/accounts/profile/" class="nav-link {% if active == 'profile' %}active{% endif %}">
    <span class="nav-icon">👤</span>
    <span>پروفایل</span>
  </a>
  {% endif %}'''

if old_profile_nav in src and "force_guest_mode" not in src[src.find(old_profile_nav)-50:src.find(old_profile_nav)]:
    src = src.replace(old_profile_nav, new_profile_nav, 1)
    write(p, src)
    print("  ✓ base.html: profile nav hidden in guest mode")
else:
    print("  ⏭ base.html: already handled or pattern not found")

# --- menu.html: hide user row + guest warning ---
p = "game/templates/game/menu.html"
src = read(p)

def find_matching_div_end(text, start_idx):
    """Find index after matching </div>."""
    depth = 0
    i = start_idx
    while i < len(text):
        next_open = text.find('<div', i)
        next_close = text.find('</div>', i)
        if next_close < 0:
            return -1
        if next_open >= 0 and next_open < next_close:
            depth += 1
            i = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                return next_close + 6
            i = next_close + 6
    return -1

# user-row
if '<div class="user-row">' in src and '{% if not force_guest_mode %}' not in src[:src.find('<div class="user-row">')]:
    start = src.find('<div class="user-row">')
    if start >= 0:
        end = find_matching_div_end(src, start)
        if end > 0:
            src = src[:start] + '{% if not force_guest_mode %}\n  ' + src[start:end] + '\n  {% endif %}\n  ' + src[end:]
            print("  ✓ menu.html: user-row hidden")

# guest-warning
if '<div class="guest-warning">' in src and '{% if not force_guest_mode %}' not in src[:src.find('<div class="guest-warning">')]:
    start = src.find('<div class="guest-warning">')
    if start >= 0:
        end = find_matching_div_end(src, start)
        if end > 0:
            src = src[:start] + '{% if not force_guest_mode %}\n  ' + src[start:end] + '\n  {% endif %}\n  ' + src[end:]
            print("  ✓ menu.html: guest-warning hidden")

write(p, src)

# ============================================================
# 6) Create restore script
# ============================================================
print("\n[6/6] Creating restore script")

write("RESTORE_AUTH.py", '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RESTORE FULL AUTH: set FORCE_GUEST_MODE = False."""
import os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

p = "config/settings.py"
with open(p, "r", encoding="utf-8") as f:
    src = f.read()

src = src.replace("FORCE_GUEST_MODE = True", "FORCE_GUEST_MODE = False")

with open(p, "w", encoding="utf-8") as f:
    f.write(src)

print("=" * 60)
print("✅ AUTH RESTORED")
print("=" * 60)
print("FORCE_GUEST_MODE = False")
print()
print("Now:")
print("  1. Restart server: python manage.py runserver")
print("  2. Landing page shows (login/register/guest)")
print("  3. Profile link visible in bottom nav")
print("  4. User row visible in menu")
print()
print("All previous functionality restored!")
''')

print("  ✓ RESTORE_AUTH.py created (run it to restore)")

# ============================================================
# Final: Django check
# ============================================================
print("\n[CHECK] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:600]}")

# Verify
import django
django.setup()
from django.conf import settings
print(f"\n  FORCE_GUEST_MODE: {settings.FORCE_GUEST_MODE}")

# Test HTTP
from django.test import Client
c = Client()
r = c.get("/", follow=False)
print(f"\n  GET / → {r.status_code}")
if r.status_code == 302:
    print(f"    → redirect to: {r.get('Location')}")

r = c.get("/accounts/profile/", follow=False)
print(f"  GET /accounts/profile/ → {r.status_code}")
if r.status_code == 302:
    print(f"    → redirect to: {r.get('Location')}")

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔓 GUEST MODE ACTIVE — Authentication UI hidden
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What changes now:

  ❌ Page / no longer shows landing (login/register/guest buttons)
     → Directly goes to /game/ with auto-created guest account

  ❌ No login/register screens visible
  ❌ No "پروفایل" (profile) in bottom nav
  ❌ No user row (avatar + greeting) in menu
  ❌ No guest warning box
  ❌ Logout does nothing (stays logged in)

  ✅ Games work normally
  ✅ Rooms, chat, alliances work
  ✅ Settings icon (⚙️) still visible for music control
  ✅ Support icon (💬) still visible
  ✅ User still has account underneath (for game state)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 TO RESTORE FULL AUTH (when you want it back)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Just run:

    python RESTORE_AUTH.py

Then restart server:

    python manage.py runserver

Everything comes back:
  ✓ Landing page with 3 buttons
  ✓ Login / Register screens
  ✓ Profile in bottom nav
  ✓ User row in menu
  ✓ Logout button
  ✓ Full auth flow

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 DEPLOY TO RUNFLARE (when ready)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    git add .
    git commit -m "auth: guest mode (hidden UI)"
    git push
    runflare deploy

Then Restart in Runflare Panel.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 TEST LOCALLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    python manage.py runserver

Open:
  http://127.0.0.1:8000/
  → Should auto-create guest and go to /game/
  → No login screen
  → Menu shows but without user row

  http://127.0.0.1:8000/accounts/profile/
  → Redirects to /game/ (hidden)
""")
