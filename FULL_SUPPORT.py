#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess, re

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def read(p):
    try:
        with open(p, "r", encoding="utf-8") as f: return f.read()
    except: return ""
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) SUPPORT APP
# ============================================================
print("\n[1/8] Support app")
os.makedirs("support", exist_ok=True)
write("support/__init__.py", "")
write("support/apps.py", '''from django.apps import AppConfig


class SupportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "support"
''')

write("support/models.py", '''# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models


class SupportTicket(models.Model):
    STATUS = [
        ("open", "باز"),
        ("in_progress", "در حال بررسی"),
        ("answered", "پاسخ داده شده"),
        ("closed", "بسته شده"),
    ]
    PRIORITY = [
        ("low", "کم"),
        ("normal", "معمولی"),
        ("high", "فوری"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_tickets")
    subject = models.CharField(max_length=100)
    body = models.TextField(max_length=2000)
    category = models.CharField(max_length=20, default="general")  # general, bug, idea, payment
    status = models.CharField(max_length=15, choices=STATUS, default="open")
    priority = models.CharField(max_length=10, choices=PRIORITY, default="normal")
    admin_reply = models.TextField(blank=True, default="")
    replied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"#{self.id} - {self.subject[:30]}"

    def status_display(self):
        return dict(self.STATUS).get(self.status, self.status)
''')

write("support/views.py", '''# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import SupportTicket


@login_required
def support_home(request):
    if not getattr(request.user, "has_chosen_avatar", False):
        return redirect("accounts:avatar_select")

    # Submit new ticket
    if request.method == "POST":
        subject = (request.POST.get("subject") or "").strip()[:100]
        body = (request.POST.get("body") or "").strip()[:2000]
        category = request.POST.get("category", "general")

        if not subject or len(subject) < 3:
            messages.error(request, "موضوع باید حداقل ۳ حرف باشد.")
        elif not body or len(body) < 10:
            messages.error(request, "متن پیام باید حداقل ۱۰ حرف باشد.")
        else:
            ticket = SupportTicket.objects.create(
                user=request.user,
                subject=subject,
                body=body,
                category=category if category in ("general","bug","idea","payment") else "general",
            )
            messages.success(request, f"✅ تیکت #{ticket.id} ثبت شد. به زودی پاسخ می‌دیم.")
            return redirect("support:home")

    my_tickets = SupportTicket.objects.filter(user=request.user)[:20]

    return render(request, "support/home.html", {
        "tickets": my_tickets,
        "active": "home",
    })


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    return render(request, "support/ticket.html", {
        "ticket": ticket,
        "active": "home",
    })


@login_required
def ticket_close(request, ticket_id):
    if request.method != "POST":
        return redirect("support:home")
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    if ticket.status != "closed":
        ticket.status = "closed"
        ticket.save(update_fields=["status"])
        messages.success(request, f"تیکت #{ticket.id} بسته شد.")
    return redirect("support:home")
''')

write("support/urls.py", '''from django.urls import path
from . import views

app_name = "support"

urlpatterns = [
    path("", views.support_home, name="home"),
    path("<int:ticket_id>/", views.ticket_detail, name="ticket"),
    path("<int:ticket_id>/close/", views.ticket_close, name="close"),
]
''')

# Register in settings
print("\n[1b/8] Add support to INSTALLED_APPS")
p = "config/settings.py"
src = read(p)
if '"support"' not in src:
    src = src.replace(
        '"social",',
        '"social",\n    "support",',
        1
    )
    write(p, src)
    print("  ✓ support added to INSTALLED_APPS")
else:
    print("  ✓ already added")

# Add URL
print("\n[1c/8] Add support URL")
p = "config/urls.py"
src = read(p)
if "support.urls" not in src:
    src = src.replace(
        '    path("alliance/", include("alliance.urls")),',
        '    path("alliance/", include("alliance.urls")),\n    path("support/", include("support.urls")),',
        1
    )
    write(p, src)
    print("  ✓ support URL added")

# ============================================================
# 2) SUPPORT TEMPLATES
# ============================================================
print("\n[2/8] Support templates")
write("support/templates/support/home.html", '''{% extends "base.html" %}
{% block title %}پشتیبانی{% endblock %}
{% block extra_css %}
<style>
  .head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
  .head h1 { font-size: 22px; font-weight: 900; color: var(--gold); }

  .hero {
    background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.35), transparent 60%),
                linear-gradient(135deg, #0a1e2a, #0f0f1e);
    border: 2px solid rgba(6,182,212,0.5);
    border-radius: 22px;
    padding: 24px 20px;
    margin-bottom: 20px;
    text-align: center;
  }
  .hero .icon { font-size: 56px; margin-bottom: 10px; filter: drop-shadow(0 0 20px rgba(6,182,212,0.6)); }
  .hero h2 { font-size: 20px; font-weight: 900; background: linear-gradient(135deg, #67e8f9, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 6px; }
  .hero p { color: var(--muted); font-size: 13px; line-height: 1.6; }

  .form-box { background: var(--card); border: 1.5px solid var(--border); border-radius: 18px; padding: 20px; margin-bottom: 20px; }
  .form-box h3 { font-size: 15px; color: #67e8f9; margin-bottom: 14px; }
  label { display: block; color: var(--muted); font-size: 12px; margin: 12px 0 6px; font-weight: bold; }
  input[type=text], textarea, select { width: 100%; padding: 12px 14px; border-radius: 10px; border: 1.5px solid var(--border); background: var(--bg); color: var(--text); font-size: 14px; font-family: inherit; box-sizing: border-box; }
  textarea { resize: vertical; min-height: 100px; }
  input:focus, textarea:focus, select:focus { outline: none; border-color: #06b6d4; }
  button.submit { width: 100%; margin-top: 16px; padding: 14px; border: none; border-radius: 12px; background: linear-gradient(135deg, #06b6d4, #3b82f6); color: #fff; font-size: 15px; font-weight: 900; font-family: inherit; cursor: pointer; box-shadow: 0 8px 20px rgba(6,182,212,0.4); }

  .my-tickets { margin-top: 24px; }
  .my-tickets h3 { font-size: 15px; color: var(--gold); margin-bottom: 12px; }

  .ticket-card { display: flex; align-items: flex-start; gap: 12px; padding: 14px; background: var(--card); border: 1.5px solid var(--border); border-radius: 14px; margin-bottom: 8px; text-decoration: none; color: var(--text); transition: 0.2s; }
  .ticket-card:hover { border-color: #06b6d4; transform: translateX(-3px); }
  .ticket-card .icon { font-size: 28px; flex-shrink: 0; }
  .ticket-card .info { flex: 1; min-width: 0; }
  .ticket-card .title { font-size: 14px; font-weight: bold; margin-bottom: 4px; }
  .ticket-card .meta { font-size: 11px; color: var(--muted); }
  .ticket-card .badge { font-size: 10px; padding: 3px 10px; border-radius: 8px; font-weight: bold; flex-shrink: 0; }
  .badge-open { background: rgba(234,179,8,0.2); color: #fde68a; }
  .badge-answered { background: rgba(34,197,94,0.2); color: #86efac; }
  .badge-closed { background: rgba(100,116,139,0.2); color: #cbd5e1; }
  .badge-in_progress { background: rgba(59,130,246,0.2); color: #93c5fd; }

  .flash { padding: 12px 16px; border-radius: 12px; margin-bottom: 12px; font-size: 13px; }
  .flash-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
  .flash-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }

  .empty { text-align: center; padding: 40px 20px; background: var(--card); border: 1px dashed var(--border); border-radius: 14px; color: var(--muted); font-size: 13px; }
  .empty .em { font-size: 50px; display: block; margin-bottom: 10px; opacity: 0.5; }
</style>
{% endblock %}
{% block content %}
  <div class="head">
    <a href="/game/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>💬 پشتیبانی</h1>
  </div>

  {% if messages %}
    {% for m in messages %}<div class="flash flash-{{ m.tags }}">{{ m }}</div>{% endfor %}
  {% endif %}

  <div class="hero">
    <div class="icon">💬</div>
    <h2>چطور می‌تونیم کمکت کنیم؟</h2>
    <p>سوال، مشکل یا پیشنهادی داری؟ یه پیام بفرست.<br>تیم پشتیبانی در اسرع وقت جواب می‌ده.</p>
  </div>

  <div class="form-box">
    <h3>📝 ارسال پیام جدید</h3>
    <form method="post">
      {% csrf_token %}
      <label>موضوع</label>
      <input type="text" name="subject" required maxlength="100" placeholder="مثلاً: باگ در بازی گروهی">

      <label>دسته‌بندی</label>
      <select name="category">
        <option value="general">سوال عمومی</option>
        <option value="bug">باگ یا مشکل</option>
        <option value="idea">پیشنهاد و ایده</option>
        <option value="payment">پرداخت و اشتراک</option>
      </select>

      <label>متن پیام</label>
      <textarea name="body" required maxlength="2000" placeholder="مشکل یا سوال خود را با جزئیات بنویسید..."></textarea>

      <button type="submit" class="submit">📤 ارسال</button>
    </form>
  </div>

  {% if tickets %}
    <div class="my-tickets">
      <h3>📜 تیکت‌های من</h3>
      {% for t in tickets %}
        <a href="/support/{{ t.id }}/" class="ticket-card">
          <div class="icon">
            {% if t.category == 'bug' %}🐛
            {% elif t.category == 'idea' %}💡
            {% elif t.category == 'payment' %}💳
            {% else %}📝{% endif %}
          </div>
          <div class="info">
            <div class="title">{{ t.subject }}</div>
            <div class="meta">#{{ t.id }} · {{ t.created_at|date:"Y/m/d H:i" }}</div>
          </div>
          <span class="badge badge-{{ t.status }}">{{ t.status_display }}</span>
        </a>
      {% endfor %}
    </div>
  {% endif %}
{% endblock %}
''')

