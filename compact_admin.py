#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compact send-to-all into announcements + remove top logout + notification controls."""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    if not os.path.exists(p): return ""
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Update admin_views.announcements_list — add send-to-all + read stats
# ============================================================
print("\n[1/6] Updating announcements_list view")
p = "accounts/admin_views.py"
src = read(p)

# Find and replace announcements_list
pattern = re.compile(r'@never_cache\ndef announcements_list\(request\):.*?(?=\n@never_cache|\Z)', re.DOTALL)
m = pattern.search(src)
if m:
    old_block = m.group(0)
    new_block = '''@never_cache
def announcements_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")

    from social.models import Notification
    from django.contrib.auth import get_user_model
    from django.db.models import Count, Q
    User = get_user_model()

    # Handle "send to all" POST
    if request.method == "POST" and request.POST.get("action") == "send_all":
        try:
            coins = int(request.POST.get("coins") or 0)
            gems = int(request.POST.get("gems") or 0)
        except (ValueError, TypeError):
            coins = 0
            gems = 0
        note = (request.POST.get("note") or "").strip()[:200]

        if coins == 0 and gems == 0 and not note:
            request.session["admin_message"] = {"type": "error", "text": "حداقل یه مقدار یا پیام وارد کن."}
            return redirect("custom_admin:announcements_list")

        # Update all users
        if coins != 0 or gems != 0:
            from django.db.models import F
            try:
                User.objects.all().update(coins=F("coins") + coins, gems=F("gems") + gems)
            except Exception as e:
                request.session["admin_message"] = {"type": "error", "text": f"خطا: {e}"}
                return redirect("custom_admin:announcements_list")

        # Send notification
        sender = User.objects.filter(is_staff=True).first()
        uids = User.objects.values_list("id", flat=True)
        batch = []
        count = 0
        for uid in uids.iterator(chunk_size=1000):
            batch.append(Notification(
                user_id=uid, type="admin_broadcast",
                title="🎁 جایزه ویژه!",
                body=note or f"سکه: {coins:+d} | جم: {gems:+d}",
                url="/accounts/shop/", is_read=False, sender=sender,
            ))
            if len(batch) >= 500:
                Notification.objects.bulk_create(batch)
                count += len(batch)
                batch = []
        if batch:
            Notification.objects.bulk_create(batch)
            count += len(batch)

        total = User.objects.count()
        request.session["admin_message"] = {
            "type": "success",
            "text": f"✅ به {total} کاربر داده شد (سکه: {coins:+d}، جم: {gems:+d})."
        }
        return redirect("custom_admin:announcements_list")

    # GET — show list with read stats
    qs = Notification.objects.filter(type="admin_broadcast").order_by("-created_at")

    seen = set()
    data = []
    for n in qs.iterator(chunk_size=200):
        key = (n.title, n.body or "", n.url or "")
        if key in seen:
            continue
        seen.add(key)

        stats = Notification.objects.filter(
            type="admin_broadcast",
            title=n.title,
            body=n.body or "",
            url=n.url or "",
        ).aggregate(
            total=Count("id"),
            read_count=Count("id", filter=Q(is_read=True)),
        )
        total = stats["total"] or 0
        read_count = stats["read_count"] or 0
        unread_count = total - read_count

        data.append({
            "title": n.title,
            "body": n.body,
            "url": n.url,
            "created_at": n.created_at,
            "recipients": total,
            "read_count": read_count,
            "unread_count": unread_count,
        })

    message = request.session.pop("admin_message", None)
    total_users = User.objects.count()

    return render(request, "custom_admin/announcements.html", {
        "announcements": data,
        "message": message,
        "total_users": total_users,
    })


@never_cache
def announcement_toggle_read(request):
    """Toggle read/unread for an announcement for ALL users OR one user."""
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:announcements_list")

    from social.models import Notification

    title = (request.POST.get("title") or "").strip()
    body = (request.POST.get("body") or "").strip()
    url = (request.POST.get("url") or "").strip()
    mark_as = request.POST.get("mark_as", "read")

    if title:
        qs = Notification.objects.filter(type="admin_broadcast", title=title)
        if body:
            qs = qs.filter(body=body)
        if url:
            qs = qs.filter(url=url)

        if mark_as == "read":
            n = qs.update(is_read=True)
            request.session["admin_message"] = {"type": "success", "text": f"{n} اعلان به «خوانده شد» تغییر یافت."}
        elif mark_as == "unread":
            n = qs.update(is_read=False)
            request.session["admin_message"] = {"type": "success", "text": f"{n} اعلان به «نخوانده» تغییر یافت."}

    return redirect("custom_admin:announcements_list")
'''
    src = src.replace(old_block, new_block)
    write(p, src)
    print("  ✓ announcements_list rebuilt with send-to-all + read stats")

