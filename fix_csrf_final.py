#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final fix: hardcode CSRF and proxy settings in base settings.py."""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

p = "config/settings.py"
src = read(p)

# Block to add/ensure at the end of the file
FINAL_BLOCK = '''

# ============================================================
# FINAL PRODUCTION FIX (always applied)
# ============================================================

# 1. Trust Runflare domain for CSRF (critical!)
CSRF_TRUSTED_ORIGINS = [
    "https://esmfamil-c78-esmfamil-db.runflare.cloud",
    "https://esmfamil.com",
    "https://www.esmfamil.com",
]

# 2. Tell Django it is behind an HTTPS proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# 3. Ensure cookies work correctly in this environment
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
'''

# Only add if not already present
if "FINAL PRODUCTION FIX" not in src:
    src = src.rstrip() + FINAL_BLOCK + "\n"
    write(p, src)
    print("  ✓ Added FINAL PRODUCTION FIX block to settings.py")
else:
    print("  ✓ FINAL PRODUCTION FIX block already exists")

# Also ensure DEBUG is False for production safety
if re.search(r'^DEBUG\s*=\s*True', src, re.MULTILINE):
    src = re.sub(r'^DEBUG\s*=\s*True', 'DEBUG = False', src, flags=re.MULTILINE)
    write(p, src)
    print("  ✓ Set DEBUG = False")

# Verify
print("\n[VERIFY] Django check...")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:400]}")
