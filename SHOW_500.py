#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Show EXACTLY what the 500 error is"""
import os, sys, traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

import django
django.setup()

from django.test import Client
from accounts.models import User

print("\n" + "="*70)
print("🔍 DIAGNOSTIC — What's the 500 error?")
print("="*70)

# Clean test user
User.objects.filter(username__startswith="__diag500_").delete()
u = User.objects.create_user(
    username="__diag500_u", password="x"*10, alias="تست",
    is_active=True, has_chosen_avatar=True, has_completed_registration=True,
    coins=200,
)

c = Client()
c.force_login(u)
c.session["beta_unlocked"] = True
c.session.save()

urls = [
    ("/game/", "خانه"),
    ("/support/", "پشتیبانی"),
    ("/game/puzzle/", "بازی معما"),
    ("/game/guess/", "بازی ۰-۱۰۰"),
    ("/game/memory/", "بازی حافظه"),
    ("/game/rooms/", "بازی‌ها"),
    ("/panel-admin/support/", "پنل ادمین پشتیبانی"),
]

# Enable DEBUG to see real errors
from django.conf import settings
original_debug = settings.DEBUG
settings.DEBUG = True

for url, name in urls:
    print(f"\n{'='*70}")
    print(f"📄 {url}  ({name})")
    print('='*70)
    try:
        r = c.get(url, follow=False)
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 200:
            print(f"   ✅ OK")
        elif r.status_code == 500:
            print(f"   ❌ 500 ERROR")
            content = r.content.decode('utf-8', errors='ignore')
            
            # Extract traceback from error page
            import re
            # Find exception value
            exc_match = re.search(r'<pre class="exception_value">(.*?)</pre>', content, re.DOTALL)
            if exc_match:
                err = exc_match.group(1).strip()
                # Unescape HTML
                err = err.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#x27;', "'")
                print(f"\n   🚨 EXCEPTION:")
                print(f"   {err[:500]}")
            
            # Find exception type
            type_match = re.search(r'<title>(.*?)</title>', content)
            if type_match:
                print(f"\n   📋 Type: {type_match.group(1).strip()[:200]}")
            
            # Find last traceback frame in project code
            frames = re.findall(r'File &quot;([^&]+)&quot;, line (\d+), in (\w+)', content)
            if frames:
                print(f"\n   📍 Traceback frames:")
                for f in frames[-5:]:
                    if 'esmfamil' in f[0] or 'venv' not in f[0]:
                        print(f"      {f[0]}:{f[1]} in {f[2]}")
            
            # Get more details
            tb_match = re.search(r'<h2>(.*?)</h2>', content)
            if tb_match:
                title = re.sub('<[^>]+>', '', tb_match.group(1))
                print(f"\n   📝 Title: {title[:200]}")
        else:
            print(f"   → {r.get('Location', '?')[:100]}")
    except Exception as e:
        print(f"   ❌ EXCEPTION:")
        print(f"   {type(e).__name__}: {str(e)[:300]}")
        print(f"\n   Full traceback:")
        traceback.print_exc()

settings.DEBUG = original_debug
u.delete()

# Also test with real error log
print("\n" + "="*70)
print("🔍 Checking Django error log")
print("="*70)

# Try importing key modules to catch import errors
print("\n→ Testing imports:")

modules_to_test = [
    "support",
    "support.models",
    "support.views",
    "support.urls",
    "game.views",
    "game.urls",
    "accounts.admin_views",
    "accounts.admin_urls",
]

for mod in modules_to_test:
    try:
        __import__(mod)
        print(f"  ✅ {mod}")
    except Exception as e:
        print(f"  ❌ {mod}")
        print(f"     {type(e).__name__}: {str(e)[:300]}")

# Check urls
print("\n→ Testing URL resolution:")
from django.urls import reverse, resolve

urls_to_test = [
    ("support:home", {}),
    ("game:puzzle", {}),
    ("game:guess", {}),
    ("game:memory", {}),
]

for name, kwargs in urls_to_test:
    try:
        path = reverse(name, kwargs=kwargs)
        print(f"  ✅ {name} → {path}")
    except Exception as e:
        print(f"  ❌ {name}: {type(e).__name__}: {str(e)[:200]}")

print("\n" + "="*70)
print("DONE")
print("="*70)
print("""
اگر بالا خطا دیدی، متن کاملش رو کپی کن و بفرست.
اگر همه ✅ بود، ولی تو مرورگر ۵۰۰ می‌بینی، یعنی cache مرورگر.
""")
