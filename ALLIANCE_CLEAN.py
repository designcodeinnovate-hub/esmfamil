#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Complete clean rebuild of alliance app."""
import os, sys, subprocess, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) models.py - keep existing, verify
# ============================================================
print("\n[1/10] models.py verify")
p = "alliance/models.py"
src = read(p)
if "class Alliance(models.Model):" in src and "class AllianceMember(models.Model):" in src:
    print("  ✓ models OK")
else:
    print("  ⚠ models missing classes — rewriting")
    write(p, '''# -*- coding: utf-8 -*-
import random
import string
from django.conf import settings
from django.db import models
from django.utils import timezone


def _generate_invite_code():
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Alliance.objects.filter(invite_code=code).exists():
            return code


class Alliance(models.Model):
    name = models.CharField(max_length=40, unique=True)
    tag = models.CharField(max_length=8, blank=True)
    description = models.CharField(max_length=200, blank=True)
    emblem = models.CharField(max_length=4, default="🛡️")
    invite_code = models.CharField(max_length=6, unique=True, editable=False)
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="led_alliances",
    )
    max_members = models.PositiveIntegerField(default=30)
    password = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = _generate_invite_code()
        super().save(*args, **kwargs)

    def member_count(self):
        return self.members.count()

    def __str__(self):
        return f"{self.emblem} {self.name}"


class AllianceMember(models.Model):
    ROLE_CHOICES = [
        ("leader", "رهبر"),
        ("officer", "افسر"),
        ("member", "عضو"),
    ]
    alliance = models.ForeignKey(Alliance, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alliance_memberships")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("alliance", "user")

    def __str__(self):
        return f"{self.user.alias} in {self.alliance.name}"


class AllianceMessage(models.Model):
    alliance = models.ForeignKey(Alliance, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.CharField(max_length=500)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sent_at",)

    def __str__(self):
        return f"{self.sender.alias}: {self.body[:30]}")
''')

# ============================================================
# 2) views.py - full rewrite
# ============================================================
print("\n[2/10] views.py full rewrite")

