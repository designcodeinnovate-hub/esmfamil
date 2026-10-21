#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Complete rebuild of support + games (puzzle, guess, memory)"""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    try:
        with open(p, "r", encoding="utf-8") as f: return f.read()
    except: return ""
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) SUPPORT APP — complete rebuild
# ============================================================
print("\n[1/7] Building support app")

# __init__.py
write("support/__init__.py", "")

# apps.py
write("support/apps.py", '''from django.apps import AppConfig


class SupportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "support"
''')

# models.py — clean
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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="my_support_tickets",
    )
    subject = models.CharField(max_length=100)
    body = models.TextField(max_length=2000)
    category = models.CharField(max_length=20, default="general")
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

# views.py
write("support/views.py", '''# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import SupportTicket


@login_required
def support_home(request):
    if not getattr(request.user, "has_chosen_avatar", False):
        return redirect("accounts:avatar_select")

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
                category=category if category in ("general", "bug", "idea", "payment") else "general",
            )
            messages.success(request, f"✅ تیکت #{ticket.id} ثبت شد.")
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

# urls.py
write("support/urls.py", '''from django.urls import path
from . import views

app_name = "support"

urlpatterns = [
    path("", views.support_home, name="home"),
    path("<int:ticket_id>/", views.ticket_detail, name="ticket"),
    path("<int:ticket_id>/close/", views.ticket_close, name="close"),
]
''')

# migrations folder
os.makedirs("support/migrations", exist_ok=True)
if not os.path.exists("support/migrations/__init__.py"):
    write("support/migrations/__init__.py", "")

# Templates
write("support/templates/support/home.html", '''{% extends "base.html" %}
{% block title %}پشتیبانی{% endblock %}
{% block extra_css %}
<style>
  .page-head{display:flex;align-items:center;gap:12px;margin-bottom:20px}
  .page-head h1{font-size:22px;font-weight:900;color:var(--gold)}
  .hero{background:linear-gradient(135deg,#0a1e2a,#0f0f1e);border:2px solid rgba(6,182,212,0.5);border-radius:20px;padding:24px 20px;margin-bottom:20px;text-align:center}
  .hero .icon{font-size:52px;margin-bottom:10px}
  .hero h2{font-size:19px;font-weight:900;background:linear-gradient(135deg,#67e8f9,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:6px}
  .hero p{color:var(--muted);font-size:13px;line-height:1.6}
  .form-box{background:var(--card);border:1.5px solid var(--border);border-radius:18px;padding:20px;margin-bottom:20px}
  .form-box h3{font-size:15px;color:#67e8f9;margin-bottom:14px}
  label{display:block;color:var(--muted);font-size:12px;margin:12px 0 6px;font-weight:700}
  input[type=text],textarea,select{width:100%;padding:12px 14px;border-radius:10px;border:1.5px solid var(--border);background:var(--bg);color:var(--text);font-size:14px;font-family:inherit;box-sizing:border-box}
  textarea{resize:vertical;min-height:100px}
  input:focus,textarea:focus,select:focus{outline:none;border-color:#06b6d4}
  button.submit{width:100%;margin-top:16px;padding:14px;border:none;border-radius:12px;background:linear-gradient(135deg,#06b6d4,#3b82f6);color:#fff;font-size:15px;font-weight:900;font-family:inherit;cursor:pointer}
  .ticket-card{display:flex;align-items:flex-start;gap:12px;padding:14px;background:var(--card);border:1.5px solid var(--border);border-radius:14px;margin-bottom:8px;text-decoration:none;color:var(--text);transition:0.2s}
  .ticket-card:hover{border-color:#06b6d4;transform:translateX(-3px)}
  .ticket-card .icon{font-size:26px;flex-shrink:0}
  .ticket-card .info{flex:1;min-width:0}
  .ticket-card .title{font-size:14px;font-weight:bold;margin-bottom:4px}
  .ticket-card .meta{font-size:11px;color:var(--muted)}
  .ticket-card .badge{font-size:10px;padding:3px 10px;border-radius:8px;font-weight:bold;flex-shrink:0}
  .badge-open{background:rgba(234,179,8,0.2);color:#fde68a}
  .badge-answered{background:rgba(34,197,94,0.2);color:#86efac}
  .badge-closed{background:rgba(100,116,139,0.2);color:#cbd5e1}
  .badge-in_progress{background:rgba(59,130,246,0.2);color:#93c5fd}
</style>
{% endblock %}
{% block content %}
<div class="page-head">
  <a href="/game/" class="back-btn"><span class="arrow-icon">→</span></a>
  <h1>💬 پشتیبانی</h1>
</div>

<div class="hero">
  <div class="icon">💬</div>
  <h2>چطور می‌تونیم کمکت کنیم؟</h2>
  <p>سوال یا مشکلی داری؟ یه پیام بفرست.</p>
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
      <option value="idea">پیشنهاد</option>
      <option value="payment">پرداخت</option>
    </select>
    <label>متن پیام</label>
    <textarea name="body" required maxlength="2000" placeholder="مشکل رو با جزئیات بنویس..."></textarea>
    <button type="submit" class="submit">📤 ارسال</button>
  </form>
</div>

{% if tickets %}
  <h3 style="font-size:15px;color:var(--gold);margin-bottom:12px;">📜 تیکت‌های من</h3>
  {% for t in tickets %}
    <a href="/support/{{ t.id }}/" class="ticket-card">
      <div class="icon">{% if t.category == 'bug' %}🐛{% elif t.category == 'idea' %}💡{% elif t.category == 'payment' %}💳{% else %}📝{% endif %}</div>
      <div class="info">
        <div class="title">{{ t.subject }}</div>
        <div class="meta">#{{ t.id }} · {{ t.created_at|date:"Y/m/d H:i" }}</div>
      </div>
      <span class="badge badge-{{ t.status }}">{{ t.status_display }}</span>
    </a>
  {% endfor %}
{% endif %}
{% endblock %}
''')

write("support/templates/support/ticket.html", '''{% extends "base.html" %}
{% block title %}تیکت #{{ ticket.id }}{% endblock %}
{% block extra_css %}
<style>
  .page-head{display:flex;align-items:center;gap:12px;margin-bottom:20px}
  .page-head h1{font-size:20px;font-weight:900;color:var(--gold)}
  .ticket-box{background:var(--card);border:1.5px solid var(--border);border-radius:18px;padding:20px;margin-bottom:16px}
  .t-header{display:flex;align-items:flex-start;gap:14px;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid var(--border)}
  .t-icon{font-size:34px;flex-shrink:0}
  .t-info{flex:1}
  .t-title{font-size:17px;font-weight:900;margin-bottom:4px}
  .t-meta{font-size:11px;color:var(--muted)}
  .t-badge{font-size:10px;padding:4px 12px;border-radius:8px;font-weight:bold;flex-shrink:0}
  .badge-open{background:rgba(234,179,8,0.2);color:#fde68a}
  .badge-answered{background:rgba(34,197,94,0.2);color:#86efac}
  .badge-closed{background:rgba(100,116,139,0.2);color:#cbd5e1}
  .badge-in_progress{background:rgba(59,130,246,0.2);color:#93c5fd}
  .t-body{padding:16px;background:rgba(15,23,42,0.5);border-radius:12px;font-size:14px;line-height:1.8;white-space:pre-wrap}
  .reply-box{margin-top:18px;padding:18px;background:rgba(34,197,94,0.08);border:1.5px solid rgba(34,197,94,0.4);border-radius:14px}
  .reply-box h3{font-size:14px;color:#86efac;margin-bottom:10px}
  .reply-body{font-size:14px;line-height:1.8;color:#fff;white-space:pre-wrap;padding:12px;background:rgba(15,23,42,0.5);border-radius:10px}
  .reply-time{font-size:10px;color:#94a3b8;margin-top:8px;font-family:monospace}
  .no-reply{text-align:center;padding:20px;background:rgba(234,179,8,0.08);border:1px dashed rgba(234,179,8,0.3);border-radius:12px;color:#fde68a;font-size:13px;margin-top:16px}
  .actions{display:flex;gap:10px;margin-top:20px}
  .actions a,.actions button{flex:1;padding:12px;border-radius:12px;border:none;font-family:inherit;font-weight:900;font-size:14px;cursor:pointer;text-decoration:none;text-align:center}
  .btn-back{background:rgba(148,163,184,0.2);color:#fff}
  .btn-close{background:rgba(239,68,68,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.4) !important}
</style>
{% endblock %}
{% block content %}
<div class="page-head">
  <a href="/support/" class="back-btn"><span class="arrow-icon">→</span></a>
  <h1>تیکت #{{ ticket.id }}</h1>
</div>

<div class="ticket-box">
  <div class="t-header">
    <div class="t-icon">{% if ticket.category == 'bug' %}🐛{% elif ticket.category == 'idea' %}💡{% elif ticket.category == 'payment' %}💳{% else %}📝{% endif %}</div>
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
        <button type="submit" class="btn-close">✕ بستن</button>
      </form>
    {% endif %}
  </div>
</div>
{% endblock %}
''')

# Admin views
print("\n[1b/7] Adding admin support views")
admin_src = read("accounts/admin_views.py")

if "def support_list" not in admin_src:
    admin_support = '''

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
        qs = qs.filter(Q(subject__icontains=q) | Q(user__alias__icontains=q))

    from accounts.avatars import get_emoji
    tickets_data = []
    for t in qs[:100]:
        tickets_data.append({
            "id": t.id,
            "subject": t.subject,
            "user_alias": t.user.alias,
            "user_username": t.user.username,
            "avatar": get_emoji(t.user.avatar_id),
            "category": t.category,
            "status": t.status,
            "status_display": t.status_display(),
            "created_at": t.created_at,
        })

    from django.db.models import Count
    counts = SupportTicket.objects.values("status").annotate(c=Count("id"))
    status_counts = {x["status"]: x["c"] for x in counts}

    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/support_list.html", {
        "tickets": tickets_data,
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
                try:
                    from social.notifications import notify
                    notify(user=t.user, ntype="message", title=f"پاسخ به تیکت #{t.id}", body=f"تیکت «{t.subject[:40]}» پاسخ داده شد.", url=f"/support/{t.id}/")
                except Exception:
                    pass
                request.session["admin_message"] = {"type": "success", "text": "پاسخ ارسال شد."}
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
    admin_src = admin_src.rstrip() + admin_support + "\n"
    write("accounts/admin_views.py", admin_src)
    print("  ✓ support admin views added")

# Admin urls
admin_urls = read("accounts/admin_urls.py")
if "support_list" not in admin_urls:
    if admin_urls.rstrip().endswith("]"):
        admin_urls = admin_urls.rstrip()[:-1] + '    path("support/", admin_views.support_list, name="support_list"),\n    path("support/<int:ticket_id>/", admin_views.support_detail, name="support_detail"),\n]\n'
        write("accounts/admin_urls.py", admin_urls)
        print("  ✓ support admin routes added")

# Admin templates
write("accounts/templates/custom_admin/support_list.html", '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <title>پشتیبانی — پنل ادمین</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:Tahoma,sans-serif;min-height:100vh;background:#0a0a15;color:#e2e8f0;padding:20px 16px 40px}
    .container{max-width:1300px;margin:0 auto}
    .topbar{display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#1e1b4b,#0f0f1e);border:1px solid rgba(239,68,68,0.3);padding:16px 22px;border-radius:16px;margin-bottom:20px}
    .topbar h1{font-size:20px;color:#fca5a5}
    .topbar a{padding:9px 16px;border-radius:10px;background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff;text-decoration:none;font-size:13px;font-weight:bold}
    .admin-tabs{display:flex;gap:6px;margin-bottom:20px;background:#12121f;border:1px solid rgba(148,163,184,0.15);padding:6px;border-radius:14px;overflow-x:auto}
    .admin-tab{flex:1;min-width:100px;padding:12px 14px;border-radius:10px;text-align:center;text-decoration:none;font-size:12px;font-weight:bold;color:#94a3b8;white-space:nowrap}
    .admin-tab:hover{background:rgba(148,163,184,0.1);color:#fff}
    .admin-tab.active{background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff}
    .msg{padding:12px 16px;border-radius:10px;font-size:13px;margin-bottom:16px;background:rgba(34,197,94,0.15);color:#4ade80;border:1px solid rgba(34,197,94,0.3)}
    .ticket-row{display:flex;align-items:center;gap:14px;padding:16px;background:#12121f;border:1.5px solid rgba(148,163,184,0.15);border-radius:14px;margin-bottom:10px;text-decoration:none;color:inherit}
    .ticket-row:hover{border-color:#06b6d4;transform:translateX(-3px)}
    .ticket-row .av{font-size:28px;width:48px;height:48px;border-radius:50%;background:rgba(139,92,246,0.2);display:flex;align-items:center;justify-content:center;flex-shrink:0}
    .ticket-row .info{flex:1}
    .ticket-row .title{font-size:14px;font-weight:bold;color:#fff;margin-bottom:3px}
    .ticket-row .meta{font-size:11px;color:#94a3b8}
    .badge{font-size:10px;padding:4px 12px;border-radius:8px;font-weight:bold}
    .badge-open{background:rgba(234,179,8,0.2);color:#fde68a}
    .badge-answered{background:rgba(34,197,94,0.2);color:#86efac}
    .badge-closed{background:rgba(100,116,139,0.2);color:#cbd5e1}
    .badge-in_progress{background:rgba(59,130,246,0.2);color:#93c5fd}
    .empty{text-align:center;padding:60px 20px;color:#64748b}
    .empty .icon{font-size:60px;display:block;margin-bottom:12px;opacity:0.5}
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
    <a href="/panel-admin/support/" class="admin-tab active">💬 پشتیبانی</a>
  </div>
  {% if message %}<div class="msg">{{ message.text }}</div>{% endif %}
  {% if tickets %}
    {% for t in tickets %}
      <a href="/panel-admin/support/{{ t.id }}/" class="ticket-row">
        <div class="av">{{ t.avatar }}</div>
        <div class="info">
          <div class="title">#{{ t.id }} — {{ t.subject }}</div>
          <div class="meta">👤 {{ t.user_alias }} · {{ t.created_at|jdate:"Y/m/d H:i" }}</div>
        </div>
        <span class="badge badge-{{ t.status }}">{{ t.status_display }}</span>
      </a>
    {% endfor %}
  {% else %}
    <div class="empty"><span class="icon">📭</span>هیچ تیکتی نیست</div>
  {% endif %}
</div>
</body>
</html>
''')

write("accounts/templates/custom_admin/support_detail.html", '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <title>تیکت #{{ t.id }}</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:Tahoma,sans-serif;background:#0a0a15;color:#e2e8f0;padding:20px 16px 40px}
    .container{max-width:900px;margin:0 auto}
    .topbar{display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#1e1b4b,#0f0f1e);border:1px solid rgba(239,68,68,0.3);padding:16px 22px;border-radius:16px;margin-bottom:20px}
    .topbar h1{font-size:19px;color:#fca5a5}
    .topbar a{padding:9px 16px;border-radius:10px;background:rgba(148,163,184,0.2);color:#fff;text-decoration:none;font-size:13px;font-weight:bold}
    .card{background:#12121f;border:1px solid rgba(148,163,184,0.15);border-radius:16px;padding:22px;margin-bottom:16px}
    .card h3{color:#fdba74;font-size:15px;margin-bottom:16px}
    .ticket-header{display:flex;align-items:flex-start;gap:16px;margin-bottom:18px;padding-bottom:16px;border-bottom:1px solid rgba(148,163,184,0.15)}
    .ticket-icon{font-size:44px}
    .ticket-info{flex:1}
    .ticket-title{font-size:19px;font-weight:900;color:#fff;margin-bottom:4px}
    .ticket-meta{font-size:12px;color:#94a3b8}
    .ticket-body{padding:16px;background:rgba(15,23,42,0.6);border-radius:12px;font-size:14px;line-height:1.9;white-space:pre-wrap;color:#fff}
    label{display:block;color:#94a3b8;font-size:12px;margin:12px 0 6px;font-weight:bold}
    textarea,select{width:100%;padding:12px 14px;border-radius:10px;border:1.5px solid rgba(148,163,184,0.2);background:#0a0a15;color:#fff;font-size:14px;font-family:inherit;box-sizing:border-box}
    textarea{resize:vertical;min-height:120px}
    .btn{padding:12px 24px;border-radius:10px;border:none;font-family:inherit;font-weight:900;font-size:14px;cursor:pointer;width:100%;margin-top:12px;background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff}
    .btn-delete{background:rgba(239,68,68,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.4)}
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>تیکت #{{ t.id }}</h1>
    <a href="/panel-admin/support/">← بازگشت</a>
  </div>

  {% if message %}<div class="msg" style="background:rgba(34,197,94,0.15);color:#4ade80;padding:12px 16px;border-radius:10px;margin-bottom:16px;">{{ message.text }}</div>{% endif %}

  <div class="card">
    <div class="ticket-header">
      <div class="ticket-icon">{% if t.category == 'bug' %}🐛{% elif t.category == 'idea' %}💡{% elif t.category == 'payment' %}💳{% else %}📝{% endif %}</div>
      <div class="ticket-info">
        <div class="ticket-title">{{ t.subject }}</div>
        <div class="ticket-meta">👤 {{ t.user.alias }} · {{ t.created_at|jdate:"Y/m/d H:i" }} · {{ t.status_display }}</div>
      </div>
    </div>
    <div class="ticket-body">{{ t.body }}</div>
  </div>

  <div class="card">
    <h3>💬 پاسخ ادمین</h3>
    <form method="post">
      {% csrf_token %}
      <input type="hidden" name="action" value="reply">
      <label>متن پاسخ</label>
      <textarea name="admin_reply" required>{% if t.admin_reply %}{{ t.admin_reply }}{% endif %}</textarea>
      <label>وضعیت</label>
      <select name="new_status">
        <option value="answered" {% if t.status == 'answered' %}selected{% endif %}>پاسخ داده شده</option>
        <option value="in_progress" {% if t.status == 'in_progress' %}selected{% endif %}>در حال بررسی</option>
        <option value="closed" {% if t.status == 'closed' %}selected{% endif %}>بسته شده</option>
      </select>
      <button type="submit" class="btn">📤 ارسال پاسخ</button>
    </form>
  </div>

  <div class="card" style="background:rgba(239,68,68,0.08);border-color:rgba(239,68,68,0.3);">
    <h3 style="color:#fca5a5;">⚠️ حذف</h3>
    <form method="post" onsubmit="return confirm('حذف تیکت #{{ t.id }}؟');">
      {% csrf_token %}
      <input type="hidden" name="action" value="delete">
      <button type="submit" class="btn btn-delete">🗑️ حذف تیکت</button>
    </form>
  </div>
</div>
</body>
</html>
''')

# ============================================================
# 2) GAME VIEWS — ensure puzzle, guess, memory work
# ============================================================
print("\n[2/7] Fixing game views")

game_src = read("game/views.py")

# Ensure imports
if "from django.contrib import messages" not in game_src:
    game_src = "from django.contrib import messages\n" + game_src
if "import random as _rand" not in game_src:
    game_src = "import random as _rand\n" + game_src

# Ensure puzzle_words exists
if not os.path.exists("game/puzzle_words.py"):
    words = ["کتاب","درخت","خورشید","آبشار","پروانه","خرگوش","پلنگ","دلفین","عقاب","طوطی",
             "گنجشک","اسب","شتر","خرس","گرگ","روباه","آهو","گوزن","جغد","بلبل",
             "زنبور","مورچه","عقرب","مارمولک","نهنگ","کوسه","کبوتر","سنجاب","آسمان","ابر",
             "باران","برف","رعد","دریا","اقیانوس","رودخانه","دریاچه","جنگل","کوه","تپه",
             "صحرا","بیابان","چشمه","چمن","گل","شاخه","ریشه","برگ","باد","طوفان",
             "مه","شبنم","یخ","آتشفشان","قرمز","آبی","زرد","سبز","صورتی","بنفش",
             "نارنجی","مشکی","سفید","طلایی","نقره‌ای","دفتر","میز","صندلی","تخت","پنجره",
             "دیوار","سقف","پرده","فرش","بالش","آینه","ساعت","کلید","قفل","چراغ",
             "لامپ","پنکه","یخچال","تلفن","گوشی","هدفون","چاقو","قاشق","چنگال","بشقاب",
             "لیوان","فنجان","کتری","قوری","دیگ","سطل","جارو","سبد","کیف","چمدان",
             "کفش","جوراب","شلوار","پیراهن","کلاه","دستکش","شال","روسری","عینک","دستبند",
             "گردنبند","انگشتر","توپ","عروسک","بادبادک","اسکیت","دوچرخه","راکت","شطرنج","تخته",
             "نان","برنج","مرغ","گوشت","ماهی","پنیر","کره","شیر","ماست","دوغ",
             "عسل","مربا","شکر","نمک","فلفل","زعفران","چای","قهوه","شربت","سوپ",
             "آش","پلو","کباب","خورش","سالاد","پیاز","سیر","گوجه","خیار","کاهو",
             "هویج","کدو","بادمجان","سیب","موز","پرتقال","انگور","هلو","زردآلو","گیلاس",
             "توت","انار","انجیر","خرما","انبه","آناناس","کیوی","نارگیل","لیمو","نارنگی",
             "طالبی","هندوانه","خربزه","چشم","گوش","بینی","دهان","دندان","زبان","گردن",
             "شانه","دست","انگشت","ناخن","قلب","شکم","زانو","آرنج","مو","خانه",
             "مدرسه","مسجد","بازار","فروشگاه","بیمارستان","پارک","خیابان","کوچه","میدان","پل",
             "فرودگاه","رستوران","کتابخانه","موزه","سینما","بانک","اداره","کارخانه","مزرعه","باغ",
             "ساحل","جزیره","شادی","غم","خنده","گریه","عشق","امید","ترس","خشم",
             "آرامش","هیجان","مهربانی","دوستی","پزشک","معلم","مهندس","راننده","خلبان","آشپز",
             "نجار","بنا","خیاط","نقاش","نویسنده","خواننده","بازیگر","کارگر","کشاورز","نگهبان",
             "پلیس","سرباز","قاضی","خواب","بیداری","دویدن","پریدن","نشستن","خوردن","نوشیدن",
             "خواندن","نوشتن","دیدن","فکرکردن","خندیدن","رقصیدن","آوازخواندن"]
    write("game/puzzle_words.py", f'''# -*- coding: utf-8 -*-
PUZZLE_WORDS = {words!r}

def get_puzzle_words():
    return [w for w in PUZZLE_WORDS if 4 <= len(w) <= 8]
''')

# Check which views exist
existing = set(re.findall(r'^def ([a-zA-Z_][a-zA-Z0-9_]*)\(', game_src, re.MULTILINE))

# Remove old puzzle/guess/memory sections
for keyword in ["Puzzle Game", "0-100 Guess", "Memory Game"]:
    pattern = re.compile(rf'# =+\s*\n# {keyword}.*?(?=\n# =+\s*\n# |\Z)', re.DOTALL)
    game_src = pattern.sub('', game_src)

# Append clean views
CLEAN_VIEWS = '''

# ============================================================
# PUZZLE GAME
# ============================================================
@login_required
def puzzle_home(request):
    check = _require_complete(request.user)
    if check:
        return check
    from game.puzzle_words import get_puzzle_words
    import time

    if request.method == "POST" and request.POST.get("action") == "new":
        request.session.pop("puzzle_items", None)

    if "puzzle_items" not in request.session or request.session.get("puzzle_finished"):
        pool = get_puzzle_words()
        picks = _rand.sample(pool, min(5, len(pool)))
        items = []
        total_time = 0
        for i, w in enumerate(picks):
            sec = len(w) * 5
            total_time += sec
            letters = list(w)
            for _ in range(30):
                _rand.shuffle(letters)
                if "".join(letters) != w:
                    break
            items.append({"idx": i, "word": w, "scrambled": " ".join(letters), "length": len(w), "seconds": sec})
        request.session["puzzle_items"] = items
        request.session["puzzle_start_ts"] = int(time.time())
        request.session["puzzle_total_time"] = total_time
        request.session["puzzle_finished"] = False
        request.session["puzzle_score"] = 0

    items = request.session.get("puzzle_items", [])
    start_ts = request.session.get("puzzle_start_ts", 0)
    total_time = request.session.get("puzzle_total_time", 60)
    elapsed = int(time.time() - start_ts) if start_ts else 0
    remaining = max(0, total_time - elapsed)

    if remaining <= 0 and not request.session.get("puzzle_finished"):
        request.session["puzzle_finished"] = True

    if request.session.get("puzzle_finished"):
        return render(request, "game/puzzle.html", {"finished": True, "score": request.session.get("puzzle_score", 0), "total": len(items), "active": "games"})

    return render(request, "game/puzzle.html", {"items": items, "total": len(items), "remaining": remaining, "total_time": total_time, "finished": False, "active": "games"})


@login_required
def puzzle_submit(request):
    check = _require_complete(request.user)
    if check:
        return check
    if request.method != "POST":
        return redirect("game:puzzle")
    if request.POST.get("action") == "new":
        request.session.pop("puzzle_items", None)
        return redirect("game:puzzle")
    items = request.session.get("puzzle_items", [])
    correct = 0
    for it in items:
        ans = (request.POST.get(f"ans_{it['idx']}") or "").strip().replace("ي","ی").replace("ك","ک").replace(" ","").replace("\\u200c","")
        target = it["word"].replace("ي","ی").replace("ك","ک").replace(" ","").replace("\\u200c","")
        if ans == target:
            correct += 1
    request.session["puzzle_score"] = correct * 10
    request.session["puzzle_finished"] = True
    messages.success(request, f"🎯 {correct} از {len(items)} درست!")
    return redirect("game:puzzle")


# ============================================================
# MEMORY GAME
# ============================================================
_MEMORY_EMOJIS = ["🐶","🐱","🦁","🐯","🐻","🐼","🐨","🐸","🦊","🐵","🦄","🐲"]

@login_required
def memory_home(request):
    check = _require_complete(request.user)
    if check:
        return check
    if request.method == "POST" and request.POST.get("action") == "new":
        request.session.pop("memory_cards", None)
    if "memory_cards" not in request.session:
        emojis = _rand.sample(_MEMORY_EMOJIS, 8)
        cards_raw = emojis * 2
        _rand.shuffle(cards_raw)
        cards = [{"id": i, "emoji": em, "flipped": False, "matched": False} for i, em in enumerate(cards_raw)]
        request.session["memory_cards"] = cards
    cards = request.session.get("memory_cards", [])
    return render(request, "game/memory.html", {"cards": cards, "total_pairs": len(cards) // 2, "active": "games"})


# ============================================================
# GUESS GAME (0-100)
# ============================================================
@login_required
def guess_home(request):
    check = _require_complete(request.user)
    if check:
        return check
    if request.method == "POST" and request.POST.get("action") == "new":
        request.session.pop("guess_number", None)
    if "guess_number" not in request.session:
        request.session["guess_number"] = _rand.randint(0, 100)
        request.session["guess_tries"] = 0
        request.session["guess_max"] = 7
        request.session["guess_finished"] = False
        request.session["guess_won"] = False
        request.session["guess_history"] = []
    return render(request, "game/guess.html", {
        "tries": request.session.get("guess_tries", 0),
        "max_tries": request.session.get("guess_max", 7),
        "finished": request.session.get("guess_finished", False),
        "won": request.session.get("guess_won", False),
        "number": request.session.get("guess_number") if request.session.get("guess_finished") else None,
        "history": request.session.get("guess_history", []),
        "active": "games",
    })


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
        messages.error(request, "عدد بین ۰ تا ۱۰۰ باشه.")
        return redirect("game:guess")
    number = request.session.get("guess_number", 50)
    tries = request.session.get("guess_tries", 0) + 1
    max_tries = request.session.get("guess_max", 7)
    history = request.session.get("guess_history", [])
    if guess == number:
        request.session["guess_won"] = True
        request.session["guess_finished"] = True
        history.append({"guess": guess, "result": "win"})
        messages.success(request, f"🎉 آفرین! عدد {number} بود.")
    elif tries >= max_tries:
        request.session["guess_won"] = False
        request.session["guess_finished"] = True
        history.append({"guess": guess, "result": "low" if guess < number else "high"})
        messages.error(request, f"❌ باختی! عدد {number} بود.")
    else:
        result = "low" if guess < number else "high"
        history.append({"guess": guess, "result": result})
        if result == "low":
            messages.info(request, f"⬆️ بزرگ‌تره! ({max_tries - tries} تلاش دیگه)")
        else:
            messages.info(request, f"⬇️ کوچیک‌تره! ({max_tries - tries} تلاش دیگه)")
    request.session["guess_tries"] = tries
    request.session["guess_history"] = history
    return redirect("game:guess")
'''

game_src = game_src.rstrip() + CLEAN_VIEWS + "\n"
write("game/views.py", game_src)

# ============================================================
# 3) TEMPLATES — puzzle, guess, memory
# ============================================================
print("\n[3/7] Writing game templates")

write("game/templates/game/puzzle.html", '''{% extends "base.html" %}
{% block title %}بازی معما{% endblock %}
{% block extra_css %}
<style>
  .head{display:flex;align-items:center;gap:12px;justify-content:space-between;margin-bottom:18px}
  .head-left{display:flex;align-items:center;gap:12px}
  .head h1{font-size:22px;font-weight:900;background:linear-gradient(135deg,#4ade80,#16a34a);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
  .timer-badge{background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff;padding:8px 18px;border-radius:999px;font-size:16px;font-weight:900;font-family:monospace;box-shadow:0 8px 25px rgba(239,68,68,0.4)}
  .intro{background:linear-gradient(135deg,#0a2a1a,#0f0f1e);border:2px solid rgba(34,197,94,0.5);border-radius:20px;padding:18px 20px;margin-bottom:18px;text-align:center}
  .intro h2{font-size:17px;color:#bbf7d0;margin-bottom:4px;font-weight:900}
  .intro p{font-size:12px;color:#94a3b8;line-height:1.6}
  .word-item{background:var(--card);border:1.5px solid rgba(34,197,94,0.3);border-radius:18px;padding:16px;margin-bottom:12px}
  .word-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
  .word-num{font-size:11px;color:#94a3b8;font-weight:900;font-family:monospace}
  .word-sec{font-size:10px;color:#4ade80;padding:2px 8px;background:rgba(34,197,94,0.15);border-radius:6px;font-family:monospace;font-weight:900}
  .scrambled{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;margin-bottom:12px}
  .letter-tile{width:42px;height:42px;border-radius:10px;background:linear-gradient(135deg,rgba(34,197,94,0.25),rgba(6,182,212,0.15));border:1.5px solid rgba(34,197,94,0.5);display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:900;color:#bbf7d0;box-shadow:0 4px 12px rgba(34,197,94,0.2)}
  .answer-input{width:100%;padding:14px 16px;border-radius:12px;border:2px solid rgba(34,197,94,0.4);background:rgba(15,23,42,0.8);color:#fff;font-size:20px;text-align:center;font-weight:900;letter-spacing:4px;box-sizing:border-box;font-family:inherit}
  .answer-input:focus{outline:none;border-color:#4ade80;box-shadow:0 0 20px rgba(34,197,94,0.3)}
  .btn-submit{width:100%;padding:16px;border:none;border-radius:14px;background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;font-size:17px;font-weight:900;font-family:inherit;cursor:pointer;box-shadow:0 10px 30px rgba(34,197,94,0.4);margin-top:12px}
  .btn-new{display:block;width:100%;padding:16px;border:none;border-radius:14px;background:linear-gradient(135deg,#f4c542,#eab308);color:#1a1a1a;font-size:16px;font-weight:900;font-family:inherit;cursor:pointer;text-align:center;box-shadow:0 10px 30px rgba(244,197,66,0.4);margin-top:12px}
  .finished-panel{text-align:center;padding:30px 20px;border-radius:22px;background:linear-gradient(135deg,#2a1a0e,#0f0f1e);border:2px solid rgba(244,197,66,0.5);margin-bottom:16px}
  .finished-panel .big-icon{font-size:70px;margin-bottom:12px}
  .finished-panel h2{font-size:22px;font-weight:900;color:#fde68a;margin-bottom:10px}
  .finished-panel .score-line{font-size:15px;color:#fff;font-family:monospace;margin-bottom:14px}
  .finished-panel .score-line b{color:#fde68a}
</style>
{% endblock %}
{% block content %}
<div class="head">
  <div class="head-left">
    <a href="/game/rooms/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>🎯 بازی معما</h1>
  </div>
  {% if not finished %}<div class="timer-badge">⏱ <span id="timerNum">{{ remaining }}</span></div>{% endif %}
</div>

{% if finished %}
  <div class="finished-panel">
    <div class="big-icon">🏆</div>
    <h2>نتیجه بازی</h2>
    <div class="score-line">امتیاز: <b>{{ score|default:0 }}</b> از {{ total|default:0 }}</div>
  </div>
  <form method="post" action="/game/puzzle/submit/">
    {% csrf_token %}
    <input type="hidden" name="action" value="new">
    <button type="submit" class="btn-new">🔄 بازی جدید</button>
  </form>
{% else %}
  <div class="intro">
    <h2>🧩 حروف رو مرتب کن!</h2>
    <p>هر کلمه از حروف به‌هم‌ریخته ساخته شده. کلمه‌ی درست رو تایپ کن.</p>
  </div>
  <form method="post" action="/game/puzzle/submit/" id="puzzleForm">
    {% csrf_token %}
    {% for it in items %}
      <div class="word-item">
        <div class="word-head">
          <span class="word-num">کلمه {{ forloop.counter }}</span>
          <span class="word-sec">{{ it.seconds }} ثانیه</span>
        </div>
        <div class="scrambled">
          {% for c in it.scrambled.split %}
            <div class="letter-tile">{{ c }}</div>
          {% endfor %}
        </div>
        <input type="text" name="ans_{{ it.idx }}" class="answer-input" placeholder="کلمه..." maxlength="10" autocomplete="off">
      </div>
    {% endfor %}
    <button type="submit" class="btn-submit">✅ ثبت همه</button>
  </form>
{% endif %}
{% endblock %}
{% block extra_js %}
{% if not finished %}
<script>
  let remaining = {{ remaining }};
  const timerEl = document.getElementById('timerNum');
  function tick() {
    if (remaining <= 0) { document.getElementById('puzzleForm').submit(); return; }
    remaining--;
    if (timerEl) timerEl.textContent = remaining;
    setTimeout(tick, 1000);
  }
  setTimeout(tick, 1000);
</script>
{% endif %}
{% endblock %}
''')

write("game/templates/game/guess.html", '''{% extends "base.html" %}
{% block title %}بازی ۰ تا ۱۰۰{% endblock %}
{% block extra_css %}
<style>
  .head{display:flex;align-items:center;gap:12px;margin-bottom:20px}
  .head h1{font-size:24px;font-weight:900;background:linear-gradient(135deg,#06b6d4,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
  .hero{background:linear-gradient(135deg,#0a1e2a,#0f0f1e);border:2px solid rgba(6,182,212,0.5);border-radius:22px;padding:26px 22px;margin-bottom:20px;text-align:center}
  .hero-icon{font-size:60px;margin-bottom:10px}
  .hero-title{font-size:20px;font-weight:900;color:#a5f3fc;margin-bottom:6px}
  .hero-desc{font-size:13px;color:#94a3b8;line-height:1.6}
  .tries-info{display:flex;justify-content:center;gap:6px;margin-top:18px}
  .tries-dot{width:24px;height:8px;border-radius:4px;background:rgba(148,163,184,0.2)}
  .tries-dot.used{background:linear-gradient(90deg,#ef4444,#dc2626)}
  .tries-dot.left{background:linear-gradient(90deg,#22c55e,#16a34a)}
  .history{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:16px;margin-bottom:16px;max-height:220px;overflow-y:auto}
  .history-item{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:10px;margin-bottom:6px;background:rgba(15,23,42,0.5);border:1px solid rgba(148,163,184,0.1);font-size:13px}
  .history-item .num{font-family:monospace;font-weight:900;color:#fff;width:40px;text-align:center}
  .history-item .arrow{font-size:18px}
  .history-item.low{border-color:rgba(34,197,94,0.3);background:rgba(34,197,94,0.08)}
  .history-item.low .arrow{color:#4ade80}
  .history-item.high{border-color:rgba(239,68,68,0.3);background:rgba(239,68,68,0.08)}
  .history-item.high .arrow{color:#f87171}
  .history-item.win{border-color:rgba(244,197,66,0.5);background:rgba(244,197,66,0.15)}
  .history-item.win .arrow{color:#fde68a}
  .input-form{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:22px}
  .input-form input[type=number]{width:100%;padding:20px;border-radius:14px;border:2px solid rgba(6,182,212,0.4);background:rgba(15,23,42,0.8);color:#fff;font-size:32px;font-family:monospace;text-align:center;font-weight:900;margin-bottom:14px;box-sizing:border-box;-moz-appearance:textfield}
  .input-form input[type=number]::-webkit-outer-spin-button,.input-form input[type=number]::-webkit-inner-spin-button{-webkit-appearance:none;margin:0}
  .input-form input:focus{outline:none;border-color:#22d3ee;box-shadow:0 0 25px rgba(6,182,212,0.3)}
  .btn-guess{width:100%;padding:16px;border:none;border-radius:14px;background:linear-gradient(135deg,#06b6d4,#3b82f6);color:#fff;font-size:17px;font-weight:900;font-family:inherit;cursor:pointer;box-shadow:0 10px 30px rgba(6,182,212,0.4)}
  .finished-box{text-align:center;padding:30px 20px;border-radius:20px;margin-bottom:16px}
  .finished-box.won{background:rgba(34,197,94,0.15);border:2px solid rgba(34,197,94,0.4)}
  .finished-box.lost{background:rgba(239,68,68,0.15);border:2px solid rgba(239,68,68,0.4)}
  .finished-box .fi{font-size:60px;margin-bottom:10px}
  .finished-box .ft{font-size:20px;font-weight:900;margin-bottom:6px}
  .finished-box.won .ft{color:#4ade80}
  .finished-box.lost .ft{color:#f87171}
  .finished-box .fw{font-size:16px;color:#fff;font-family:monospace}
  .btn-new{display:block;width:100%;padding:16px;border:none;border-radius:14px;background:linear-gradient(135deg,#f4c542,#eab308);color:#1a1a1a;font-size:16px;font-weight:900;font-family:inherit;cursor:pointer;text-align:center;box-shadow:0 10px 30px rgba(244,197,66,0.4);margin-top:12px}
</style>
{% endblock %}
{% block content %}
<div class="head">
  <a href="/game/rooms/" class="back-btn"><span class="arrow-icon">→</span></a>
  <h1>🎲 بازی ۰ تا ۱۰۰</h1>
</div>

<div class="hero">
  <div class="hero-icon">🎲</div>
  <div class="hero-title">حدس عدد</div>
  <div class="hero-desc">یه عدد بین ۰ تا ۱۰۰ انتخاب شده.<br>با ۷ تلاش پیداش کن!</div>
  <div class="tries-info">
    {% for i in "1234567" %}
      {% if forloop.counter0 < tries %}<div class="tries-dot used"></div>
      {% elif not finished %}<div class="tries-dot left"></div>
      {% else %}<div class="tries-dot"></div>{% endif %}
    {% endfor %}
  </div>
</div>

{% if finished %}
  <div class="finished-box {% if won %}won{% else %}lost{% endif %}">
    <div class="fi">{% if won %}🏆{% else %}😢{% endif %}</div>
    <div class="ft">{% if won %}آفرین! درست حدس زدی{% else %}تموم شد!{% endif %}</div>
    <div class="fw">عدد: {{ number }}</div>
  </div>
  <form method="post">
    {% csrf_token %}
    <input type="hidden" name="action" value="new">
    <button type="submit" class="btn-new">🔄 بازی جدید</button>
  </form>
{% else %}
  {% if history %}
    <div class="history">
      {% for h in history %}
        <div class="history-item {% if h.result == 'win' %}win{% else %}{{ h.result }}{% endif %}">
          <div class="num">{{ h.guess }}</div>
          <div class="arrow">{% if h.result == 'win' %}🎯{% elif h.result == 'low' %}⬆️{% else %}⬇️{% endif %}</div>
        </div>
      {% endfor %}
    </div>
  {% endif %}
  <form method="post" action="/game/guess/attempt/" class="input-form">
    {% csrf_token %}
    <input type="number" name="guess" min="0" max="100" required placeholder="50" autofocus>
    <button type="submit" class="btn-guess">🎯 حدس بزن</button>
  </form>
{% endif %}
{% endblock %}
''')

write("game/templates/game/memory.html", '''{% extends "base.html" %}
{% block title %}بازی حافظه{% endblock %}
{% block extra_css %}
<style>
  .head{display:flex;align-items:center;gap:12px;margin-bottom:18px}
  .head h1{font-size:22px;font-weight:900;background:linear-gradient(135deg,#a78bfa,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
  .intro{background:linear-gradient(135deg,#1a0f2e,#0f0f1e);border:2px solid rgba(139,92,246,0.5);border-radius:20px;padding:16px 20px;margin-bottom:18px;text-align:center}
  .intro h2{font-size:16px;color:#e9d5ff;margin-bottom:4px;font-weight:900}
  .intro p{font-size:12px;color:#94a3b8;line-height:1.6}
  .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:20px}
  .card{aspect-ratio:1;position:relative;perspective:600px;cursor:pointer}
  .card-inner{position:relative;width:100%;height:100%;transition:transform 0.5s;transform-style:preserve-3d}
  .card.flipped .card-inner,.card.matched .card-inner{transform:rotateY(180deg)}
  .card-face{position:absolute;inset:0;border-radius:14px;display:flex;align-items:center;justify-content:center;backface-visibility:hidden;-webkit-backface-visibility:hidden}
  .card-back{background:linear-gradient(135deg,rgba(139,92,246,0.4),rgba(6,182,212,0.3));border:2px solid rgba(139,92,246,0.6);font-size:32px;color:rgba(255,255,255,0.3)}
  .card-front{background:linear-gradient(135deg,rgba(244,197,66,0.35),rgba(139,92,246,0.25));border:2px solid rgba(244,197,66,0.6);font-size:36px;transform:rotateY(180deg)}
  .card.matched .card-front{background:linear-gradient(135deg,rgba(34,197,94,0.35),rgba(6,182,212,0.25));border-color:rgba(34,197,94,0.7)}
  .btn-new{display:block;width:100%;padding:16px;border:none;border-radius:14px;background:linear-gradient(135deg,#f4c542,#eab308);color:#1a1a1a;font-size:16px;font-weight:900;font-family:inherit;cursor:pointer;text-align:center;box-shadow:0 10px 30px rgba(244,197,66,0.4);margin-top:8px}
  .stats-bar{display:flex;gap:8px;margin-bottom:16px}
  .stat-chip{flex:1;background:rgba(139,92,246,0.15);border:1.5px solid rgba(139,92,246,0.4);border-radius:12px;padding:10px;text-align:center}
  .stat-chip .lbl{font-size:10px;color:#94a3b8;margin-bottom:2px}
  .stat-chip .val{font-size:16px;font-weight:900;color:#c4b5fd;font-family:monospace}
</style>
{% endblock %}
{% block content %}
<div class="head">
  <a href="/game/rooms/" class="back-btn"><span class="arrow-icon">→</span></a>
  <h1>🧠 بازی حافظه</h1>
</div>

<div class="stats-bar">
  <div class="stat-chip"><div class="lbl">جفت‌ها</div><div class="val" id="matchedCount">0 / {{ total_pairs }}</div></div>
  <div class="stat-chip"><div class="lbl">حرکت</div><div class="val" id="movesCount">0</div></div>
</div>

<div class="intro">
  <h2>🧠 حافظه‌ت رو بسنج!</h2>
  <p>کارت‌ها رو باز کن، جفت‌های یکسان رو پیدا کن</p>
</div>

<div class="grid" id="memoryGrid">
  {% for c in cards %}
    <div class="card" data-emoji="{{ c.emoji }}" onclick="flipCard(this)">
      <div class="card-inner">
        <div class="card-face card-back">❓</div>
        <div class="card-face card-front">{{ c.emoji }}</div>
      </div>
    </div>
  {% endfor %}
</div>

<form method="post">
  {% csrf_token %}
  <input type="hidden" name="action" value="new">
  <button type="submit" class="btn-new">🔄 بازی جدید</button>
</form>
{% endblock %}
{% block extra_js %}
<script>
  let firstCard = null, secondCard = null, lock = false, matched = 0, moves = 0;
  let totalPairs = {{ total_pairs }};
  function flipCard(card) {
    if (lock || card.classList.contains('flipped') || card.classList.contains('matched')) return;
    card.classList.add('flipped');
    if (!firstCard) { firstCard = card; return; }
    secondCard = card;
    lock = true;
    moves++;
    document.getElementById('movesCount').textContent = moves;
    if (firstCard.dataset.emoji === secondCard.dataset.emoji) {
      setTimeout(() => {
        firstCard.classList.add('matched');
        secondCard.classList.add('matched');
        matched++;
        document.getElementById('matchedCount').textContent = matched + " / " + totalPairs;
        reset();
        if (matched >= totalPairs) setTimeout(() => alert('🎉 بردی! در ' + moves + ' حرکت'), 300);
      }, 500);
    } else {
      setTimeout(() => {
        firstCard.classList.remove('flipped');
        secondCard.classList.remove('flipped');
        reset();
      }, 800);
    }
  }
  function reset() { firstCard = null; secondCard = null; lock = false; }
</script>
{% endblock %}
''')

# ============================================================
# 4) Ensure support in INSTALLED_APPS + URLs
# ============================================================
print("\n[4/7] Ensuring config")

settings_src = read("config/settings.py")
if '"support"' not in settings_src:
    if '"social",' in settings_src:
        settings_src = settings_src.replace('"social",', '"social",\n    "support",', 1)
    write("config/settings.py", settings_src)
    print("  ✓ support added to INSTALLED_APPS")

urls_src = read("config/urls.py")
if "support.urls" not in urls_src:
    if 'path("alliance/", include("alliance.urls")),' in urls_src:
        urls_src = urls_src.replace(
            'path("alliance/", include("alliance.urls")),',
            'path("alliance/", include("alliance.urls")),\n    path("support/", include("support.urls")),'
        )
    write("config/urls.py", urls_src)
    print("  ✓ support URL added")

# ============================================================
# 5) Check game/urls.py
# ============================================================
print("\n[5/7] Ensuring game/urls.py")

game_urls = read("game/urls.py")
game_views = read("game/views.py")
existing_fns = set(re.findall(r'^def ([a-zA-Z_][a-zA-Z0-9_]*)\(', game_views, re.MULTILINE))

routes = [
    ("", "home", "home"),
    ("rooms/", "rooms_list", "rooms"),
    ("rooms/manage/", "rooms_manage", "rooms_manage"),
    ("rooms/join/<str:room_code>/", "join_room", "join_room"),
    ("room/<str:room_code>/", "room", "room"),
    ("leaderboard/", "leaderboard_view", "leaderboard"),
    ("top-players/", "top_players_view", "top_players"),
    ("quick/", "quick_play", "quick_play"),
    ("quick/bot/", "bot_setup", "bot_setup"),
    ("quick/bot/play/<uuid:game_id>/", "bot_play", "bot_play"),
    ("quick/bot/submit/<uuid:game_id>/", "bot_submit", "bot_submit"),
    ("challenge/", "challenge_home", "challenge"),
    ("match/", "match_start", "match_start"),
    ("match/wait/", "match_wait", "match_wait"),
    ("match/cancel/", "match_cancel", "match_cancel"),
    ("match/status/", "match_status", "match_status"),
    ("team/start/", "team_start", "team_start"),
    ("team/wait/", "team_wait", "team_wait"),
    ("team/cancel/", "team_cancel", "team_cancel"),
    ("team/status/", "team_status", "team_status"),
    ("team/select/<str:room_code>/", "team_select", "team_select"),
    ("team/play/<str:room_code>/", "team_play", "team_play"),
    ("puzzle/", "puzzle_home", "puzzle"),
    ("puzzle/submit/", "puzzle_submit", "puzzle_submit"),
    ("memory/", "memory_home", "memory"),
    ("guess/", "guess_home", "guess"),
    ("guess/attempt/", "guess_attempt", "guess_attempt"),
]

valid = [r for r in routes if r[1] in existing_fns]
missing = [r for r in routes if r[1] not in existing_fns]

url_patterns = "\n".join([f'    path("{r[0]}", views.{r[1]}, name="{r[2]}"),' for r in valid])
write("game/urls.py", f'''from django.urls import path
from . import views

app_name = "game"

urlpatterns = [
{url_patterns}
]
''')

print(f"  ✓ {len(valid)} routes")
for r in missing:
    print(f"  ⚠ missing view: {r[1]}")

# ============================================================
# 6) Run migrations
# ============================================================
print("\n[6/7] Migrations")

for cmd in [
    [sys.executable, "manage.py", "makemigrations", "support", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    print(f"\n  $ {' '.join(cmd[1:])}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode == 0:
        if r.stdout.strip(): print(f"    {r.stdout.strip()[:300]}")
    else:
        print(f"    ⚠ {r.stderr[:300] if r.stderr else 'unknown'}")

# ============================================================
# 7) TEST
# ============================================================
print("\n[7/7] Testing")

TEST = '''
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
import django
django.setup()
from django.test import Client
from accounts.models import User

User.objects.filter(username__startswith="__final_test_").delete()
u = User.objects.create_user(
    username="__final_test_u", password="x"*10, alias="تست",
    is_active=True, has_chosen_avatar=True, has_completed_registration=True,
    coins=200,
)

c = Client()
c.force_login(u)
c.session["beta_unlocked"] = True
c.session.save()

tests = [
    ("/game/", "خانه"),
    ("/support/", "پشتیبانی"),
    ("/game/puzzle/", "معما"),
    ("/game/guess/", "۰ تا ۱۰۰"),
    ("/game/memory/", "حافظه"),
    ("/game/rooms/", "بازی‌ها"),
    ("/accounts/shop/", "فروشگاه"),
    ("/accounts/avatar/", "آواتار"),
    ("/panel-admin/support/", "ادمین پشتیبانی"),
]

for url, name in tests:
    try:
        r = c.get(url, follow=False)
        mark = "OK" if r.status_code == 200 else f"-> {r.status_code}"
        print(f"  {mark:10s} {url:25s} ({name})")
    except Exception as e:
        print(f"  ERR        {url:25s} ({name}) {type(e).__name__}")

# Test creating a ticket
try:
    r = c.post("/support/", {"subject": "__TEST_TICKET__", "body": "این یک پیام تستی طولانی است", "category": "general"}, follow=False)
    from support.models import SupportTicket
    ticket = SupportTicket.objects.filter(subject="__TEST_TICKET__").first()
    if ticket:
        print(f"\\n  ✓ Ticket created: #{ticket.id}")
        r = c.get(f"/support/{ticket.id}/")
        print(f"  {'OK' if r.status_code == 200 else 'ERR':10s} /support/{ticket.id}/ (مشاهده تیکت)")
        ticket.delete()
except Exception as e:
    print(f"  ERR ticket create: {e}")

u.delete()
'''

r = subprocess.run([sys.executable, "-c", TEST], env={**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings"}, capture_output=True, text=True, timeout=60)
print(r.stdout)
if r.stderr and "Traceback" in r.stderr:
    print(f"\n  Traceback:\n{r.stderr[:800]}")

# Final check
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True, timeout=30)
if r.returncode == 0:
    print("\n  ✓ Django check PASSED")
else:
    print(f"\n  ⚠ {r.stderr[:400] if r.stderr else r.stdout[:400]}")

print("\n" + "="*60)
print("✅ تموم شد")
print("="*60)
print("""
چه چیزایی ساخته شد:

  💬 پشتیبانی (کامل):
     ✓ /support/ → لیست + فرم
     ✓ /support/<id>/ → جزئیات + پاسخ
     ✓ /panel-admin/support/ → پنل ادمین
     ✓ migration ساخته شد

  🎯 بازی معما:
     ✓ ۲۰۰+ کلمه
     ✓ ۵ کلمه تصادفی
     ✓ تایمر

  🎲 بازی ۰ تا ۱۰۰:
     ✓ حدس عدد ۰-۱۰۰
     ✓ ۷ تلاش
     ✓ هیستوری

  🧠 بازی حافظه:
     ✓ ۸ جفت ایموجی
     ✓ 3D flip

حالا سرور رو ران کن:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)

تست:
  http://127.0.0.1:8000/support/
  http://127.0.0.1:8000/game/puzzle/
  http://127.0.0.1:8000/game/guess/
  http://127.0.0.1:8000/game/memory/
""")
