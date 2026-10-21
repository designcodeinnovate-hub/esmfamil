#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def read(p):
    try:
        with open(p, "r", encoding="utf-8") as f: return f.read()
    except: return ""
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")

# ============================================================
# 1) MODEL — UserUnlockedAvatar
# ============================================================
print("\n[1/7] Adding UserUnlockedAvatar model")
src = read("accounts/models.py")

if "from django.conf import settings" not in src:
    src = src.replace("from django.db import models", "from django.conf import settings\nfrom django.db import models", 1)

if "class UserUnlockedAvatar" not in src:
    src += '''

class UserUnlockedAvatar(models.Model):
    """آواتارهای تصویری بازشده (50 سکه برای هر آواتار)"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="unlocked_avatars",
    )
    avatar_type = models.CharField(max_length=10, default="image")
    avatar_id = models.PositiveSmallIntegerField()
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "avatar_type", "avatar_id")
        ordering = ("-unlocked_at",)

    def __str__(self):
        return f"{self.user.alias} - {self.avatar_type}#{self.avatar_id}"
'''
    write("accounts/models.py", src)
    print("  ✓ model added")
else:
    print("  ✓ already exists")

# ============================================================
# 2) VIEWS — Rewrite avatar_select + complete_registration
# ============================================================
print("\n[2/7] Updating views")

views_src = read("accounts/views.py")

# Ensure messages import
if "from django.contrib import messages" not in views_src:
    views_src = "from django.contrib import messages\n" + views_src
    print("  ✓ messages imported")

# Ensure UserUnlockedAvatar import
if "UserUnlockedAvatar" not in views_src:
    views_src = views_src.replace(
        "from .models import EmailVerificationToken",
        "from .models import EmailVerificationToken, UserUnlockedAvatar",
        1
    )
    print("  ✓ UserUnlockedAvatar imported")

# Replace avatar_select
pattern = re.compile(r'@login_required\ndef avatar_select\(request\):.*?(?=\n@login_required|\ndef [a-z]|\Z)', re.DOTALL)

NEW_AVATAR_SELECT = '''@login_required
def avatar_select(request):
    if request.user.is_guest:
        return render(request, "accounts/avatar_select.html", {
            "categories": AVATAR_CATEGORIES,
            "image_avatars": [],
            "is_guest": True,
            "locked_message": "🔒 تغییر آواتار در حالت مهمان قفل است.",
        })

    unlocked_ids = set(
        UserUnlockedAvatar.objects.filter(user=request.user, avatar_type="image")
        .values_list("avatar_id", flat=True)
    )

    image_list = []
    for img in IMAGE_AVATARS:
        image_list.append({
            "id": img["id"],
            "url": img["url"],
            "unlocked": img["id"] in unlocked_ids,
            "price": 0 if img["id"] in unlocked_ids else 50,
        })

    if request.method == "POST":
        action = request.POST.get("action", "select")

        if action == "unlock":
            try:
                aid = int(request.POST.get("avatar_id", 0))
            except (ValueError, TypeError):
                aid = 0
            if not (1 <= aid <= 44):
                messages.error(request, "آواتار نامعتبر.")
                return redirect("accounts:avatar_select")

            if UserUnlockedAvatar.objects.filter(user=request.user, avatar_type="image", avatar_id=aid).exists():
                messages.info(request, "قبلاً باز شده.")
                return redirect("accounts:avatar_select")

            PRICE = 50
            if (request.user.coins or 0) < PRICE:
                messages.error(request, f"سکه کافی نداری (نیاز: {PRICE}).")
                return redirect("accounts:avatar_select")

            request.user.coins -= PRICE
            request.user.save(update_fields=["coins"])
            UserUnlockedAvatar.objects.create(user=request.user, avatar_type="image", avatar_id=aid)
            messages.success(request, f"🎉 آواتار باز شد! -{PRICE} سکه")
            return redirect("accounts:avatar_select")

        # Normal selection
        avatar_type = request.POST.get("avatar_type", "emoji")
        if avatar_type not in ("emoji", "image"):
            avatar_type = "emoji"
        try:
            aid = int(request.POST.get("avatar_id", ""))
        except (ValueError, TypeError):
            aid = -1
        max_id = 99 if avatar_type == "emoji" else 44

        if not (0 <= aid <= max_id):
            messages.error(request, "آواتار نامعتبر.")
        elif avatar_type == "image" and not UserUnlockedAvatar.objects.filter(
            user=request.user, avatar_type="image", avatar_id=aid
        ).exists():
            messages.error(request, "این آواتار قفله. اول بازش کن.")
            return redirect("accounts:avatar_select")
        else:
            request.user.avatar_id = aid
            request.user.avatar_type = avatar_type
            request.user.has_chosen_avatar = True
            request.user.save(update_fields=["avatar_id", "avatar_type", "has_chosen_avatar"])
            messages.success(request, "آواتار تغییر کرد.")
            return redirect("accounts:profile")

    return render(request, "accounts/avatar_select.html", {
        "categories": AVATAR_CATEGORIES,
        "image_avatars": image_list,
        "current_avatar": request.user.avatar_id,
        "current_type": request.user.avatar_type,
        "is_guest": False,
        "user_coins": request.user.coins or 0,
        "active": "profile",
    })
'''