VIEWS = '''# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta

from accounts.avatars import get_emoji
from .models import Alliance, AllianceMember, AllianceMessage


def _avatar(user):
    return get_emoji(user.avatar_id)


# ============================================================
# HOME — list all alliances (or redirect if member)
# ============================================================
@login_required
def alliance_home(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    my_membership = AllianceMember.objects.filter(user=request.user).select_related("alliance").first()
    if my_membership:
        return redirect("alliance:detail", alliance_id=my_membership.alliance.id)

    query = (request.GET.get("q") or "").strip()
    qs = Alliance.objects.all().order_by("-created_at")
    if query:
        from django.db.models import Q
        qs = qs.filter(Q(name__icontains=query) | Q(tag__icontains=query))

    data = []
    for a in qs[:50]:
        count = a.member_count()
        data.append({
            "obj": a,
            "count": count,
            "is_full": count >= a.max_members,
            "has_password": bool(a.password),
            "leader_avatar": _avatar(a.leader),
        })

    return render(request, "alliance/home.html", {
        "alliances": data,
        "query": query,
        "active": "friends",
    })


# ============================================================
# CREATE
# ============================================================
@login_required
def create_alliance(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    if AllianceMember.objects.filter(user=request.user).exists():
        messages.info(request, "شما الان عضو یک اتحاد هستید.")
        return redirect("alliance:home")

    error = None
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()[:40]
        tag = (request.POST.get("tag") or "").strip().upper()[:8]
        description = (request.POST.get("description") or "").strip()[:200]
        emblem = (request.POST.get("emblem") or "🛡️").strip()[:4]
        password = (request.POST.get("password") or "").strip()[:32]
        try:
            max_members = int(request.POST.get("max_members") or 30)
        except (ValueError, TypeError):
            max_members = 30
        max_members = max(5, min(50, max_members))

        if not name:
            error = "نام اتحاد را وارد کن."
        elif len(name) < 3:
            error = "نام اتحاد باید حداقل ۳ حرف باشد."
        elif Alliance.objects.filter(name=name).exists():
            error = "این نام قبلاً گرفته شده."
        else:
            a = Alliance.objects.create(
                name=name, tag=tag, description=description,
                emblem=emblem or "🛡️", leader=request.user,
                max_members=max_members, password=password,
            )
            AllianceMember.objects.create(alliance=a, user=request.user, role="leader")
            messages.success(request, f"اتحاد «{name}» ساخته شد!")
            return redirect("alliance:detail", alliance_id=a.id)

    emojis = ["🛡️", "⚔️", "🏰", "🐉", "🦅", "🐺", "🔥", "⚡", "👑", "💎", "🌟", "🦁"]
    return render(request, "alliance/create.html", {
        "error": error,
        "emojis": emojis,
        "active": "friends",
    })


# ============================================================
# JOIN (by ID, with password check)
# ============================================================
@login_required
def join_alliance(request, alliance_id):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    if AllianceMember.objects.filter(user=request.user).exists():
        messages.info(request, "شما الان عضو یک اتحاد هستید.")
        return redirect("alliance:home")

    a = get_object_or_404(Alliance, id=alliance_id)

    if request.method != "POST":
        return redirect("alliance:home")

    if a.password:
        entered = (request.POST.get("password") or "").strip()
        if entered != a.password:
            messages.error(request, "رمز اتحاد اشتباه است.")
            return redirect("alliance:home")

    if a.member_count() >= a.max_members:
        messages.error(request, "این اتحاد پر شده است.")
        return redirect("alliance:home")

    AllianceMember.objects.create(alliance=a, user=request.user, role="member")
    messages.success(request, f"به اتحاد «{a.name}» پیوستی!")
    return redirect("alliance:detail", alliance_id=a.id)


# ============================================================
# JOIN BY CODE (legacy, keep for compatibility)
# ============================================================
@login_required
def join_by_code(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    if AllianceMember.objects.filter(user=request.user).exists():
        messages.info(request, "شما الان عضو یک اتحاد هستید.")
        return redirect("alliance:home")

    error = None
    if request.method == "POST":
        code = (request.POST.get("code") or "").strip().upper()
        a = Alliance.objects.filter(invite_code=code).first()
        if not a:
            error = "کد دعوت نامعتبر است."
        elif a.member_count() >= a.max_members:
            error = "این اتحاد پر است."
        else:
            AllianceMember.objects.create(alliance=a, user=request.user, role="member")
            messages.success(request, f"به اتحاد «{a.name}» پیوستی!")
            return redirect("alliance:detail", alliance_id=a.id)

    return render(request, "alliance/join.html", {"error": error, "active": "friends"})


# ============================================================
# DETAIL
# ============================================================
@login_required
def alliance_detail(request, alliance_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    my_membership = AllianceMember.objects.filter(alliance=a, user=request.user).first()

    if not my_membership:
        messages.info(request, "برای دیدن اتحاد باید عضو شوی.")
        return redirect("alliance:home")

    now = timezone.now()
    online_threshold = now - timedelta(minutes=5)

    members = AllianceMember.objects.filter(alliance=a).select_related("user").order_by("role", "-joined_at")
    members_data = []
    for m in members:
        is_online = m.user.last_seen and m.user.last_seen >= online_threshold
        stats = m.user.player_set.aggregate(total_score=Sum("score"))
        total_score = stats["total_score"] or 0
        level = 1 + total_score // 100
        members_data.append({
            "user": m.user,
            "avatar": _avatar(m.user),
            "role": m.role,
            "role_display": m.get_role_display(),
            "joined_at": m.joined_at,
            "is_online": is_online,
            "level": level,
        })

    recent_messages = AllianceMessage.objects.filter(alliance=a).select_related("sender").order_by("-sent_at")[:5]
    recent_messages = list(reversed(recent_messages))

    return render(request, "alliance/detail.html", {
        "alliance": a,
        "members": members_data,
        "my_role": my_membership.role,
        "is_leader": my_membership.role == "leader",
        "recent_messages": recent_messages,
        "member_count": len(members_data),
        "active": "friends",
    })


# ============================================================
# EDIT (leader only)
# ============================================================
@login_required
def alliance_edit(request, alliance_id):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    a = get_object_or_404(Alliance, id=alliance_id)
    my_m = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not my_m or my_m.role != "leader":
        messages.error(request, "فقط رهبر می‌تونه ویرایش کنه.")
        return redirect("alliance:detail", alliance_id=a.id)

    error = None
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()[:40]
        tag = (request.POST.get("tag") or "").strip().upper()[:8]
        description = (request.POST.get("description") or "").strip()[:200]
        emblem = (request.POST.get("emblem") or a.emblem).strip()[:4]
        password = (request.POST.get("password") or "").strip()[:32]
        try:
            max_members = int(request.POST.get("max_members") or a.max_members)
        except (ValueError, TypeError):
            max_members = a.max_members
        max_members = max(5, min(50, max_members))

        if not name:
            error = "نام اتحاد را وارد کن."
        elif len(name) < 3:
            error = "نام اتحاد باید حداقل ۳ حرف باشد."
        elif Alliance.objects.filter(name=name).exclude(id=a.id).exists():
            error = "این نام قبلاً گرفته شده."
        elif a.member_count() > max_members:
            error = "ظرفیت جدید از تعداد فعلی اعضا کمتر است."
        else:
            a.name = name
            a.tag = tag
            a.description = description
            a.emblem = emblem or a.emblem
            a.password = password
            a.max_members = max_members
            a.save()
            messages.success(request, "تغییرات ذخیره شد.")
            return redirect("alliance:detail", alliance_id=a.id)

    emojis = ["🛡️", "⚔️", "🏰", "🐉", "🦅", "🐺", "🔥", "⚡", "👑", "💎", "🌟", "🦁"]
    return render(request, "alliance/edit.html", {
        "alliance": a,
        "error": error,
        "emojis": emojis,
        "active": "friends",
    })


# ============================================================
# CHAT
# ============================================================
@login_required
def alliance_chat(request, alliance_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    my_membership = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not my_membership:
        return redirect("alliance:home")

    if request.method == "POST":
        body = (request.POST.get("body") or "").strip()[:500]
        if body:
            AllianceMessage.objects.create(alliance=a, sender=request.user, body=body)
        return redirect("alliance:chat", alliance_id=a.id)

    all_messages = AllianceMessage.objects.filter(alliance=a).select_related("sender").order_by("sent_at")[:200]
    messages_data = []
    for m in all_messages:
        messages_data.append({
            "sender": m.sender,
            "avatar": _avatar(m.sender),
            "body": m.body,
            "sent_at": m.sent_at,
            "is_me": m.sender_id == request.user.id,
        })

    return render(request, "alliance/chat.html", {
        "alliance": a,
        "messages": messages_data,
        "active": "friends",
    })


# ============================================================
# LEAVE
# ============================================================
@login_required
def leave_alliance(request, alliance_id):
    if request.method != "POST":
        return redirect("alliance:home")

    a = get_object_or_404(Alliance, id=alliance_id)
    m = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not m:
        return redirect("alliance:home")

    if m.role == "leader":
        if a.member_count() <= 1:
            a.delete()
            messages.info(request, "اتحاد پاک شد.")
            return redirect("alliance:home")
        else:
            messages.error(request, "رهبر نمی‌تواند اتحاد را ترک کند.")
            return redirect("alliance:detail", alliance_id=a.id)

    m.delete()
    messages.info(request, "از اتحاد خارج شدی.")
    return redirect("alliance:home")


# ============================================================
# KICK (leader only)
# ============================================================
@login_required
def kick_member(request, alliance_id, user_id):
    if request.method != "POST":
        return redirect("alliance:home")

    a = get_object_or_404(Alliance, id=alliance_id)
    my_m = AllianceMember.objects.filter(alliance=a, user=request.user).first()

    if not my_m or my_m.role != "leader":
        messages.error(request, "دسترسی نداری.")
        return redirect("alliance:detail", alliance_id=a.id)

    target = AllianceMember.objects.filter(alliance=a, user_id=user_id).first()
    if target and target.role != "leader":
        target.delete()
        messages.success(request, "عضو حذف شد.")

    return redirect("alliance:detail", alliance_id=a.id)
'''
write("alliance/views.py", VIEWS)