write("support/templates/support/ticket.html", '''{% extends "base.html" %}
{% block title %}تیکت #{{ ticket.id }}{% endblock %}
{% block extra_css %}
<style>
  .head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
  .head h1 { font-size: 20px; font-weight: 900; color: var(--gold); }

  .ticket-box { background: var(--card); border: 1.5px solid var(--border); border-radius: 18px; padding: 20px; margin-bottom: 16px; }
  .t-header { display: flex; align-items: flex-start; gap: 14px; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid var(--border); }
  .t-icon { font-size: 36px; flex-shrink: 0; }
  .t-info { flex: 1; }
  .t-title { font-size: 18px; font-weight: 900; margin-bottom: 4px; }
  .t-meta { font-size: 11px; color: var(--muted); }
  .t-badge { font-size: 10px; padding: 4px 12px; border-radius: 8px; font-weight: bold; flex-shrink: 0; }
  .badge-open { background: rgba(234,179,8,0.2); color: #fde68a; }
  .badge-answered { background: rgba(34,197,94,0.2); color: #86efac; }
  .badge-closed { background: rgba(100,116,139,0.2); color: #cbd5e1; }
  .badge-in_progress { background: rgba(59,130,246,0.2); color: #93c5fd; }

  .t-body { padding: 16px; background: rgba(15,23,42,0.5); border-radius: 12px; font-size: 14px; line-height: 1.8; white-space: pre-wrap; }

  .reply-box { margin-top: 18px; padding: 18px; background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(6,182,212,0.08)); border: 1.5px solid rgba(34,197,94,0.4); border-radius: 14px; }
  .reply-box h3 { font-size: 14px; color: #86efac; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }
  .reply-body { font-size: 14px; line-height: 1.8; color: #fff; white-space: pre-wrap; padding: 12px; background: rgba(15,23,42,0.5); border-radius: 10px; }
  .reply-time { font-size: 10px; color: #94a3b8; margin-top: 8px; font-family: monospace; }

  .no-reply { text-align: center; padding: 20px; background: rgba(234,179,8,0.08); border: 1px dashed rgba(234,179,8,0.3); border-radius: 12px; color: #fde68a; font-size: 13px; margin-top: 16px; }

  .actions { display: flex; gap: 10px; margin-top: 20px; }
  .actions a, .actions button { flex: 1; padding: 12px; border-radius: 12px; border: none; font-family: inherit; font-weight: 900; font-size: 14px; cursor: pointer; text-decoration: none; text-align: center; }
  .btn-back { background: rgba(148,163,184,0.2); color: #fff; }
  .btn-close { background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4) !important; }
</style>
{% endblock %}
{% block content %}
  <div class="head">
    <a href="/support/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>تیکت #{{ ticket.id }}</h1>
  </div>

  <div class="ticket-box">
    <div class="t-header">
      <div class="t-icon">
        {% if ticket.category == 'bug' %}🐛
        {% elif ticket.category == 'idea' %}💡
        {% elif ticket.category == 'payment' %}💳
        {% else %}📝{% endif %}
      </div>
      <div class="t-info">
        <div class="t-title">{{ ticket.subject }}</div>
        <div class="t-meta">{{ ticket.created_at|date:"Y/m/d H:i" }}</div>
      </div>
      <span class="t-badge badge-{{ ticket.status }}">{{ ticket.status_display }}</span>
    </div>

    <div class="t-body">{{ ticket.body }}</div>

    {% if ticket.admin_reply %}
      <div class="reply-box">
        <h3>💬 پاسخ پشتیبانی</h3>
        <div class="reply-body">{{ ticket.admin_reply }}</div>
        <div class="reply-time">📅 {{ ticket.replied_at|date:"Y/m/d H:i" }}</div>
      </div>
    {% elif ticket.status != "closed" %}
      <div class="no-reply">⏳ در انتظار پاسخ تیم پشتیبانی...</div>
    {% endif %}

    <div class="actions">
      <a href="/support/" class="btn-back">← بازگشت</a>
      {% if ticket.status != "closed" %}
        <form method="post" action="/support/{{ ticket.id }}/close/" style="display:contents;" onsubmit="return confirm('بستن این تیکت؟');">
          {% csrf_token %}
          <button type="submit" class="btn-close">✕ بستن تیکت</button>
        </form>
      {% endif %}
    </div>
  </div>
{% endblock %}
''')

