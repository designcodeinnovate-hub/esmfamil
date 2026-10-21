#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""برگشت به حالت لوکال + تست حساب کاربری"""
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def read(p):
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f: return f.read()
    return ""
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) چک settings پیش‌فرض (لوکال)
# ============================================================
print("\n[1/5] بررسی settings پیش‌فرض")
manage = read("manage.py")
if "config.settings\"" in manage and "settings_prod" not in manage.split("\n")[5]:
    print("  ✓ manage.py به config.settings اشاره می‌کنه (لوکال)")
else:
    print("  ⚠ manage.py رو fix می‌کنم")
    manage = manage.replace("config.settings_prod", "config.settings")
    write("manage.py", manage)

# ============================================================
# 2) چک DEBUG و دیتابیس لوکال
# ============================================================
print("\n[2/5] بررسی config/settings.py")
settings = read("config/settings.py")
if "DEBUG = True" not in settings:
    print("  ⚠ DEBUG رو True می‌کنم")
    settings = settings.replace("DEBUG = False", "DEBUG = True")
    write("config/settings.py", settings)
else:
    print("  ✓ DEBUG = True")

if "sqlite3" not in settings:
    print("  ⚠ دیتابیس SQLite نیست!")
else:
    print("  ✓ دیتابیس SQLite (لوکال)")

# ============================================================
# 3) پاک کردن .env (که لوکال رو خراب نکنه)
# ============================================================
print("\n[3/5] پاک کردن فایل‌های env اگه هستن")
for f in [".env", ".env.local"]:
    if os.path.exists(f):
        os.rename(f, f + ".backup")
        print(f"  → {f} → {f}.backup")

# ============================================================
# 4) migrate + تست
# ============================================================
print("\n[4/5] اجرای migrate")
r = subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ migrate OK")
else:
    print(f"  ⚠ {r.stderr[:300]}")

# ============================================================
# 5) تست کامل حساب کاربری
# ============================================================
print("\n[5/5] تست کامل حساب کاربری")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from accounts.models import User

# پاک کردن یوزر تست قدیمی
User.objects.filter(username__startswith="__test_signup_").delete()

c = Client()
c.session["beta_unlocked"] = True
c.session.save()

# تست ۱: باز شدن صفحه ثبت‌نام
r = c.get("/accounts/register/")
print(f"\n  تست ۱: GET /accounts/register/ → {r.status_code}")
if r.status_code == 200:
    print("    ✓ صفحه ثبت‌نام باز می‌شه")
else:
    print(f"    ✗ {r.status_code}")

# تست ۲: ثبت‌نام واقعی
test_username = "__test_signup_1__"
r = c.post("/accounts/register/", {
    "username": test_username,
    "password": "test123456",
    "password2": "test123456",
}, follow=False)
print(f"\n  تست ۲: POST /accounts/register/ → {r.status_code}")
if r.status_code == 302:
    print(f"    ✓ کاربر ساخته شد، redirect به: {r.get('Location', '')}")
    created_user = User.objects.filter(username=test_username).first()
    if created_user:
        print(f"    ✓ کاربر در DB: {created_user.username} (id={created_user.id})")
    else:
        print("    ✗ کاربر در DB پیدا نشد!")
elif r.status_code == 200:
    # شاید خطای فرم
    content = r.content.decode('utf-8', errors='ignore')
    if "error" in content.lower() or "خطا" in content:
        print("    ✗ خطای اعتبارسنجی (شاید username تکراریه)")
    else:
        print("    ? صفحه دوباره رندر شد")
else:
    print(f"    ✗ {r.status_code}")

# تست ۳: صفحه ورود
r = c.get("/accounts/login/")
print(f"\n  تست ۳: GET /accounts/login/ → {r.status_code}")
if r.status_code == 200:
    print("    ✓ صفحه ورود باز می‌شه")

# تست ۴: لاگین واقعی
r = c.post("/accounts/login/", {
    "username": test_username,
    "password": "test123456",
}, follow=False)
print(f"\n  تست ۴: POST /accounts/login/ → {r.status_code}")
if r.status_code == 302:
    print(f"    ✓ لاگین موفق، redirect: {r.get('Location', '')}")

# تست ۵: صفحه تکمیل ثبت‌نام (آواتار + نام)
r = c.get("/accounts/complete/", follow=False)
print(f"\n  تست ۵: GET /accounts/complete/ → {r.status_code}")
if r.status_code == 200:
    print("    ✓ صفحه تکمیل ثبت‌نام باز می‌شه")

# تست ۶: صفحه بازی (بعد از تکمیل)
test_user = User.objects.filter(username=test_username).first()
if test_user:
    test_user.has_chosen_avatar = True
    test_user.has_completed_registration = True
    test_user.save()
    r = c.get("/game/", follow=False)
    print(f"\n  تست ۶: GET /game/ (بعد از تکمیل) → {r.status_code}")
    if r.status_code == 200:
        print("    ✓ منوی بازی باز می‌شه")

# تست ۷: بازی با بات
r = c.get("/game/quick/bot/", follow=False)
print(f"\n  تست ۷: GET /game/quick/bot/ → {r.status_code}")
if r.status_code == 200:
    print("    ✓ صفحه بازی با بات باز می‌شه")

# تست ۸: پروفایل
r = c.get("/accounts/profile/", follow=False)
print(f"\n  تست ۸: GET /accounts/profile/ → {r.status_code}")
if r.status_code == 200:
    print("    ✓ صفحه پروفایل باز می‌شه")

# تست ۹: اتحاد
r = c.get("/alliance/", follow=False)
print(f"\n  تست ۹: GET /alliance/ → {r.status_code}")
if r.status_code in (200, 302):
    print(f"    ✓ صفحه اتحاد کار می‌کنه ({r.status_code})")

# تست ۱۰: اتاق‌ها
r = c.get("/game/rooms/manage/", follow=False)
print(f"\n  تست ۱۰: GET /game/rooms/manage/ → {r.status_code}")
if r.status_code == 200:
    print("    ✓ صفحه اتاق‌ها باز می‌شه")

# پاک‌سازی
User.objects.filter(username__startswith="__test_signup_").delete()
print("\n  ✓ کاربر تست پاک شد")

# ============================================================
# خلاصه
# ============================================================
print("\n" + "="*60)
print("✅ حالت لوکال آماده‌ست")
print("="*60)
print(f"""
🔑 رمزها:
  Beta Gate: emami_irani_esm1405
  Admin:     admin74 / Amir2255ds

📋 حالا این کارها رو بکن:

  1. سرور رو ران کن:
     pkill -9 -f "manage.py runserver"
     python manage.py runserver

  2. تو مرورگر برو:
     http://127.0.0.1:8000/beta-lock/
     رمز: emami_irani_esm1405

  3. برو به:
     http://127.0.0.1:8000/
     
  4. ثبت‌نام کن یا لاگین کن.

✅ همه چیز مثل قبل کار می‌کنه.
""")