# ============================================================
# 3) urls.py - full rewrite
# ============================================================
print("\n[3/10] urls.py full rewrite")
write("alliance/urls.py", '''# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = "alliance"

urlpatterns = [
    path("", views.alliance_home, name="home"),
    path("create/", views.create_alliance, name="create"),
    path("join/", views.join_by_code, name="join"),
    path("join-id/<int:alliance_id>/", views.join_alliance, name="join_alliance"),
    path("<int:alliance_id>/", views.alliance_detail, name="detail"),
    path("<int:alliance_id>/edit/", views.alliance_edit, name="edit"),
    path("<int:alliance_id>/chat/", views.alliance_chat, name="chat"),
    path("<int:alliance_id>/leave/", views.leave_alliance, name="leave"),
    path("<int:alliance_id>/kick/<int:user_id>/", views.kick_member, name="kick"),
]
''')

# ============================================================
# 4) HOME template
# ============================================================
print("\n[4/10] home.html")
write("alliance/templates/alliance/home.html", '''{% extends "base.html" %}
{% block title %}اتحاد{% endblock %}

{% block extra_css %}
<style>
  .hero-card { padding: 26px 22px; background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.4), transparent 55%), radial-gradient(circle at 0% 100%, rgba(236,72,153,0.2), transparent 55%), linear-gradient(135deg, #1a0f2e, #170a24, #0f0f1e); border: 2px solid rgba(139,92,246,0.55); border-radius: 24px; margin-bottom: 18px; text-align: center; position: relative; overflow: hidden; box-shadow: 0 15px 40px rgba(139,92,246,0.25); }
  .hero-card .icon { font-size: 56px; margin-bottom: 8px; filter: drop-shadow(0 0 20px rgba(167,139,250,0.6)); }
  .hero-card h1 { font-size: 22px; font-weight: 900; margin-bottom: 8px; background: linear-gradient(135deg, #e9d5ff, #a78bfa, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .hero-card p { color: var(--muted); font-size: 13px; line-height: 1.7; margin-bottom: 18px; }
  .create-btn { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 16px 24px; border-radius: 16px; background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; text-decoration: none; font-weight: 900; font-size: 16px; box-shadow: 0 10px 30px rgba(34,197,94,0.4); transition: 0.2s; }
  .create-btn:hover { transform: translateY(-2px); }
  .create-btn .plus { font-size: 22px; font-weight: 900; }
  .search-bar { display: flex; gap: 8px; background: var(--card); border: 1.5px solid var(--border); border-radius: 16px; padding: 4px; margin-bottom: 18px; }
  .search-bar:focus-within { border-color: var(--purple); }
  .search-bar input { flex: 1; padding: 12px 16px; border-radius: 12px; border: none; background: transparent; color: #fff; font-size: 15px; font-family: inherit; }
  .search-bar input:focus { outline: none; }
  .search-bar button { padding: 0 20px; border-radius: 12px; background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; border: none; font-weight: bold; font-family: inherit; cursor: pointer; font-size: 15px; }
  .section-title { font-size: 15px; color: var(--gold); font-weight: bold; margin: 8px 0 14px; display: flex; align-items: center; gap: 8px; }
  .section-title .count { background: rgba(244,197,66,0.15); padding: 3px 10px; border-radius: 8px; font-size: 11px; font-family: monospace; }
  .alliance-list { display: flex; flex-direction: column; gap: 10px; }
  .alliance-card { display: flex; align-items: center; gap: 14px; padding: 16px; background: var(--card); border: 1.5px solid var(--border); border-radius: 18px; transition: 0.2s; }
  .alliance-card:hover { border-color: rgba(139,92,246,0.6); transform: translateX(-3px); }
  .alliance-card.is-full { opacity: 0.6; }
  .alliance-emblem { width: 56px; height: 56px; flex-shrink: 0; border-radius: 16px; background: linear-gradient(135deg, rgba(139,92,246,0.3), rgba(6,182,212,0.15)); border: 1px solid rgba(255,255,255,0.12); display: flex; align-items: center; justify-content: center; font-size: 30px; }
  .alliance-info { flex: 1; min-width: 0; }
  .alliance-name-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
  .alliance-name { font-size: 15px; font-weight: bold; color: #fff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .alliance-tag { background: var(--gold); color: #1a1a1a; padding: 2px 8px; border-radius: 6px; font-size: 9px; font-weight: 900; font-family: monospace; }
  .alliance-meta { font-size: 11.5px; color: var(--muted); display: flex; align-items: center; gap: 6px; }
  .alliance-meta .dot { opacity: 0.5; }
  .join-btn { padding: 10px 16px; border-radius: 12px; background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; border: none; font-family: inherit; font-weight: bold; font-size: 13px; cursor: pointer; box-shadow: 0 6px 15px rgba(139,92,246,0.35); flex-shrink: 0; }
  .join-btn:hover { transform: scale(1.05); }
  .join-btn.full { background: rgba(148,163,184,0.2); box-shadow: none; cursor: not-allowed; }
  .empty-state { text-align: center; padding: 50px 20px; background: var(--card); border: 1.5px dashed var(--border); border-radius: 20px; }
  .empty-state .icon { font-size: 60px; margin-bottom: 14px; display: block; opacity: 0.5; }
  .empty-state h3 { font-size: 17px; margin-bottom: 8px; }
  .empty-state p { color: var(--muted); font-size: 13px; margin-bottom: 20px; line-height: 1.6; }
  .pass-modal-bg { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }
  .pass-modal-bg.active { display: flex; }
  .pass-modal { background: linear-gradient(135deg, rgba(30,41,59,0.98), rgba(15,23,42,0.98)); border: 1.5px solid rgba(139,92,246,0.5); border-radius: 22px; padding: 26px 22px; max-width: 380px; width: 100%; text-align: center; }
  .pass-modal .icon { font-size: 48px; margin-bottom: 10px; }
  .pass-modal h3 { font-size: 18px; color: #c4b5fd; margin-bottom: 6px; }
  .pass-modal p { font-size: 12px; color: var(--muted); margin-bottom: 16px; line-height: 1.6; }
  .pass-modal input { width: 100%; padding: 14px; border-radius: 12px; border: 1.5px solid var(--border); background: var(--bg); color: #fff; font-size: 16px; font-family: monospace; text-align: center; letter-spacing: 3px; margin-bottom: 14px; box-sizing: border-box; }
  .pass-modal-actions { display: flex; gap: 8px; }
  .pass-modal-actions button { flex: 1; padding: 12px; border-radius: 12px; font-family: inherit; font-weight: bold; font-size: 14px; cursor: pointer; border: none; }
  .btn-join-p { background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; }
  .btn-cancel-p { background: rgba(148,163,184,0.2); color: #fff; }
</style>
{% endblock %}

{% block content %}
  <div class="hero-card">
    <div class="icon">🛡️</div>
    <h1>اتحاد</h1>
    <p>با دوستانت یه تیم بساز،<br>با هم بازی کن و به بالای جدول برس!</p>
    <a href="/alliance/create/" class="create-btn">
      <span class="plus">+</span>
      <span>ساخت اتحاد جدید</span>
    </a>
  </div>

  <form method="get" class="search-bar">
    <input type="text" name="q" placeholder="جستجوی نام یا تگ اتحاد..." value="{{ query }}" autocomplete="off">
    <button type="submit">🔍</button>
  </form>

  <div class="section-title">
    <span>🌍 اتحادهای فعال</span>
    <span class="count">{{ alliances|length }}</span>
  </div>

  {% if alliances %}
    <div class="alliance-list">
      {% for a in alliances %}
        <div class="alliance-card {% if a.is_full %}is-full{% endif %}">
          <div class="alliance-emblem">{{ a.obj.emblem }}</div>
          <div class="alliance-info">
            <div class="alliance-name-row">
              <div class="alliance-name">{{ a.obj.name }}</div>
              {% if a.obj.tag %}<span class="alliance-tag">{{ a.obj.tag }}</span>{% endif %}
              {% if a.has_password %}<span>🔒</span>{% endif %}
            </div>
            <div class="alliance-meta">
              <span>{{ a.leader_avatar }} {{ a.obj.leader.alias }}</span>
              <span class="dot">•</span>
              <span>{{ a.count }} / {{ a.obj.max_members }} عضو</span>
            </div>
          </div>
          {% if a.is_full %}
            <button class="join-btn full" disabled>پر</button>
          {% elif a.has_password %}
            <button class="join-btn" onclick="openPass({{ a.obj.id }}, '{{ a.obj.name|escapejs }}')">🔐 ورود</button>
          {% else %}
            <form method="post" action="/alliance/join-id/{{ a.obj.id }}/" style="display:inline; margin:0;">
              {% csrf_token %}
              <button type="submit" class="join-btn">ورود</button>
            </form>
          {% endif %}
        </div>
      {% endfor %}
    </div>
  {% elif query %}
    <div class="empty-state">
      <span class="icon">🔍</span>
      <h3>نتیجه‌ای پیدا نشد</h3>
      <p>اتحادی با این مشخصات وجود ندارد.</p>
      <a href="/alliance/" class="join-btn" style="display:inline-block; padding:12px 22px;">پاک کردن</a>
    </div>
  {% else %}
    <div class="empty-state">
      <span class="icon">🏰</span>
      <h3>هنوز اتحادی نیست!</h3>
      <p>اولین نفری باش که یه اتحاد می‌سازه</p>
      <a href="/alliance/create/" class="create-btn" style="max-width:280px; margin:0 auto;">
        <span class="plus">+</span><span>ساخت اولین اتحاد</span>
      </a>
    </div>
  {% endif %}

  <div class="pass-modal-bg" id="passModal">
    <div class="pass-modal">
      <div class="icon">🔐</div>
      <h3>رمز اتحاد</h3>
      <p>اتحاد <b id="passName"></b> رمز دارد.<br>رمز را وارد کن.</p>
      <form method="post" id="passForm">
        {% csrf_token %}
        <input type="password" name="password" placeholder="رمز" required autofocus>
        <div class="pass-modal-actions">
          <button type="submit" class="btn-join-p">ورود</button>
          <button type="button" class="btn-cancel-p" onclick="closePass()">انصراف</button>
        </div>
      </form>
    </div>
  </div>
{% endblock %}

{% block extra_js %}
<script>
  function openPass(id, name) {
    document.getElementById('passForm').action = '/alliance/join-id/' + id + '/';
    document.getElementById('passName').textContent = name;
    document.getElementById('passModal').classList.add('active');
    setTimeout(function() {
      var inp = document.querySelector('#passForm input[name="password"]');
      if (inp) inp.focus();
    }, 100);
  }
  function closePass() {
    document.getElementById('passModal').classList.remove('active');
  }
  document.getElementById('passModal').addEventListener('click', function(e) {
    if (e.target.id === 'passModal') closePass();
  });
</script>
{% endblock %}
''')

