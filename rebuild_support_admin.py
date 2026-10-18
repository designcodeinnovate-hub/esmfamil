#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Complete rebuild of admin support panel with close/delete + beautiful UI."""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    if not os.path.exists(p): return ""
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Verify/rebuild admin views
# ============================================================
print("\n[1/5] Verifying admin support views")
p = "accounts/admin_views.py"
src = read(p)

# Check if views exist
has_list = "def support_tickets_list(request):" in src
has_detail = "def support_ticket_admin(request, ticket_id):" in src
has_close = "action == \"close\"" in src
has_delete = "action == \"delete\"" in src

print(f"  support_tickets_list: {'✓' if has_list else '✗'}")
print(f"  support_ticket_admin: {'✓' if has_detail else '✗'}")
print(f"  close action: {'✓' if has_close else '✗'}")
print(f"  delete action: {'✓' if has_delete else '✗'}")

if not (has_list and has_detail and has_close and has_delete):
    print("  ⚠ Some views missing — rebuilding all")
    
    # Remove old versions
    for pattern in [
        r'@never_cache\ndef support_tickets_list\(request\):.*?(?=\n@never_cache|\Z)',
        r'@never_cache\ndef support_ticket_admin\(request, ticket_id\):.*?(?=\n@never_cache|\Z)',
    ]:
        m = re.search(pattern, src, re.DOTALL)
        if m:
            src = src[:m.start()] + src[m.end():]
    
    new_views = '''

# ============================================================
# Admin — Support Tickets (Complete)
# ============================================================
@never_cache
def support_tickets_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    
    from accounts.models import SupportTicket, SupportMessage
    from django.db.models import Count, Q
    
    status_filter = (request.GET.get("status") or "").strip()
    qs = SupportTicket.objects.all().select_related("user").order_by("-updated_at")
    
    if status_filter in ("open", "answered", "closed"):
        qs = qs.filter(status=status_filter)
    
    data = []
    for t in qs[:200]:
        last_msg = t.messages.order_by("-created_at").first()
        msgs_list = t.messages.order_by("created_at")
        
        data.append({
            "id": t.id,
            "subject": t.subject,
            "status": t.status,
            "status_display": t.get_status_display(),
            "user_alias": t.user.alias or t.user.username,
            "username": t.user.username,
            "avatar_id": t.user.avatar_id,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "message_count": t.message_count(),
            "last_msg": (last_msg.body[:80] + "...") if last_msg and len(last_msg.body) > 80 else (last_msg.body if last_msg else "—"),
        })
    
    message = request.session.pop("admin_message", None)
    
    return render(request, "custom_admin/support_tickets.html", {
        "tickets": data,
        "status_filter": status_filter,
        "message": message,
        "count_open": SupportTicket.objects.filter(status="open").count(),
        "count_answered": SupportTicket.objects.filter(status="answered").count(),
        "count_closed": SupportTicket.objects.filter(status="closed").count(),
        "count_total": SupportTicket.objects.count(),
    })


@never_cache
def support_ticket_admin(request, ticket_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    
    from accounts.models import SupportTicket, SupportMessage
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    ticket = SupportTicket.objects.filter(id=ticket_id).select_related("user").first()
    if not ticket:
        request.session["admin_message"] = {"type": "error", "text": "تیکت پیدا نشد."}
        return redirect("custom_admin:support_tickets_list")
    
    if request.method == "POST":
        action = request.POST.get("action", "")
        
        if action == "reply":
            body = (request.POST.get("body") or "").strip()[:2000]
            if body:
                admin_user = User.objects.filter(is_staff=True).first()
                SupportMessage.objects.create(
                    ticket=ticket, sender=admin_user, body=body, is_staff=True,
                )
                ticket.status = "answered"
                ticket.save()
                request.session["admin_message"] = {"type": "success", "text": "✓ پاسخ ارسال شد."}
            return redirect("custom_admin:support_ticket_admin", ticket_id=ticket.id)
        
        elif action == "close":
            ticket.status = "closed"
            ticket.save()
            request.session["admin_message"] = {"type": "success", "text": "🔒 تیکت بسته شد."}
            return redirect("custom_admin:support_ticket_admin", ticket_id=ticket.id)
        
        elif action == "reopen":
            ticket.status = "open"
            ticket.save()
            request.session["admin_message"] = {"type": "success", "text": "🔓 تیکت باز شد."}
            return redirect("custom_admin:support_ticket_admin", ticket_id=ticket.id)
        
        elif action == "delete":
            ticket.delete()
            request.session["admin_message"] = {"type": "success", "text": "🗑️ تیکت حذف شد."}
            return redirect("custom_admin:support_tickets_list")
    
    msgs_data = [{
        "id": m.id,
        "sender_alias": (m.sender.alias if m.sender else "🤖 پشتیبانی"),
        "sender_username": (m.sender.username if m.sender else "system"),
        "body": m.body,
        "is_staff": m.is_staff,
        "created_at": m.created_at,
    } for m in ticket.messages.select_related("sender").all()]
    
    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/support_ticket_detail.html", {
        "ticket": ticket,
        "ticket_messages": msgs_data,
        "message": message,
    })
'''
    
    src = src.rstrip() + new_views + "\n"
    write(p, src)
    print("  ✓ Admin support views rebuilt")