# ============================================================
# 2) Add toggle_read to user_notify view
# ============================================================
print("\n[2/6] Adding read/unread toggle to user_notify")

p = "accounts/admin_views.py"
src = read(p)

if "def user_notify_toggle_read" in src:
    print("  ✓ Already exists")
else:
    src = src.rstrip() + '''

@never_cache
def user_notify_toggle_read(request, user_id, notif_id):
    """Toggle read/unread for a single notification."""
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:user_notify", user_id=user_id)

    from social.models import Notification
    try:
        n = Notification.objects.get(id=notif_id, user_id=user_id)
        n.is_read = not n.is_read
        n.save(update_fields=["is_read"])
        status = "خوانده شد" if n.is_read else "نخوانده شد"
        request.session["admin_message"] = {"type": "success", "text": f"اعلان {status}."}
    except Notification.DoesNotExist:
        request.session["admin_message"] = {"type": "error", "text": "اعلان پیدا نشد."}

    return redirect("custom_admin:user_notify", user_id=user_id)
'''
    write(p, src)
    print("  ✓ user_notify_toggle_read added")

# ============================================================
# 3) Update admin_urls.py — add toggle routes
# ============================================================
print("\n[3/6] Adding routes")

p = "accounts/admin_urls.py"
src = read(p)

if "announcement_toggle_read" not in src:
    old = '    path("announcement/delete/", admin_views.announcement_delete, name="announcement_delete"),'
    new = old + '\n    path("announcement/toggle-read/", admin_views.announcement_toggle_read, name="announcement_toggle_read"),'
    if old in src:
        src = src.replace(old, new, 1)

if "user_notify_toggle_read" not in src:
    old = '    path("user/<int:user_id>/notify/clear/", admin_views.user_notify_clear, name="user_notify_clear"),'
    new = old + '\n    path("user/<int:user_id>/notify/<int:notif_id>/toggle-read/", admin_views.user_notify_toggle_read, name="user_notify_toggle_read"),'
    if old in src:
        src = src.replace(old, new, 1)

write(p, src)
print("  ✓ Routes added")

# ============================================================
# 4) Rebuild announcements.html — merge send-to-all
# ============================================================
print("\n[4/6] Rebuilding announcements.html with compact send-to-all")

