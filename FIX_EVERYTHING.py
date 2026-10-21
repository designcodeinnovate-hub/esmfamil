#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""برگرداندن کامل + روشن کردن سرور"""
import os, sys, subprocess, re

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def log(msg): print(msg, flush=True)
def read(p):
    try:
        with open(p, "r", encoding="utf-8") as f: return f.read()
    except: return ""
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)

log("\n" + "="*60)
log("🔧 بازگرداندن به حالت لوکال")
log("="*60)

# ============================================================
# 1) پاک کردن env variables
# ============================================================
log("\n[1/7] پاک کردن env variables")
for var in list(os.environ.keys()):
    if var.startswith("DJANGO_") or var in ("DATABASE_URL", "REDIS_URL"):
        del os.environ[var]
        log(f"  ✓ حذف {var}")

# ============================================================
# 2) manage.py — force config.settings
# ============================================================
log("\n[2/7] manage.py")
manage = read("manage.py")
if "settings_prod" in manage:
    manage = manage.replace("config.settings_prod", "config.settings")
    write("manage.py", manage)
    log("  ✓ اصلاح شد")
else:
    log("  ✓ درست بود")

# ============================================================
# 3) wsgi.py + asgi.py — force config.settings
# ============================================================
log("\n[3/7] wsgi.py + asgi.py")
for f in ["config/wsgi.py", "config/asgi.py"]:
    src = read(f)
    if "settings_prod" in src:
        src = src.replace("config.settings_prod", "config.settings")
        write(f, src)
        log(f"  ✓ {f} اصلاح شد")
    else:
        log(f"  ✓ {f} درست بود")

# ============================================================
# 4) config/settings.py — DEBUG, DB, ALLOWED_HOSTS
# ============================================================
log("\n[4/7] config/settings.py")
settings = read("config/settings.py")

# DEBUG
if "DEBUG = False" in settings:
    settings = settings.replace("DEBUG = False", "DEBUG = True")
    log("  ✓ DEBUG = True")
else:
    log("  ✓ DEBUG درست بود")

# DATABASES
if "django.db.backends.sqlite3" not in settings:
    settings = re.sub(
        r"DATABASES\s*=\s*\{.*?\n\}",
        'DATABASES = {\n    "default": {\n        "ENGINE": "django.db.backends.sqlite3",\n        "NAME": BASE_DIR / "db.sqlite3",\n    }\n}',
        settings, count=1, flags=re.DOTALL
    )
    log("  ✓ DATABASES = SQLite")

# ALLOWED_HOSTS
if 'ALLOWED_HOSTS = ["*"]' not in settings:
    settings = re.sub(r'ALLOWED_HOSTS\s*=\s*\[[^\]]*\]', 'ALLOWED_HOSTS = ["*"]', settings)
    log("  ✓ ALLOWED_HOSTS = ['*']")

write("config/settings.py", settings)
log("  ✓ ذخیره شد")

# ============================================================
# 5) .env رو کنار بذار
# ============================================================
log("\n[5/7] .env files")
for f in [".env", ".env.local", ".env.prod"]:
    if os.path.exists(f):
        os.rename(f, f + ".off")
        log(f"  → {f} کنار گذاشته شد")
log("  ✓ تمیز")

# ============================================================
# 6) migrate
# ============================================================
log("\n[6/7] Migrate")
r = subprocess.run(
    [sys.executable, "manage.py", "migrate", "--noinput"],
    capture_output=True, text=True
)
if r.returncode == 0:
    log("  ✓ OK")
else:
    log(f"  ⚠ {r.stderr[:300]}")

# ============================================================
# 7) تست کامل با HTTP Client
# ============================================================
log("\n[7/7] تست کامل")
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

