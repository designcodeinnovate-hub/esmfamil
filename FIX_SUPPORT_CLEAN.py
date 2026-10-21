#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clean all support models from accounts/models.py"""
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
# 1) Read accounts/models.py
# ============================================================
print("\n[1/6] Reading accounts/models.py")
src = read("accounts/models.py")
print(f"  File size: {len(src)} chars")

# Find all class names
all_classes = re.findall(r'^class ([A-Za-z_][A-Za-z0-9_]*)', src, re.MULTILINE)
print(f"  Classes found: {all_classes}")

# ============================================================
# 2) Remove SupportMessage class
# ============================================================
print("\n[2/6] Removing SupportMessage")
if "class SupportMessage" in src:
    # Remove class block
    pattern = re.compile(
        r'\n\nclass SupportMessage\(models\.Model\):.*?(?=\n\nclass |\n\n# |\Z)',
        re.DOTALL
    )
    m = pattern.search(src)
    if m:
        removed_len = len(m.group(0))
        src = src[:m.start()] + src[m.end():]
        print(f"  ✓ Removed SupportMessage ({removed_len} chars)")
    else:
        # Try line-by-line
        lines = src.split("\n")
        result = []
        skip = False
        for line in lines:
            if line.startswith("class SupportMessage"):
                skip = True
                continue
            if skip:
                if line.startswith("class ") or (line and not line.startswith(" ") and not line.startswith("#") and not line.startswith("@")):
                    skip = False
                    result.append(line)
                continue
            result.append(line)
        src = "\n".join(result)
        print("  ✓ Removed SupportMessage (line-by-line)")
else:
    print("  ✓ No SupportMessage found")

# ============================================================
# 3) Also remove any remaining support-related stuff
# ============================================================
print("\n[3/6] Checking for other support references")

# Check for remaining references
refs = re.findall(r'SupportTicket|SupportMessage', src)
if refs:
    print(f"  ⚠ Still {len(refs)} references to Support* — cleaning")

    # Remove any imports
    src = re.sub(r'from support[^\n]*\n', '', src)
    src = re.sub(r'import support[^\n]*\n', '', src)
else:
    print("  ✓ No Support* references")

write("accounts/models.py", src)

# ============================================================
# 4) Check accounts/migrations for SupportTicket references
# ============================================================
print("\n[4/6] Checking accounts/migrations")
migrations = sorted([f for f in os.listdir("accounts/migrations") if f.endswith(".py") and f.startswith("0")])

for m in migrations:
    content = read(f"accounts/migrations/{m}")
    if "SupportTicket" in content or "SupportMessage" in content:
        print(f"  ⚠ {m} has Support references")
    else:
        print(f"  ✓ {m} clean")

# ============================================================
# 5) Fix or delete the fake migration if needed
# ============================================================
print("\n[5/6] Fixing migrations")

# Find the "remove_supportticket" migration we created earlier
for m in migrations:
    if "remove_supportticket" in m:
        content = read(f"accounts/migrations/{m}")
        if "DeleteModel" in content and "SupportTicket" in content:
            # Check if there's also a SupportMessage that needs removal
            if "SupportMessage" not in content:
                # Add SupportMessage to the operations
                new_content = content.replace(
                    "migrations.DeleteModel(\n            name='SupportTicket',\n        ),",
                    "migrations.DeleteModel(\n            name='SupportMessage',\n        ),\n        migrations.DeleteModel(\n            name='SupportTicket',\n        ),"
                )
                if new_content != content:
                    write(f"accounts/migrations/{m}", new_content)
                    print(f"  ✓ Added SupportMessage to {m}")
                else:
                    print(f"  ⚠ Could not modify {m}")
            else:
                print(f"  ✓ {m} already has SupportMessage")

# ============================================================
# 6) Run makemigrations + migrate + check
# ============================================================
print("\n[6/6] Running migrations + check")

cmds = [
    [sys.executable, "manage.py", "makemigrations", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]

for cmd in cmds:
    print(f"\n  $ {' '.join(cmd[1:])}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            out = r.stdout.strip()
            if out:
                print(f"    {out[:500]}")
        else:
            print(f"    ⚠ ERR: {r.stderr.strip()[:500] if r.stderr else 'unknown'}")
    except subprocess.TimeoutExpired:
        print("    ⚠ Timeout")

print("\n  $ manage.py check")
try:
    r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True, timeout=30)
    if r.returncode == 0:
        print("  ✅ ALL CHECKS PASSED")
        print("\n✅ حالا سرور رو ران کن:")
        print("   pkill -9 -f 'manage.py runserver'")
        print("   python manage.py runserver")
    else:
        print(f"  ⚠ Still errors:")
        print(r.stderr[:1200] if r.stderr else r.stdout[:1200])
except subprocess.TimeoutExpired:
    print("  ⚠ Check timeout")
