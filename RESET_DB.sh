#!/bin/bash
set -e

cd /home/spd_max/projects/esmfamil

echo "=========================================="
echo "🔄 RESET DATABASE + MIGRATIONS"
echo "=========================================="
echo ""

# 1) بکاپ بگیر (فقط اگه دیتابیس هست)
if [ -f "db.sqlite3" ]; then
    cp db.sqlite3 "db.sqlite3.before_reset_$(date +%Y%m%d_%H%M)"
    echo "✓ Backup created: db.sqlite3.before_reset_*"
fi

# 2) حذف دیتابیس
rm -f db.sqlite3
echo "✓ Database deleted"

# 3) حذف migration های خراب (همه به جز __init__.py)
for app in accounts support game social alliance; do
    if [ -d "$app/migrations" ]; then
        find "$app/migrations" -name "0*.py" -type f -delete
        echo "✓ Cleared $app/migrations"
    fi
done

# 4) مطمئن شو __init__.py هست
for app in accounts support game social alliance; do
    if [ -d "$app/migrations" ]; then
        touch "$app/migrations/__init__.py"
    fi
done

# 5) ساخت migration های جدید
echo ""
echo "→ Creating fresh migrations..."
python manage.py makemigrations accounts --noinput
python manage.py makemigrations game --noinput
python manage.py makemigrations social --noinput
python manage.py makemigrations alliance --noinput
python manage.py makemigrations support --noinput

# 6) migrate
echo ""
echo "→ Running migrate..."
python manage.py migrate --noinput

# 7) نتیجه
echo ""
echo "=========================================="
echo "✅ RESET COMPLETE"
echo "=========================================="
echo ""
echo "→ Verifying tables..."
python manage.py shell -c "
from django.db import connection
with connection.cursor() as c:
    c.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name IN ('accounts_userunlockedavatar', 'support_supportticket', 'accounts_user', 'game_game')\")
    tables = [r[0] for r in c.fetchall()]
    for t in ['accounts_user', 'accounts_userunlockedavatar', 'support_supportticket', 'game_game']:
        if t in tables:
            print(f'  ✅ {t}')
        else:
            print(f'  ❌ {t} MISSING')
"

echo ""
echo "→ Ready! Now run:"
echo "   python manage.py runserver"