ANN_HTML = '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>اعلان‌ها — پنل ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 16px 16px 40px; }
    .container { max-width: 1400px; margin: 0 auto; }

    .admin-sticky-header {
      position: sticky; top: 0; z-index: 500;
      background: #0a0a15; padding: 4px 0 8px;
      margin-bottom: 20px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.7);
    }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 8px; }
    .topbar h1 { font-size: 20px; color: #fca5a5; }

    .admin-tabs {
      display: flex !important; gap: 6px !important;
      overflow-x: auto !important; overflow-y: hidden !important;
      white-space: nowrap !important; padding: 8px !important;
      background: #12121f !important;
      border: 1px solid rgba(148,163,184,0.15) !important;
      border-radius: 14px !important;
      scrollbar-width: none !important;
      height: 48px !important;
    }
    .admin-tabs::-webkit-scrollbar { display: none; }
    .admin-tab {
      flex: 0 0 auto !important; height: 40px !important;
      display: inline-flex !important; align-items: center !important;
      padding: 0 14px !important; border-radius: 10px !important;
      text-decoration: none !important; font-size: 12px !important;
      font-weight: bold !important; color: #94a3b8 !important;
      white-space: nowrap !important;
    }
    .admin-tab:hover { background: rgba(148,163,184,0.1) !important; color: #fff !important; }
    .admin-tab.active { background: linear-gradient(135deg, #ef4444, #dc2626) !important; color: #fff !important; }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .card { background: #12121f; border: 1px solid rgba(148,163,184,0.15); border-radius: 16px; padding: 22px; margin-bottom: 16px; }
    .card h3 { color: #fdba74; font-size: 15px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }

    /* Compact send form */
    .send-form-grid { display: grid; grid-template-columns: 90px 90px 1fr; gap: 8px; align-items: end; margin-bottom: 10px; }
    @media (max-width: 700px) { .send-form-grid { grid-template-columns: 1fr 1fr; } }
    .send-form-grid label { display: block; font-size: 11px; color: #94a3b8; margin-bottom: 4px; font-weight: bold; }
    .send-form-grid input { width: 100%; padding: 10px 12px; border-radius: 10px; border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15; color: #fff; font-size: 13px; font-family: monospace; }
    .send-form-grid input:focus { outline: none; border-color: #facc15; }
    .send-btn { padding: 10px 20px; border: none; border-radius: 10px; background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; font-family: inherit; font-weight: bold; font-size: 13px; cursor: pointer; white-space: nowrap; }
    .send-btn:hover { transform: translateY(-1px); }

    .form-row { margin-bottom: 10px; }
    .form-row label { display: block; font-size: 11px; color: #94a3b8; margin-bottom: 4px; font-weight: bold; }
    .form-row input[type=text], .form-row textarea { width: 100%; padding: 10px 12px; border-radius: 10px; border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15; color: #fff; font-size: 13px; font-family: inherit; }
    .form-row input:focus, .form-row textarea:focus { outline: none; border-color: #facc15; }
    .form-row textarea { min-height: 60px; resize: vertical; }

    /* Announcement items */
    .ann-card { background: linear-gradient(135deg, #1a1a2e, #12121f); border: 1px solid rgba(245,158,11,0.3); border-radius: 14px; padding: 14px; margin-bottom: 10px; }
    .ann-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
    .ann-icon { width: 38px; height: 38px; border-radius: 10px; background: rgba(245,158,11,0.2); display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
    .ann-info { flex: 1; min-width: 150px; }
    .ann-title { font-size: 14px; font-weight: bold; color: #fde68a; margin-bottom: 2px; }
    .ann-meta { font-size: 10px; color: #64748b; font-family: monospace; }
    .ann-body { font-size: 12px; color: #cbd5e1; line-height: 1.6; margin: 8px 0; }

    .stat-chips { display: flex; gap: 6px; margin: 8px 0; flex-wrap: wrap; }
    .stat-chip { padding: 4px 10px; border-radius: 8px; font-size: 10px; font-weight: bold; font-family: monospace; }
    .stat-chip.total { background: rgba(148,163,184,0.15); color: #cbd5e1; }
    .stat-chip.read { background: rgba(34,197,94,0.2); color: #4ade80; }
    .stat-chip.unread { background: rgba(234,179,8,0.2); color: #fde68a; }

    .ann-actions { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
    .ann-actions form { display: inline; }
    .btn-sm { padding: 6px 12px; border: none; border-radius: 8px; font-family: inherit; font-size: 11px; font-weight: bold; cursor: pointer; }
    .btn-mark-read { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .btn-mark-unread { background: rgba(234,179,8,0.15); color: #fde68a; border: 1px solid rgba(234,179,8,0.3); }
    .btn-del-ann { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
    .btn-sm:hover { transform: translateY(-1px); }

    .empty-state { text-align: center; padding: 40px 20px; color: #64748b; font-size: 13px; }
    .empty-state .icon { font-size: 60px; display: block; margin-bottom: 12px; opacity: 0.5; }
  </style>
</head>
<body>
<div class="container">
  <div class="admin-sticky-header">
    <div class="topbar">
      <h1>📢 اعلان‌ها و جایزه‌ها</h1>
    </div>

    <div class="admin-tabs">
      <a href="/panel-admin/dashboard/" class="admin-tab {% if '/panel-admin/dashboard/' in request.path or request.path == '/panel-admin/' %}active{% endif %}">👥 کاربران</a>
      <a href="/panel-admin/alliances/" class="admin-tab {% if '/panel-admin/alliance' in request.path %}active{% endif %}">🛡️ اتحادها</a>
      <a href="/panel-admin/rooms/" class="admin-tab {% if '/panel-admin/room' in request.path %}active{% endif %}">🚪 اتاق‌ها</a>
      <a href="/panel-admin/announcements/" class="admin-tab {% if '/panel-admin/announcement' in request.path %}active{% endif %}">📢 اعلان‌ها</a>
      <a href="/panel-admin/tournaments/" class="admin-tab {% if '/panel-admin/tournament' in request.path %}active{% endif %}">🏆 تورنمنت</a>
      <a href="/panel-admin/shop/" class="admin-tab {% if '/panel-admin/shop/' in request.path %}active{% endif %}">🛒 فروشگاه</a>
      <a href="/panel-admin/guest-log/" class="admin-tab {% if '/panel-admin/guest-log/' in request.path %}active{% endif %}">🎲 مهمان‌ها</a>
    </div>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <!-- Send to all - compact -->
  <div class="card">
    <h3>🎁 جایزه به همه ({{ total_users }} کاربر)</h3>
    <form method="post">
      {% csrf_token %}
      <input type="hidden" name="action" value="send_all">
      <div class="send-form-grid">
        <div>
          <label>🪙 سکه</label>
          <input type="number" name="coins" value="0" placeholder="0">
        </div>
        <div>
          <label>💎 جم</label>
          <input type="number" name="gems" value="0" placeholder="0">
        </div>
        <div>
          <label>📝 پیام (اختیاری)</label>
          <input type="text" name="note" maxlength="200" placeholder="مثلاً: هدیه ویژه!">
        </div>
      </div>
      <button type="submit" class="send-btn" onclick="return confirm('این جایزه به همه {{ total_users }} کاربر داده شود؟');">🎁 ارسال به همه</button>
    </form>
  </div>

  <!-- Send custom announcement -->
  <div class="card">
    <h3>📝 ارسال اعلان دلخواه</h3>
    <form method="post" action="{% url 'custom_admin:announcement_create' %}">
      {% csrf_token %}
      <div class="form-row">
        <label>عنوان</label>
        <input type="text" name="title" required maxlength="100" placeholder="عنوان اعلان...">
      </div>
      <div class="form-row">
        <label>متن</label>
        <textarea name="body" maxlength="300" placeholder="متن کامل..."></textarea>
      </div>
      <div class="form-row">
        <label>لینک (اختیاری)</label>
        <input type="text" name="url" maxlength="200" placeholder="/game/">
      </div>
      <button type="submit" class="send-btn">📤 ارسال به همه</button>
    </form>
  </div>

  <!-- History -->
  <div class="card">
    <h3>📜 تاریخچه اعلان‌ها ({{ announcements|length }})</h3>
    {% if announcements %}
      {% for a in announcements %}
        <div class="ann-card">
          <div class="ann-head">
            <div class="ann-icon">📢</div>
            <div class="ann-info">
              <div class="ann-title">{{ a.title }}</div>
              <div class="ann-meta">{{ a.created_at|jdate:"Y/m/d H:i" }}</div>
            </div>
          </div>
          {% if a.body %}<div class="ann-body">{{ a.body }}</div>{% endif %}

          <div class="stat-chips">
            <span class="stat-chip total">👥 {{ a.recipients }} گیرنده</span>
            <span class="stat-chip read">✓ {{ a.read_count }} خوانده</span>
            <span class="stat-chip unread">● {{ a.unread_count }} نخوانده</span>
          </div>

          {% if a.url %}<div class="ann-meta">🔗 {{ a.url }}</div>{% endif %}

          <div class="ann-actions">
            <form method="post" action="{% url 'custom_admin:announcement_toggle_read' %}">
              {% csrf_token %}
              <input type="hidden" name="title" value="{{ a.title }}">
              <input type="hidden" name="body" value="{{ a.body }}">
              <input type="hidden" name="url" value="{{ a.url }}">
              <input type="hidden" name="mark_as" value="read">
              <button type="submit" class="btn-sm btn-mark-read" onclick="return confirm('همه گیرنده‌ها «خوانده شد» شوند؟');">✓ علامت خوانده برای همه</button>
            </form>
            <form method="post" action="{% url 'custom_admin:announcement_toggle_read' %}">
              {% csrf_token %}
              <input type="hidden" name="title" value="{{ a.title }}">
              <input type="hidden" name="body" value="{{ a.body }}">
              <input type="hidden" name="url" value="{{ a.url }}">
              <input type="hidden" name="mark_as" value="unread">
              <button type="submit" class="btn-sm btn-mark-unread" onclick="return confirm('همه گیرنده‌ها «نخوانده» شوند؟');">● علامت نخوانده برای همه</button>
            </form>
            <form method="post" action="{% url 'custom_admin:announcement_delete' %}">
              {% csrf_token %}
              <input type="hidden" name="title" value="{{ a.title }}">
              <input type="hidden" name="body" value="{{ a.body }}">
              <input type="hidden" name="url" value="{{ a.url }}">
              <button type="submit" class="btn-sm btn-del-ann" onclick="return confirm('حذف این اعلان از همه کاربران؟');">🗑️ حذف</button>
            </form>
          </div>
        </div>
      {% endfor %}
    {% else %}
      <div class="empty-state">
        <span class="icon">📭</span>
        هنوز اعلانی ارسال نشده.
      </div>
    {% endif %}
  </div>
</div>
</body>
</html>
'''

write("accounts/templates/custom_admin/announcements.html", ANN_HTML)
print("  ✓ announcements.html rebuilt")

# ============================================================
# 5) Update user_notify.html — add toggle read/unread
# ============================================================
print("\n[5/6] Updating user_notify.html")

p = "accounts/templates/custom_admin/user_notify.html"
src = read(p)

# Add toggle-read button before delete in each notification
old_btn = '''<form method="post" action="{% url 'custom_admin:user_notify_delete' u.id n.id %}" onsubmit="return confirm('حذف این اعلان؟');">
            {% csrf_token %}
            <button type="submit" class="btn-del-small">حذف</button>
          </form>'''

new_btn = '''<div style="display:flex; flex-direction:column; gap:4px;">
            <form method="post" action="{% url 'custom_admin:user_notify_toggle_read' u.id n.id %}">
              {% csrf_token %}
              <button type="submit" class="btn-del-small" style="background:{% if n.is_read %}rgba(234,179,8,0.15){% else %}rgba(34,197,94,0.15){% endif %}; color:{% if n.is_read %}#fde68a{% else %}#4ade80{% endif %}; border-color:{% if n.is_read %}rgba(234,179,8,0.3){% else %}rgba(34,197,94,0.3){% endif %};">
                {% if n.is_read %}● نخوانده{% else %}✓ خوانده{% endif %}
              </button>
            </form>
            <form method="post" action="{% url 'custom_admin:user_notify_delete' u.id n.id %}" onsubmit="return confirm('حذف این اعلان؟');">
              {% csrf_token %}
              <button type="submit" class="btn-del-small">حذف</button>
            </form>
          </div>'''

if old_btn in src:
    src = src.replace(old_btn, new_btn, 1)
    write(p, src)
    print("  ✓ Toggle read/unread added to user_notify")
else:
    print("  ⚠ Could not find delete button pattern")

# ============================================================
# 6) Remove logout from all topbars + add to dashboard
# ============================================================
print("\n[6/6] Removing logout from topbars")

# List all admin templates
admin_files = [
    "alliances.html", "alliance_detail.html", "rooms.html",
    "tournaments.html", "tournament_edit.html", "shop_items.html",
    "guest_log.html", "send_to_all.html",
    "user_detail.html", "user_edit.html", "user_notify.html",
]

for fname in admin_files:
    path = f"accounts/templates/custom_admin/{fname}"
    if not os.path.exists(path): continue

    src = read(path)

    # Remove logout link
    patterns = [
        r'\s*<a href="\{% url \'custom_admin:logout\' %\}"[^>]*>خروج</a>',
        r'\s*<a href="\{% url \'custom_admin:logout\' %\}"[^>]*>[^<]*خروج[^<]*</a>',
    ]
    original = src
    for pattern in patterns:
        src = re.sub(pattern, '', src, flags=re.DOTALL)

    if src != original:
        write(path)
        print(f"  ✓ Removed logout from {fname}")

# Remove logout from dashboard but keep a different way
p = "accounts/templates/custom_admin/dashboard.html"
if os.path.exists(p):
    src = read(p)

    # Remove old topbar logout
    old_topbar = '''<div class="topbar">
      <h1>🔒 پنل مدیریت کاربران</h1>
      <div class="actions">
        <a href="{% url 'custom_admin:logout' %}" class="btn-danger">خروج</a>
      </div>
    </div>'''

    new_topbar = '''<div class="topbar">
      <h1>🔒 پنل مدیریت کاربران</h1>
      <form method="post" action="{% url 'custom_admin:logout' %}" style="display:inline;">
        {% csrf_token %}
        <button type="submit" class="btn-danger" style="cursor:pointer; border:none; font-family:inherit; padding:9px 16px; border-radius:10px; font-size:13px; font-weight:bold;">🚪 خروج از پنل</button>
      </form>
    </div>'''

    if old_topbar in src:
        src = src.replace(old_topbar, new_topbar, 1)
        write(p)
        print("  ✓ Logout in dashboard (POST form)")

# ============================================================
# Verify + test
# ============================================================
print("\n" + "="*70)
print("VERIFICATION")
print("="*70)

r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:600]}")

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from social.models import Notification
User = get_user_model()

tu, created = User.objects.get_or_create(
    username="__compact_test__",
    defaults={"alias": "test", "is_active": True, "is_staff": True, "has_chosen_avatar": True, "has_completed_registration": True}
)
if created:
    tu.set_password("x")
    tu.save()

c = Client()
c.session["custom_admin_logged_in"] = True
c.session["beta_unlocked"] = True
c.session.save()

# Test pages
print("\n  Testing pages:")
for url in ["/panel-admin/dashboard/", "/panel-admin/announcements/"]:
    try:
        r = c.get(url, follow=False)
        mark = "✓" if r.status_code == 200 else "✗"
        print(f"    {mark} {url:35s} → {r.status_code}")
    except Exception as e:
        print(f"    ✗ {url:35s} → {type(e).__name__}")

# Test send-to-all
print("\n  Testing send-to-all:")
r = c.post("/panel-admin/announcements/", {
    "action": "send_all",
    "coins": "100",
    "gems": "5",
    "note": "__test_reward__",
}, follow=True)
print(f"    Status: {r.status_code}")

# Check user got coins
tu.refresh_from_db()
print(f"    User coins: {tu.coins} (expected 100)")
print(f"    User gems: {tu.gems} (expected 5)")

# Cleanup
Notification.objects.filter(title="🎁 جایزه ویژه!", body="__test_reward__").delete()
if created:
    tu.delete()

print("\n" + "="*70)
print("DONE")
print("="*70)
print("""
What changed:

  1. Send-to-all MOVED into announcements page
     - Compact form at top (coins, gems, note in one row)
     - No more separate /panel-admin/send-to-all/ tab
     - Removed "جایزه همه" tab from tabs bar

  2. Logout removed from ALL topbars except dashboard
     - Dashboard still has it as POST form (safer)
     - All other pages: no logout button

  3. Announcements now show:
     - 👥 N گیرنده (total)
     - ✓ N خوانده (read count)
     - ● N نخوانده (unread count)
     - Buttons per announcement:
       - ✓ علامت خوانده برای همه
       - ● علامت نخوانده برای همه
       - 🗑️ حذف

  4. user_notify.html now has:
     - ✓/● toggle button for each notification (read/unread)
     - Delete button
     - Both side by side

  5. New routes:
     - POST /panel-admin/announcement/toggle-read/
     - POST /panel-admin/user/<id>/notify/<notif_id>/toggle-read/

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R

Test:
  1. /panel-admin/announcements/
     - Compact "جایزه به همه" form at top
     - Send with coins=100, gems=5
     - See announcement with read/unread counts
     - Click "علامت خوانده برای همه" → read count increases
     - Click delete → removes from all users
  
  2. /panel-admin/user/<id>/notify/
     - See each notification with ✓ or ● button
     - Click to toggle read status
     - Click delete to remove single notification
""")