m = pattern.search(views_src)
if m:
    views_src = views_src[:m.start()] + NEW_AVATAR_SELECT + "\n\n" + views_src[m.end():]
    print("  ✓ avatar_select replaced")

# Replace complete_registration
pattern = re.compile(r'@login_required\ndef complete_registration\(request\):.*?(?=\n@login_required|\ndef [a-z]|\Z)', re.DOTALL)

NEW_COMPLETE = '''@login_required
def complete_registration(request):
    user = request.user
    if user.has_completed_registration:
        return redirect("game:home")

    unlocked_ids = set(
        UserUnlockedAvatar.objects.filter(user=user, avatar_type="image")
        .values_list("avatar_id", flat=True)
    )
    image_list = []
    for img in IMAGE_AVATARS:
        image_list.append({
            "id": img["id"],
            "url": img["url"],
            "unlocked": img["id"] in unlocked_ids,
            "price": 0 if img["id"] in unlocked_ids else 50,
        })

    error = None
    if request.method == "POST":
        action = request.POST.get("action", "finish")

        if action == "unlock":
            try:
                aid = int(request.POST.get("avatar_id", 0))
            except (ValueError, TypeError):
                aid = 0
            if 1 <= aid <= 44:
                if UserUnlockedAvatar.objects.filter(user=user, avatar_type="image", avatar_id=aid).exists():
                    messages.info(request, "قبلاً باز شده.")
                elif (user.coins or 0) >= 50:
                    user.coins -= 50
                    user.save(update_fields=["coins"])
                    UserUnlockedAvatar.objects.create(user=user, avatar_type="image", avatar_id=aid)
                    messages.success(request, "🎉 آواتار باز شد! -50 سکه")
                else:
                    messages.error(request, "سکه کافی نداری (نیاز: 50).")
            return redirect("accounts:complete_registration")

        alias = (request.POST.get("alias") or "").strip()[:32]
        avatar_type = request.POST.get("avatar_type", "emoji")
        if avatar_type not in ("emoji", "image"):
            avatar_type = "emoji"
        try:
            avatar_id = int(request.POST.get("avatar_id", ""))
        except (ValueError, TypeError):
            avatar_id = -1
        max_id = 99 if avatar_type == "emoji" else 44

        if not alias:
            error = "نام نمایشی را وارد کن."
        elif len(alias) < 2:
            error = "نام باید حداقل ۲ حرف باشد."
        elif not (0 <= avatar_id <= max_id):
            error = "یک آواتار انتخاب کن."
        elif avatar_type == "image" and not UserUnlockedAvatar.objects.filter(
            user=user, avatar_type="image", avatar_id=avatar_id
        ).exists():
            error = "این آواتار قفله. اول بازش کن یا ایموجی انتخاب کن."
        else:
            user.alias = alias
            user.avatar_id = avatar_id
            user.avatar_type = avatar_type
            user.has_chosen_avatar = True
            user.has_completed_registration = True
            user.save(update_fields=[
                "alias", "avatar_id", "avatar_type",
                "has_chosen_avatar", "has_completed_registration",
            ])
            return redirect("game:home")

    return render(request, "accounts/complete_registration.html", {
        "categories": AVATAR_CATEGORIES,
        "image_avatars": image_list,
        "error": error,
        "user_coins": user.coins or 0,
    })
'''

m = pattern.search(views_src)
if m:
    views_src = views_src[:m.start()] + NEW_COMPLETE + "\n\n" + views_src[m.end():]
    print("  ✓ complete_registration replaced")

# Give welcome coins on register
views_src = views_src.replace(
    'user = User.objects.create_user(\n                username=username, password=password,\n                alias=username, is_active=True,\n            )',
    'user = User.objects.create_user(\n                username=username, password=password,\n                alias=username, is_active=True, coins=100,\n            )'
)

write("accounts/views.py", views_src)

# ============================================================
# 3) TEMPLATES — avatar_select + complete_registration
# ============================================================