# اجرای تست در subprocess جداگانه (که django.setup() درست کار کنه)
TEST_CODE = '''
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

# پاک کردن تستی‌های قبلی
User.objects.filter(username__startswith="__t_").delete()

c = Client()
c.session["beta_unlocked"] = True
c.session.save()

print("=" * 55)
print("تست صفحات مهم")
print("=" * 55)

tests = [
    ("/", "صفحه اصلی (landing)"),
    ("/accounts/register/", "صفحه ثبت‌نام"),
    ("/accounts/login/", "صفحه ورود"),
    ("/accounts/profile/", "پروفایل"),
    ("/accounts/complete/", "تکمیل ثبت‌نام"),
    ("/game/", "منوی بازی"),
    ("/game/rooms/manage/", "اتاق‌ها"),
    ("/alliance/", "اتحاد"),
]

for url, name in tests:
    try:
        r = c.get(url, follow=False)
        status = r.status_code
        ok = "OK" if status == 200 else f"-> {status}"
        print(f"  {url:30s} {name:25s} {ok}")
    except Exception as e:
        print(f"  {url:30s} {name:25s} ERR: {type(e).__name__}: {str(e)[:80]}")

print()
print("=" * 55)
print("تست ثبت‌نام کامل")
print("=" * 55)

# ثبت‌نام
r = c.post("/accounts/register/", {
    "username": "__t_signup__",
    "password": "test123456",
    "password2": "test123456",
}, follow=False)

if r.status_code == 302:
    loc = r.get("Location", "")
    print(f"  ثبت‌نام: ✓ redirect → {loc}")
    u = User.objects.filter(username="__t_signup__").first()
    if u:
        print(f"  کاربر: {u.username} (id={u.id})")
        print(f"  is_active: {u.is_active}")
    else:
        print(f"  ❌ کاربر در DB نیست")
elif r.status_code == 200:
    content = r.content.decode("utf-8", errors="ignore")
    if "error" in content or "خطا" in content:
        print(f"  ثبت‌نام: ✗ خطای فرم")
    else:
        print(f"  ثبت‌نام: ? رندر مجدد (200)")
else:
    print(f"  ثبت‌نام: ✗ {r.status_code}")

# لاگین
c2 = Client()
c2.session["beta_unlocked"] = True
c2.session.save()
r = c2.post("/accounts/login/", {
    "username": "__t_signup__",
    "password": "test123456",
}, follow=False)

if r.status_code == 302:
    print(f"  لاگین: ✓ redirect → {r.get('Location', '')}")
else:
    print(f"  لاگین: ✗ {r.status_code}")

# تکمیل ثبت‌نام
u = User.objects.filter(username="__t_signup__").first()
if u:
    c3 = Client()
    c3.force_login(u)
    c3.session["beta_unlocked"] = True
    c3.session.save()
    r = c3.post("/accounts/complete/", {
        "alias": "کاربر تست",
        "avatar_type": "emoji",
        "avatar_id": "0",
    }, follow=False)
    if r.status_code == 302:
        print(f"  تکمیل: ✓ redirect → {r.get('Location', '')}")
    else:
        print(f"  تکمیل: ✗ {r.status_code}")

    # بازی
    r = c3.get("/game/", follow=False)
    print(f"  منوی بازی: {'✓' if r.status_code == 200 else f'✗ {r.status_code}'}")

    # پروفایل
    r = c3.get("/accounts/profile/", follow=False)
    print(f"  پروفایل: {'✓' if r.status_code == 200 else f'✗ {r.status_code}'}")

# پاک‌سازی
User.objects.filter(username__startswith="__t_").delete()
print("\\n  ✓ کاربر تست پاک شد")
'''

r = subprocess.run(
    [sys.executable, "-c", TEST_CODE],
    env={**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings"},
    capture_output=True, text=True
)
print(r.stdout)
if r.stderr and "Traceback" in r.stderr:
    log("  خطای تست:")
    log(r.stderr[:600])

# ============================================================
# خلاصه
# ============================================================
log("")
log("="*60)
log("✅ کارت تمومه")
log("="*60)
log("""
حالا سرور رو روشن کن (یا اگه روشنه، Ctrl+C و دوباره):

    pkill -9 -f "manage.py runserver"
    python manage.py runserver

بعد تو مرورگر (به همین ترتیب):

  ۱. http://127.0.0.1:8000/beta-lock/
     رمز: emami_irani_esm1405

  ۲. http://127.0.0.1:8000/
     روی «ساخت حساب جدید» کلیک کن

  ۳. یا مستقیم:
     http://127.0.0.1:8000/accounts/register/

🔑 رمزها:
  Beta Gate: emami_irani_esm1405
  Admin:     admin74 / Amir2255ds
""")
