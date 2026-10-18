#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Alliance — clean rebuild + full test."""
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")
def backup(p):
    if os.path.exists(p):
        try:
            with open(p + ".bak_alliance", "w", encoding="utf-8") as f:
                f.write(read(p))
        except: pass

# ============================================================
# 1) models.py — keep if exists, else write
# ============================================================
print("\n[1/6] models.py")
if not os.path.exists("alliance/models.py"):
    write("alliance/models.py", "")
src = read("alliance/models.py")
if "class Alliance(" in src and "class AllianceMember(" in src:
    print("  ✓ models OK")
else:
    print("  ⚠ rewriting models")
    backup("alliance/models.py")
    write("alliance/models.py", '''import random, string
from django.conf import settings
from django.db import models
from django.utils import timezone


def _gen_code():
    while True:
        c = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Alliance.objects.filter(invite_code=c).exists():
            return c


class Alliance(models.Model):
    name = models.CharField(max_length=40, unique=True)
    tag = models.CharField(max_length=8, blank=True)
    description = models.CharField(max_length=200, blank=True)
    emblem = models.CharField(max_length=4, default="🛡️")
    invite_code = models.CharField(max_length=6, unique=True, editable=False)
    leader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="led_alliances")
    max_members = models.PositiveIntegerField(default=30)
    password = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = _gen_code()
        super().save(*args, **kwargs)

    def member_count(self):
        return self.members.count()

    def __str__(self):
        return f"{self.emblem} {self.name}"


class AllianceMember(models.Model):
    ROLE_CHOICES = [("leader", "رهبر"), ("officer", "افسر"), ("member", "عضو")]
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
''')

# ============================================================
# 2) views.py — full clean rewrite
# ============================================================
print("\n[2/6] views.py")