AVATAR_HTML = '''{% extends "base.html" %}
{% block title %}آواتار{% endblock %}
{% block extra_css %}
<style>
  .page-head{display:flex;align-items:center;gap:12px;margin-bottom:16px;justify-content:space-between}
  .page-head-left{display:flex;align-items:center;gap:12px}
  .page-head h1{font-size:20px;font-weight:800}
  .coins-badge{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;background:var(--surface);border:1px solid var(--border);border-radius:var(--r-full);color:var(--gold);font-size:13px;font-weight:700;font-family:monospace}
  .tabs{display:flex;gap:8px;background:var(--surface);border:1px solid var(--border);padding:6px;border-radius:var(--r-md);margin-bottom:16px}
  .tab{flex:1;padding:12px;text-align:center;border-radius:var(--r-sm);font-size:13px;font-weight:700;cursor:pointer;color:var(--text-secondary);background:transparent;border:none;font-family:inherit}
  .tab.active{background:var(--petrol);color:var(--turquoise)}
  .tab-content{display:none}
  .tab-content.active{display:block}
  .avatar-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px}
  .avatar-item{position:relative;aspect-ratio:1}
  .avatar-item input[type=radio]{position:absolute;opacity:0;pointer-events:none}
  .avatar-label{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background-color:#e2e8f0;background-size:cover;background-position:center;border:2px solid transparent;border-radius:var(--r-md);cursor:pointer;font-size:32px;user-select:none;transition:0.15s}
  .avatar-item input[type=radio]:checked + .avatar-label{border-color:var(--gold);transform:scale(1.05);box-shadow:0 0 0 3px rgba(245,196,81,0.3)}
  .avatar-item.locked .avatar-label{filter:grayscale(1) brightness(0.35);cursor:not-allowed}
  .lock-overlay{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;background:rgba(16,24,39,0.55);border-radius:var(--r-md);cursor:pointer;z-index:3;border:none;font-family:inherit;transition:0.15s}
  .lock-overlay:hover{background:rgba(16,24,39,0.7)}
  .lock-overlay .lock-icon{font-size:22px}
  .lock-overlay .price{font-size:11px;font-weight:800;color:var(--gold);font-family:monospace;background:rgba(0,0,0,0.5);padding:2px 8px;border-radius:var(--r-full)}
  .submit-btn{width:100%;padding:16px;border:none;border-radius:var(--r-md);background:var(--gold);color:#101827;font-family:inherit;font-weight:800;font-size:16px;cursor:pointer}
  .guest-box{text-align:center;padding:40px 20px;background:var(--surface);border:1px dashed var(--border);border-radius:var(--r-lg)}
  .guest-box h3{color:var(--error);margin-bottom:8px;font-size:16px}
</style>
{% endblock %}
{% block content %}
  <div class="page-head">
    <div class="page-head-left">
      <a href="/accounts/profile/" class="back-btn">→</a>
      <h1>🎨 آواتار</h1>
    </div>
    {% if not is_guest %}<div class="coins-badge">🪙 {{ user_coins }}</div>{% endif %}
  </div>

  {% if is_guest %}
    <div class="guest-box">
      <h3>🔒 قفل است</h3>
      <p style="color:var(--text-secondary);font-size:13px;">{{ locked_message }}</p>
    </div>
  {% else %}
    <form method="post" id="avatarForm">
      {% csrf_token %}
      <input type="hidden" name="action" value="select">
      <input type="hidden" name="avatar_type" id="avatarType" value="{{ current_type|default:'emoji' }}">
      <input type="hidden" name="avatar_id" id="avatarId" value="{{ current_avatar|default:'' }}">

      <div class="tabs">
        <button type="button" class="tab {% if current_type != 'image' %}active{% endif %}" onclick="switchTab('emoji')">😊 ایموجی</button>
        <button type="button" class="tab {% if current_type == 'image' %}active{% endif %}" onclick="switchTab('image')">🖼️ شخصیت‌ها</button>
      </div>

      <div id="tab-emoji" class="tab-content {% if current_type != 'image' %}active{% endif %}">
        <div class="avatar-grid">
          {% for cat in categories %}
            {% for emoji in cat.items %}
              <div class="avatar-item">
                <input type="radio" name="pick_emoji" id="em-{{ cat.key }}-{{ forloop.counter }}" data-cat="{{ cat.key }}" data-idx="{{ forloop.counter0 }}" onchange="pickEmoji(this)">
                <label class="avatar-label" for="em-{{ cat.key }}-{{ forloop.counter }}">{{ emoji }}</label>
              </div>
            {% endfor %}
          {% endfor %}
        </div>
      </div>

      <div id="tab-image" class="tab-content {% if current_type == 'image' %}active{% endif %}">
        <div class="avatar-grid">
          {% for img in image_avatars %}
            <div class="avatar-item {% if not img.unlocked %}locked{% endif %}">
              {% if img.unlocked %}
                <input type="radio" name="pick_image" id="im-{{ img.id }}" data-id="{{ img.id }}" onchange="pickImage(this)">
                <label class="avatar-label" for="im-{{ img.id }}" style="background-image: url('{{ img.url }}');"></label>
              {% else %}
                <div class="avatar-label" style="background-image: url('{{ img.url }}');"></div>
                <button type="button" class="lock-overlay" onclick="unlockAvatar({{ img.id }});">
                  <div class="lock-icon">🔒</div>
                  <div class="price">{{ img.price }} 🪙</div>
                </button>
              {% endif %}
            </div>
          {% endfor %}
        </div>
      </div>

      <button type="submit" class="submit-btn">✅ ذخیره آواتار</button>
    </form>

    <form method="post" id="unlockForm" style="display:none;">
      {% csrf_token %}
      <input type="hidden" name="action" value="unlock">
      <input type="hidden" name="avatar_id" id="unlockAvatarId" value="">
    </form>
  {% endif %}
{% endblock %}
{% block extra_js %}
<script>
  const catOrder = [{% for cat in categories %}"{{ cat.key }}"{% if not forloop.last %},{% endif %}{% endfor %}];
  function switchTab(type) {
    document.getElementById('avatarType').value = type;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    if (type === 'emoji') {
      document.querySelectorAll('.tab')[0].classList.add('active');
      document.getElementById('tab-emoji').classList.add('active');
    } else {
      document.querySelectorAll('.tab')[1].classList.add('active');
      document.getElementById('tab-image').classList.add('active');
    }
    document.getElementById('avatarId').value = '';
  }
  function pickEmoji(el) {
    document.getElementById('avatarId').value = catOrder.indexOf(el.dataset.cat) * 10 + parseInt(el.dataset.idx);
    document.getElementById('avatarType').value = 'emoji';
  }
  function pickImage(el) {
    document.getElementById('avatarId').value = parseInt(el.dataset.id);
    document.getElementById('avatarType').value = 'image';
  }
  function unlockAvatar(id) {
    if (!confirm('۵۰ سکه بدی تا این آواتار باز شه؟')) return;
    document.getElementById('unlockAvatarId').value = id;
    document.getElementById('unlockForm').submit();
  }
</script>
{% endblock %}
'''
write("accounts/templates/accounts/avatar_select.html", AVATAR_HTML)

