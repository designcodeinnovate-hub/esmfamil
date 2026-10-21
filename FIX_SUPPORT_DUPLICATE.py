#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove duplicate SupportTicket from accounts/models.py"""
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
# 1) Check where SupportTicket is in accounts/models.py
# ============================================================
print("\n[1/5] Checking accounts/models.py")
accounts_models = read("accounts/models.py")

if "class SupportTicket" not in accounts_models:
    print("  ✓ No SupportTicket in accounts/models.py")
else:
    print("  ⚠ Found SupportTicket in accounts/models.py — removing...")
    
    # Find and remove the entire class
    # Strategy: from "class SupportTicket" to end of class (next "class " or end of file)
    pattern = re.compile(
        r'\n\nclass SupportTicket\(models\.Model\):.*?(?=\n\nclass |\Z)',
        re.DOTALL
    )
    match = pattern.search(accounts_models)
    if match:
        removed = match.group(0)
        accounts_models = accounts_models[:match.start()] + accounts_models[match.end():]
        write("accounts/models.py", accounts_models)
        print(f"  ✓ Removed {len(removed)} chars")
    else:
        print("  ⚠ Could not match class pattern — trying line-by-line")
        lines = accounts_models.split("\n")
        new_lines = []
        skip = False
        indent_level = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("class SupportTicket"):
                skip = True
                indent_level = len(line) - len(line.lstrip())
                continue
            if skip:
                # Skip until we find a line that starts at same or lower indent AND starts with "class "
                current_indent = len(line) - len(line.lstrip())
                if line.strip() and current_indent <= indent_level and not line.strip().startswith("#"):
                    skip = False
                    new_lines.append(line)
                continue
            new_lines.append(line)
        write("accounts/models.py", "\n".join(new_lines))
        print("  ✓ Removed via line-by-line")

# ============================================================
# 2) Check for migration issues
# ============================================================
print("\n[2/5] Checking migrations")
accounts_migrations = os.listdir("accounts/migrations") if os.path.exists("accounts/migrations") else []
support_migrations = os.listdir("support/migrations") if os.path.exists("support/migrations") else []

print(f"  accounts migrations: {[m for m in accounts_migrations if m.endswith('.py') and m.startswith('0')]}")
print(f"  support migrations: {[m for m in support_migrations if m.endswith('.py') and m.startswith('0')]}")

# Check if any accounts migration references SupportTicket
has_support_in_accounts = False
for m in accounts_migrations:
    if m.endswith('.py') and m.startswith('0'):
        content = read(f"accounts/migrations/{m}")
        if "SupportTicket" in content:
            print(f"  ⚠ {m} has SupportTicket reference")
            has_support_in_accounts = True

# ============================================================
# 3) Create fake migration if needed to remove accounts_supportticket table
# ============================================================
print("\n[3/5] Handling migrations")

if has_support_in_accounts:
    # Find latest migration number
    mig_nums = []
    for m in accounts_migrations:
        if m.endswith('.py') and m.startswith('0'):
            try:
                num = int(m.split('_')[0])
                mig_nums.append(num)
            except: pass
    
    if mig_nums:
        next_num = max(mig_nums) + 1
        new_mig_name = f"{next_num:04d}_remove_supportticket.py"
        
        # Find last migration for dependencies
        last_mig = sorted([m for m in accounts_migrations if m.endswith('.py') and m.startswith('0')])[-1]
        last_mig_name = last_mig.replace('.py', '')
        
        migration_content = f'''# -*- coding: utf-8 -*-
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '{last_mig_name}'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SupportTicket',
        ),
    ]
'''
        write(f"accounts/migrations/{new_mig_name}", migration_content)
        print(f"  ✓ Created {new_mig_name}")

# ============================================================
# 4) Also fix support/models.py related_name to be safe
# ============================================================
print("\n[4/5] Fixing support/models.py related_name")
support_models = read("support/models.py")

if 'related_name="support_tickets"' in support_models:
    # Change to something unique
    support_models = support_models.replace(
        'related_name="support_tickets"',
        'related_name="user_support_tickets"'
    )
    write("support/models.py", support_models)
    print("  ✓ Changed related_name to user_support_tickets")

# ============================================================
# 5) Run makemigrations + migrate
# ============================================================
print("\n[5/5] Running migrations")

cmds = [
    [sys.executable, "manage.py", "makemigrations", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]

for cmd in cmds:
    print(f"\n  $ {' '.join(cmd[1:])}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode == 0:
        if r.stdout.strip():
            print(f"    {r.stdout.strip()[:400]}")
    else:
        print(f"    ⚠ ERR: {r.stderr.strip()[:400] if r.stderr else 'unknown'}")

# ============================================================
# Final check
# ============================================================
print("\n[Check] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True, timeout=30)
if r.returncode == 0:
    print("  ✓ ALL CHECKS PASSED")
    print("\n✅ حالا سرور رو ران کن:")
    print("   python manage.py runserver")
else:
    print(f"  ⚠ Still errors:")
    print(r.stderr[:800] if r.stderr else r.stdout[:800])
    print("\n⚠ باید خطاهای بالا رو بفرستی")