backup("alliance/views.py")
write("alliance/views.py", '''# -*- coding: utf-8 -*-
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q, Sum

from accounts.avatars import get_emoji
from .models import Alliance, AllianceMember, AllianceMessage


def _av(user):
    try:
        return get_emoji(user.avatar_id)
    except Exception:
        return "👤"


@login_required
def alliance_home(request):
    if not getattr(request.user, "has_chosen_avatar", False):
        return redirect("accounts:avatar_select")

    mem = AllianceMember.objects.filter(user=request.user).select_related("alliance").first()
    if mem:
        return redirect("alliance:detail", alliance_id=mem.alliance.id)

    q = (request.GET.get("q") or "").strip()
    qs = Alliance.objects.all().order_by("-created_at")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(tag__icontains=q))

    data = []
    for a in qs[:50]:
        n = a.member_count()
        data.append({
            "obj": a, "count": n,
            "is_full": n >= a.max_members,
            "has_password": bool(a.password),
            "leader_avatar": _av(a.leader),
        })

    return render(request, "alliance/home.html", {
        "alliances": data, "query": q, "active": "friends",
    })


@login_required
def create_alliance(request):
    if not getattr(request.user, "has_chosen_avatar", False):
        return redirect("accounts:avatar_select")

    if AllianceMember.objects.filter(user=request.user).exists():
        messages.info(request, "شما الان عضو یک اتحاد هستید.")
        return redirect("alliance:home")

    error = None
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()[:40]
        tag = (request.POST.get("tag") or "").strip().upper()[:8]
        desc = (request.POST.get("description") or "").strip()[:200]
        emblem = (request.POST.get("emblem") or "🛡️").strip()[:4]
        password = (request.POST.get("password") or "").strip()[:32]
        try:
            mx = int(request.POST.get("max_members") or 30)
        except (ValueError, TypeError):
            mx = 30
        mx = max(5, min(50, mx))

        if not name:
            error = "نام اتحاد را وارد کن."
        elif len(name) < 3:
            error = "نام باید حداقل ۳ حرف باشد."
        elif Alliance.objects.filter(name=name).exists():
            error = "این نام قبلاً گرفته شده."
        else:
            a = Alliance.objects.create(
                name=name, tag=tag, description=desc,
                emblem=emblem or "🛡️", leader=request.user,
                max_members=mx, password=password,
            )
            AllianceMember.objects.create(alliance=a, user=request.user, role="leader")
            messages.success(request, f"اتحاد «{name}» ساخته شد!")
            return redirect("alliance:detail", alliance_id=a.id)

    emojis = ["🛡️", "⚔️", "🏰", "🐉", "🦅", "🐺", "🔥", "⚡", "👑", "💎", "🌟", "🦁"]
    return render(request, "alliance/create.html", {
        "error": error, "emojis": emojis, "active": "friends",
    })


@login_required
def join_alliance(request, alliance_id):
    if not getattr(request.user, "has_chosen_avatar", False):
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


@login_required
def join_by_code(request):
    if not getattr(request.user, "has_chosen_avatar", False):
        return redirect("accounts:avatar_select")

    if AllianceMember.objects.filter(user=request.user).exists():
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


@login_required
def alliance_detail(request, alliance_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    mem = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not mem:
        messages.info(request, "برای دیدن اتحاد باید عضو شوی.")
        return redirect("alliance:home")

    online_cutoff = timezone.now() - timedelta(minutes=5)
    rows = AllianceMember.objects.filter(alliance=a).select_related("user").order_by("role", "-joined_at")

    members = []
    for m in rows:
        u = m.user
        try:
            is_online = bool(u.last_seen and u.last_seen >= online_cutoff)
        except Exception:
            is_online = False
        try:
            agg = u.player_set.aggregate(t=Sum("score"))
            total = agg.get("t") or 0
        except Exception:
            total = 0
        members.append({
            "user": u, "avatar": _av(u), "role": m.role,
            "role_display": m.get_role_display(), "joined_at": m.joined_at,
            "is_online": is_online, "level": 1 + total // 100,
        })

    recent = list(reversed(
        AllianceMessage.objects.filter(alliance=a).select_related("sender").order_by("-sent_at")[:5]
    ))

    return render(request, "alliance/detail.html", {
        "alliance": a, "members": members,
        "my_role": mem.role, "is_leader": mem.role == "leader",
        "recent_messages": recent, "member_count": len(members),
        "active": "friends",
    })


@login_required
def alliance_edit(request, alliance_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    mem = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not mem or mem.role != "leader":
        messages.error(request, "فقط رهبر می‌تونه ویرایش کنه.")
        return redirect("alliance:detail", alliance_id=a.id)

    error = None
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()[:40]
        tag = (request.POST.get("tag") or "").strip().upper()[:8]
        desc = (request.POST.get("description") or "").strip()[:200]
        emblem = (request.POST.get("emblem") or a.emblem).strip()[:4]
        password = (request.POST.get("password") or "").strip()[:32]
        try:
            mx = int(request.POST.get("max_members") or a.max_members)
        except (ValueError, TypeError):
            mx = a.max_members
        mx = max(5, min(50, mx))

        if not name:
            error = "نام اتحاد را وارد کن."
        elif len(name) < 3:
            error = "نام باید حداقل ۳ حرف باشد."
        elif Alliance.objects.filter(name=name).exclude(id=a.id).exists():
            error = "این نام قبلاً گرفته شده."
        elif a.member_count() > mx:
            error = "ظرفیت جدید از اعضای فعلی کمتره."
        else:
            a.name, a.tag, a.description = name, tag, desc
            a.emblem, a.password, a.max_members = emblem or a.emblem, password, mx
            a.save()
            messages.success(request, "تغییرات ذخیره شد.")
            return redirect("alliance:detail", alliance_id=a.id)

    emojis = ["🛡️", "⚔️", "🏰", "🐉", "🦅", "🐺", "🔥", "⚡", "👑", "💎", "🌟", "🦁"]
    return render(request, "alliance/edit.html", {
        "alliance": a, "error": error, "emojis": emojis, "active": "friends",
    })


@login_required
def alliance_chat(request, alliance_id):
    a = get_object_or_404(Alliance, id=alliance_id)
    mem = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not mem:
        return redirect("alliance:home")

    if request.method == "POST":
        body = (request.POST.get("body") or "").strip()[:500]
        if body:
            AllianceMessage.objects.create(alliance=a, sender=request.user, body=body)
        return redirect("alliance:chat", alliance_id=a.id)

    msgs = AllianceMessage.objects.filter(alliance=a).select_related("sender").order_by("sent_at")[:200]
    data = [{
        "sender": m.sender, "avatar": _av(m.sender), "body": m.body,
        "sent_at": m.sent_at, "is_me": m.sender_id == request.user.id,
    } for m in msgs]

    return render(request, "alliance/chat.html", {
        "alliance": a, "messages": data, "active": "friends",
    })


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
        messages.error(request, "رهبر نمی‌تونه اتحاد رو ترک کنه.")
        return redirect("alliance:detail", alliance_id=a.id)
    m.delete()
    messages.info(request, "از اتحاد خارج شدی.")
    return redirect("alliance:home")


@login_required
def kick_member(request, alliance_id, user_id):
    if request.method != "POST":
        return redirect("alliance:home")
    a = get_object_or_404(Alliance, id=alliance_id)
    me = AllianceMember.objects.filter(alliance=a, user=request.user).first()
    if not me or me.role != "leader":
        messages.error(request, "دسترسی نداری.")
        return redirect("alliance:detail", alliance_id=a.id)
    target = AllianceMember.objects.filter(alliance=a, user_id=user_id).first()
    if target and target.role != "leader":
        target.delete()
        messages.success(request, "عضو حذف شد.")
    return redirect("alliance:detail", alliance_id=a.id)
''')