# ============================================================
# 5) CREATE template
# ============================================================
print("\n[5/10] create.html")
write("alliance/templates/alliance/create.html", '''{% extends "base.html" %}
{% block title %}ساخت اتحاد{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }
  .error-msg { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); padding: 12px 16px; border-radius: 12px; margin-bottom: 14px; font-size: 13px; }
  .box { background: var(--card); border: 1px solid var(--border); padding: 22px; border-radius: 18px; margin-bottom: 14px; }
  label { display: block; color: var(--muted); font-size: 13px; margin: 12px 0 6px; }
  input[type=text], input[type=password], input[type=number], textarea { width: 100%; padding: 12px 14px; border-radius: 12px; border: 1.5px solid var(--border); background: var(--bg); color: var(--text); font-size: 15px; font-family: inherit; box-sizing: border-box; }
  textarea { resize: vertical; min-height: 80px; }
  input:focus, textarea:focus { outline: none; border-color: var(--gold); }
  .emojis { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
  .emoji-opt { padding: 12px 0; text-align: center; font-size: 26px; background: var(--bg); border: 2px solid transparent; border-radius: 12px; cursor: pointer; transition: 0.15s; }
  .emoji-opt:hover { border-color: var(--gold); }
  .emoji-opt input { display: none; }
  .emoji-opt:has(input:checked) { border-color: var(--gold); background: linear-gradient(135deg, rgba(244,197,66,0.3), rgba(249,115,22,0.2)); box-shadow: 0 0 20px rgba(244,197,66,0.4); }
  button.save { width: 100%; margin-top: 20px; padding: 16px; border: none; border-radius: 14px; font-size: 17px; font-weight: bold; font-family: inherit; cursor: pointer; color: #1a1a1a; background: linear-gradient(135deg, #22c55e, #16a34a); box-shadow: 0 10px 30px rgba(34,197,94,0.4); }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <a href="/alliance/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>🏰 <span>ساخت اتحاد</span></h1>
  </div>

  {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}

  <form method="post">
    {% csrf_token %}
    <div class="box">
      <label>نماد اتحاد</label>
      <div class="emojis">
        {% for e in emojis %}
          <label class="emoji-opt">
            <input type="radio" name="emblem" value="{{ e }}" {% if forloop.first %}checked{% endif %}>
            {{ e }}
          </label>
        {% endfor %}
      </div>
    </div>
    <div class="box">
      <label>نام اتحاد (حداقل ۳ حرف)</label>
      <input type="text" name="name" maxlength="40" required placeholder="مثلاً: عقاب‌های آتشین">
      <label>برچسب کوتاه (اختیاری)</label>
      <input type="text" name="tag" maxlength="8" placeholder="مثلاً: IRN">
      <label>توضیح (اختیاری)</label>
      <textarea name="description" maxlength="200" placeholder="چند خط درباره تیمت..."></textarea>
      <label>ظرفیت اعضا (۵ تا ۵۰)</label>
      <input type="number" name="max_members" min="5" max="50" value="30">
      <label>رمز اتحاد (اختیاری)</label>
      <input type="password" name="password" maxlength="32" placeholder="خالی = بدون رمز">
    </div>
    <button type="submit" class="save">🚀 ساخت اتحاد</button>
  </form>
{% endblock %}
''')