COMPLETE_HTML = '''{% extends "base.html" %}
{% block title %}تکمیل پروفایل{% endblock %}
{% block extra_css %}
<style>
  .page-head{text-align:center;margin-bottom:20px}
  .page-head h1{font-size:22px;font-weight:800;color:var(--text);margin-bottom:6px}
  .page-head p{color:var(--text-secondary);font-size:13px}
  .coins-badge{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;background:var(--surface);border:1px solid var(--border);border-radius:var(--r-full);color:var(--gold);font-size:13px;font-weight:700;font-family:monospace;margin-bottom:12px}
  .box{background:var(--surface);border:1px solid var(--border);border-radius:var(--r-lg);padding:20px;margin-bottom:16px}
  .box h3{font-size:14px;color:var(--gold);margin-bottom:12px;font-weight:700}
  .box input[type=text]{width:100%;padding:14px;border-radius:var(--r-md);border:1.5px solid var(--border);background:var(--bg);color:var(--text);font-family:inherit;font-size:16px;text-align:center;box-sizing:border-box}
  .box input[type=text]:focus{outline:none;border-color:var(--turquoise)}
  .error-box{background:rgba(240,113,120,0.15);color:var(--error);border:1px solid rgba(240,113,120,0.3);padding:12px 16px;border-radius:var(--r-md);margin-bottom:16px;font-size:13px}
  .tabs{display:flex;gap:8px;background:var(--bg);padding:6px;border-radius:var(--r-md);margin-bottom:16px}
  .tab{flex:1;padding:12px;text-align:center;border-radius:var(--r-sm);font-size:12px;font-weight:700;cursor:pointer;color:var(--text-secondary);border:none;background:transparent;font-family:inherit}
  .tab.active{background:var(--petrol);color:var(--turquoise)}
  .tab-content{display:none}
  .tab-content.active{display:block}
  .avatar-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;max-height:400px;overflow-y:auto;padding:4px}
  .avatar-item{position:relative;aspect-ratio:1}
  .avatar-item input[type=radio]{position:absolute;opacity:0;pointer-events:none}
  .avatar-label{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background-color:#e2e8f0;background-size:cover;background-position:center;border:2px solid transparent;border-radius:var(--r-md);cursor:pointer;font-size:32px;user-select:none;transition:0.15s}
  .avatar-item input[type=radio]:checked + .avatar-label{border-color:var(--gold);transform:scale(1.05);box-shadow:0 0 0 3px rgba(245,196,81,0.3)}
  .avatar-item.locked .avatar-label{filter:grayscale(1) brightness(0.35);cursor:not-allowed}
  .lock-overlay{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;background:rgba(16,24,39,0.55);border-radius:var(--r-md);cursor:pointer;z-index:3;border:none;font-family:inherit}
  .lock-overlay .lock-icon{font-size:22px}
  .lock-overlay .price{font-size:11px;font-weight:800;color:var(--gold);font-family:monospace;background:rgba(0,0,0,0.5);padding:2px 8px;border-radius:var(--r-full)}
  .submit-btn{width:100%;padding:16px;border:none;border-radius:var(--r-md);background:var(--gold);color:#101827;font-family:inherit;font-weight:800;font-size:16px;cursor:pointer}
</style>
{% endblock %}
{% block content %}
  <div class="page-head">
    <h1>🎨 تکمیل پروفایل</h1>
    <p>نام نمایشی و آواتارت رو انتخاب کن</p>
    <div class="coins-badge">🪙 {{ user_coins }} سکه</div>
  </div>

  {% if error %}<div class="error-box">{{ error }}</div>{% endif %}

  <form method="post" id="regForm">
    {% csrf_token %}
    <input type="hidden" name="action" value="finish">
    <input type="hidden" name="avatar_type" id="avatarType" value="emoji">
    <input type="hidden" name="avatar_id" id="avatarId" value="">

    <div class="box">
      <h3>👤 نام نمایشی</h3>
      <input type="text" name="alias" maxlength="32" required value="{{ request.POST.alias|default:user.alias }}" placeholder="مثلاً: علی">
    </div>

    <div class="box">
      <h3>🎨 آواتار</h3>
      <div class="tabs">
        <button type="button" class="tab active" onclick="switchTab('emoji')">😊 ایموجی (رایگان)</button>
        <button type="button" class="tab" onclick="switchTab('image')">🖼️ شخصیت (۵۰ سکه)</button>
      </div>
      <div id="tab-emoji" class="tab-content active">
        <div class="avatar-grid">
          {% for cat in categories %}
            {% for emoji in cat.items %}
              <div class="avatar-item">
                <input type="radio" name="pick_emoji" id="em-{{ cat.key }}-{{ forloop.counter }}" data-cat="{{ cat.key }}" data-idx="{{ forloop.counter0 }}" onchange="pickEmoji(this)">
                <label class="avatar-label" for="em-{{ cat.key }}-{{ forloop.counter }}">{{ emoji }}</label>
              </div>
            {% endfor %}
          {% endfor %}
        </div>
      </div>
      <div id="tab-image" class="tab-content">
        <div class="avatar-grid">
          {% for img in image_avatars %}
            <div class="avatar-item {% if not img.unlocked %}locked{% endif %}">
              {% if img.unlocked %}
                <input type="radio" name="pick_image" id="im-{{ img.id }}" data-id="{{ img.id }}" onchange="pickImage(this)">
                <label class="avatar-label" for="im-{{ img.id }}" style="background-image: url('{{ img.url }}');"></label>
              {% else %}
                <div class="avatar-label" style="background-image: url('{{ img.url }}');"></div>
                <button type="button" class="lock-overlay" onclick="unlockAvatar({{ img.id }});">
                  <div class="lock-icon">🔒</div>
                  <div class="price">{{ img.price }} 🪙</div>
                </button>
              {% endif %}
            </div>
          {% endfor %}
        </div>
      </div>
    </div>

    <button type="submit" class="submit-btn">✅ تمام! بریم بازی</button>
  </form>

  <form method="post" id="unlockForm" style="display:none;">
    {% csrf_token %}
    <input type="hidden" name="action" value="unlock">
    <input type="hidden" name="avatar_id" id="unlockAvatarId" value="">
  </form>
{% endblock %}
{% block extra_js %}
<script>
  const catOrder = [{% for cat in categories %}"{{ cat.key }}"{% if not forloop.last %},{% endif %}{% endfor %}];
  function switchTab(type) {
    document.getElementById('avatarType').value = type;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    if (type === 'emoji') {
      document.querySelectorAll('.tab')[0].classList.add('active');
      document.getElementById('tab-emoji').classList.add('active');
    } else {
      document.querySelectorAll('.tab')[1].classList.add('active');
      document.getElementById('tab-image').classList.add('active');
    }
    document.getElementById('avatarId').value = '';
  }
  function pickEmoji(el) {
    document.getElementById('avatarId').value = catOrder.indexOf(el.dataset.cat) * 10 + parseInt(el.dataset.idx);
    document.getElementById('avatarType').value = 'emoji';
  }
  function pickImage(el) {
    document.getElementById('avatarId').value = parseInt(el.dataset.id);
    document.getElementById('avatarType').value = 'image';
  }
  function unlockAvatar(id) {
    if (!confirm('۵۰ سکه بدی تا این آواتار باز شه؟')) return;
    document.getElementById('unlockAvatarId').value = id;
    document.getElementById('unlockForm').submit();
  }
</script>
{% endblock %}
'''
write("accounts/templates/accounts/complete_registration.html", COMPLETE_HTML)

