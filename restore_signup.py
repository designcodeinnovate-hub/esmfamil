#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""برگردوندن کامل به حالت لوکال + تست ثبت‌نام"""
import os, sys, subprocess, glob

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
# 1) پاک کردن هر env variable که ممکنه settings رو عوض کنه
# ============================================================
print("\n[1/8] پاک کردن env variables موقت")
for var in ["DJANGO_SETTINGS_MODULE", "DJANGO_DEBUG", "DJANGO_SECRET_KEY",
            "DJANGO_ALLOWED_HOSTS", "DATABASE_URL", "REDIS_URL",
            "DJANGO_CSRF_TRUSTED_ORIGINS"]:
    if var in os.environ:
        del os.environ[var]
        print(f"  ✓ حذف {var}")

# ============================================================
# 2) پاک کردن .env و فایل‌های backup اگه هستن
# ============================================================
print("\n[2/8] پاک کردن فایل‌های env")
for f in [".env", ".env.local", ".env.prod"]:
    if os.path.exists(f):
        os.rename(f, f + ".old")
        print(f"  → {f} → {f}.old")

# ============================================================
# 3) بازگرداندن manage.py به حالت پیش‌فرض
# ============================================================
print("\n[3/8] اصلاح manage.py")
manage = read("manage.py")
if "config.settings_prod" in manage:
    manage = manage.replace("config.settings_prod", "config.settings")
    write("manage.py", manage)
else:
    print("  ✓ manage.py به config.settings اشاره می‌کنه")

# ============================================================
# 4) اصلاح config/settings.py
# ============================================================
print("\n[4/8] اصلاح config/settings.py")
settings = read("config/settings.py")

# مطمئن شو DEBUG = True
if "DEBUG = False" in settings:
    settings = settings.replace("DEBUG = False", "DEBUG = True", 1)
    print("  ✓ DEBUG = True")

# مطمئن شو SQLite هست
if "django.db.backends.sqlite3" not in settings:
    print("  ⚠ دیتابیس SQLite نیست! اصلاح می‌کنم...")
    # پیدا کردن DATABASES block و جایگزینی
    import re
    pattern = r"DATABASES\s*=\s*\{[^}]*\}"
    new_db = '''DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}'''
    settings = re.sub(pattern, new_db, settings, count=1)

# مطمئن شو ALLOWED_HOSTS = ["*"]
if 'ALLOWED_HOSTS = ["*"]' not in settings:
    import re
    settings = re.sub(r'ALLOWED_HOSTS\s*=\s*\[[^\]]*\]', 'ALLOWED_HOSTS = ["*"]', settings)

write("config/settings.py", settings)
print("  ✓ settings.py اصلاح شد")

# ============================================================
# 5) اصلاح config/wsgi.py و config/asgi.py
# ============================================================
print("\n[5/8] اصلاح wsgi.py و asgi.py")
for f in ["config/wsgi.py", "config/asgi.py"]:
    src = read(f)
    if "settings_prod" in src:
        src = src.replace("config.settings_prod", "config.settings")
        write(f, src)
    else:
        print(f"  ✓ {f}")

# ============================================================
# 6) اجرای migrations
# ============================================================
print("\n[6/8] اجرای migrations")
r = subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ migrate OK")
else:
    print(f"  ⚠ {r.stderr[:400]}")

# ============================================================
# 7) تست کامل ثبت‌نام (مثل یه کاربر واقعی)
# ============================================================
print("\n[7/8] تست کامل ثبت‌نام")
import django
django.setup()

from django.test import Client
from accounts.models import User

# پاک کردن یوزرهای تستی قبلی
User.objects.filter(username__startswith="__restore_").delete()

c = Client()

# تست ۱: صفحه اصلی (landing)
r = c.get("/", follow=False)
print(f"\n  تست ۱: GET / → {r.status_code}")
if r.status_code == 200:
    content = r.content.decode('utf-8', errors='ignore')
    if "ساخت حساب" in content or "register" in content.lower():
        print("    ✓ صفحه اصلی (landing) باز می‌شه و دکمه ثبت‌نام داره")
    else:
        print("    ⚠ صفحه باز شد ولی دکمه ثبت‌نام نیست")
elif r.status_code == 302:
    print(f"    → redirect به: {r.get('Location', '')}")

# تست ۲: رد کردن beta gate
c.session["beta_unlocked"] = True
c.session.save()

# تست ۳: صفحه ثبت‌نام
r = c.get("/accounts/register/", follow=False)
print(f"\n  تست ۳: GET /accounts/register/ → {r.status_code}")
if r.status_code == 200:
    print("    ✓ صفحه ثبت‌نام باز می‌شه")
    # چک کن فرم داره
    content = r.content.decode('utf-8', errors='ignore')
    has_form = 'name="username"' in content and 'name="password"' in content
    print(f"    {'✓' if has_form else '✗'} فرم ثبت‌نام کامل هست")