# ============================================================
# 6) DETAIL template
# ============================================================
print("\n[6/10] detail.html")
write("alliance/templates/alliance/detail.html", '''{% extends "base.html" %}
{% block title %}{{ alliance.name }}{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
  .hero-card { text-align: center; padding: 30px 20px; background: linear-gradient(135deg, rgba(30,41,59,0.8), rgba(15,23,42,0.9)); border: 1px solid rgba(148,163,184,0.2); border-radius: 24px; margin-bottom: 20px; position: relative; overflow: hidden; }
  .hero-card::before { content: ""; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(244,197,66,0.1) 0%, transparent 60%); pointer-events: none; }
  .emblem-big { font-size: 76px; margin-bottom: 12px; filter: drop-shadow(0 10px 20px rgba(0,0,0,0.5)); }
  .alliance-title { font-size: 26px; font-weight: 900; background: linear-gradient(135deg, #fde68a, #f4c542, #ca8a04); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 6px; }
  .invite-box { display: inline-flex; align-items: center; gap: 10px; background: rgba(15,23,42,0.8); border: 1px solid var(--border); padding: 8px 16px; border-radius: 12px; margin-top: 16px; cursor: pointer; }
  .invite-box:hover { border-color: var(--gold); }
  .invite-code { font-family: monospace; font-size: 18px; letter-spacing: 3px; color: var(--gold); font-weight: bold; }
  .capacity-bar-wrap { margin-top: 16px; }
  .capacity-bar-labels { display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); margin-bottom: 6px; }
  .capacity-bar { height: 8px; background: rgba(148,163,184,0.15); border-radius: 8px; overflow: hidden; }
  .capacity-fill { height: 100%; background: linear-gradient(90deg, #8b5cf6, #06b6d4); border-radius: 8px; }
  .stats-row { display: flex; gap: 10px; margin-bottom: 20px; }
  .stat-box { flex: 1; background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 16px; text-align: center; }
  .stat-val { font-size: 22px; font-weight: bold; color: #fff; margin-bottom: 4px; }
  .stat-lbl { font-size: 11px; color: var(--muted); }
  .action-grid { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
  .action-grid a, .action-grid button { flex: 1; min-width: 140px; text-align: center; padding: 14px; border-radius: 14px; text-decoration: none; font-weight: bold; font-size: 15px; border: none; font-family: inherit; cursor: pointer; }
  .btn-chat { background: linear-gradient(135deg, #06b6d4, #3b82f6); color: #fff; }
  .btn-edit { background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; }
  .btn-leave { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; }
  .member-list { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 20px; }
  .member-list h3 { font-size: 15px; color: var(--gold); margin-bottom: 16px; display: flex; justify-content: space-between; }
  .badge-count { display: inline-block; background: var(--border); color: #fff; font-size: 10px; padding: 2px 8px; border-radius: 8px; font-weight: bold; }
  .member-row { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
  .member-row:last-child { border-bottom: none; }
  .member-av-wrapper { position: relative; }
  .member-av { width: 44px; height: 44px; border-radius: 50%; background: rgba(15,23,42,0.6); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; font-size: 22px; background-size: cover; background-position: center; }
  .online-dot { position: absolute; bottom: 0; right: 0; width: 12px; height: 12px; background: #22c55e; border-radius: 50%; border: 2px solid var(--card); }
  .member-info { flex: 1; }
  .member-name { font-size: 14px; font-weight: bold; color: #fff; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  .member-join { font-size: 11px; color: var(--dim); }
  .level-badge { background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; font-size: 10px; padding: 2px 6px; border-radius: 6px; font-family: monospace; }
  .role-badge { font-size: 11px; padding: 4px 10px; border-radius: 8px; font-weight: bold; }
  .role-leader { background: rgba(244,197,66,0.2); color: #facc15; border: 1px solid rgba(244,197,66,0.3); }
  .role-officer { background: rgba(59,130,246,0.2); color: #93c5fd; border: 1px solid rgba(59,130,246,0.3); }
  .role-member { background: rgba(100,116,139,0.2); color: #cbd5e1; border: 1px solid rgba(100,116,139,0.3); }
  .kick-btn { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); color: #f87171; border-radius: 8px; padding: 6px 10px; cursor: pointer; font-size: 12px; font-family: inherit; }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <a href="/alliance/" class="back-btn"><span class="arrow-icon">→</span></a>
  </div>

  <div class="hero-card">
    <div class="emblem-big">{{ alliance.emblem }}</div>
    <div class="alliance-title">{{ alliance.name }}</div>
    {% if alliance.tag %}<div style="color:var(--muted); font-size:14px; letter-spacing:2px;">{{ alliance.tag }}</div>{% endif %}
    <div class="invite-box" onclick="copyCode()">
      <span class="invite-code" id="codeText">{{ alliance.invite_code }}</span>
      <span style="font-size:16px;">📋</span>
    </div>
    <div style="font-size:10px; color:var(--dim); margin-top:6px;">برای کپی کلیک کنید</div>

    <div class="capacity-bar-wrap">
      <div class="capacity-bar-labels">
        <span>ظرفیت اعضا</span>
        <span style="font-family:monospace;">{{ member_count }} / {{ alliance.max_members }}</span>
      </div>
      <div class="capacity-bar">
        <div class="capacity-fill" style="width: {% widthratio member_count alliance.max_members 100 %}%;"></div>
      </div>
    </div>
  </div>

  <div class="stats-row">
    <div class="stat-box">
      <div class="stat-val">{{ member_count }} / {{ alliance.max_members }}</div>
      <div class="stat-lbl">ظرفیت اعضا</div>
    </div>
    <div class="stat-box">
      <div class="stat-val">{{ alliance.created_at|date:"Y/m/d" }}</div>
      <div class="stat-lbl">تأسیس</div>
    </div>
  </div>

  <div class="action-grid">
    <a href="/alliance/{{ alliance.id }}/chat/" class="btn-chat">💬 چت گروهی</a>
    {% if my_role == 'leader' %}
      <a href="/alliance/{{ alliance.id }}/edit/" class="btn-edit">✏️ ویرایش</a>
    {% endif %}
    <form method="post" action="/alliance/{{ alliance.id }}/leave/" style="flex:1; min-width:140px;" onsubmit="return confirm('{% if my_role == 'leader' %}اتحاد منحل شود؟{% else %}از اتحاد خارج شوی؟{% endif %}');">
      {% csrf_token %}
      <button type="submit" class="btn-leave" style="width:100%;">{% if my_role == 'leader' %}🗑️ حذف{% else %}🚪 خروج{% endif %}</button>
    </form>
  </div>

  <div class="member-list">
    <h3>👥 اعضای اتحاد <span class="badge-count">{{ member_count }}</span></h3>
    {% for mem in members %}
      <div class="member-row">
        <div class="member-av-wrapper">
          {% if mem.user.avatar_type == 'image' and mem.user.avatar_id %}
            <div class="member-av" style="background-image: url('/static/avatars/images/{{ mem.user.avatar_id|stringformat:"03d" }}.jpg');"></div>
          {% else %}
            <div class="member-av">{{ mem.avatar }}</div>
          {% endif %}
          {% if mem.is_online %}<div class="online-dot"></div>{% endif %}
        </div>
        <div class="member-info">
          <div class="member-name">
            {{ mem.user.alias }}
            {% if mem.user.id == request.user.id %}<span style="color:var(--teal);font-size:10px;">(شما)</span>{% endif %}
            <span class="level-badge">Lv {{ mem.level }}</span>
          </div>
          <div class="member-join">عضو از {{ mem.joined_at|date:"Y/m/d" }}</div>
        </div>
        <span class="role-badge role-{{ mem.role }}">
          {% if mem.role == 'leader' %}👑 رهبر{% elif mem.role == 'officer' %}🛡️ افسر{% else %}👤 عضو{% endif %}
        </span>
        {% if is_leader and mem.role != 'leader' %}
          <form method="post" action="/alliance/{{ alliance.id }}/kick/{{ mem.user.id }}/" onsubmit="return confirm('حذف شود؟');" style="margin:0;">
            {% csrf_token %}
            <button type="submit" class="kick-btn">حذف</button>
          </form>
        {% endif %}
      </div>
    {% endfor %}
  </div>
{% endblock %}

{% block extra_js %}
<script>
  function copyCode() {
    const code = document.getElementById('codeText').innerText;
    navigator.clipboard.writeText(code).then(() => {
      if (typeof window.soundSuccess === 'function') window.soundSuccess();
      alert('کد دعوت کپی شد: ' + code);
    }).catch(() => alert('کد دعوت: ' + code));
  }
</script>
{% endblock %}
''')