# ============================================================
# 3) ADMIN — SUPPORT VIEWS
# ============================================================
print("\n[3/8] Admin support views")
p = "accounts/admin_views.py"
src = read(p)

if "def support_list" not in src:
    ADMIN_SUPPORT = '''

# ============================================================
# Admin — Support Tickets
# ============================================================
@never_cache
def support_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    from support.models import SupportTicket

    status_filter = request.GET.get("status", "")
    q = (request.GET.get("q") or "").strip()

    qs = SupportTicket.objects.all().select_related("user").order_by("-created_at")
    if status_filter in ("open", "in_progress", "answered", "closed"):
        qs = qs.filter(status=status_filter)
    if q:
        from django.db.models import Q
        qs = qs.filter(Q(subject__icontains=q) | Q(user__alias__icontains=q) | Q(user__username__icontains=q))

    tickets = qs[:100]
    from accounts.avatars import get_emoji
    data = []
    for t in tickets:
        data.append({
            "id": t.id,
            "subject": t.subject,
            "user_alias": t.user.alias,
            "user_username": t.user.username,
            "avatar": get_emoji(t.user.avatar_id),
            "category": t.category,
            "status": t.status,
            "status_display": t.status_display(),
            "priority": t.priority,
            "created_at": t.created_at,
            "has_reply": bool(t.admin_reply),
        })

    # counts
    from django.db.models import Count
    counts = SupportTicket.objects.values("status").annotate(c=Count("id"))
    status_counts = {x["status"]: x["c"] for x in counts}

    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/support_list.html", {
        "tickets": data,
        "status_filter": status_filter,
        "search": q,
        "status_counts": status_counts,
        "message": message,
    })


@never_cache
def support_detail(request, ticket_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    from support.models import SupportTicket
    try:
        t = SupportTicket.objects.get(id=ticket_id)
    except SupportTicket.DoesNotExist:
        return redirect("custom_admin:support_list")

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "reply":
            reply = (request.POST.get("admin_reply") or "").strip()[:5000]
            new_status = request.POST.get("new_status", "answered")
            if new_status not in ("open", "in_progress", "answered", "closed"):
                new_status = "answered"
            if reply:
                from django.utils import timezone
                t.admin_reply = reply
                t.replied_at = timezone.now()
                t.status = new_status
                t.save(update_fields=["admin_reply", "replied_at", "status"])
                # Notify user
                try:
                    from social.notifications import notify
                    notify(
                        user=t.user,
                        ntype="message",
                        title=f"پاسخ به تیکت #{t.id}",
                        body=f"تیکت «{t.subject[:40]}» پاسخ داده شد.",
                        url=f"/support/{t.id}/",
                    )
                except Exception:
                    pass
                request.session["admin_message"] = {"type": "success", "text": "پاسخ ارسال شد."}
            return redirect("custom_admin:support_detail", ticket_id=t.id)

        elif action == "status":
            ns = request.POST.get("new_status", "open")
            if ns in ("open", "in_progress", "answered", "closed"):
                t.status = ns
                t.save(update_fields=["status"])
                request.session["admin_message"] = {"type": "success", "text": f"وضعیت: {t.status_display()}"}
            return redirect("custom_admin:support_detail", ticket_id=t.id)

        elif action == "delete":
            t.delete()
            request.session["admin_message"] = {"type": "success", "text": "تیکت حذف شد."}
            return redirect("custom_admin:support_list")

    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/support_detail.html", {
        "t": t,
        "message": message,
    })
'''
    src = src.rstrip() + ADMIN_SUPPORT + "\n"
    write(p, src)
    print("  ✓ support admin views added")

# Routes
p = "accounts/admin_urls.py"
src = read(p)
if "support_list" not in src:
    anchor = '    path("shop/", admin_views.shop_items_list, name="shop_items_list"),'
    if anchor in src:
        src = src.replace(
            anchor,
            anchor + '\n    path("support/", admin_views.support_list, name="support_list"),\n    path("support/<int:ticket_id>/", admin_views.support_detail, name="support_detail"),'
        )
    else:
        src = src.rsplit("]", 1)[0] + '    path("support/", admin_views.support_list, name="support_list"),\n    path("support/<int:ticket_id>/", admin_views.support_detail, name="support_detail"),\n]'
    write(p, src)
    print("  ✓ support admin routes added")

