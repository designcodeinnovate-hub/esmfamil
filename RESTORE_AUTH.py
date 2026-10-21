#!/usr/bin/env python3
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