# ============================================================
# 7) EDIT template
# ============================================================
print("\n[7/10] edit.html")
write("alliance/templates/alliance/edit.html", '''{% extends "base.html" %}
{% block title %}ویرایش اتحاد{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }
  .error-msg { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); padding: 12px 16px; border-radius: 12px; margin-bottom: 14px; font-size: 13px; }
  .box { background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 22px; margin-bottom: 14px; }
  .box h3 { font-size: 14px; color: var(--gold); margin-bottom: 16px; }
  label { display: block; color: var(--muted); font-size: 13px; margin: 12px 0 6px; }
  input[type=text], input[type=password], input[type=number], textarea { width: 100%; padding: 12px 14px; border-radius: 12px; border: 1.5px solid var(--border); background: var(--bg); color: var(--text); font-size: 15px; font-family: inherit; box-sizing: border-box; }
  textarea { resize: vertical; min-height: 70px; }
  input:focus, textarea:focus { outline: none; border-color: var(--purple); }
  .emojis { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
  .emoji-opt { padding: 12px 0; text-align: center; font-size: 26px; background: var(--bg); border: 2px solid transparent; border-radius: 12px; cursor: pointer; transition: 0.15s; }
  .emoji-opt:hover { border-color: var(--gold); }
  .emoji-opt input { display: none; }
  .emoji-opt:has(input:checked) { border-color: var(--gold); background: linear-gradient(135deg, rgba(244,197,66,0.25), rgba(139,92,246,0.15)); }
  button.save { width: 100%; margin-top: 16px; padding: 16px; border: none; border-radius: 14px; font-size: 16px; font-weight: bold; font-family: inherit; cursor: pointer; color: #fff; background: linear-gradient(135deg, #8b5cf6, #6b4eff); box-shadow: 0 10px 30px rgba(139,92,246,0.4); }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <a href="/alliance/{{ alliance.id }}/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>✏️ <span>ویرایش اتحاد</span></h1>
  </div>

  {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}

  <form method="post">
    {% csrf_token %}
    <div class="box">
      <h3>🎨 نماد اتحاد</h3>
      <div class="emojis">
        {% for e in emojis %}
          <label class="emoji-opt">
            <input type="radio" name="emblem" value="{{ e }}" {% if e == alliance.emblem %}checked{% endif %}>
            {{ e }}
          </label>
        {% endfor %}
      </div>
    </div>
    <div class="box">
      <h3>📝 اطلاعات اتحاد</h3>
      <label>نام اتحاد</label>
      <input type="text" name="name" maxlength="40" required value="{{ alliance.name }}">
      <label>تگ (اختیاری)</label>
      <input type="text" name="tag" maxlength="8" value="{{ alliance.tag }}">
      <label>توضیح</label>
      <textarea name="description" maxlength="200">{{ alliance.description }}</textarea>
    </div>
    <div class="box">
      <h3>⚙️ تنظیمات</h3>
      <label>ظرفیت اعضا (۵ تا ۵۰)</label>
      <input type="number" name="max_members" min="5" max="50" value="{{ alliance.max_members }}">
      <label>رمز اتحاد (خالی = بدون رمز)</label>
      <input type="password" name="password" maxlength="32" value="{{ alliance.password }}">
    </div>
    <button type="submit" class="save">💾 ذخیره تغییرات</button>
  </form>
{% endblock %}
''')

