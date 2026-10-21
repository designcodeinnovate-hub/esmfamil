#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

# ============================================================
# 1) manage.py → config.settings
# ============================================================
print("[1] manage.py")
if os.path.exists("manage.py"):
    with open("manage.py", "r") as f: src = f.read()
    if "config.settings_prod" in src:
        src = src.replace("config.settings_prod", "config.settings")
        with open("manage.py", "w") as f: f.write(src)
        print("  ✓ به config.settings برگشت")
    else:
        print("  ✓ درست بود")

# ============================================================
# 2) settings.py → DEBUG=True + SQLite
# ============================================================
print("[2] settings.py")
with open("config/settings.py", "r") as f: src = f.read()

if "DEBUG = False" in src:
    src = src.replace("DEBUG = False", "DEBUG = True")
    print("  ✓ DEBUG = True")

if "django.db.backends.sqlite3" not in src:
    import re
    src = re.sub(
        r"DATABASES\s*=\s*\{[^}]*\}",
        'DATABASES = {\n    "default": {\n        "ENGINE": "django.db.backends.sqlite3",\n        "NAME": BASE_DIR / "db.sqlite3",\n    }\n}',
        src, count=1
    )
    print("  ✓ SQLite تنظیم شد")

if 'ALLOWED_HOSTS = ["*"]' not in src:
    import re
    src = re.sub(r'ALLOWED_HOSTS\s*=\s*\[[^\]]*\]', 'ALLOWED_HOSTS = ["*"]', src)

with open("config/settings.py", "w") as f: f.write(src)
print("  ✓ ذخیره شد")

# ============================================================
# 3) .env رو کنار بذار
# ============================================================
print("[3] .env")
for f in [".env", ".env.local"]:
    if os.path.exists(f):
        os.rename(f, f + ".off")
        print(f"  → {f} کنار گذاشته شد")
print("  ✓ تمیز")

# ============================================================
# 4) migrate
# ============================================================
print("[4] migrate")
r = subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"],
                   capture_output=True, text=True)
print("  ✓ OK" if r.returncode == 0 else f"  ⚠ {r.stderr[:200]}")

# ============================================================
# 5) تست صفحات مهم
# ============================================================
print("[5] تست صفحات")
env = os.environ.copy()
env["DJANGO_SETTINGS_MODULE"] = "config.settings"

TEST = '''
import os, django
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
django.setup()

from django.test import Client
from accounts.models import User

# پاک کردن تستی‌ها
User.objects.filter(username__startswith="__chk_").delete()

c = Client()
c.session["beta_unlocked"] = True
c.session.save()

pages = [
    ("/", "صفحه اصلی"),
    ("/accounts/register/", "ثبت‌نام"),
    ("/accounts/login/", "ورود"),
    ("/accounts/profile/", "پروفایل (قبل لاگین)"),
]

for url, name in pages:
    try:
        r = c.get(url, follow=False)
        icon = "OK" if r.status_code == 200 else f"-> {r.status_code}"
        print(f"  {url:30s} {name:25s} {icon}")
    except Exception as e:
        print(f"  {url:30s} {name:25s} ERR: {type(e).__name__}")
'''

r = subprocess.run([sys.executable, "-c", TEST], env=env, capture_output=True, text=True)
print(r.stdout)
if r.stderr and "Traceback" in r.stderr:
    print("  خطا:", r.stderr[:400])

# ============================================================
# 6) خلاصه
# ============================================================
print("""
============================================================
✅ همه چیز به حالت قبل برگشت
============================================================

حالا این کارها رو بکن:

  1. سرور رو خاموش کن:
     pkill -9 -f "manage.py runserver"

  2. سرور رو روشن کن:
     python manage.py runserver

  3. مرورگر:
     http://127.0.0.1:8000/beta-lock/
     رمز: emami_irani_esm1405

  4. بعد:
     http://127.0.0.1:8000/

  روی «ساخت حساب جدید» کلیک کن.
  یا مستقیم: http://127.0.0.1:8000/accounts/register/

============================================================
""")