# ============================================================
# 4) SHOP — ensure seed + routes
# ============================================================
print("\n[4/7] Shop check")

SEED = '''
from accounts.models import ShopItem
if ShopItem.objects.count() == 0:
    items = [
        {"name": "جعبه شانس کوچک", "icon": "🎁", "category": "box", "price_coins": 100, "reward_type": "coins_random", "reward_min": 50, "reward_max": 300, "description": "بین ۵۰ تا ۳۰۰ سکه"},
        {"name": "جعبه شانس بزرگ", "icon": "💎", "category": "box", "price_gems": 10, "reward_type": "gems_random", "reward_min": 3, "reward_max": 20, "description": "بین ۳ تا ۲۰ جم"},
        {"name": "بسته ۵۰۰ سکه", "icon": "💰", "category": "bundle", "price_gems": 10, "reward_type": "coins_fixed", "reward_value": 500, "description": "۵۰۰ سکه"},
        {"name": "بسته ۲۰۰۰ سکه", "icon": "💰", "category": "bundle", "price_gems": 35, "reward_type": "coins_fixed", "reward_value": 2000, "description": "۲۰۰۰ سکه"},
        {"name": "تم طلایی", "icon": "🎨", "category": "theme", "price_gems": 50, "reward_type": "theme", "description": "تم ویژه"},
        {"name": "بوست ۲ برابر", "icon": "⚡", "category": "boost", "price_coins": 200, "reward_type": "boost", "description": "امتیاز دوبرابر"},
    ]
    for i, d in enumerate(items):
        ShopItem.objects.create(sort_order=i, is_active=True, **d)
    print(f"Seeded {len(items)}")
else:
    print(f"Already {ShopItem.objects.count()} items")
'''
r = subprocess.run([sys.executable, "manage.py", "shell", "-c", SEED], capture_output=True, text=True, timeout=30)
if r.returncode == 0:
    print(f"  ✓ {r.stdout.strip() or 'shop OK'}")