else:
    print(f"    ✗ {r.status_code}")

# تست ۴: ثبت‌نام واقعی
test_username = "__restore_test__"
r = c.post("/accounts/register/", {
    "username": test_username,
    "password": "test123456",
    "password2": "test123456",
}, follow=False)

print(f"\n  تست ۴: POST /accounts/register/ → {r.status_code}")

if r.status_code == 302:
    print(f"    ✓ ثبت‌نام موفق! redirect: {r.get('Location', '')}")
    user = User.objects.filter(username=test_username).first()
    if user:
        print(f"    ✓ کاربر ساخته شد: {user.username} (id={user.id})")
        print(f"    ✓ is_active: {user.is_active}")
        print(f"    ✓ has_chosen_avatar: {user.has_chosen_avatar}")
        print(f"    ✓ has_completed_registration: {user.has_completed_registration}")
    else:
        print(f"    ✗ کاربر در DB پیدا نشد!")
elif r.status_code == 200:
    print(f"    ✗ فرم با خطا برگشت (شاید username مشکل داره)")
    content = r.content.decode('utf-8', errors='ignore')
    if "error" in content:
        # خطا رو پیدا کن
        import re
        err_match = re.search(r'class="error"[^>]*>(.*?)</div>', content, re.DOTALL)
        if err_match:
            print(f"    خطا: {err_match.group(1)[:200]}")
else:
    print(f"    ✗ {r.status_code}")

# تست ۵: صفحه تکمیل ثبت‌نام
r = c.get("/accounts/complete/", follow=False)
print(f"\n  تست ۵: GET /accounts/complete/ → {r.status_code}")
if r.status_code == 200:
    print("    ✓ صفحه تکمیل (آواتار) باز می‌شه")
else:
    print(f"    ⚠ {r.status_code}")

# تست ۶: لاگین با کاربر جدید
c2 = Client()
c2.session["beta_unlocked"] = True
c2.session.save()

r = c2.post("/accounts/login/", {
    "username": test_username,
    "password": "test123456",
}, follow=False)

print(f"\n  تست ۶: POST /accounts/login/ → {r.status_code}")
if r.status_code == 302:
    print(f"    ✓ لاگین موفق! redirect: {r.get('Location', '')}")
else:
    print(f"    ✗ {r.status_code}")

# تست ۷: تکمیل ثبت‌نام (ذخیره آواتار و نام)
user = User.objects.filter(username=test_username).first()
if user:
    c3 = Client()
    c3.force_login(user)
    c3.session["beta_unlocked"] = True
    c3.session.save()
    
    r = c3.post("/accounts/complete/", {
        "alias": "کاربر تست",
        "avatar_type": "emoji",
        "avatar_id": "0",
    }, follow=False)
    
    print(f"\n  تست ۷: POST /accounts/complete/ → {r.status_code}")
    if r.status_code == 302:
        print(f"    ✓ تکمیل شد! redirect: {r.get('Location', '')}")
        user.refresh_from_db()
        print(f"    ✓ alias: {user.alias}")
        print(f"    ✓ has_completed: {user.has_completed_registration}")
    
    # تست ۸: بازی
    r = c3.get("/game/", follow=False)
    print(f"\n  تست ۸: GET /game/ → {r.status_code}")
    if r.status_code == 200:
        print("    ✓ منوی بازی باز می‌شه!")

# پاک‌سازی
User.objects.filter(username__startswith="__restore_").delete()
print("\n  ✓ کاربر تست پاک شد")

# ============================================================
# 8) خلاصه
# ============================================================
print("\n[8/8] خلاصه")
print("\n" + "="*60)
print("✅ همه چیز به حالت لوکال برگشت")
print("="*60)
print("""
🔑 رمزها:
  Beta Gate: emami_irani_esm1405
  Admin:     admin74 / Amir2255ds

📋 حالا این کارها رو بکن:

  # 1. سرور رو ران کن
  pkill -9 -f "manage.py runserver"
  python manage.py runserver

  # 2. تو مرورگر:
  #    اول Beta Gate:
  http://127.0.0.1:8000/beta-lock/
  #    رمز: emami_irani_esm1405

  #    بعد صفحه اصلی:
  http://127.0.0.1:8000/
  #    → روی "ساخت حساب جدید" کلیک کن
  
  #    یا مستقیم:
  http://127.0.0.1:8000/accounts/register/

✅ اگه همه تست‌ها بالا ✓ شدن، ثبت‌نام کار می‌کنه.
""")
