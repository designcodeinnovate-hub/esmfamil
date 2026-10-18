#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare project for Runflare deployment — run once."""
import os, stat, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()

def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✅ {p}")

def exists(p): return os.path.exists(p)

# ========== 1) .gitignore ==========
gitignore = """\
# Python
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/

# Virtualenv
venv/
.venv/
env/

# Django
db.sqlite3
db.sqlite3.*
*.sqlite3
*.log
staticfiles/
media/

# Env & secrets
.env
.env.*

# Backup / dump
*.bak
*.backup
PROJECT_DUMP.txt
*.dump*
*.swp

# IDE
.vscode/
.idea/
!.vscode/settings.json
!.vscode/launch.json

# OS
.DS_Store
Thumbs.db
"""

gi_path = os.path.join(ROOT, ".gitignore")
if exists(gi_path) and ".env" in read(gi_path):
    print("  ⏭ .gitignore already OK")
else:
    write(gi_path, gitignore)

# ========== 2) .env.example ==========
env_example = """\
# ===== Runflare Environment Variables =====
# اینا رو تو پنل Runflare → Environment Variables وارد کن

DJANGO_SETTINGS_MODULE=config.settings_prod
DJANGO_SECRET_KEY=CHANGE_ME_TO_A_LONG_RANDOM_STRING
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-app.runflare.run
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-app.runflare.run
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://default:password@host:6379/0
"""
write(os.path.join(ROOT, ".env.example"), env_example)

# ========== 3) settings_prod.py — security headers ==========
prod_path = os.path.join(ROOT, "config", "settings_prod.py")
if exists(prod_path):
    src = read(prod_path)
    additions = []
    if "SESSION_COOKIE_SECURE" not in src:
        additions.append("SESSION_COOKIE_SECURE = not DEBUG")
    if "CSRF_COOKIE_SECURE" not in src:
        additions.append("CSRF_COOKIE_SECURE = not DEBUG")
    if "SESSION_COOKIE_HTTPONLY" not in src:
        additions.append("SESSION_COOKIE_HTTPONLY = True")
    if "SECURE_CONTENT_TYPE_NOSNIFF" not in src:
        additions.append("SECURE_CONTENT_TYPE_NOSNIFF = True")
    if "X_FRAME_OPTIONS" not in src:
        additions.append('X_FRAME_OPTIONS = "DENY"')
    if "SECURE_HSTS_SECONDS" not in src:
        additions.append("SECURE_HSTS_SECONDS = 0")
    if additions:
        src = src.rstrip() + "\n\n# ===== Security (auto-added) =====\n" + "\n".join(additions) + "\n"
        write(prod_path, src)
    else:
        print("  ⏭ settings_prod.py — already has security config")

# ========== 4) chmod build.sh ==========
bs = os.path.join(ROOT, "build.sh")
if exists(bs):
    st = os.stat(bs)
    os.chmod(bs, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"  ✅ build.sh — executable")

# ========== 5) Remove sensitive files from git tracking ==========
sensitive = ["db.sqlite3", "db.sqlite3.backup", "PROJECT_DUMP.txt", ".dump.js.swp"]
for f in sensitive:
    r = subprocess.run(["git", "rm", "--cached", "-f", f],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  🗑 untracked from git: {f}")
    else:
        print(f"  ⏭ not in git (or already removed): {f}")

# ========== 6) Final message ==========
print("\n" + "="*60)
print("✅ همه تغییرات اعمال شد!")
print("="*60)