# ============================================================
# 3) urls.py
# ============================================================
print("\n[3/6] urls.py")
backup("alliance/urls.py")
write("alliance/urls.py", '''from django.urls import path
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
# 4) Templates
# ============================================================
print("\n[4/6] templates")
os.makedirs("alliance/templates/alliance", exist_ok=True)

# ---- home.html ----
backup("alliance/templates/alliance/home.html")
write("alliance/templates/alliance/home.html", '''{% extends "base.html" %}
{% block title %}اتحاد{% endblock %}
{% block extra_css %}
<style>
.hero{padding:26px 22px;background:radial-gradient(circle at 100% 0%,rgba(139,92,246,.4),transparent 55%),radial-gradient(circle at 0% 100%,rgba(236,72,153,.2),transparent 55%),linear-gradient(135deg,#1a0f2e,#170a24,#0f0f1e);border:2px solid rgba(139,92,246,.55);border-radius:24px;margin-bottom:18px;text-align:center;box-shadow:0 15px 40px rgba(139,92,246,.25)}
.hero .em{font-size:56px;margin-bottom:8px}
.hero h1{font-size:22px;font-weight:900;margin-bottom:8px;background:linear-gradient(135deg,#e9d5ff,#a78bfa,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero p{color:var(--muted);font-size:13px;line-height:1.7;margin-bottom:18px}
.cbtn{display:flex;align-items:center;justify-content:center;gap:10px;padding:16px 24px;border-radius:16px;background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;text-decoration:none;font-weight:900;font-size:16px;box-shadow:0 10px 30px rgba(34,197,94,.4)}
.search{display:flex;gap:8px;background:var(--card);border:1.5px solid var(--border);border-radius:16px;padding:4px;margin-bottom:18px}
.search input{flex:1;padding:12px 16px;border-radius:12px;border:none;background:transparent;color:#fff;font-size:15px;font-family:inherit}
.search input:focus{outline:none}
.search button{padding:0 20px;border-radius:12px;background:linear-gradient(135deg,#8b5cf6,#6b4eff);color:#fff;border:none;font-weight:bold;font-family:inherit;cursor:pointer;font-size:15px}
.sect{font-size:15px;color:var(--gold);font-weight:bold;margin:8px 0 14px;display:flex;align-items:center;gap:8px}
.sect .c{background:rgba(244,197,66,.15);padding:3px 10px;border-radius:8px;font-size:11px;font-family:monospace}
.list{display:flex;flex-direction:column;gap:10px}
.card{display:flex;align-items:center;gap:14px;padding:16px;background:var(--card);border:1.5px solid var(--border);border-radius:18px;transition:.2s}
.card:hover{border-color:rgba(139,92,246,.6);transform:translateX(-3px)}
.card.full{opacity:.6}
.emb{width:56px;height:56px;border-radius:16px;background:linear-gradient(135deg,rgba(139,92,246,.3),rgba(6,182,212,.15));border:1px solid rgba(255,255,255,.12);display:flex;align-items:center;justify-content:center;font-size:30px;flex-shrink:0}
.info{flex:1;min-width:0}
.name-row{display:flex;align-items:center;gap:6px;margin-bottom:4px}
.name{font-size:15px;font-weight:bold;color:#fff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tag{background:var(--gold);color:#1a1a1a;padding:2px 8px;border-radius:6px;font-size:9px;font-weight:900;font-family:monospace}
.meta{font-size:11.5px;color:var(--muted);display:flex;align-items:center;gap:6px}
.jbtn{padding:10px 16px;border-radius:12px;background:linear-gradient(135deg,#8b5cf6,#6b4eff);color:#fff;border:none;font-family:inherit;font-weight:bold;font-size:13px;cursor:pointer;flex-shrink:0}
.jbtn.full{background:rgba(148,163,184,.2);cursor:not-allowed}
.empty{text-align:center;padding:50px 20px;background:var(--card);border:1.5px dashed var(--border);border-radius:20px}
.empty .em{font-size:60px;margin-bottom:14px;display:block;opacity:.5}
.empty h3{font-size:17px;margin-bottom:8px}
.empty p{color:var(--muted);font-size:13px;margin-bottom:20px;line-height:1.6}
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);backdrop-filter:blur(8px);z-index:1000;align-items:center;justify-content:center;padding:20px}
.modal-bg.active{display:flex}
.modal{background:linear-gradient(135deg,rgba(30,41,59,.98),rgba(15,23,42,.98));border:1.5px solid rgba(139,92,246,.5);border-radius:22px;padding:26px 22px;max-width:380px;width:100%;text-align:center}
.modal .em{font-size:48px;margin-bottom:10px}
.modal h3{font-size:18px;color:#c4b5fd;margin-bottom:6px}
.modal p{font-size:12px;color:var(--muted);margin-bottom:16px;line-height:1.6}
.modal input{width:100%;padding:14px;border-radius:12px;border:1.5px solid var(--border);background:var(--bg);color:#fff;font-size:16px;font-family:monospace;text-align:center;letter-spacing:3px;margin-bottom:14px;box-sizing:border-box}
.acts{display:flex;gap:8px}
.acts button{flex:1;padding:12px;border-radius:12px;font-family:inherit;font-weight:bold;font-size:14px;cursor:pointer;border:none}
.bok{background:linear-gradient(135deg,#8b5cf6,#6b4eff);color:#fff}
.bno{background:rgba(148,163,184,.2);color:#fff}
</style>
{% endblock %}
{% block content %}
<div class="hero">
  <div class="em">🛡️</div>
  <h1>اتحاد</h1>
  <p>با دوستانت یه تیم بساز،<br>با هم بازی کن و به بالای جدول برس!</p>
  <a href="/alliance/create/" class="cbtn">+ ساخت اتحاد جدید</a>
</div>

<form method="get" class="search">
  <input type="text" name="q" placeholder="جستجو..." value="{{ query }}" autocomplete="off">
  <button type="submit">🔍</button>
</form>

<div class="sect"><span>🌍 اتحادهای فعال</span><span class="c">{{ alliances|length }}</span></div>

{% if alliances %}
<div class="list">
{% for a in alliances %}
  <div class="card {% if a.is_full %}full{% endif %}">
    <div class="emb">{{ a.obj.emblem }}</div>
    <div class="info">
      <div class="name-row">
        <div class="name">{{ a.obj.name }}</div>
        {% if a.obj.tag %}<span class="tag">{{ a.obj.tag }}</span>{% endif %}
        {% if a.has_password %}<span>🔒</span>{% endif %}
      </div>
      <div class="meta">
        <span>{{ a.leader_avatar }} {{ a.obj.leader.alias }}</span>
        <span>•</span>
        <span>{{ a.count }} / {{ a.obj.max_members }}</span>
      </div>
    </div>
    {% if a.is_full %}
      <button class="jbtn full" disabled>پر</button>
    {% elif a.has_password %}
      <button class="jbtn" onclick="openPass({{ a.obj.id }}, '{{ a.obj.name|escapejs }}')">🔐</button>
    {% else %}
      <form method="post" action="/alliance/join-id/{{ a.obj.id }}/" style="margin:0;">
        {% csrf_token %}
        <button type="submit" class="jbtn">ورود</button>
      </form>
    {% endif %}
  </div>
{% endfor %}
</div>
{% elif query %}
<div class="empty"><span class="em">🔍</span><h3>نتیجه‌ای پیدا نشد</h3><p>اتحادی با این مشخصات نیست.</p><a href="/alliance/" class="jbtn" style="display:inline-block;padding:12px 22px;">پاک کردن</a></div>
{% else %}
<div class="empty"><span class="em">🏰</span><h3>هنوز اتحادی نیست!</h3><p>اولین نفری باش که یه اتحاد می‌سازه</p><a href="/alliance/create/" class="cbtn" style="max-width:280px;margin:0 auto;">+ ساخت اولین اتحاد</a></div>
{% endif %}

<div class="modal-bg" id="passModal">
  <div class="modal">
    <div class="em">🔐</div>
    <h3>رمز اتحاد</h3>
    <p>اتحاد <b id="passName"></b> رمز دارد.</p>
    <form method="post" id="passForm">
      {% csrf_token %}
      <input type="password" name="password" placeholder="رمز" required>
      <div class="acts">
        <button type="submit" class="bok">ورود</button>
        <button type="button" class="bno" onclick="closePass()">انصراف</button>
      </div>
    </form>
  </div>
</div>
{% endblock %}
{% block extra_js %}
<script>
function openPass(id, name){
  document.getElementById('passForm').action = '/alliance/join-id/' + id + '/';
  document.getElementById('passName').textContent = name;
  document.getElementById('passModal').classList.add('active');
}
function closePass(){ document.getElementById('passModal').classList.remove('active'); }
document.getElementById('passModal').addEventListener('click', function(e){
  if (e.target.id === 'passModal') closePass();
});
</script>
{% endblock %}
''')

# ---- create.html ----
backup("alliance/templates/alliance/create.html")
write("alliance/templates/alliance/create.html", '''{% extends "base.html" %}
{% block title %}ساخت اتحاد{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.head h1{font-size:22px;font-weight:bold}
.head h1 span{color:var(--gold)}
.err{background:rgba(239,68,68,.15);color:#fca5a5;border:1px solid rgba(239,68,68,.35);padding:12px 16px;border-radius:12px;margin-bottom:14px;font-size:13px}
.box{background:var(--card);border:1px solid var(--border);padding:22px;border-radius:18px;margin-bottom:14px}
label{display:block;color:var(--muted);font-size:13px;margin:12px 0 6px}
input,textarea{width:100%;padding:12px 14px;border-radius:12px;border:1.5px solid var(--border);background:var(--bg);color:var(--text);font-size:15px;font-family:inherit;box-sizing:border-box}
textarea{resize:vertical;min-height:80px}
input:focus,textarea:focus{outline:none;border-color:var(--gold)}
.ems{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}
.eo{padding:12px 0;text-align:center;font-size:26px;background:var(--bg);border:2px solid transparent;border-radius:12px;cursor:pointer}
.eo:hover{border-color:var(--gold)}
.eo input{display:none}
.eo:has(input:checked){border-color:var(--gold);background:linear-gradient(135deg,rgba(244,197,66,.3),rgba(249,115,22,.2));box-shadow:0 0 20px rgba(244,197,66,.4)}
.save{width:100%;margin-top:20px;padding:16px;border:none;border-radius:14px;font-size:17px;font-weight:bold;font-family:inherit;cursor:pointer;color:#1a1a1a;background:linear-gradient(135deg,#22c55e,#16a34a);box-shadow:0 10px 30px rgba(34,197,94,.4)}
</style>
{% endblock %}
{% block content %}
<div class="head"><a href="/alliance/" class="back-btn"><span class="arrow-icon">→</span></a><h1>🏰 <span>ساخت اتحاد</span></h1></div>
{% if error %}<div class="err">{{ error }}</div>{% endif %}
<form method="post">
  {% csrf_token %}
  <div class="box">
    <label>نماد اتحاد</label>
    <div class="ems">
      {% for e in emojis %}
        <label class="eo"><input type="radio" name="emblem" value="{{ e }}" {% if forloop.first %}checked{% endif %}>{{ e }}</label>
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

# ---- detail.html ----
backup("alliance/templates/alliance/detail.html")
write("alliance/templates/alliance/detail.html", '''{% extends "base.html" %}
{% block title %}{{ alliance.name }}{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.hero{text-align:center;padding:30px 20px;background:linear-gradient(135deg,rgba(30,41,59,.8),rgba(15,23,42,.9));border:1px solid rgba(148,163,184,.2);border-radius:24px;margin-bottom:20px;position:relative;overflow:hidden}
.hero::before{content:"";position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle,rgba(244,197,66,.1) 0,transparent 60%);pointer-events:none}
.emb-big{font-size:76px;margin-bottom:12px}
.title{font-size:26px;font-weight:900;background:linear-gradient(135deg,#fde68a,#f4c542,#ca8a04);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:6px}
.code-box{display:inline-flex;align-items:center;gap:10px;background:rgba(15,23,42,.8);border:1px solid var(--border);padding:8px 16px;border-radius:12px;margin-top:16px;cursor:pointer}
.code-box:hover{border-color:var(--gold)}
.code-txt{font-family:monospace;font-size:18px;letter-spacing:3px;color:var(--gold);font-weight:bold}
.cap-wrap{margin-top:16px}
.cap-labels{display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-bottom:6px}
.cap-bar{height:8px;background:rgba(148,163,184,.15);border-radius:8px;overflow:hidden}
.cap-fill{height:100%;background:linear-gradient(90deg,#8b5cf6,#06b6d4);border-radius:8px}
.stats{display:flex;gap:10px;margin-bottom:20px}
.stat{flex:1;background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px;text-align:center}
.stat-val{font-size:22px;font-weight:bold;color:#fff;margin-bottom:4px}
.stat-lbl{font-size:11px;color:var(--muted)}
.actions{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}
.actions a,.actions button{flex:1;min-width:140px;text-align:center;padding:14px;border-radius:14px;text-decoration:none;font-weight:bold;font-size:15px;border:none;font-family:inherit;cursor:pointer;color:#fff}
.btn-chat{background:linear-gradient(135deg,#06b6d4,#3b82f6)}
.btn-edit{background:linear-gradient(135deg,#8b5cf6,#6b4eff)}
.btn-leave{background:linear-gradient(135deg,#ef4444,#dc2626)}
.members{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:20px}
.members h3{font-size:15px;color:var(--gold);margin-bottom:16px;display:flex;justify-content:space-between}
.badge{display:inline-block;background:var(--border);color:#fff;font-size:10px;padding:2px 8px;border-radius:8px;font-weight:bold}
.mrow{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05)}
.mrow:last-child{border-bottom:none}
.avwrap{position:relative}
.mav{width:44px;height:44px;border-radius:50%;background:rgba(15,23,42,.6);border:1px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:22px;background-size:cover;background-position:center}
.dot-on{position:absolute;bottom:0;right:0;width:12px;height:12px;background:#22c55e;border-radius:50%;border:2px solid var(--card)}
.minfo{flex:1}
.mname{font-size:14px;font-weight:bold;color:#fff;display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.mjoin{font-size:11px;color:var(--dim)}
.lvl{background:linear-gradient(135deg,#8b5cf6,#6b4eff);color:#fff;font-size:10px;padding:2px 6px;border-radius:6px;font-family:monospace}
.rbadge{font-size:11px;padding:4px 10px;border-radius:8px;font-weight:bold}
.r-leader{background:rgba(244,197,66,.2);color:#facc15;border:1px solid rgba(244,197,66,.3)}
.r-officer{background:rgba(59,130,246,.2);color:#93c5fd;border:1px solid rgba(59,130,246,.3)}
.r-member{background:rgba(100,116,139,.2);color:#cbd5e1;border:1px solid rgba(100,116,139,.3)}
.kbtn{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);color:#f87171;border-radius:8px;padding:6px 10px;cursor:pointer;font-size:12px;font-family:inherit}
</style>
{% endblock %}
{% block content %}
<div class="head"><a href="/alliance/" class="back-btn"><span class="arrow-icon">→</span></a></div>
<div class="hero">
  <div class="emb-big">{{ alliance.emblem }}</div>
  <div class="title">{{ alliance.name }}</div>
  {% if alliance.tag %}<div style="color:var(--muted);font-size:14px;letter-spacing:2px;">{{ alliance.tag }}</div>{% endif %}
  <div class="code-box" onclick="copyCode()">
    <span class="code-txt" id="codeTxt">{{ alliance.invite_code }}</span>
    <span>📋</span>
  </div>
  <div style="font-size:10px;color:var(--dim);margin-top:6px;">برای کپی کلیک کنید</div>
  <div class="cap-wrap">
    <div class="cap-labels"><span>ظرفیت</span><span>{{ member_count }} / {{ alliance.max_members }}</span></div>
    <div class="cap-bar"><div class="cap-fill" style="width:{% widthratio member_count alliance.max_members 100 %}%;"></div></div>
  </div>
</div>

<div class="stats">
  <div class="stat"><div class="stat-val">{{ member_count }} / {{ alliance.max_members }}</div><div class="stat-lbl">ظرفیت</div></div>
  <div class="stat"><div class="stat-val">{{ alliance.created_at|date:"Y/m/d" }}</div><div class="stat-lbl">تأسیس</div></div>
</div>

<div class="actions">
  <a href="/alliance/{{ alliance.id }}/chat/" class="btn-chat">💬 چت</a>
  {% if my_role == 'leader' %}<a href="/alliance/{{ alliance.id }}/edit/" class="btn-edit">✏️ ویرایش</a>{% endif %}
  <form method="post" action="/alliance/{{ alliance.id }}/leave/" style="flex:1;min-width:140px;margin:0;" onsubmit="return confirm('{% if my_role == 'leader' %}اتحاد منحل شود؟{% else %}از اتحاد خارج شوی؟{% endif %}');">
    {% csrf_token %}
    <button type="submit" class="btn-leave" style="width:100%;">{% if my_role == 'leader' %}🗑️ حذف{% else %}🚪 خروج{% endif %}</button>
  </form>
</div>

<div class="members">
  <h3>👥 اعضا <span class="badge">{{ member_count }}</span></h3>
  {% for m in members %}
    <div class="mrow">
      <div class="avwrap">
        {% if m.user.avatar_type == 'image' and m.user.avatar_id %}
          <div class="mav" style="background-image:url('/static/avatars/images/{{ m.user.avatar_id|stringformat:"03d" }}.jpg');"></div>
        {% else %}
          <div class="mav">{{ m.avatar }}</div>
        {% endif %}
        {% if m.is_online %}<div class="dot-on"></div>{% endif %}
      </div>
      <div class="minfo">
        <div class="mname">
          {{ m.user.alias }}
          {% if m.user.id == request.user.id %}<span style="color:var(--teal);font-size:10px;">(شما)</span>{% endif %}
          <span class="lvl">Lv {{ m.level }}</span>
        </div>
        <div class="mjoin">عضو از {{ m.joined_at|date:"Y/m/d" }}</div>
      </div>
      <span class="rbadge r-{{ m.role }}">
        {% if m.role == 'leader' %}👑 رهبر{% elif m.role == 'officer' %}🛡️ افسر{% else %}👤 عضو{% endif %}
      </span>
      {% if is_leader and m.role != 'leader' %}
        <form method="post" action="/alliance/{{ alliance.id }}/kick/{{ m.user.id }}/" style="margin:0;" onsubmit="return confirm('حذف شود؟');">
          {% csrf_token %}
          <button type="submit" class="kbtn">حذف</button>
        </form>
      {% endif %}
    </div>
  {% endfor %}
</div>
{% endblock %}
{% block extra_js %}
<script>
function copyCode(){
  const c = document.getElementById('codeTxt').innerText;
  navigator.clipboard.writeText(c).then(()=>alert('کپی شد: '+c)).catch(()=>alert('کد: '+c));
}
</script>
{% endblock %}
''')

# ---- edit.html ----
backup("alliance/templates/alliance/edit.html")
write("alliance/templates/alliance/edit.html", '''{% extends "base.html" %}
{% block title %}ویرایش اتحاد{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.head h1{font-size:22px;font-weight:bold}
.head h1 span{color:var(--gold)}
.err{background:rgba(239,68,68,.15);color:#fca5a5;border:1px solid rgba(239,68,68,.35);padding:12px 16px;border-radius:12px;margin-bottom:14px;font-size:13px}
.box{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:22px;margin-bottom:14px}
.box h3{font-size:14px;color:var(--gold);margin-bottom:16px}
label{display:block;color:var(--muted);font-size:13px;margin:12px 0 6px}
input,textarea{width:100%;padding:12px 14px;border-radius:12px;border:1.5px solid var(--border);background:var(--bg);color:var(--text);font-size:15px;font-family:inherit;box-sizing:border-box}
textarea{resize:vertical;min-height:70px}
input:focus,textarea:focus{outline:none;border-color:var(--purple)}
.ems{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}
.eo{padding:12px 0;text-align:center;font-size:26px;background:var(--bg);border:2px solid transparent;border-radius:12px;cursor:pointer}
.eo:hover{border-color:var(--gold)}
.eo input{display:none}
.eo:has(input:checked){border-color:var(--gold);background:linear-gradient(135deg,rgba(244,197,66,.25),rgba(139,92,246,.15))}
.save{width:100%;margin-top:16px;padding:16px;border:none;border-radius:14px;font-size:16px;font-weight:bold;font-family:inherit;cursor:pointer;color:#fff;background:linear-gradient(135deg,#8b5cf6,#6b4eff);box-shadow:0 10px 30px rgba(139,92,246,.4)}
</style>
{% endblock %}
{% block content %}
<div class="head"><a href="/alliance/{{ alliance.id }}/" class="back-btn"><span class="arrow-icon">→</span></a><h1>✏️ <span>ویرایش اتحاد</span></h1></div>
{% if error %}<div class="err">{{ error }}</div>{% endif %}
<form method="post">
  {% csrf_token %}
  <div class="box">
    <h3>🎨 نماد</h3>
    <div class="ems">
      {% for e in emojis %}
        <label class="eo"><input type="radio" name="emblem" value="{{ e }}" {% if e == alliance.emblem %}checked{% endif %}>{{ e }}</label>
      {% endfor %}
    </div>
  </div>
  <div class="box">
    <h3>📝 اطلاعات</h3>
    <label>نام اتحاد</label>
    <input type="text" name="name" maxlength="40" required value="{{ alliance.name }}">
    <label>تگ</label>
    <input type="text" name="tag" maxlength="8" value="{{ alliance.tag }}">
    <label>توضیح</label>
    <textarea name="description" maxlength="200">{{ alliance.description }}</textarea>
  </div>
  <div class="box">
    <h3>⚙️ تنظیمات</h3>
    <label>ظرفیت (۵ تا ۵۰)</label>
    <input type="number" name="max_members" min="5" max="50" value="{{ alliance.max_members }}">
    <label>رمز (خالی = بدون رمز)</label>
    <input type="password" name="password" maxlength="32" value="{{ alliance.password }}">
  </div>
  <button type="submit" class="save">💾 ذخیره</button>
</form>
{% endblock %}
''')

# ---- chat.html ----
backup("alliance/templates/alliance/chat.html")
write("alliance/templates/alliance/chat.html", '''{% extends "base.html" %}
{% block title %}چت {{ alliance.name }}{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.chead{display:flex;align-items:center;gap:12px;padding:16px;background:var(--card);border:1px solid var(--border);border-radius:16px;margin-bottom:16px}
.chead .em{font-size:32px}
.chead .info{flex:1}
.chead .name{font-size:16px;font-weight:bold;color:#fff}
.chead .sub{font-size:12px;color:var(--muted)}
.cbody{min-height:400px;max-height:55vh;overflow-y:auto;display:flex;flex-direction:column;gap:12px;padding:10px;background:rgba(15,23,42,.3);border-radius:20px;margin-bottom:16px}
.msg{display:flex;gap:10px;align-items:flex-end}
.msg.me{flex-direction:row-reverse}
.mav{width:32px;height:32px;border-radius:50%;background:rgba(51,65,85,.8);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;background-size:cover;background-position:center;border:1px solid var(--border)}
.bub{max-width:75%;padding:12px 16px;border-radius:18px;background:var(--card);border:1px solid var(--border);font-size:14px;line-height:1.5;color:#fff;border-bottom-right-radius:4px}
.msg.me .bub{background:linear-gradient(135deg,#3b82f6,#2563eb);border-color:#2563eb;border-bottom-right-radius:18px;border-bottom-left-radius:4px}
.sname{font-size:11px;color:var(--muted);margin-bottom:4px}
.time{font-size:9px;color:var(--dim);margin-top:6px;text-align:left}
.cinput{display:flex;gap:10px;background:var(--card);padding:10px;border-radius:16px;border:1px solid var(--border)}
.cinput input{flex:1;background:transparent;border:none;color:#fff;font-size:15px;padding:10px;font-family:inherit}
.cinput input:focus{outline:none}
.cinput button{background:linear-gradient(135deg,#06b6d4,#3b82f6);color:#fff;border:none;width:44px;height:44px;border-radius:12px;font-size:18px;cursor:pointer}
</style>
{% endblock %}
{% block content %}
<div class="head"><a href="/alliance/{{ alliance.id }}/" class="back-btn"><span class="arrow-icon">→</span></a></div>
<div class="chead">
  <div class="em">{{ alliance.emblem }}</div>
  <div class="info">
    <div class="name">{{ alliance.name }}</div>
    <div class="sub">چت گروهی</div>
  </div>
</div>
<div class="cbody" id="chatBody">
  {% for m in messages %}
    <div class="msg {% if m.is_me %}me{% endif %}">
      {% if m.sender.avatar_type == 'image' and m.sender.avatar_id %}
        <div class="mav" style="background-image:url('/static/avatars/images/{{ m.sender.avatar_id|stringformat:"03d" }}.jpg');"></div>
      {% else %}
        <div class="mav">{{ m.avatar }}</div>
      {% endif %}
      <div>
        {% if not m.is_me %}<div class="sname">{{ m.sender.alias }}</div>{% endif %}
        <div class="bub">{{ m.body }}</div>
        <div class="time">{{ m.sent_at|date:"H:i" }}</div>
      </div>
    </div>
  {% empty %}
    <div style="text-align:center;color:var(--dim);font-size:13px;margin:auto;">هنوز پیامی نیست. اولین نفر باش!</div>
  {% endfor %}
</div>
<form method="post" class="cinput">
  {% csrf_token %}
  <input type="text" name="body" maxlength="500" required placeholder="پیامت را بنویس..." autocomplete="off" autofocus>
  <button type="submit">↑</button>
</form>
{% endblock %}
{% block extra_js %}
<script>
const b = document.getElementById('chatBody');
if (b) b.scrollTop = b.scrollHeight;
</script>
{% endblock %}
''')

# ---- join.html ----
backup("alliance/templates/alliance/join.html")
write("alliance/templates/alliance/join.html", '''{% extends "base.html" %}
{% block title %}ورود با کد{% endblock %}
{% block extra_css %}
<style>
.head{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.head h1{font-size:22px;font-weight:bold}
.head h1 span{color:var(--gold)}
.err{background:rgba(239,68,68,.15);color:#fca5a5;border:1px solid rgba(239,68,68,.35);padding:12px 16px;border-radius:12px;margin-bottom:14px;font-size:13px;text-align:center}
.box{background:var(--card);border:1px solid var(--border);padding:28px 22px;border-radius:18px;text-align:center}
label{display:block;color:var(--muted);font-size:13px;margin-bottom:10px}
input{width:100%;padding:18px;border-radius:14px;border:2px solid var(--border);background:var(--bg);color:var(--text);font-size:26px;font-family:monospace;text-align:center;letter-spacing:8px;text-transform:uppercase;box-sizing:border-box}
input:focus{outline:none;border-color:var(--teal)}
button{width:100%;margin-top:20px;padding:16px;border:none;border-radius:14px;font-size:17px;font-weight:bold;font-family:inherit;cursor:pointer;color:#fff;background:linear-gradient(135deg,#06b6d4,#3b82f6)}
</style>
{% endblock %}
{% block content %}
<div class="head"><a href="/alliance/" class="back-btn"><span class="arrow-icon">→</span></a><h1>🔑 <span>ورود با کد</span></h1></div>
{% if error %}<div class="err">{{ error }}</div>{% endif %}
<div class="box">
  <form method="post">
    {% csrf_token %}
    <label>کد ۶ حرفی</label>
    <input type="text" name="code" maxlength="6" required placeholder="ABC123" autocomplete="off">
    <button type="submit">🚀 پیوستن</button>
  </form>
</div>
{% endblock %}
''')

# ============================================================
# 5) Migrations
# ============================================================
print("\n[5/6] Migrations")
for cmd in [
    [sys.executable, "manage.py", "makemigrations", "alliance", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd[1:])}")
    if r.returncode != 0 and r.stderr.strip():
        print(f"    ⚠ {r.stderr.strip()[:300]}")

# ============================================================
# 6) TEST
# ============================================================
print("\n[6/6] TESTING")
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

print("\n  → Loading views...")
try:
    from alliance import views
    for fn in ["alliance_home","create_alliance","join_alliance","join_by_code",
               "alliance_detail","alliance_edit","alliance_chat","leave_alliance","kick_member"]:
        ok = hasattr(views, fn)
        print(f"    {'✓' if ok else '✗'} {fn}")
except Exception as e:
    print(f"    ❌ import failed: {e}")
    sys.exit(1)

print("\n  → Testing URLs...")
try:
    from django.urls import reverse
    tests = [
        ("alliance:home", {}),
        ("alliance:create", {}),
        ("alliance:detail", {"alliance_id": 1}),
        ("alliance:edit", {"alliance_id": 1}),
        ("alliance:chat", {"alliance_id": 1}),
    ]
    for name, kwargs in tests:
        try:
            url = reverse(name, kwargs=kwargs)
            print(f"    ✓ {name} → {url}")
        except Exception as e:
            print(f"    ✗ {name} → {type(e).__name__}")
except Exception as e:
    print(f"    ❌ URL test failed: {e}")

print("\n  → Testing with HTTP client...")
try:
    tu = User.objects.filter(username="__alliance_diag__").first()
    created = False
    if not tu:
        tu = User.objects.create_user(
            username="__alliance_diag__", password="x" * 10,
            alias="دیباگ", is_active=True,
            has_chosen_avatar=True, has_completed_registration=True,
        )
        created = True

    c = Client()
    c.force_login(tu)

    # Test home
    r = c.get("/alliance/")
    print(f"    /alliance/ → {r.status_code}")
    if r.status_code >= 500:
        print(f"      ERROR: {r.content.decode()[:300]}")

    # Test create
    r = c.get("/alliance/create/")
    print(f"    /alliance/create/ → {r.status_code}")
    if r.status_code >= 500:
        print(f"      ERROR: {r.content.decode()[:300]}")

    # Test creating an alliance via POST
    r = c.post("/alliance/create/", {
        "name": "__test_alliance__",
        "tag": "TST",
        "description": "test",
        "emblem": "🛡️",
        "max_members": "10",
        "password": "",
    }, follow=False)
    print(f"    POST create → {r.status_code} {r.get('Location', '')}")

    from alliance.models import Alliance
    test_a = Alliance.objects.filter(name="__test_alliance__").first()
    if test_a:
        print(f"    ✓ Created: {test_a.name} (id={test_a.id})")

        # Test detail
        r = c.get(f"/alliance/{test_a.id}/")
        print(f"    /alliance/{test_a.id}/ → {r.status_code}")

        # Test edit
        r = c.get(f"/alliance/{test_a.id}/edit/")
        print(f"    /alliance/{test_a.id}/edit/ → {r.status_code}")

        # Test chat
        r = c.get(f"/alliance/{test_a.id}/chat/")
        print(f"    /alliance/{test_a.id}/chat/ → {r.status_code}")

        # Cleanup
        test_a.delete()
        print(f"    ✓ Cleaned up test alliance")
    else:
        print(f"    ⚠ Alliance not created - checking form errors")

    if created:
        tu.delete()

except Exception as e:
    import traceback
    print(f"    ❌ Test failed: {e}")
    traceback.print_exc()

# Final check
print("\n  → Django check...")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("    ✓ PASSED")
else:
    print(f"    ⚠ {r.stderr[:400]}")

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
Now run:
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)

Then visit:
  /alliance/          — list
  /alliance/create/   — create form

If pages fail, the test output above shows EXACTLY which URL
and what status code. Send it.

Password reminders:
  Beta: emami_irani_esm1405
  Admin: admin74 / Amir2255ds
""")
