#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
# 1) حذف Beta Gate از middleware
# ============================================================
print("\n[1/5] حذف Beta Gate")
settings = read("config/settings.py")

# حذف از MIDDLEWARE
if "config.beta_gate.BetaGateMiddleware" in settings:
    settings = re.sub(
        r'\s*"config\.beta_gate\.BetaGateMiddleware",?\s*\n',
        '\n',
        settings
    )
    print("  ✓ از MIDDLEWARE حذف شد")
else:
    print("  ✓ قبلاً نبود")

# اطمینان از DEBUG
if "DEBUG = False" in settings:
    settings = settings.replace("DEBUG = False", "DEBUG = True")
    print("  ✓ DEBUG = True")

write("config/settings.py", settings)

# ============================================================
# 2) حذف beta از urls.py
# ============================================================
print("\n[2/5] حذف /beta-lock از urls.py")
urls = read("config/urls.py")

# حذف import
urls = re.sub(r'from config\.beta_views import[^\n]*\n', '', urls)

# حذف مسیرها
urls = re.sub(r'\s*path\("beta-lock/"[^\n]*\n', '\n', urls)
urls = re.sub(r'\s*path\("beta-logout/"[^\n]*\n', '\n', urls)

write("config/urls.py", urls)

# ============================================================
# 3) بازگرداندن نوار پایین با پروفایل
# ============================================================
print("\n[3/5] نوار پایین با پروفایل")

# پیدا کردن base.html
for tpl_path in ["templates/base.html"]:
    if not os.path.exists(tpl_path):
        continue
    base = read(tpl_path)

    # پیدا کردن nav
    nav_pattern = re.compile(r'<nav class="bottom-nav">.*?</nav>', re.DOTALL)
    m = nav_pattern.search(base)

    if m:
        new_nav = '''<nav class="bottom-nav">
  <a href="/game/" class="nav-link {% if active == 'home' %}active{% endif %}">
    <span class="nav-icon">🏠</span>
    <span>خانه</span>
  </a>
  <a href="/game/rooms/" class="nav-link {% if active == 'games' %}active{% endif %}">
    <span class="nav-icon">🎮</span>
    <span>بازی‌ها</span>
  </a>
  <a href="/game/rooms/manage/" class="nav-link {% if active == 'rooms' %}active{% endif %}">
    <span class="nav-icon">🚪</span>
    <span>اتاق‌ها</span>
  </a>
  <a href="/social/" class="nav-link {% if active == 'friends' %}active{% endif %}">
    <span class="nav-icon">👥</span>
    <span>دوستان</span>
  </a>
  <a href="/accounts/profile/" class="nav-link {% if active == 'profile' %}active{% endif %}">
    <span class="nav-icon">👤</span>
    <span>پروفایل</span>
  </a>
</nav>'''
        base = base[:m.start()] + new_nav + base[m.end():]
        write(tpl_path, base)
        print("  ✓ نوار پایین با ۵ آیتم + پروفایل")

# ============================================================
# 4) تست کامل
# ============================================================
print("\n[4/5] تست")
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

TEST = '''
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

import django
django.setup()

from django.test import Client
from accounts.models import User

User.objects.filter(username__startswith="__z_").delete()

c = Client()

print("=" * 55)
print("تست")
print("=" * 55)

pages = [
    ("/", "صفحه اصلی"),
    ("/accounts/register/", "ثبت‌نام"),
    ("/accounts/login/", "ورود"),
]

for url, name in pages:
    try:
        r = c.get(url, follow=False)
        st = r.status_code
        note = ""
        if st == 302:
            note = f" -> {r.get('Location', '')}"
        print(f"  {url:28s} {name:15s} {st}{note}")
    except Exception as e:
        print(f"  {url:28s} {name:15s} ERR {type(e).__name__}")

# ثبت‌نام
print()
r = c.post("/accounts/register/", {
    "username": "__z_test__",
    "password": "test123456",
    "password2": "test123456",
}, follow=False)

print(f"ثبت‌نام → {r.status_code}")
if r.status_code == 302:
    print(f"  ✓ redirect: {r.get('Location', '')}")
    u = User.objects.filter(username="__z_test__").first()
    if u:
        print(f"  ✓ user: {u.username} (id={u.id})")
elif r.status_code == 200:
    content = r.content.decode("utf-8", errors="ignore")
    if "error" in content.lower():
        import re
        m = re.search(r'class="error"[^>]*>(.*?)</div>', content, re.DOTALL)
        if m:
            print(f"  ✗ خطا: {m.group(1)[:200]}")

# تکمیل + پروفایل
u = User.objects.filter(username="__z_test__").first()
if u:
    c2 = Client()
    c2.force_login(u)
    r = c2.get("/accounts/profile/", follow=False)
    print(f"\\nپروفایل → {r.status_code}")

    r = c2.post("/accounts/complete/", {
        "alias": "کاربر تست",
        "avatar_type": "emoji",
        "avatar_id": "0",
    }, follow=False)
    print(f"تکمیل → {r.status_code}")
    if r.status_code == 302:
        print(f"  ✓ redirect: {r.get('Location', '')}")

    r = c2.get("/game/", follow=False)
    print(f"بازی → {r.status_code}")

User.objects.filter(username__startswith="__z_").delete()
print("\\n✓ پاک‌سازی")
'''

r = subprocess.run(
    [sys.executable, "-c", TEST],
    env={**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings"},
    capture_output=True, text=True
)
print(r.stdout)
if r.stderr and "Traceback" in r.stderr:
    print("STDERR:", r.stderr[:600])

# ============================================================
# 5) migrate
# ============================================================
print("\n[5/5] migrate")
r = subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ OK")
else:
    print(f"  ⚠ {r.stderr[:300]}")

print("\n" + "="*60)
print("✅ تمام")
print("="*60)
print("""
حالا:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver

مرورگر:
  http://127.0.0.1:8000/                ← مستقیم صفحه اصلی (بدون قفل)
  http://127.0.0.1:8000/accounts/register/   ← ثبت‌نام
  http://127.0.0.1:8000/accounts/profile/    ← پروفایل
""")