# ============================================================
# 8) CHAT template
# ============================================================
print("\n[8/10] chat.html")
write("alliance/templates/alliance/chat.html", '''{% extends "base.html" %}
{% block title %}چت {{ alliance.name }}{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
  .chat-header { display: flex; align-items: center; gap: 12px; padding: 16px; background: var(--card); border: 1px solid var(--border); border-radius: 16px; margin-bottom: 16px; }
  .chat-header .emblem { font-size: 32px; }
  .chat-header .info { flex: 1; }
  .chat-header .name { font-size: 16px; font-weight: bold; color: #fff; }
  .chat-header .sub { font-size: 12px; color: var(--muted); }
  .chat-body { min-height: 400px; max-height: 55vh; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; padding: 10px; background: rgba(15,23,42,0.3); border-radius: 20px; margin-bottom: 16px; }
  .chat-body::-webkit-scrollbar { width: 6px; }
  .chat-body::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.2); border-radius: 6px; }
  .msg { display: flex; gap: 10px; align-items: flex-end; }
  .msg.me { flex-direction: row-reverse; }
  .msg-av { width: 32px; height: 32px; border-radius: 50%; background: rgba(51,65,85,0.8); display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; background-size: cover; background-position: center; border: 1px solid var(--border); }
  .msg-bubble { max-width: 75%; padding: 12px 16px; border-radius: 18px; background: var(--card); border: 1px solid var(--border); font-size: 14px; line-height: 1.5; color: #fff; border-bottom-right-radius: 4px; }
  .msg.me .msg-bubble { background: linear-gradient(135deg, #3b82f6, #2563eb); border-color: #2563eb; border-bottom-right-radius: 18px; border-bottom-left-radius: 4px; }
  .msg-sender { font-size: 11px; color: var(--muted); margin-bottom: 4px; }
  .msg-time { font-size: 9px; color: var(--dim); margin-top: 6px; text-align: left; }
  .chat-input { display: flex; gap: 10px; background: var(--card); padding: 10px; border-radius: 16px; border: 1px solid var(--border); }
  .chat-input input { flex: 1; background: transparent; border: none; color: #fff; font-size: 15px; padding: 10px; font-family: inherit; }
  .chat-input input:focus { outline: none; }
  .chat-input button { background: linear-gradient(135deg, #06b6d4, #3b82f6); color: #fff; border: none; width: 44px; height: 44px; border-radius: 12px; font-size: 18px; cursor: pointer; }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <a href="/alliance/{{ alliance.id }}/" class="back-btn"><span class="arrow-icon">→</span></a>
  </div>

  <div class="chat-header">
    <div class="emblem">{{ alliance.emblem }}</div>
    <div class="info">
      <div class="name">{{ alliance.name }}</div>
      <div class="sub">چت گروهی اعضا</div>
    </div>
  </div>

  <div class="chat-body" id="chatBody">
    {% for m in messages %}
      <div class="msg {% if m.is_me %}me{% endif %}">
        {% if m.sender.avatar_type == 'image' and m.sender.avatar_id %}
          <div class="msg-av" style="background-image: url('/static/avatars/images/{{ m.sender.avatar_id|stringformat:"03d" }}.jpg');"></div>
        {% else %}
          <div class="msg-av">{{ m.avatar }}</div>
        {% endif %}
        <div>
          {% if not m.is_me %}<div class="msg-sender">{{ m.sender.alias }}</div>{% endif %}
          <div class="msg-bubble">{{ m.body }}</div>
          <div class="msg-time">{{ m.sent_at|date:"H:i" }}</div>
        </div>
      </div>
    {% empty %}
      <div style="text-align:center; color:var(--dim); font-size:13px; margin:auto;">هنوز پیامی فرستاده نشده. اولین نفر باش!</div>
    {% endfor %}
  </div>

  <form method="post" class="chat-input">
    {% csrf_token %}
    <input type="text" name="body" maxlength="500" required placeholder="پیامت را اینجا بنویس..." autocomplete="off" autofocus>
    <button type="submit">↑</button>
  </form>
{% endblock %}

{% block extra_js %}
<script>
  const body = document.getElementById('chatBody');
  if (body) body.scrollTop = body.scrollHeight;
</script>
{% endblock %}
''')

