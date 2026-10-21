#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix: _rand import + support migration"""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def read(p):
    try:
        with open(p, "r", encoding="utf-8") as f: return f.read()
    except: return ""
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) FIX _rand import in game/views.py
# ============================================================
print("\n[1/6] Fixing _rand in game/views.py")
src = read("game/views.py")

# Check if _rand is used but not imported
uses_rand = "_rand." in src
imported_rand = "import random as _rand" in src

if uses_rand and not imported_rand:
    print("  ⚠ _rand is used but not imported — adding import")
    # Add after other imports (near top)
    # Try to add after "import random" or at top
    if "import random\n" in src:
        src = src.replace("import random\n", "import random\nimport random as _rand\n", 1)
    elif "import random" in src:
        # Find line with import random
        lines = src.split("\n")
        for i, line in enumerate(lines):
            if "import random" in line:
                lines.insert(i+1, "import random as _rand")
                break
        src = "\n".join(lines)
    else:
        # Add at very top after docstring
        lines = src.split("\n")
        # Find first non-comment, non-import line
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1
            elif line.strip() and not line.startswith("#") and not line.startswith('"""') and not line.startswith("'''"):
                break
        lines.insert(insert_at, "import random as _rand")
        src = "\n".join(lines)
    write("game/views.py", src)
    print("  ✓ _rand imported")
elif imported_rand:
    print("  ✓ _rand already imported")
else:
    print("  ✓ No _rand usage found")

# Also ensure `random` is imported (used in some places)
if "import random\n" not in src and "import random " not in src:
    # Check if random is used
    if "random." in src:
        lines = src.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1
            else:
                break
        lines.insert(insert_at, "import random")
        src = "\n".join(lines)
        write("game/views.py", src)
        print("  ✓ random imported")

# ============================================================
# 2) Create support migration folder + __init__.py
# ============================================================
print("\n[2/6] Ensuring support/migrations folder")
os.makedirs("support/migrations", exist_ok=True)
if not os.path.exists("support/migrations/__init__.py"):
    write("support/migrations/__init__.py", "")
    print("  ✓ __init__.py created")
else:
    print("  ✓ Already exists")

# ============================================================
# 3) Ensure support app is in INSTALLED_APPS
# ============================================================
print("\n[3/6] Checking INSTALLED_APPS")
settings = read("config/settings.py")
if '"support"' not in settings:
    print("  ⚠ support not in INSTALLED_APPS — adding")
    # Find the social entry or add at end
    if '"social",' in settings:
        settings = settings.replace('"social",', '"social",\n    "support",', 1)
    elif '"social"' in settings:
        settings = settings.replace('"social"', '"social",\n    "support"', 1)
    else:
        # Find INSTALLED_APPS end
        match = re.search(r'(INSTALLED_APPS\s*=\s*\[.*?)(\])', settings, re.DOTALL)
        if match:
            settings = settings[:match.end(1)] + '\n    "support",\n' + match.group(2) + settings[match.end(2):]
    write("config/settings.py", settings)
    print("  ✓ support added to INSTALLED_APPS")
else:
    print("  ✓ support already in INSTALLED_APPS")

# ============================================================
# 4) Check support/models.py exists and is valid
# ============================================================
print("\n[4/6] Checking support/models.py")
if not os.path.exists("support/models.py"):
    print("  ⚠ support/models.py missing — creating")
    write("support/models.py", '''# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models


class SupportTicket(models.Model):
    STATUS = [
        ("open", "باز"),
        ("in_progress", "در حال بررسی"),
        ("answered", "پاسخ داده شده"),
        ("closed", "بسته شده"),
    ]
    PRIORITY = [
        ("low", "کم"),
        ("normal", "معمولی"),
        ("high", "فوری"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="my_support_tickets",
    )
    subject = models.CharField(max_length=100)
    body = models.TextField(max_length=2000)
    category = models.CharField(max_length=20, default="general")
    status = models.CharField(max_length=15, choices=STATUS, default="open")
    priority = models.CharField(max_length=10, choices=PRIORITY, default="normal")
    admin_reply = models.TextField(blank=True, default="")
    replied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"#{self.id} - {self.subject[:30]}"

    def status_display(self):
        return dict(self.STATUS).get(self.status, self.status)
''')
else:
    print("  ✓ support/models.py exists")
    # Ensure related_name is unique
    s = read("support/models.py")
    if 'related_name="my_support_tickets"' not in s:
        s = s.replace('related_name="support_tickets"', 'related_name="my_support_tickets"')
        s = s.replace('related_name="user_support_tickets"', 'related_name="my_support_tickets"')
        write("support/models.py", s)
        print("  ✓ Fixed related_name")