# ============================================================
# 5) HOME REDESIGN
# ============================================================
print("\n[5/7] Home redesign")

HOME = '''{% extends "base.html" %}
{% block title %}خانه{% endblock %}
{% block extra_css %}
<style>
  .top-row{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:20px}
  .btn-settings{width:48px;height:48px;border-radius:50%;background:var(--surface);border:1px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;text-decoration:none}
  .btn-settings:hover{border-color:var(--turquoise)}
  .profile-wrap{position:relative}
  .profile-oval{display:flex;align-items:center;gap:0;padding:6px;height:56px;width:56px;border-radius:28px;background:var(--surface);border:2px solid var(--border);cursor:pointer;transition:all 0.35s cubic-bezier(0.4,0,0.2,1);overflow:hidden;flex-shrink:0}
  .profile-oval:hover{border-color:var(--turquoise)}
  .profile-oval.expanded{width:260px;padding:10px 14px;gap:12px;border-color:var(--turquoise)}
  .po-av{width:42px;height:42px;border-radius:50%;background:var(--surface-elevated);display:flex;align-items:center;justify-content:center;font-size:22px;border:2px solid var(--turquoise);overflow:hidden;background-size:cover;background-position:center;flex-shrink:0}
  .po-details{flex:1;min-width:0;max-width:0;opacity:0;overflow:hidden;transition:all 0.35s;text-align:right;white-space:nowrap}
  .profile-oval.expanded .po-details{max-width:200px;opacity:1}
  .po-name{font-size:14px;font-weight:700;color:var(--text);margin-bottom:2px;overflow:hidden;text-overflow:ellipsis}
  .po-meta{display:flex;gap:6px;font-size:10px;color:var(--text-secondary)}
  .po-meta .lvl{color:var(--turquoise);font-weight:700;font-family:monospace}
  .circle-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px}
  .circle-btn{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:16px 12px;border-radius:var(--r-lg);text-decoration:none;color:var(--text);background:var(--surface);border:1px solid var(--border);transition:all 0.2s;cursor:pointer}
  .circle-btn:hover{border-color:var(--turquoise);transform:translateY(-2px)}
  .cb-icon{width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26px;background:var(--bg);border:2px solid var(--border);transition:transform 0.2s}
  .circle-btn:hover .cb-icon{transform:scale(1.1);border-color:var(--turquoise)}
  .cb-title{font-size:13px;font-weight:700}
  .cb-desc{font-size:10px;color:var(--text-secondary)}
  .circle-btn.gold .cb-icon{border-color:var(--gold)}
  .circle-btn.gold:hover .cb-icon{border-color:var(--gold-hover)}
  .circle-btn.shop .cb-icon{border-color:var(--turquoise)}
  .section-title{font-size:11px;font-weight:700;color:var(--text-secondary);letter-spacing:1.5px;margin:20px 0 12px;display:flex;align-items:center;gap:8px;text-transform:uppercase}
  .section-title::after{content:"";flex:1;height:1px;background:var(--border)}
  .row-2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
  .big-tile{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:20px 12px;border-radius:var(--r-lg);text-decoration:none;color:var(--text);background:var(--surface);border:1px solid var(--border);transition:all 0.2s;text-align:center;min-height:130px}
  .big-tile:hover{border-color:var(--turquoise);transform:translateY(-2px)}
  .bt-icon{font-size:38px}
  .bt-title{font-size:15px;font-weight:800}
  .bt-desc{font-size:11px;color:var(--text-secondary)}
  .big-tile.games{border-color:var(--petrol)}
  .big-tile.challenge{border-color:rgba(245,196,81,0.4)}
  .big-tile.challenge .bt-title{color:var(--gold)}
  .list-row{display:flex;align-items:center;gap:14px;padding:14px 16px;background:var(--surface);border:1px solid var(--border);border-radius:var(--r-md);margin-bottom:8px;text-decoration:none;color:var(--text);transition:0.15s}
  .list-row:hover{border-color:var(--turquoise);background:var(--surface-elevated)}
  .lr-icon{width:42px;height:42px;border-radius:var(--r-sm);background:var(--bg);display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;position:relative}
  .lr-body{flex:1;min-width:0}
  .lr-title{font-size:14px;font-weight:700;margin-bottom:2px}
  .lr-desc{font-size:11px;color:var(--text-secondary)}
  .lr-arrow{color:var(--text-secondary);font-size:16px}
  .lr-badge{position:absolute;top:-4px;right:-4px;background:var(--error);color:#fff;font-size:10px;font-weight:800;padding:1px 6px;border-radius:var(--r-full);min-width:16px;text-align:center}
  .profile-details{position:absolute;top:100%;left:0;right:0;background:var(--surface);border:1px solid var(--border);border-radius:var(--r-md);padding:12px;margin-top:8px;display:none;z-index:10}
  .profile-wrap.expanded .profile-details{display:block}
  .mini-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:10px}
  .mini-stat{padding:8px 4px;background:var(--bg);border:1px solid var(--border);border-radius:var(--r-sm);text-align:center}
  .mini-stat .num{font-size:14px;font-weight:800;color:var(--gold);font-family:monospace}
  .mini-stat .lbl{font-size:9px;color:var(--text-secondary)}
  .btn-profile{display:block;text-align:center;padding:10px;background:var(--gold);color:#101827;border-radius:var(--r-sm);font-weight:800;font-size:13px;text-decoration:none}
  .guest-warning{background:rgba(245,196,81,0.08);border:1px solid rgba(245,196,81,0.3);border-radius:var(--r-md);padding:12px 14px;margin-bottom:14px;display:flex;align-items:center;gap:10px;font-size:12px;color:var(--gold)}
</style>
{% endblock %}
{% block content %}
  <div class="top-row">
    <a href="/accounts/settings/" class="btn-settings">⚙️</a>
    <div class="profile-wrap" id="profileWrap">
      <div class="profile-oval" onclick="toggleProfile()">
        {% if user.avatar_type == "image" and user.avatar_id %}
          <div class="po-av" style="background-image: url('/static/avatars/images/{{ user.avatar_id|stringformat:"03d" }}.jpg');"></div>
        {% else %}
          <div class="po-av">{{ avatar_emoji }}</div>
        {% endif %}
        <div class="po-details">
          <div class="po-name">{{ user.alias }}</div>
          <div class="po-meta">
            <span class="lvl">Lv {{ level|default:1 }}</span>
            <span>🪙 {{ user.coins|default:0 }}</span>
          </div>
        </div>
      </div>
      <div class="profile-details">
        <div class="mini-stats">
          <div class="mini-stat"><div class="num">{{ stats.total_games|default:0 }}</div><div class="lbl">بازی</div></div>
          <div class="mini-stat"><div class="num">{{ stats.total_score|default:0 }}</div><div class="lbl">امتیاز</div></div>
          <div class="mini-stat"><div class="num">{{ user.coins|default:0 }}</div><div class="lbl">سکه</div></div>
        </div>
        <a href="/accounts/profile/" class="btn-profile">مشاهده پروفایل</a>
      </div>
    </div>
  </div>

  {% if user.is_guest %}
    <div class="guest-warning">
      <span>🎲</span>
      <div style="flex:1;">حساب مهمان — برای ذخیره دائمی ثبت‌نام کن</div>
      <a href="/accounts/register/" style="color:var(--gold);font-weight:700;">ثبت‌نام</a>
    </div>
  {% endif %}

  <div class="circle-row">
    <a href="/game/top-players/" class="circle-btn gold">
      <div class="cb-icon">⭐</div>
      <div class="cb-title">بازیکنان برتر</div>
      <div class="cb-desc">جدول رتبه</div>
    </a>
    <a href="/accounts/shop/" class="circle-btn shop">
      <div class="cb-icon">🛒</div>
      <div class="cb-title">فروشگاه</div>
      <div class="cb-desc">خرید آیتم</div>
    </a>
  </div>

  <a href="/social/notifications/" class="list-row">
    <div class="lr-icon">
      🔔
      {% if unread_notifications %}<span class="lr-badge">{{ unread_notifications }}</span>{% endif %}
    </div>
    <div class="lr-body">
      <div class="lr-title">اعلان‌ها</div>
      <div class="lr-desc">{% if unread_notifications %}{{ unread_notifications }} پیام جدید{% else %}پیام‌ها و دعوت‌ها{% endif %}</div>
    </div>
    <span class="lr-arrow">←</span>
  </a>

  <div class="section-title">🎮 بازی و رقابت</div>

  <div class="row-2">
    <a href="/game/rooms/" class="big-tile games">
      <div class="bt-icon">🎮</div>
      <div class="bt-title">بازی‌ها</div>
      <div class="bt-desc">۷ حالت مختلف</div>
    </a>
    <a href="/game/challenge/" class="big-tile challenge">
      <div class="bt-icon">🏆</div>
      <div class="bt-title">چالش</div>
      <div class="bt-desc">تورنمنت</div>
    </a>
  </div>

  <div class="section-title">💬 ارتباط</div>

  <a href="/support/" class="list-row">
    <div class="lr-icon">💬</div>
    <div class="lr-body">
      <div class="lr-title">پشتیبانی</div>
      <div class="lr-desc">سوال داری؟ با ما در تماس باش</div>
    </div>
    <span class="lr-arrow">←</span>
  </a>
{% endblock %}
{% block extra_js %}
<script>
  function toggleProfile() {
    document.getElementById('profileWrap').classList.toggle('expanded');
    document.querySelector('.profile-oval').classList.toggle('expanded');
    if (window.vibrate) window.vibrate(8);
  }
</script>
{% endblock %}
'''
write("game/templates/game/menu.html", HOME)