# ============================================================
# 9) JOIN template (fallback for join by code)
# ============================================================
print("\n[9/10] join.html")
write("alliance/templates/alliance/join.html", '''{% extends "base.html" %}
{% block title %}ورود با کد{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }
  .error-msg { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); padding: 12px 16px; border-radius: 12px; margin-bottom: 14px; font-size: 13px; text-align: center; }
  .box { background: var(--card); border: 1px solid var(--border); padding: 28px 22px; border-radius: 18px; text-align: center; }
  label { display: block; color: var(--muted); font-size: 13px; margin-bottom: 10px; }
  input[type=text] { width: 100%; padding: 18px; border-radius: 14px; border: 2px solid var(--border); background: var(--bg); color: var(--text); font-size: 26px; font-family: monospace; text-align: center; letter-spacing: 8px; text-transform: uppercase; box-sizing: border-box; }
  input:focus { outline: none; border-color: var(--teal); }
  button { width: 100%; margin-top: 20px; padding: 16px; border: none; border-radius: 14px; font-size: 17px; font-weight: bold; font-family: inherit; cursor: pointer; color: #fff; background: linear-gradient(135deg, #06b6d4, #3b82f6); }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <a href="/alliance/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>🔑 <span>ورود با کد</span></h1>
  </div>

  {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}

  <div class="box">
    <form method="post">
      {% csrf_token %}
      <label>کد دعوت ۶ حرفی</label>
      <input type="text" name="code" maxlength="6" required placeholder="ABC123" autocomplete="off">
      <button type="submit">🚀 پیوستن</button>
    </form>
  </div>
{% endblock %}
''')

# ============================================================
# 10) Migrations + check + test
# ============================================================
print("\n[10/10] Migrations + check + test")

for cmd in [
    [sys.executable, "manage.py", "makemigrations", "alliance", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd[1:])}")
    if r.stdout.strip(): print("   ", r.stdout.strip().replace("\n", "\n    ")[:300])
    if r.returncode != 0 and r.stderr.strip():
        print("   ERR:", r.stderr.strip()[:300])

r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("\n  ✓ Django check PASSED")
else:
    print("\n  ⚠ check errors:")
    print(r.stderr[:1500] if r.stderr else r.stdout[:1500])

# Test all pages
print("\n[Test] Loading pages")
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

try:
    tu = User.objects.filter(username="__alliance_test__").first()
    created = False
    if not tu:
        tu = User.objects.create_user(
            username="__alliance_test__", password="x" * 10,
            alias="at", is_active=True,
            has_chosen_avatar=True, has_completed_registration=True,
        )
        created = True
    c = Client()
    c.force_login(tu)

    pages = [
        ("/alliance/", "home"),
        ("/alliance/create/", "create"),
    ]
    for url, name in pages:
        r = c.get(url)
        status = r.status_code
        ok = "✓" if status == 200 else "→" if status in (301, 302) else "✗"
        print(f"  {ok} {url} → {status} ({name})")

    if created:
        tu.delete()
except Exception as e:
    print(f"  ⚠ test error: {e}")

print("\n" + "=" * 60)
print("DONE!")
print("=" * 60)
print("""
What was rebuilt:
  ✓ alliance/models.py     (Alliance, AllianceMember, AllianceMessage)
  ✓ alliance/views.py      (all views: home, create, join, join-by-code,
                            detail, edit, chat, leave, kick)
  ✓ alliance/urls.py       (all routes)
  ✓ alliance/templates/
      - home.html          (list + search + password modal)
      - create.html        (full form with capacity + password)
      - detail.html        (hero + capacity bar + members + actions)
      - edit.html          (leader-only edit)
      - chat.html          (group chat)
      - join.html          (fallback join-by-code)

Next:
  Ctrl+C (if server running)
  python manage.py runserver
  Ctrl+Shift+R (hard refresh browser)

Test:
  /alliance/          → list (or redirect if member)
  /alliance/create/   → create form
  /social/            → alliance card at top

Password reminders:
  Beta Gate: emami_irani_esm1405
  Admin:     admin74 / Amir2255ds
""")