else:
    print("  ✓ All views already exist")

# ============================================================
# 2) Rebuild support_tickets.html — beautiful list
# ============================================================
print("\n[2/5] Rebuilding support_tickets.html (beautiful)")

TICKETS_HTML = '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>پشتیبانی — پنل ادمین</title>
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
.topbar {
  display: flex; justify-content: space-between; align-items: center;
  background: linear-gradient(135deg, #1e1b4b, #0f0f1e);
  border: 1px solid rgba(139,92,246,0.4);
  padding: 16px 22px; border-radius: 16px; margin-bottom: 8px;
}
.topbar h1 { font-size: 20px; color: #c4b5fd; }

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

/* ===== Stats ===== */
.stats-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
  margin-bottom: 20px;
}
@media (max-width: 700px) { .stats-grid { grid-template-columns: 1fr 1fr; } }
.stat-card {
  padding: 18px; border-radius: 16px; text-align: center;
  border: 1.5px solid; position: relative; overflow: hidden;
  transition: 0.2s;
}
.stat-card:hover { transform: translateY(-2px); }
.stat-card.open {
  background: linear-gradient(135deg, rgba(234,179,8,0.15), rgba(15,23,42,0.6));
  border-color: rgba(234,179,8,0.4);
}
.stat-card.answered {
  background: linear-gradient(135deg, rgba(34,197,94,0.15), rgba(15,23,42,0.6));
  border-color: rgba(34,197,94,0.4);
}
.stat-card.closed {
  background: linear-gradient(135deg, rgba(100,116,139,0.15), rgba(15,23,42,0.6));
  border-color: rgba(100,116,139,0.4);
}
.stat-card.total {
  background: linear-gradient(135deg, rgba(139,92,246,0.15), rgba(15,23,42,0.6));
  border-color: rgba(139,92,246,0.4);
}
.stat-icon { font-size: 28px; margin-bottom: 6px; }
.stat-val { font-size: 26px; font-weight: 900; font-family: monospace; color: #fff; margin-bottom: 3px; }
.stat-lbl { font-size: 11px; color: #94a3b8; font-weight: bold; }

/* ===== Filter ===== */
.filter-row {
  display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap;
  padding: 8px; background: #12121f; border: 1px solid rgba(148,163,184,0.15);
  border-radius: 14px;
}
.filter-btn {
  padding: 10px 18px; border-radius: 10px; font-size: 13px; font-weight: bold;
  text-decoration: none; color: #94a3b8;
  background: transparent; border: 1px solid transparent;
  transition: 0.2s;
}
.filter-btn:hover { background: rgba(148,163,184,0.1); color: #fff; }
.filter-btn.active {
  background: linear-gradient(135deg, #8b5cf6, #6b4eff);
  color: #fff; border-color: transparent;
  box-shadow: 0 4px 15px rgba(139,92,246,0.4);
}

/* ===== Ticket list ===== */
.tickets-list { display: flex; flex-direction: column; gap: 10px; }

.ticket-item {
  display: flex; align-items: center; gap: 14px;
  padding: 16px; background: #12121f;
  border: 1.5px solid rgba(148,163,184,0.15);
  border-radius: 14px;
  text-decoration: none; color: #e2e8f0;
  transition: 0.2s;
  position: relative; overflow: hidden;
}
.ticket-item:hover {
  border-color: rgba(139,92,246,0.6);
  transform: translateX(-4px);
  box-shadow: 0 8px 25px rgba(139,92,246,0.15);
}
.ticket-item::before {
  content: ""; position: absolute;
  top: 0; bottom: 0; right: 0; width: 4px;
  background: #94a3b8;
}
.ticket-item.status-open::before { background: linear-gradient(180deg, #facc15, #eab308); }
.ticket-item.status-answered::before { background: linear-gradient(180deg, #4ade80, #22c55e); }
.ticket-item.status-closed::before { background: linear-gradient(180deg, #64748b, #475569); }

.ticket-avatar {
  width: 48px; height: 48px; border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #6b4eff);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: bold; color: #fff;
  flex-shrink: 0;
  border: 2px solid rgba(255,255,255,0.1);
}
.ticket-body { flex: 1; min-width: 0; }
.ticket-subject {
  font-size: 15px; font-weight: bold; color: #fff;
  margin-bottom: 4px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.ticket-meta {
  font-size: 11px; color: #94a3b8;
  font-family: monospace;
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
.ticket-meta .dot { opacity: 0.5; }
.ticket-last-msg {
  font-size: 12px; color: #cbd5e1;
  margin-top: 6px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  padding: 6px 10px; background: rgba(15,23,42,0.5);
  border-radius: 8px;
}
.ticket-status {
  padding: 6px 14px; border-radius: 10px;
  font-size: 11px; font-weight: 900;
  flex-shrink: 0;
}
.ticket-status.open {
  background: rgba(234,179,8,0.2); color: #fde68a;
  border: 1px solid rgba(234,179,8,0.4);
}
.ticket-status.answered {
  background: rgba(34,197,94,0.2); color: #4ade80;
  border: 1px solid rgba(34,197,94,0.4);
}
.ticket-status.closed {
  background: rgba(100,116,139,0.2); color: #cbd5e1;
  border: 1px solid rgba(100,116,139,0.4);
}
.ticket-arrow {
  font-size: 20px; color: #64748b;
  flex-shrink: 0;
  transition: 0.2s;
}
.ticket-item:hover .ticket-arrow { color: #c4b5fd; transform: translateX(-4px); }

.empty-state {
  text-align: center; padding: 60px 20px;
  background: #12121f; border: 1.5px dashed rgba(148,163,184,0.2);
  border-radius: 18px;
  color: #64748b;
}
.empty-state .icon { font-size: 64px; display: block; margin-bottom: 14px; opacity: 0.5; }
.empty-state h3 { font-size: 17px; color: #fff; margin-bottom: 8px; }
.empty-state p { font-size: 13px; line-height: 1.6; }
</style>
</head>
<body>
<div class="container">
  <div class="admin-sticky-header">
    <div class="topbar"><h1>💬 پشتیبانی — تیکت‌ها</h1></div>
    <div class="admin-tabs">
      <a href="/panel-admin/dashboard/" class="admin-tab {% if '/panel-admin/dashboard/' in request.path or request.path == '/panel-admin/' %}active{% endif %}">👥 کاربران</a>
      <a href="/panel-admin/alliances/" class="admin-tab {% if '/panel-admin/alliance' in request.path %}active{% endif %}">🛡️ اتحادها</a>
      <a href="/panel-admin/rooms/" class="admin-tab {% if '/panel-admin/room' in request.path %}active{% endif %}">🚪 اتاق‌ها</a>
      <a href="/panel-admin/announcements/" class="admin-tab {% if '/panel-admin/announcement' in request.path %}active{% endif %}">📢 اعلان‌ها</a>
      <a href="/panel-admin/tournaments/" class="admin-tab {% if '/panel-admin/tournament' in request.path %}active{% endif %}">🏆 تورنمنت</a>
      <a href="/panel-admin/shop/" class="admin-tab {% if '/panel-admin/shop/' in request.path %}active{% endif %}">🛒 فروشگاه</a>
      <a href="/panel-admin/support/" class="admin-tab {% if '/panel-admin/support' in request.path %}active{% endif %}">💬 پشتیبانی</a>
    </div>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <div class="stats-grid">
    <div class="stat-card open">
      <div class="stat-icon">⏳</div>
      <div class="stat-val">{{ count_open }}</div>
      <div class="stat-lbl">باز</div>
    </div>
    <div class="stat-card answered">
      <div class="stat-icon">✅</div>
      <div class="stat-val">{{ count_answered }}</div>
      <div class="stat-lbl">پاسخ داده</div>
    </div>
    <div class="stat-card closed">
      <div class="stat-icon">🔒</div>
      <div class="stat-val">{{ count_closed }}</div>
      <div class="stat-lbl">بسته</div>
    </div>
    <div class="stat-card total">
      <div class="stat-icon">📊</div>
      <div class="stat-val">{{ count_total }}</div>
      <div class="stat-lbl">کل</div>
    </div>
  </div>

  <div class="filter-row">
    <a href="?" class="filter-btn {% if not status_filter %}active{% endif %}">📋 همه ({{ count_total }})</a>
    <a href="?status=open" class="filter-btn {% if status_filter == 'open' %}active{% endif %}">⏳ باز ({{ count_open }})</a>
    <a href="?status=answered" class="filter-btn {% if status_filter == 'answered' %}active{% endif %}">✅ پاسخ داده ({{ count_answered }})</a>
    <a href="?status=closed" class="filter-btn {% if status_filter == 'closed' %}active{% endif %}">🔒 بسته ({{ count_closed }})</a>
  </div>

  {% if tickets %}
    <div class="tickets-list">
      {% for t in tickets %}
        <a href="/panel-admin/support/{{ t.id }}/" class="ticket-item status-{{ t.status }}">
          <div class="ticket-avatar">
            {% if t.avatar_id is not None %}{{ t.avatar_id }}{% else %}👤{% endif %}
          </div>
          <div class="ticket-body">
            <div class="ticket-subject">{{ t.subject }}</div>
            <div class="ticket-meta">
              <span>👤 {{ t.user_alias }}</span>
              <span class="dot">·</span>
              <span>@{{ t.username }}</span>
              <span class="dot">·</span>
              <span>🕐 {{ t.updated_at|jdate:"Y/m/d H:i" }}</span>
              <span class="dot">·</span>
              <span>💬 {{ t.message_count }} پیام</span>
            </div>
            {% if t.last_msg %}
              <div class="ticket-last-msg">💭 {{ t.last_msg }}</div>
            {% endif %}
          </div>
          <span class="ticket-status {{ t.status }}">{{ t.status_display }}</span>
          <span class="ticket-arrow">←</span>
        </a>
      {% endfor %}
    </div>
  {% else %}
    <div class="empty-state">
      <span class="icon">📭</span>
      <h3>هیچ تیکتی نیست</h3>
      <p>
        {% if status_filter %}
          با این فیلتر تیکتی پیدا نشد.
        {% else %}
          کاربران هنوز تیکتی ارسال نکرده‌اند.
        {% endif %}
      </p>
    </div>
  {% endif %}
</div>
</body>
</html>
'''

write("accounts/templates/custom_admin/support_tickets.html", TICKETS_HTML)
print("  ✓ support_tickets.html rebuilt (beautiful)")

# ============================================================
# 3) Rebuild support_ticket_detail.html — beautiful chat with close/delete
# ============================================================
print("\n[3/5] Rebuilding support_ticket_detail.html (with close/delete)")

DETAIL_HTML = '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>تیکت #{{ ticket.id }} — پشتیبانی</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 16px 16px 40px; }
.container { max-width: 1000px; margin: 0 auto; }

.topbar {
  display: flex; justify-content: space-between; align-items: center;
  background: linear-gradient(135deg, #1e1b4b, #0f0f1e);
  border: 1px solid rgba(139,92,246,0.4);
  padding: 16px 22px; border-radius: 16px; margin-bottom: 16px;
  flex-wrap: wrap; gap: 12px;
}
.topbar h1 { font-size: 18px; color: #c4b5fd; }
.topbar-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.topbar a, .topbar button {
  padding: 9px 16px; border-radius: 10px; text-decoration: none;
  font-size: 13px; font-weight: bold; color: #fff;
  border: none; cursor: pointer; font-family: inherit;
  display: inline-flex; align-items: center; gap: 6px;
}
.btn-back { background: rgba(148,163,184,0.2); }
.btn-back:hover { background: rgba(148,163,184,0.3); }
.btn-close { background: linear-gradient(135deg, #eab308, #d97706); }
.btn-close:hover { transform: translateY(-1px); }
.btn-reopen { background: linear-gradient(135deg, #22c55e, #16a34a); }
.btn-reopen:hover { transform: translateY(-1px); }
.btn-delete { background: linear-gradient(135deg, #ef4444, #dc2626); }
.btn-delete:hover { transform: translateY(-1px); }

.msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
.msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
.msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

/* ===== Ticket Header ===== */
.ticket-head {
  background: linear-gradient(135deg, #12121f, #1a1a2e);
  border: 1.5px solid rgba(139,92,246,0.3);
  border-radius: 18px;
  padding: 20px 22px;
  margin-bottom: 18px;
  display: flex; align-items: center; gap: 16px;
  flex-wrap: wrap;
}
.ticket-avatar {
  width: 60px; height: 60px; border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #6b4eff);
  display: flex; align-items: center; justify-content: center;
  font-size: 26px; font-weight: bold; color: #fff;
  flex-shrink: 0;
  border: 3px solid rgba(255,255,255,0.15);
}
.ticket-info { flex: 1; min-width: 200px; }
.ticket-subject {
  font-size: 20px; font-weight: 900; color: #fff;
  margin-bottom: 6px;
}
.ticket-user {
  font-size: 13px; color: #94a3b8;
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
.ticket-user .dot { opacity: 0.5; }
.ticket-status-badge {
  padding: 8px 18px; border-radius: 12px;
  font-size: 12px; font-weight: 900;
  white-space: nowrap;
}
.ticket-status-badge.open {
  background: rgba(234,179,8,0.2); color: #fde68a;
  border: 1.5px solid rgba(234,179,8,0.5);
}
.ticket-status-badge.answered {
  background: rgba(34,197,94,0.2); color: #4ade80;
  border: 1.5px solid rgba(34,197,94,0.5);
}
.ticket-status-badge.closed {
  background: rgba(100,116,139,0.2); color: #cbd5e1;
  border: 1.5px solid rgba(100,116,139,0.5);
}

/* ===== Chat ===== */
.chat-container {
  background: #12121f;
  border: 1px solid rgba(148,163,184,0.15);
  border-radius: 18px;
  overflow: hidden;
  margin-bottom: 16px;
}
.chat-body {
  padding: 20px;
  min-height: 350px;
  max-height: 55vh;
  overflow-y: auto;
  display: flex; flex-direction: column; gap: 14px;
}
.chat-body::-webkit-scrollbar { width: 6px; }
.chat-body::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.4); border-radius: 6px; }

.msg-bubble {
  max-width: 75%;
  padding: 14px 18px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  color: #fff;
  align-self: flex-start;
  position: relative;
  animation: fadeIn 0.3s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
.msg-bubble.user {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border: 1px solid #2563eb;
  align-self: flex-end;
  border-bottom-right-radius: 4px;
  box-shadow: 0 4px 15px rgba(59,130,246,0.25);
}
.msg-bubble.staff {
  background: linear-gradient(135deg, rgba(139,92,246,0.25), rgba(6,182,212,0.15));
  border: 1px solid rgba(139,92,246,0.4);
  border-bottom-left-radius: 4px;
  box-shadow: 0 4px 15px rgba(139,92,246,0.15);
}
.msg-bubble.system {
  background: rgba(100,116,139,0.15);
  border: 1px solid rgba(100,116,139,0.3);
  color: #cbd5e1;
  align-self: center;
  text-align: center;
  font-size: 12px;
  max-width: 90%;
}
.msg-sender {
  font-size: 11px; font-weight: bold;
  color: #c4b5fd;
  margin-bottom: 6px;
  display: flex; align-items: center; gap: 6px;
}
.msg-bubble.user .msg-sender { color: #bfdbfe; }
.msg-bubble.staff .msg-sender { color: #c4b5fd; }
.msg-sender .badge {
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 5px;
  background: rgba(255,255,255,0.15);
}
.msg-time {
  font-size: 10px; color: rgba(255,255,255,0.5);
  margin-top: 6px;
  font-family: monospace;
}

/* ===== Input ===== */
.chat-input-wrap {
  padding: 14px;
  background: rgba(10,10,21,0.5);
  border-top: 1px solid rgba(148,163,184,0.15);
}
.chat-input {
  display: flex; gap: 10px;
}
.chat-input input {
  flex: 1;
  padding: 14px 18px;
  border-radius: 12px;
  border: 1.5px solid rgba(148,163,184,0.2);
  background: #0a0a15;
  color: #fff;
  font-size: 14px;
  font-family: inherit;
}
.chat-input input:focus {
  outline: none;
  border-color: #8b5cf6;
  box-shadow: 0 0 15px rgba(139,92,246,0.2);
}
.chat-input button {
  padding: 14px 24px;
  border-radius: 12px;
  border: none;
  background: linear-gradient(135deg, #8b5cf6, #6b4eff);
  color: #fff;
  font-size: 14px;
  font-weight: 900;
  font-family: inherit;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(139,92,246,0.4);
  transition: 0.2s;
}
.chat-input button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(139,92,246,0.6);
}

.closed-notice {
  padding: 16px;
  background: rgba(100,116,139,0.1);
  border: 1px solid rgba(100,116,139,0.3);
  border-radius: 12px;
  text-align: center;
  color: #cbd5e1;
  font-size: 13px;
  line-height: 1.6;
}

/* ===== Action buttons (bottom) ===== */
.action-row {
  display: flex; gap: 12px; flex-wrap: wrap;
}
.action-row form { flex: 1; min-width: 140px; }
.action-row button {
  width: 100%;
  padding: 14px;
  border-radius: 14px;
  border: none;
  font-family: inherit;
  font-weight: 900;
  font-size: 14px;
  cursor: pointer;
  transition: 0.2s;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.action-row button:hover { transform: translateY(-2px); }
.btn-action-close {
  background: linear-gradient(135deg, #eab308, #d97706);
  color: #1a1a1a;
  box-shadow: 0 6px 20px rgba(234,179,8,0.3);
}
.btn-action-reopen {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: #fff;
  box-shadow: 0 6px 20px rgba(34,197,94,0.3);
}
.btn-action-delete {
  background: rgba(239,68,68,0.15);
  color: #fca5a5;
  border: 1.5px solid rgba(239,68,68,0.4);
}
.btn-action-delete:hover {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff;
}
</style>
</head>
<body>
<div class="container">

  <div class="topbar">
    <h1>💬 تیکت #{{ ticket.id }}</h1>
    <div class="topbar-actions">
      <a href="/panel-admin/support/" class="btn-back">← بازگشت</a>
      {% if ticket.status == "closed" %}
        <form method="post" style="display:inline;">
          {% csrf_token %}
          <input type="hidden" name="action" value="reopen">
          <button type="submit" class="btn-reopen">🔓 باز کردن</button>
        </form>
      {% else %}
        <form method="post" style="display:inline;">
          {% csrf_token %}
          <input type="hidden" name="action" value="close">
          <button type="submit" class="btn-close" onclick="return confirm('تیکت بسته شود؟');">🔒 بستن</button>
        </form>
      {% endif %}
      <form method="post" style="display:inline;" onsubmit="return confirm('آیا مطمئنی؟ این تیکت برای همیشه حذف می‌شود.');">
        {% csrf_token %}
        <input type="hidden" name="action" value="delete">
        <button type="submit" class="btn-delete">🗑️ حذف</button>
      </form>
    </div>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <div class="ticket-head">
    <div class="ticket-avatar">
      {% if ticket.user.avatar_id is not None %}{{ ticket.user.avatar_id }}{% else %}👤{% endif %}
    </div>
    <div class="ticket-info">
      <div class="ticket-subject">{{ ticket.subject }}</div>
      <div class="ticket-user">
        <span>👤 {{ ticket.user.alias|default:ticket.user.username }}</span>
        <span class="dot">·</span>
        <span>@{{ ticket.user.username }}</span>
        <span class="dot">·</span>
        <span>🕐 {{ ticket.created_at|jdate:"Y/m/d H:i" }}</span>
        <span class="dot">·</span>
        <span>💬 {{ ticket.message_count }} پیام</span>
      </div>
    </div>
    <div class="ticket-status-badge {{ ticket.status }}">{{ ticket.get_status_display }}</div>
  </div>

  <div class="chat-container">
    <div class="chat-body" id="chatBody">
      {% for m in ticket_messages %}
        <div class="msg-bubble {% if m.is_staff %}staff{% else %}user{% endif %}">
          <div class="msg-sender">
            {% if m.is_staff %}🛡️ {{ m.sender_alias }} <span class="badge">پشتیبانی</span>{% else %}👤 {{ m.sender_alias }}{% endif %}
          </div>
          {{ m.body }}
          <div class="msg-time">{{ m.created_at|jdate:"Y/m/d H:i" }}</div>
        </div>
      {% empty %}
        <div class="msg-bubble system">
          هنوز پیامی در این تیکت نیست.
        </div>
      {% endfor %}
    </div>

    <div class="chat-input-wrap">
      {% if ticket.status == "closed" %}
        <div class="closed-notice">
          🔒 این تیکت بسته شده است.<br>
          برای پاسخ دادن، ابتدا آن را باز کنید.
        </div>
      {% else %}
        <form method="post" class="chat-input">
          {% csrf_token %}
          <input type="hidden" name="action" value="reply">
          <input type="text" name="body" required maxlength="2000" placeholder="پاسخ خود را بنویسید..." autocomplete="off" autofocus>
          <button type="submit">📤 ارسال</button>
        </form>
      {% endif %}
    </div>
  </div>

  <div class="action-row">
    {% if ticket.status == "closed" %}
      <form method="post">
        {% csrf_token %}
        <input type="hidden" name="action" value="reopen">
        <button type="submit" class="btn-action-reopen">🔓 باز کردن مجدد</button>
      </form>
    {% else %}
      <form method="post">
        {% csrf_token %}
        <input type="hidden" name="action" value="close">
        <button type="submit" class="btn-action-close" onclick="return confirm('تیکت بسته شود؟ کاربر دیگر نمی‌تواند پیام بفرستد.');">🔒 بستن تیکت</button>
      </form>
    {% endif %}
    <form method="post" onsubmit="return confirm('آیا مطمئنی؟ این تیکت و همه پیام‌هایش برای همیشه حذف می‌شود.');">
      {% csrf_token %}
      <input type="hidden" name="action" value="delete">
      <button type="submit" class="btn-action-delete">🗑️ حذف کامل تیکت</button>
    </form>
  </div>

</div>

<script>
const b = document.getElementById('chatBody');
if (b) b.scrollTop = b.scrollHeight;
</script>
</body>
</html>
'''

write("accounts/templates/custom_admin/support_ticket_detail.html", DETAIL_HTML)
print("  ✓ support_ticket_detail.html rebuilt (beautiful with close/delete)")

# ============================================================
# 4) Add support tab to all admin pages
# ============================================================
print("\n[4/5] Adding support tab to all admin templates")

admin_pages = [
    "dashboard.html", "alliances.html", "alliance_detail.html",
    "rooms.html", "announcements.html", "tournaments.html",
    "tournament_edit.html", "shop_items.html",
    "user_detail.html", "user_edit.html", "user_notify.html",
]

for fname in admin_pages:
    path = f"accounts/templates/custom_admin/{fname}"
    if not os.path.exists(path): continue
    src = read(path)
    
    if "/panel-admin/support/" in src:
        print(f"  ⏭ {fname} already has support tab")
        continue
    
    # Find last admin-tab and add support after it
    old = '    <a href="/panel-admin/shop/" class="admin-tab {% if \'/panel-admin/shop/\' in request.path %}active{% endif %}">🛒 فروشگاه</a>'
    new = old + '''
    <a href="/panel-admin/support/" class="admin-tab {% if '/panel-admin/support' in request.path %}active{% endif %}">💬 پشتیبانی</a>'''
    
    if old in src:
        src = src.replace(old, new, 1)
        write(path, src)
        print(f"  ✓ Support tab added to {fname}")
    else:
        # Try alternate
        old2 = '<a href="/panel-admin/shop/" class="admin-tab'
        if old2 in src:
            idx = src.find(old2)
            end = src.find("</a>", idx) + 4
            insert = '\n    <a href="/panel-admin/support/" class="admin-tab {% if \'/panel-admin/support\' in request.path %}active{% endif %}">💬 پشتیبانی</a>'
            src = src[:end] + insert + src[end:]
            write(path, src)
            print(f"  ✓ Support tab added to {fname} (fallback)")

# ============================================================
# 5) Test
# ============================================================
print("\n[5/5] Django check + test")

r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:600]}")

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from accounts.models import SupportTicket, SupportMessage
User = get_user_model()

# Create test ticket
tu, created = User.objects.get_or_create(
    username="__support_test_admin__",
    defaults={"alias": "sup-test", "is_active": True, "has_chosen_avatar": True, "has_completed_registration": True}
)
if created:
    tu.set_password("x")
    tu.save()

test_ticket = SupportTicket.objects.create(user=tu, subject="__test_subject__", status="open")
SupportMessage.objects.create(ticket=test_ticket, sender=tu, body="test message", is_staff=False)

# Admin client
c = Client()
c.session["custom_admin_logged_in"] = True
c.session["beta_unlocked"] = True
c.session.save()

print("\n  Testing admin support pages:")
r = c.get("/panel-admin/support/", follow=False)
print(f"    ✓ List: {r.status_code}" if r.status_code == 200 else f"    ✗ List: {r.status_code}")

r = c.get(f"/panel-admin/support/{test_ticket.id}/", follow=False)
print(f"    ✓ Detail: {r.status_code}" if r.status_code == 200 else f"    ✗ Detail: {r.status_code}")

# Test reply
r = c.post(f"/panel-admin/support/{test_ticket.id}/", {"action": "reply", "body": "پاسخ ادمین"}, follow=False)
print(f"    ✓ Reply: {r.status_code}" if r.status_code == 302 else f"    ✗ Reply: {r.status_code}")

# Test close
r = c.post(f"/panel-admin/support/{test_ticket.id}/", {"action": "close"}, follow=False)
test_ticket.refresh_from_db()
print(f"    ✓ Close: status={test_ticket.status}" if test_ticket.status == "closed" else f"    ✗ Close: status={test_ticket.status}")

# Test reopen
r = c.post(f"/panel-admin/support/{test_ticket.id}/", {"action": "reopen"}, follow=False)
test_ticket.refresh_from_db()
print(f"    ✓ Reopen: status={test_ticket.status}" if test_ticket.status == "open" else f"    ✗ Reopen: status={test_ticket.status}")

# Test delete
r = c.post(f"/panel-admin/support/{test_ticket.id}/", {"action": "delete"}, follow=False)
exists = SupportTicket.objects.filter(id=test_ticket.id).exists()
print(f"    ✓ Delete: removed={not exists}" if not exists else f"    ✗ Delete: still exists")

# Cleanup
if created:
    tu.delete()

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
What was rebuilt:

  1. ✅ Admin views verified (or rebuilt if missing)
     - support_tickets_list
     - support_ticket_admin (reply/close/reopen/delete)

  2. ✅ support_tickets.html — beautiful ticket list:
     - 4 stat cards (open/answered/closed/total) with color
     - Filter buttons (all/open/answered/closed)
     - Each ticket shows:
       - Avatar + user alias + @username
       - Subject
       - Last message preview
       - Time + message count
       - Status badge (colored)
       - Colored left border by status
     - Hover: lift + purple shadow + arrow slides
     - Empty state with icon

  3. ✅ support_ticket_detail.html — beautiful chat:
     - Header with avatar, subject, user, status
     - Chat bubbles:
       - User = blue (right aligned)
       - Staff = purple (left aligned)
       - System = gray (centered)
     - Input box below chat
     - If closed: shows "closed notice" instead of input
     - Bottom action buttons:
       - 🔒 بستن (if open) OR 🔓 باز کردن (if closed)
       - 🗑️ حذف کامل (with confirmation)
     - Top bar also has close/reopen/delete buttons

  4. ✅ Support tab added to all admin pages
     💬 پشتیبانی — always in tab bar

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R

Test:
  1. /panel-admin/support/ → see beautiful list of tickets
  2. Click any ticket → see chat
  3. Click 🔒 بستن → ticket closes (input disappears)
  4. Click 🔓 باز کردن → reopens (input comes back)
  5. Click 🗑️ حذف → confirms then deletes
  6. Filter buttons work: همه / باز / پاسخ داده / بسته
""")