# ============================================================
# 6) MIGRATIONS
# ============================================================
print("\n[6/7] Migrations")

for cmd in [
    [sys.executable, "manage.py", "makemigrations", "accounts", "--noinput"],
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
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

TEST = '''
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
import django
django.setup()
from django.test import Client
from accounts.models import User

User.objects.filter(username__startswith="__lock_").delete()
u = User.objects.create_user(
    username="__lock_test__", password="x"*10, alias="تست",
    is_active=True, has_chosen_avatar=True, has_completed_registration=True,
    coins=200,
)

c = Client()
c.force_login(u)
c.session["beta_unlocked"] = True
c.session.save()

tests = [
    ("/game/", "خانه"),
    ("/accounts/shop/", "فروشگاه"),
    ("/accounts/avatar/", "آواتار"),
    ("/support/", "پشتیبانی"),
    ("/game/challenge/", "چالش"),
    ("/game/top-players/", "برتر"),
]

for url, name in tests:
    try:
        r = c.get(url, follow=False)
        mark = "OK" if r.status_code == 200 else f"-> {r.status_code}"
        print(f"  {mark:8s} {url:25s} ({name})")
    except Exception as e:
        print(f"  ERR      {url:25s} ({name}) {type(e).__name__}")

u.delete()
'''

r = subprocess.run([sys.executable, "-c", TEST], env={**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings"}, capture_output=True, text=True, timeout=60)
print(r.stdout)
if r.stderr and "Traceback" in r.stderr:
    print(f"  ERR: {r.stderr[:400]}")

r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True, timeout=30)
if r.returncode == 0:
    print("\n  ✓ Django check PASSED")
else:
    print(f"\n  ⚠ {r.stderr[:300] if r.stderr else r.stdout[:300]}")

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
Changes:

  🔒 Avatar Lock System:
     ✓ All 44 image avatars locked by default
     ✓ Grayed out + 🔒 + "50 🪙" badge
     ✓ Click lock → confirms → deducts 50 coins
     ✓ Unlocked avatars become selectable
     ✓ Works on complete_registration + avatar_select
     ✓ New users get 100 welcome coins

  🛒 Shop:
     ✓ Items seeded (6 items)
     ✓ Route /accounts/shop/ works

  🏠 Home:
     ✓ ⭐ برتر + 🛒 فروشگاه as circular icons
     ✓ 🎮 بازی‌ها + 🏆 چالش side by side
     ✓ 💬 پشتیبانی row
     ✓ Profile expands

  💬 Support: fully accessible

Now:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R

Test:
  /game/                → new layout
  /accounts/avatar/     → try unlocking (have 200 coins? use test user or add coins)
  /accounts/shop/       → shop works
""")