# Admin templates
write("accounts/templates/custom_admin/support_list.html", '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>پشتیبانی — پنل ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 1300px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; }
    .topbar h1 { font-size: 20px; color: #fca5a5; }
    .topbar a { padding: 9px 16px; border-radius: 10px; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold; }
    .admin-tabs { display: flex; gap: 6px; margin-bottom: 20px; background: #12121f; border: 1px solid rgba(148,163,184,0.15); padding: 6px; border-radius: 14px; overflow-x: auto; }
    .admin-tab { flex: 1; min-width: 100px; padding: 12px 14px; border-radius: 10px; text-align: center; text-decoration: none; font-size: 12px; font-weight: bold; color: #94a3b8; transition: 0.2s; white-space: nowrap; }
    .admin-tab:hover { background: rgba(148,163,184,0.1); color: #fff; }
    .admin-tab.active { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; }
    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }

    .stats-row { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
    .stat-chip { flex: 1; min-width: 120px; padding: 14px 16px; border-radius: 14px; text-align: center; border: 1.5px solid; }
    .stat-chip.open { background: rgba(234,179,8,0.1); border-color: rgba(234,179,8,0.4); }
    .stat-chip.in_progress { background: rgba(59,130,246,0.1); border-color: rgba(59,130,246,0.4); }
    .stat-chip.answered { background: rgba(34,197,94,0.1); border-color: rgba(34,197,94,0.4); }
    .stat-chip.closed { background: rgba(100,116,139,0.1); border-color: rgba(100,116,139,0.4); }
    .stat-chip .l { font-size: 11px; color: #94a3b8; margin-bottom: 4px; }
    .stat-chip .v { font-size: 22px; font-weight: 900; color: #fff; font-family: monospace; }

    .filter-row { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
    .filter-row input, .filter-row select { padding: 12px 16px; border-radius: 12px; border: 1px solid rgba(148,163,184,0.2); background: #1a1a2e; color: #fff; font-size: 14px; font-family: inherit; }
    .filter-row input { flex: 1; min-width: 200px; }
    .filter-row button { padding: 12px 22px; border-radius: 12px; border: none; background: linear-gradient(135deg, #facc15, #eab308); color: #1a1a1a; font-weight: bold; font-size: 14px; font-family: inherit; cursor: pointer; }

    .ticket-row { display: flex; align-items: center; gap: 14px; padding: 16px; background: #12121f; border: 1.5px solid rgba(148,163,184,0.15); border-radius: 14px; margin-bottom: 10px; text-decoration: none; color: inherit; transition: 0.2s; }
    .ticket-row:hover { border-color: #06b6d4; transform: translateX(-3px); }
    .ticket-row .av { font-size: 28px; width: 48px; height: 48px; border-radius: 50%; background: rgba(139,92,246,0.2); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .ticket-row .info { flex: 1; min-width: 0; }
    .ticket-row .title { font-size: 14px; font-weight: bold; color: #fff; margin-bottom: 3px; }
    .ticket-row .meta { font-size: 11px; color: #94a3b8; }
    .ticket-row .badge { font-size: 10px; padding: 4px 12px; border-radius: 8px; font-weight: bold; flex-shrink: 0; }
    .badge-open { background: rgba(234,179,8,0.2); color: #fde68a; }
    .badge-answered { background: rgba(34,197,94,0.2); color: #86efac; }
    .badge-closed { background: rgba(100,116,139,0.2); color: #cbd5e1; }
    .badge-in_progress { background: rgba(59,130,246,0.2); color: #93c5fd; }
    .cat-icon { font-size: 22px; flex-shrink: 0; }

    .empty { text-align: center; padding: 60px 20px; color: #64748b; }
    .empty .icon { font-size: 60px; display: block; margin-bottom: 12px; opacity: 0.5; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>💬 پشتیبانی</h1>
    <a href="{% url 'custom_admin:logout' %}">خروج</a>
  </div>

  <div class="admin-tabs">
    <a href="/panel-admin/dashboard/" class="admin-tab">👥 کاربران</a>
    <a href="/panel-admin/alliances/" class="admin-tab">🛡️ اتحادها</a>
    <a href="/panel-admin/rooms/" class="admin-tab">🚪 اتاق‌ها</a>
    <a href="/panel-admin/rooms/active/" class="admin-tab">🎮 در حال بازی</a>
    <a href="/panel-admin/announcements/" class="admin-tab">📢 اعلان‌ها</a>
    <a href="/panel-admin/tournaments/" class="admin-tab">🏆 تورنمنت‌ها</a>
    <a href="/panel-admin/support/" class="admin-tab active">💬 پشتیبانی</a>
  </div>

  {% if message %}<div class="msg msg-success">{{ message.text }}</div>{% endif %}

  <div class="stats-row">
    <div class="stat-chip open"><div class="l">باز</div><div class="v">{{ status_counts.open|default:0 }}</div></div>
    <div class="stat-chip in_progress"><div class="l">در حال بررسی</div><div class="v">{{ status_counts.in_progress|default:0 }}</div></div>
    <div class="stat-chip answered"><div class="l">پاسخ داده شده</div><div class="v">{{ status_counts.answered|default:0 }}</div></div>
    <div class="stat-chip closed"><div class="l">بسته</div><div class="v">{{ status_counts.closed|default:0 }}</div></div>
  </div>

  <form method="get" class="filter-row">
    <input type="text" name="q" value="{{ search }}" placeholder="جستجو با موضوع یا نام کاربری...">
    <select name="status">
      <option value="">همه وضعیت‌ها</option>
      <option value="open" {% if status_filter == "open" %}selected{% endif %}>باز</option>
      <option value="in_progress" {% if status_filter == "in_progress" %}selected{% endif %}>در حال بررسی</option>
      <option value="answered" {% if status_filter == "answered" %}selected{% endif %}>پاسخ داده شده</option>
      <option value="closed" {% if status_filter == "closed" %}selected{% endif %}>بسته</option>
    </select>
    <button type="submit">🔍 فیلتر</button>
  </form>

  {% if tickets %}
    {% for t in tickets %}
      <a href="/panel-admin/support/{{ t.id }}/" class="ticket-row">
        <div class="av">{{ t.avatar }}</div>
        <div class="cat-icon">
          {% if t.category == 'bug' %}🐛
          {% elif t.category == 'idea' %}💡
          {% elif t.category == 'payment' %}💳
          {% else %}📝{% endif %}
        </div>
        <div class="info">
          <div class="title">#{{ t.id }} — {{ t.subject }}</div>
          <div class="meta">👤 {{ t.user_alias }} (@{{ t.user_username }}) · {{ t.created_at|jdate:"Y/m/d H:i" }}</div>
        </div>
        <span class="badge badge-{{ t.status }}">{{ t.status_display }}</span>
      </a>
    {% endfor %}
  {% else %}
    <div class="empty">
      <span class="icon">📭</span>
      هیچ تیکتی وجود ندارد
    </div>
  {% endif %}
</div>
</body>
</html>
''')

write("accounts/templates/custom_admin/support_detail.html", '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>تیکت #{{ t.id }}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 900px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
    .topbar h1 { font-size: 19px; color: #fca5a5; }
    .topbar .actions { display: flex; gap: 8px; }
    .topbar a { padding: 9px 16px; border-radius: 10px; text-decoration: none; font-size: 13px; font-weight: bold; color: #fff; }
    .btn-back { background: rgba(148,163,184,0.2); }
    .btn-logout { background: linear-gradient(135deg, #ef4444, #dc2626); }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }

    .card { background: #12121f; border: 1px solid rgba(148,163,184,0.15); border-radius: 16px; padding: 22px; margin-bottom: 16px; }
    .card h3 { color: #fdba74; font-size: 15px; margin-bottom: 16px; }

    .ticket-header { display: flex; align-items: flex-start; gap: 16px; margin-bottom: 18px; padding-bottom: 16px; border-bottom: 1px solid rgba(148,163,184,0.15); }
    .ticket-icon { font-size: 44px; flex-shrink: 0; }
    .ticket-info { flex: 1; }
    .ticket-title { font-size: 19px; font-weight: 900; color: #fff; margin-bottom: 4px; }
    .ticket-meta { font-size: 12px; color: #94a3b8; }
    .ticket-badge { font-size: 11px; padding: 5px 14px; border-radius: 8px; font-weight: bold; flex-shrink: 0; }
    .badge-open { background: rgba(234,179,8,0.2); color: #fde68a; }
    .badge-answered { background: rgba(34,197,94,0.2); color: #86efac; }
    .badge-closed { background: rgba(100,116,139,0.2); color: #cbd5e1; }
    .badge-in_progress { background: rgba(59,130,246,0.2); color: #93c5fd; }

    .ticket-body { padding: 16px; background: rgba(15,23,42,0.6); border-radius: 12px; font-size: 14px; line-height: 1.9; white-space: pre-wrap; color: #fff; }

    label { display: block; color: #94a3b8; font-size: 12px; margin: 12px 0 6px; font-weight: bold; }
    textarea, select { width: 100%; padding: 12px 14px; border-radius: 10px; border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15; color: #fff; font-size: 14px; font-family: inherit; box-sizing: border-box; }
    textarea { resize: vertical; min-height: 120px; }
    textarea:focus, select:focus { outline: none; border-color: #06b6d4; }

    .btn { padding: 12px 24px; border-radius: 10px; border: none; font-family: inherit; font-weight: 900; font-size: 14px; cursor: pointer; }
    .btn-submit { background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; box-shadow: 0 8px 20px rgba(34,197,94,0.4); width: 100%; margin-top: 12px; }
    .btn-delete { background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4) !important; }
    .btn-toggle { background: rgba(148,163,184,0.2); color: #fff; }

    .reply-existing { padding: 16px; background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(6,182,212,0.08)); border: 1.5px solid rgba(34,197,94,0.4); border-radius: 12px; margin-bottom: 16px; }
    .reply-existing h4 { font-size: 13px; color: #86efac; margin-bottom: 8px; }
    .reply-existing .body { font-size: 13px; line-height: 1.8; white-space: pre-wrap; }
    .reply-existing .time { font-size: 10px; color: #94a3b8; margin-top: 8px; font-family: monospace; }

    .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(148,163,184,0.1); font-size: 13px; }
    .info-row:last-child { border-bottom: none; }
    .info-row .k { color: #94a3b8; }
    .info-row .v { color: #fff; font-family: monospace; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>تیکت #{{ t.id }}</h1>
    <div class="actions">
      <a href="/panel-admin/support/" class="btn-back">← بازگشت</a>
      <a href="{% url 'custom_admin:logout' %}" class="btn-logout">خروج</a>
    </div>
  </div>

  {% if message %}<div class="msg msg-success">{{ message.text }}</div>{% endif %}

  <div class="card">
    <div class="ticket-header">
      <div class="ticket-icon">
        {% if t.category == 'bug' %}🐛
        {% elif t.category == 'idea' %}💡
        {% elif t.category == 'payment' %}💳
        {% else %}📝{% endif %}
      </div>
      <div class="ticket-info">
        <div class="ticket-title">{{ t.subject }}</div>
        <div class="ticket-meta">👤 {{ t.user.alias }} (@{{ t.user.username }}) · {{ t.created_at|jdate:"Y/m/d H:i" }}</div>
      </div>
      <span class="ticket-badge badge-{{ t.status }}">{{ t.status_display }}</span>
    </div>

    <div class="ticket-body">{{ t.body }}</div>
  </div>

  {% if t.admin_reply %}
    <div class="card">
      <h3>📬 پاسخ ارسال‌شده</h3>
      <div class="reply-existing">
        <h4>پاسخ شما:</h4>
        <div class="body">{{ t.admin_reply }}</div>
        <div class="time">📅 {{ t.replied_at|jdate:"Y/m/d H:i" }}</div>
      </div>
    </div>
  {% endif %}

  <div class="card">
    <h3>💬 ارسال / ویرایش پاسخ</h3>
    <form method="post">
      {% csrf_token %}
      <input type="hidden" name="action" value="reply">
      <label>متن پاسخ</label>
      <textarea name="admin_reply" placeholder="پاسخ خود را بنویسید..." required>{% if t.admin_reply %}{{ t.admin_reply }}{% endif %}</textarea>
      <label>وضعیت جدید</label>
      <select name="new_status">
        <option value="answered" {% if t.status == 'answered' %}selected{% endif %}>پاسخ داده شده</option>
        <option value="in_progress" {% if t.status == 'in_progress' %}selected{% endif %}>در حال بررسی</option>
        <option value="closed" {% if t.status == 'closed' %}selected{% endif %}>بسته شده</option>
        <option value="open" {% if t.status == 'open' %}selected{% endif %}>باز</option>
      </select>
      <button type="submit" class="btn btn-submit">📤 ارسال پاسخ</button>
    </form>
  </div>

  <div class="card" style="background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.3);">
    <h3 style="color: #fca5a5;">⚠️ منطقه خطر</h3>
    <form method="post" onsubmit="return confirm('حذف تیکت #{{ t.id }}؟');" style="margin-top: 10px;">
      {% csrf_token %}
      <input type="hidden" name="action" value="delete">
      <button type="submit" class="btn btn-delete" style="width: 100%;">🗑️ حذف تیکت</button>
    </form>
  </div>
</div>
</body>
</html>
''')

# ============================================================
# 4) FIX PUZZLE GAME
# ============================================================
print("\n[4/8] Fix puzzle game")
p = "game/views.py"
src = read(p)

# Remove old puzzle views
pattern = re.compile(r'# =+\s*\n# Puzzle Game[^\n]*\n# =+.*?(?=\n# =+\s*\n# Memory|\n# =+\s*\n# 0-100|\Z)', re.DOTALL)
src = pattern.sub('', src)

NEW_PUZZLE = '''

# ============================================================
# Puzzle Game — arrange scrambled letters
# ============================================================
from game.puzzle_words import get_puzzle_words

@login_required
def puzzle_home(request):
    check = _require_complete(request.user)
    if check:
        return check

    # New game
    if request.method == "POST" and request.POST.get("action") == "new":
        _start_puzzle(request)
        return redirect("game:puzzle")

    # Start if no game
    if "puzzle_items" not in request.session or request.session.get("puzzle_finished"):
        _start_puzzle(request)
        return redirect("game:puzzle")

    items = request.session.get("puzzle_items", [])
    import time
    start_ts = request.session.get("puzzle_start_ts", 0)
    total_time = request.session.get("puzzle_total_time", 60)
    elapsed = int(time.time() - start_ts) if start_ts else 0
    remaining = max(0, total_time - elapsed)

    # If time up → auto-finish
    if remaining <= 0 and not request.session.get("puzzle_finished"):
        request.session["puzzle_finished"] = True

    if request.session.get("puzzle_finished"):
        return render(request, "game/puzzle.html", {
            "finished": True,
            "score": request.session.get("puzzle_score", 0),
            "total": len(items),
            "active": "games",
        })

    return render(request, "game/puzzle.html", {
        "items": items,
        "total": len(items),
        "remaining": remaining,
        "total_time": total_time,
        "finished": False,
        "active": "games",
    })


def _shuffle_letters(word):
    letters = list(word)
    for _ in range(30):
        _rand.shuffle(letters)
        if "".join(letters) != word:
            return " ".join(letters)
    return " ".join(letters)


def _start_puzzle(request):
    pool = get_puzzle_words()
    if not pool:
        pool = ["کتاب", "درخت", "خورشید", "آبشار", "پروانه"]
    
    picks = _rand.sample(pool, min(5, len(pool)))
    items = []
    total_time = 0
    for i, w in enumerate(picks):
        sec = len(w) * 5
        total_time += sec
        items.append({
            "idx": i,
            "word": w,
            "scrambled": _shuffle_letters(w),
            "length": len(w),
            "seconds": sec,
        })
    
    import time
    request.session["puzzle_items"] = items
    request.session["puzzle_start_ts"] = int(time.time())
    request.session["puzzle_total_time"] = total_time
    request.session["puzzle_finished"] = False
    request.session["puzzle_score"] = 0


@login_required
def puzzle_submit(request):
    check = _require_complete(request.user)
    if check:
        return check
    if request.method != "POST":
        return redirect("game:puzzle")
    
    if request.POST.get("action") == "new":
        _start_puzzle(request)
        return redirect("game:puzzle")

    items = request.session.get("puzzle_items", [])
    if not items:
        return redirect("game:puzzle")

    correct = 0
    for it in items:
        ans = (request.POST.get(f"ans_{it['idx']}") or "").strip()
        ans = ans.replace("ي", "ی").replace("ك", "ک").replace(" ", "").replace("\u200c", "")
        target = it["word"].replace("ي", "ی").replace("ك", "ک").replace(" ", "").replace("\u200c", "")
        if ans == target:
            correct += 1

    request.session["puzzle_score"] = correct * 10
    request.session["puzzle_finished"] = True
    messages.success(request, f"🎯 {correct} از {len(items)} درست!")
    return redirect("game:puzzle")
'''

src = src.rstrip() + NEW_PUZZLE + "\n"
write(p, src)
print("  ✓ puzzle rebuilt")

# ============================================================
# 5) FIX 0-100 GAME
# ============================================================
print("\n[5/8] Fix 0-100 game")
p = "game/views.py"
src = read(p)

# Remove old guess views
pattern = re.compile(r'# =+\s*\n# 0-100[^\n]*\n# =+.*?(?=\n# =+\s*\n# |\Z)', re.DOTALL)
src = pattern.sub('', src)

NEW_GUESS = '''

# ============================================================
# 0-100 Guess Game
# ============================================================
@login_required
def guess_home(request):
    check = _require_complete(request.user)
    if check:
        return check

    if request.method == "POST" and request.POST.get("action") == "new":
        _start_guess(request)
        return redirect("game:guess")

    if "guess_number" not in request.session or request.session.get("guess_finished"):
        if "guess_number" not in request.session:
            _start_guess(request)
            return redirect("game:guess")

    return render(request, "game/guess.html", {
        "tries": request.session.get("guess_tries", 0),
        "max_tries": request.session.get("guess_max", 7),
        "finished": request.session.get("guess_finished", False),
        "won": request.session.get("guess_won", False),
        "number": request.session.get("guess_number") if request.session.get("guess_finished") else None,
        "history": request.session.get("guess_history", []),
        "active": "games",
    })


def _start_guess(request):
    request.session["guess_number"] = _rand.randint(0, 100)
    request.session["guess_tries"] = 0
    request.session["guess_max"] = 7
    request.session["guess_finished"] = False
    request.session["guess_won"] = False
    request.session["guess_history"] = []


@login_required
def guess_attempt(request):
    check = _require_complete(request.user)
    if check:
        return check
    if request.method != "POST":
        return redirect("game:guess")

    try:
        guess = int(request.POST.get("guess", -1))
    except (ValueError, TypeError):
        return redirect("game:guess")

    if not (0 <= guess <= 100):
        messages.error(request, "عدد باید بین ۰ تا ۱۰۰ باشه.")
        return redirect("game:guess")

    number = request.session.get("guess_number")
    tries = request.session.get("guess_tries", 0) + 1
    max_tries = request.session.get("guess_max", 7)
    history = request.session.get("guess_history", [])

    if guess == number:
        request.session["guess_won"] = True
        request.session["guess_finished"] = True
        request.session["guess_tries"] = tries
        history.append({"guess": guess, "result": "win"})
        request.session["guess_history"] = history
        messages.success(request, f"🎉 آفرین! عدد {number} بود. توی {tries} تلاش درست حدس زدی.")
    elif tries >= max_tries:
        request.session["guess_won"] = False
        request.session["guess_finished"] = True
        request.session["guess_tries"] = tries
        history.append({"guess": guess, "result": "low" if guess < number else "high"})
        request.session["guess_history"] = history
        messages.error(request, f"❌ باختی! عدد {number} بود.")
    else:
        request.session["guess_tries"] = tries
        result = "low" if guess < number else "high"
        history.append({"guess": guess, "result": result})
        request.session["guess_history"] = history
        if result == "low":
            messages.info(request, f"⬆️ عدد بزرگ‌تره! ({max_tries - tries} تلاش دیگه)")
        else:
            messages.info(request, f"⬇️ عدد کوچیک‌تره! ({max_tries - tries} تلاش دیگه)")

    return redirect("game:guess")
'''

src = src.rstrip() + NEW_GUESS + "\n"
write(p, src)
print("  ✓ 0-100 game rebuilt")

# Ensure imports
p = "game/views.py"
src = read(p)
if "from game.puzzle_words import get_puzzle_words" not in src:
    src = src.replace(
        "from django.contrib import messages\n",
        "from django.contrib import messages\nfrom game.puzzle_words import get_puzzle_words\n",
        1
    )
    write(p, src)
    print("  ✓ puzzle_words imported")

# ============================================================
# 6) HOME PAGE — new layout
# ============================================================
print("\n[6/8] Home page layout")
write("game/templates/game/menu.html", '''{% extends "base.html" %}
{% block title %}خانه{% endblock %}

{% block extra_css %}
<style>
  /* ============ ANIMATED BACKGROUND ============ */
  .bg-pattern {
    position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden;
  }
  .bg-pattern::before, .bg-pattern::after {
    content: ""; position: absolute; inset: -50%;
    background-image:
      radial-gradient(circle, rgba(244,197,66,0.35) 1px, transparent 1.5px),
      radial-gradient(circle, rgba(139,92,246,0.3) 1px, transparent 1.5px);
    background-size: 60px 60px, 90px 90px;
    background-position: 0 0, 30px 30px;
    animation: dotsFloat 30s linear infinite;
    opacity: 0.4;
  }
  .bg-pattern::after { animation-duration: 45s; animation-direction: reverse; }
  @keyframes dotsFloat { from { transform: translate(0, 0); } to { transform: translate(60px, 90px); } }
  
  .fly-dot {
    position: fixed; width: 4px; height: 4px; border-radius: 50%;
    background: #f4c542; box-shadow: 0 0 8px #f4c542;
    opacity: 0.6; z-index: 0; pointer-events: none; animation: flyUp linear infinite;
  }
  @keyframes flyUp {
    from { transform: translateY(100vh) scale(0.3); opacity: 0; }
    20% { opacity: 0.7; }
    to { transform: translateY(-50px) scale(1); opacity: 0; }
  }

  /* ============ TOP BAR: settings + profile ============ */
  .top-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 16px;
    position: relative;
    z-index: 3;
    min-height: 80px;
  }
  
  .btn-settings {
    width: 52px;
    height: 52px;
    border-radius: 16px;
    background: linear-gradient(135deg, var(--card), #0f0f1e);
    border: 2px solid rgba(148,163,184,0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    font-size: 24px;
    flex-shrink: 0;
    transition: all 0.3s;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  }
  .btn-settings:hover {
    border-color: var(--gold);
    transform: rotate(45deg) scale(1.08);
    box-shadow: 0 8px 20px rgba(244,197,66,0.3);
  }

  /* ============ PROFILE (right, expands leftward) ============ */
  .profile-wrap {
    display: flex;
    justify-content: flex-end;
    flex: 1;
    min-width: 0;
  }
  .profile-oval {
    display: flex;
    align-items: center;
    gap: 0;
    padding: 6px;
    height: 68px;
    width: 68px;
    border-radius: 34px;
    background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.35), transparent 60%),
                linear-gradient(135deg, var(--card), #0f0f1e);
    border: 2.5px solid rgba(244,197,66,0.6);
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    position: relative;
    box-shadow: 0 0 25px rgba(244,197,66,0.3);
    flex-shrink: 0;
  }
  .profile-oval:hover { border-color: #fde68a; box-shadow: 0 0 40px rgba(244,197,66,0.5); }
  .profile-oval.expanded {
    width: 260px;
    padding: 12px 16px;
    gap: 12px;
  }
  
  .po-av {
    width: 52px; height: 52px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2a2a4a, #1a1a2e);
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; border: 2px solid #f4c542;
    box-shadow: 0 0 15px rgba(244,197,66,0.5);
    overflow: hidden; background-size: cover; background-position: center;
    flex-shrink: 0; transition: all 0.3s;
  }
  .profile-oval.expanded .po-av { width: 56px; height: 56px; font-size: 28px; }
  
  .po-details {
    flex: 1; min-width: 0; max-width: 0; opacity: 0; overflow: hidden;
    transition: all 0.4s; text-align: right; white-space: nowrap;
  }
  .profile-oval.expanded .po-details { max-width: 200px; opacity: 1; }
  .po-name {
    font-size: 15px; font-weight: 900; color: #fde68a; margin-bottom: 3px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .po-meta {
    display: flex; gap: 6px; align-items: center; font-size: 10px; color: #94a3b8;
    flex-wrap: wrap;
  }
  .po-meta .badge {
    background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff;
    padding: 1px 6px; border-radius: 6px; font-family: monospace;
    font-weight: 900; font-size: 9px;
  }

  /* ============ VERTICAL CIRCLE LIST (right side) ============ */
  .right-column {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 10px;
    margin-bottom: 20px;
    position: relative;
    z-index: 2;
  }
  
  .circle-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 18px 10px 14px;
    border-radius: 999px;
    text-decoration: none;
    color: #fff;
    border: 2px solid;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    font-family: inherit;
    min-width: 130px;
    justify-content: flex-end;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
  }
  .circle-item:hover { transform: translateX(-4px) scale(1.03); }
  .circle-item:active { transform: scale(0.97); }
  .circle-item .ci {
    font-size: 24px; width: 34px; height: 34px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }
  .circle-item .cl {
    font-size: 14px; font-weight: 900;
    white-space: nowrap;
  }
  
  /* Top players */
  .circle-top {
    background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.3), transparent 60%),
                linear-gradient(135deg, #2a1a0e, #1a0f1a);
    border-color: rgba(244,197,66,0.6);
  }
  .circle-top:hover { border-color: #fde68a; box-shadow: 0 8px 25px rgba(244,197,66,0.4); }
  .circle-top .ci {
    background: radial-gradient(circle, rgba(244,197,66,0.4), rgba(234,179,8,0.15));
    box-shadow: 0 0 12px rgba(244,197,66,0.6);
  }
  .circle-top .cl { color: #fde68a; }

  /* Challenge */
  .circle-challenge {
    background: radial-gradient(circle at 100% 0%, rgba(239,68,68,0.3), transparent 60%),
                linear-gradient(135deg, #2a0a0a, #1a0606);
    border-color: rgba(239,68,68,0.6);
  }
  .circle-challenge:hover { border-color: #fca5a5; box-shadow: 0 8px 25px rgba(239,68,68,0.4); }
  .circle-challenge .ci {
    background: radial-gradient(circle, rgba(239,68,68,0.4), rgba(249,115,22,0.15));
    box-shadow: 0 0 12px rgba(239,68,68,0.6);
  }
  .circle-challenge .cl { color: #fca5a5; }

  /* ============ 3 SQUARES (main menu) ============ */
  .section-label {
    font-size: 11px; color: var(--muted); font-weight: 900; letter-spacing: 2px;
    margin: 4px 4px 12px; display: flex; align-items: center; gap: 8px;
    position: relative; z-index: 2;
  }
  .section-label::after {
    content: ""; flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(148,163,184,0.2), transparent);
  }
  
  .sq-grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
    margin-bottom: 16px; position: relative; z-index: 2;
  }
  .sq-tile {
    aspect-ratio: 1;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 6px; padding: 12px 8px;
    border-radius: 20px; text-decoration: none; color: #fff;
    position: relative; overflow: hidden; border: 2px solid;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer; font-family: inherit;
    background: transparent;
  }
  .sq-tile:hover { transform: translateY(-4px) scale(1.04); }
  .sq-tile::after {
    content: ""; position: absolute; top: 0; left: -100%;
    width: 60%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
    transform: skewX(-20deg); animation: shine 4s infinite;
    z-index: 2; pointer-events: none;
  }
  @keyframes shine { 0% { left: -100%; } 50%,100% { left: 200%; } }
  .sq-icon { font-size: 38px; line-height: 1; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.5)); animation: float 3s ease-in-out infinite; }
  .sq-tile:nth-child(1) .sq-icon { animation-delay: 0s; }
  .sq-tile:nth-child(2) .sq-icon { animation-delay: 0.4s; }
  .sq-tile:nth-child(3) .sq-icon { animation-delay: 0.8s; }
  @keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
  .sq-tile:hover .sq-icon { transform: scale(1.2) rotate(-8deg); animation: none; }
  .sq-title { font-size: 12px; font-weight: 900; }
  .sq-sub { font-size: 9px; opacity: 0.75; }
  
  .sq-notif {
    background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.4), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #0f0f1e);
    border-color: rgba(139,92,246,0.6);
  }
  .sq-notif:hover { border-color: rgba(167,139,250,0.95); box-shadow: 0 18px 45px rgba(139,92,246,0.45); }
  .sq-notif .sq-title { color: #c4b5fd; }
  
  .sq-games {
    background: radial-gradient(circle at 100% 0%, rgba(236,72,153,0.4), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #120824);
    border-color: rgba(236,72,153,0.6);
  }
  .sq-games:hover { border-color: rgba(236,72,153,0.95); box-shadow: 0 18px 45px rgba(236,72,153,0.45); }
  .sq-games .sq-title { color: #f9a8d4; }
  
  .sq-support {
    background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.4), transparent 60%),
                linear-gradient(135deg, #0a1e2a, #0f0f1e);
    border-color: rgba(6,182,212,0.6);
  }
  .sq-support:hover { border-color: rgba(34,211,238,0.95); box-shadow: 0 18px 45px rgba(6,182,212,0.45); }
  .sq-support .sq-title { color: #a5f3fc; }

  .sq-badge {
    position: absolute; top: 8px; right: 8px;
    background: #ef4444; color: #fff;
    font-size: 10px; font-weight: 900;
    padding: 2px 8px; border-radius: 999px;
    box-shadow: 0 3px 10px rgba(239,68,68,0.6);
    animation: pulseBadge 2s infinite;
    z-index: 3;
  }
  @keyframes pulseBadge { 0%,100% { transform: scale(1); } 50% { transform: scale(1.18); } }

  /* Guest warning */
  .guest-warning {
    background: linear-gradient(135deg, rgba(234,179,8,0.15), rgba(249,115,22,0.08));
    border: 1.5px solid rgba(234,179,8,0.35);
    border-radius: 14px; padding: 12px 14px; margin-bottom: 14px;
    display: flex; align-items: center; gap: 12px;
    position: relative; z-index: 2;
  }
  .guest-warning .gw-icon { font-size: 26px; flex-shrink: 0; }
  .guest-warning .gw-body { flex: 1; }
  .guest-warning .gw-title { font-size: 12px; font-weight: 900; color: #fde68a; margin-bottom: 2px; }
  .guest-warning .gw-desc { font-size: 10px; color: #fbbf24; line-height: 1.5; }
  .guest-warning .gw-logout {
    background: rgba(239,68,68,0.2); color: #fca5a5;
    border: 1px solid rgba(239,68,68,0.4);
    padding: 7px 12px; border-radius: 10px;
    font-size: 11px; font-weight: 900; text-decoration: none;
  }
</style>
{% endblock %}

{% block content %}
  <div class="bg-pattern"></div>
  <div class="fly-dot" style="left: 15%; animation-duration: 12s;"></div>
  <div class="fly-dot" style="left: 40%; animation-duration: 15s; animation-delay: 2s; background: #8b5cf6; box-shadow: 0 0 8px #8b5cf6;"></div>
  <div class="fly-dot" style="left: 65%; animation-duration: 18s; animation-delay: 4s;"></div>
  <div class="fly-dot" style="left: 85%; animation-duration: 14s; animation-delay: 1s; background: #06b6d4; box-shadow: 0 0 8px #06b6d4;"></div>

  <!-- Top row: settings (left) + profile (right) -->
  <div class="top-row">
    <a href="/accounts/settings/" class="btn-settings" title="تنظیمات">⚙️</a>
    
    <div class="profile-wrap">
      <div class="profile-oval" id="profileOval" onclick="toggleProfile()">
        {% if user.avatar_type == "image" and user.avatar_id %}
          <div class="po-av" style="background-image: url('/static/avatars/images/{{ user.avatar_id|stringformat:"03d" }}.jpg');"></div>
        {% else %}
          <div class="po-av">{{ avatar_emoji }}</div>
        {% endif %}
        <div class="po-details">
          <div class="po-name">{{ user.alias }}</div>
          <div class="po-meta">
            <span class="badge">Lv {{ level|default:1 }}</span>
            <span>🪙 {{ user.coins|default:0 }}</span>
            <span>💎 {{ user.gems|default:0 }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Right column: top players + challenge -->
  <div class="right-column">
    <a href="/game/top-players/" class="circle-item circle-top">
      <span class="cl">بازیکنان برتر</span>
      <span class="ci">⭐</span>
    </a>
    <a href="/game/challenge/" class="circle-item circle-challenge">
      <span class="cl">چالش</span>
      <span class="ci">🏆</span>
    </a>
  </div>

  {% if user.is_guest %}
    <div class="guest-warning">
      <span class="gw-icon">🎲</span>
      <div class="gw-body">
        <div class="gw-title">حساب مهمان</div>
        <div class="gw-desc">برای ذخیره دائمی، ثبت‌نام کن</div>
      </div>
      <a href="/accounts/register/" class="gw-logout">ثبت‌نام</a>
    </div>
  {% endif %}

  <!-- 3 middle squares -->
  <div class="section-label">📋 منو اصلی</div>

  <div class="sq-grid">
    <a href="/social/notifications/" class="sq-tile sq-notif">
      {% if unread_notifications %}<span class="sq-badge">{{ unread_notifications }}</span>{% endif %}
      <div class="sq-icon">🔔</div>
      <div class="sq-title">اعلان‌ها</div>
      <div class="sq-sub">{% if unread_notifications %}{{ unread_notifications }} جدید{% else %}پیام‌ها{% endif %}</div>
    </a>

    <a href="/game/rooms/" class="sq-tile sq-games">
      <div class="sq-icon">🎮</div>
      <div class="sq-title">بازی‌ها</div>
      <div class="sq-sub">۷ حالت</div>
    </a>

    <a href="/support/" class="sq-tile sq-support">
      <div class="sq-icon">💬</div>
      <div class="sq-title">پشتیبانی</div>
      <div class="sq-sub">در تماس باش</div>
    </a>
  </div>

{% endblock %}

{% block extra_js %}
<script>
  function toggleProfile() {
    document.getElementById('profileOval').classList.toggle('expanded');
    if (window.vibrate) window.vibrate(8);
    if (window.soundClick) window.soundClick();
  }
</script>
{% endblock %}
''')

# ============================================================
# 7) Migrations + check
# ============================================================
print("\n[7/8] Migrations")
for cmd in [
    [sys.executable, "manage.py", "makemigrations", "support", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd[1:])}")
    if r.returncode != 0 and r.stderr.strip():
        print(f"    ⚠ {r.stderr[:300]}")

print("\n[8/8] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ PASSED")
else:
    print(f"  ⚠ {r.stderr[:800]}")

print("\n" + "="*60)
print("✅ همه چیز آماده")
print("="*60)
print("""
چه چیزایی:

  💬 پشتیبانی (کامل):
     ✓ کاربر: /support/ → فرم + لیست تیکت‌ها
     ✓ جزئیات: /support/<id>/ → مشاهده پاسخ
     ✓ ادمین: /panel-admin/support/ → لیست همه
     ✓ ادمین: /panel-admin/support/<id>/ → پاسخ + تغییر وضعیت
     ✓ اعلان خودکار به کاربر

  🎯 بازی معما (فیکس):
     ✓ ۵ کلمه تصادفی از ۲۰۰+ کلمه
     ✓ حروف به‌هم‌ریخته → تایپ کن
     ✓ زمان: ۵ ثانیه به ازای هر حرف
     ✓ تایمر سراسری

  🎲 بازی ۰ تا ۱۰۰ (فیکس):
     ✓ عدد ۰-۱۰۰ تصادفی
     ✓ ۷ تلاش
     ✓ هیستوری بالا/پایین

  🏠 خانه جدید:
     ✓ راست بالا: پروفایل (دایره → کلیک → بیضی به چپ)
     ✓ چپ بالا: تنظیمات ⚙️
     ✓ راست پایین: ⭐ بازیکنان برتر + 🏆 چالش
     ✓ وسط: 🔔 اعلان + 🎮 بازی‌ها + 💬 پشتیبانی
     ✓ فروشگاه حذف شد (چالش جاش اومد)

حالا:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R

تست:
  http://127.0.0.1:8000/game/                    ← خانه
  http://127.0.0.1:8000/support/                 ← پشتیبانی
  http://127.0.0.1:8000/panel-admin/support/     ← ادمین پشتیبانی
  http://127.0.0.1:8000/game/puzzle/             ← معما
  http://127.0.0.1:8000/game/guess/              ← ۰ تا ۱۰۰
""")