# ============================================================
# 5) Run migrations for support app
# ============================================================
print("\n[5/6] Running support migrations")

# First: makemigrations for support
print("\n  $ makemigrations support")
r = subprocess.run(
    [sys.executable, "manage.py", "makemigrations", "support", "--noinput"],
    capture_output=True, text=True, timeout=60
)
if r.returncode == 0:
    out = r.stdout.strip()
    if "No changes" in out:
        print("    ✓ No changes (migration exists)")
    else:
        print(f"    ✓ Created: {out[:200]}")
else:
    print(f"    ⚠ ERR: {r.stderr[:400] if r.stderr else 'unknown'}")

# Check if migration file was created
mig_files = [f for f in os.listdir("support/migrations") if f.startswith("0") and f.endswith(".py")]
print(f"    Migration files: {mig_files}")

# Then: migrate
print("\n  $ migrate")
r = subprocess.run(
    [sys.executable, "manage.py", "migrate", "--noinput"],
    capture_output=True, text=True, timeout=60
)
if r.returncode == 0:
    out = r.stdout.strip()
    # Filter to just support
    support_lines = [l for l in out.split("\n") if "support" in l.lower()]
    if support_lines:
        for line in support_lines:
            print(f"    {line}")
    else:
        print("    ✓ Already migrated")
else:
    print(f"    ⚠ ERR: {r.stderr[:400] if r.stderr else 'unknown'}")

# ============================================================
# 6) Test all pages again
# ============================================================
print("\n[6/6] Testing all pages")
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

TEST = '''
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
import django
django.setup()
from django.test import Client
from accounts.models import User

# Cleanup
try:
    User.objects.filter(username__startswith="__diag_").delete()
except Exception as e:
    print("cleanup warn:", e)

u = User.objects.create_user(
    username="__diag_user__", password="x"*10, alias="تست",
    is_active=True, has_chosen_avatar=True, has_completed_registration=True,
)

c = Client()
c.force_login(u)
c.session["beta_unlocked"] = True
c.session.save()

tests = [
    ("/game/", "خانه"),
    ("/support/", "پشتیبانی"),
    ("/game/puzzle/", "معما"),
    ("/game/guess/", "۰ تا ۱۰۰"),
    ("/game/memory/", "حافظه"),
    ("/game/rooms/", "بازی‌ها"),
    ("/game/top-players/", "برتر"),
]

for url, name in tests:
    try:
        r = c.get(url, follow=False)
        mark = "✓" if r.status_code == 200 else f"⚠ {r.status_code}"
        print(f"  {mark} {url:22s} ({name})")
    except Exception as e:
        print(f"  ❌ {url:22s} ({name}) → {type(e).__name__}: {str(e)[:60]}")

u.delete()
'''

r = subprocess.run(
    [sys.executable, "-c", TEST],
    env={**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings"},
    capture_output=True, text=True, timeout=60
)
print(r.stdout)
if r.stderr and "Traceback" in r.stderr:
    print("\n  Traceback:")
    print(r.stderr[:600])

# ============================================================
# Final check
# ============================================================
print("\n[Final] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True, timeout=30)
if r.returncode == 0:
    print("  ✓ PASSED")
else:
    print(f"  ⚠ {r.stderr[:500] if r.stderr else r.stdout[:500]}")

print("\n" + "="*60)
print("✅ تموم شد")
print("="*60)
print("""
حالا سرور رو ران کن:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R
""")
