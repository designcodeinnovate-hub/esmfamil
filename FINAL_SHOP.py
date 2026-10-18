#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Models
# ============================================================
print("\n[1/9] Adding ShopItem + Purchase models")
p = "accounts/models.py"
src = read(p)

if "from django.conf import settings" not in src:
    src = src.replace(
        "from django.db import models",
        "from django.conf import settings\nfrom django.db import models",
        1
    )

if "class ShopItem(models.Model):" in src:
    print("  SKIP: already exists")
else:
    src += '''

class ShopItem(models.Model):
    CATEGORY_CHOICES = [
        ("box", "جعبه شانس"),
        ("boost", "بوست"),
        ("theme", "تم"),
        ("bundle", "بسته ارز"),
        ("cosmetic", "آیتم ظاهری"),
    ]
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=8, default="🎁")
    category = models.CharField(max_length=12, choices=CATEGORY_CHOICES, default="cosmetic")
    price_coins = models.PositiveIntegerField(default=0)
    price_gems = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    reward_type = models.CharField(max_length=20, blank=True)
    reward_value = models.IntegerField(default=0)
    reward_min = models.IntegerField(default=0)
    reward_max = models.IntegerField(default=0)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sort_order", "-created_at")

    def __str__(self):
        return f"{self.icon} {self.name}"


class Purchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchases")
    item = models.ForeignKey(ShopItem, on_delete=models.SET_NULL, null=True, blank=True, related_name="purchases")
    item_name = models.CharField(max_length=60)
    item_icon = models.CharField(max_length=8, default="🎁")
    price_paid_coins = models.PositiveIntegerField(default=0)
    price_paid_gems = models.PositiveIntegerField(default=0)
    reward_given = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.alias} - {self.item_name}"
'''
    write(p, src)
    print("  + ShopItem + Purchase added")

# ============================================================
# 2) shop_views.py
# ============================================================
print("\n[2/9] Creating shop_views.py")
write("accounts/shop_views.py", '''# -*- coding: utf-8 -*-
import random
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import ShopItem, Purchase


@login_required
def shop_home(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    items = ShopItem.objects.filter(is_active=True)
    categories = {"box": [], "boost": [], "theme": [], "bundle": [], "cosmetic": []}
    for item in items:
        if item.category in categories:
            item.is_sold_out = (item.stock is not None and item.stock <= 0)
            categories[item.category].append(item)

    recent = Purchase.objects.filter(user=request.user)[:8]

    return render(request, "accounts/shop.html", {
        "categories": categories,
        "recent_purchases": recent,
        "active": "profile",
        "user_coins": request.user.coins or 0,
        "user_gems": request.user.gems or 0,
    })


@login_required
def shop_buy(request, item_id):
    if request.method != "POST":
        return redirect("accounts:shop")
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    item = get_object_or_404(ShopItem, id=item_id, is_active=True)

    if item.stock is not None and item.stock <= 0:
        messages.error(request, "این آیتم تمام شده.")
        return redirect("accounts:shop")
    if item.price_coins and (request.user.coins or 0) < item.price_coins:
        messages.error(request, f"سکه کافی نداری (نیاز: {item.price_coins}).")
        return redirect("accounts:shop")
    if item.price_gems and (request.user.gems or 0) < item.price_gems:
        messages.error(request, f"جم کافی نداری (نیاز: {item.price_gems}).")
        return redirect("accounts:shop")

    if item.price_coins: request.user.coins -= item.price_coins
    if item.price_gems: request.user.gems -= item.price_gems

    reward_text = ""
    if item.reward_type == "coins_fixed":
        request.user.coins += item.reward_value
        reward_text = f"+{item.reward_value} سکه"
    elif item.reward_type == "gems_fixed":
        request.user.gems += item.reward_value
        reward_text = f"+{item.reward_value} جم"
    elif item.reward_type == "coins_random":
        amount = random.randint(max(1, item.reward_min or 50), max(item.reward_min or 50, item.reward_max or 300))
        request.user.coins += amount
        reward_text = f"🎉 +{amount} سکه!"
    elif item.reward_type == "gems_random":
        amount = random.randint(max(1, item.reward_min or 1), max(item.reward_min or 1, item.reward_max or 15))
        request.user.gems += amount
        reward_text = f"🎉 +{amount} جم!"
    elif item.reward_type == "theme":
        reward_text = "🎨 تم فعال شد"
    elif item.reward_type == "boost":
        reward_text = "⚡ بوست فعال شد"

    request.user.save(update_fields=["coins", "gems"])

    if item.stock is not None:
        item.stock = max(0, item.stock - 1)
        item.save(update_fields=["stock"])

    Purchase.objects.create(
        user=request.user, item=item,
        item_name=item.name, item_icon=item.icon,
        price_paid_coins=item.price_coins,
        price_paid_gems=item.price_gems,
        reward_given=reward_text,
    )
    messages.success(request, f"{item.icon} {item.name} خریداری شد! {reward_text}")
    return redirect("accounts:shop")


@login_required
def shop_exchange(request):
    if request.method != "POST":
        return redirect("accounts:shop")
    try:
        amount = int(request.POST.get("amount") or 0)
        direction = request.POST.get("direction", "coins_to_gems")
    except (ValueError, TypeError):
        messages.error(request, "مقدار نامعتبر.")
        return redirect("accounts:shop")
    if amount <= 0:
        messages.error(request, "مقدار باید بیشتر از صفر باشد.")
        return redirect("accounts:shop")

    if direction == "coins_to_gems":
        needed = amount * 100
        if (request.user.coins or 0) < needed:
            messages.error(request, f"سکه کافی نداری (نیاز: {needed}).")
            return redirect("accounts:shop")
        request.user.coins -= needed
        request.user.gems += amount
        request.user.save(update_fields=["coins", "gems"])
        messages.success(request, f"تبدیل شد! -{needed} سکه → +{amount} جم")
    else:
        if (request.user.gems or 0) < amount:
            messages.error(request, f"جم کافی نداری (نیاز: {amount}).")
            return redirect("accounts:shop")
        reward = amount * 80
        request.user.gems -= amount
        request.user.coins += reward
        request.user.save(update_fields=["coins", "gems"])
        messages.success(request, f"تبدیل شد! -{amount} جم → +{reward} سکه")

    return redirect("accounts:shop")
''')

# ============================================================
# 3) urls.py
# ============================================================
print("\n[3/9] Updating accounts/urls.py")
p = "accounts/urls.py"
src = read(p)

if "from . import shop_views" not in src:
    src = src.replace(
        "from .views import (",
        "from . import shop_views\nfrom .views import (",
        1
    )

src = src.replace(
    'path("shop/", shop_view, name="shop"),',
    'path("shop/", shop_views.shop_home, name="shop"),\n    path("shop/buy/<int:item_id>/", shop_views.shop_buy, name="shop_buy"),\n    path("shop/exchange/", shop_views.shop_exchange, name="shop_exchange"),',
    1
)
write(p, src)
print("  ✓ shop routes added")

# ============================================================
# 4) shop.html (player)
# ============================================================
print("\n[4/9] Building player shop template")
SHOP_HTML = '''{% extends "base.html" %}
{% block title %}فروشگاه{% endblock %}

{% block extra_css %}
<style>
  .page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }
  .wallet-header { display: flex; gap: 10px; margin-bottom: 18px; }
  .wallet-card { flex: 1; padding: 16px 14px; border-radius: 18px; text-align: center; }
  .wallet-coins-bg { background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.35), transparent 60%), linear-gradient(135deg, #2a1a0e, #1a0f0a); border: 2px solid rgba(244,197,66,0.5); }
  .wallet-gems-bg { background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.4), transparent 60%), linear-gradient(135deg, #1a0f2e, #150a24); border: 2px solid rgba(139,92,246,0.5); }
  .wallet-icon { font-size: 32px; margin-bottom: 6px; }
  .wallet-amount { font-size: 22px; font-weight: 900; font-family: monospace; color: #fff; }
  .wallet-label { font-size: 11px; color: rgba(255,255,255,0.7); margin-top: 3px; }
  .flash { padding: 12px 16px; border-radius: 12px; margin-bottom: 14px; font-size: 13px; }
  .flash-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
  .flash-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }
  .exchange-box { background: linear-gradient(135deg, #0f0f1e, #1a1a2e); border: 1.5px solid rgba(6,182,212,0.4); border-radius: 18px; padding: 20px; margin-bottom: 20px; }
  .exchange-title { font-size: 15px; font-weight: bold; color: #22d3ee; margin-bottom: 14px; text-align: center; }
  .exchange-row { display: flex; gap: 10px; align-items: center; margin-bottom: 10px; }
  .exchange-row label { font-size: 12px; color: var(--muted); min-width: 60px; }
  .exchange-row input, .exchange-row select { flex: 1; padding: 10px 12px; border-radius: 10px; border: 1.5px solid var(--border); background: var(--bg); color: #fff; font-size: 14px; font-family: monospace; }
  .exchange-btn { width: 100%; padding: 12px; border: none; border-radius: 12px; background: linear-gradient(135deg, #06b6d4, #3b82f6); color: #fff; font-family: inherit; font-weight: bold; font-size: 14px; cursor: pointer; margin-top: 6px; }
  .exchange-rate { font-size: 11px; color: var(--muted); text-align: center; margin-top: 8px; }
  .cat-header { display: flex; align-items: center; gap: 10px; margin: 22px 0 12px; }
  .cat-header .icon { font-size: 24px; }
  .cat-header h2 { font-size: 17px; font-weight: bold; color: #fff; }
  .cat-header .count { font-size: 11px; padding: 2px 8px; border-radius: 8px; background: rgba(148,163,184,0.2); color: var(--muted); font-family: monospace; }
  .items-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
  .item-card { background: var(--card); border: 1.5px solid var(--border); border-radius: 16px; padding: 14px 10px; text-align: center; transition: 0.2s; position: relative; overflow: hidden; }
  .item-card:hover { transform: translateY(-2px); border-color: var(--gold); }
  .item-card.box { border-color: rgba(139,92,246,0.4); }
  .item-card.box:hover { border-color: var(--purple); box-shadow: 0 8px 25px rgba(139,92,246,0.25); }
  .item-card.box::before { content: ""; position: absolute; inset: -50%; background: conic-gradient(from 0deg, transparent, rgba(139,92,246,0.15), transparent, rgba(6,182,212,0.15), transparent); animation: spin 8s linear infinite; z-index: 0; pointer-events: none; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .item-card > * { position: relative; z-index: 1; }
  .item-icon { font-size: 42px; margin-bottom: 8px; display: block; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.4)); }
  .item-name { font-size: 13px; font-weight: bold; color: #fff; margin-bottom: 4px; line-height: 1.4; min-height: 36px; }
  .item-desc { font-size: 10px; color: var(--muted); margin-bottom: 10px; line-height: 1.5; min-height: 28px; }
  .item-price { display: inline-flex; align-items: center; gap: 4px; padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: bold; font-family: monospace; margin-bottom: 8px; }
  .item-price.coins { background: rgba(244,197,66,0.15); color: #fde68a; border: 1px solid rgba(244,197,66,0.3); }
  .item-price.gems { background: rgba(139,92,246,0.15); color: #c4b5fd; border: 1px solid rgba(139,92,246,0.3); }
  .item-price.free { background: rgba(34,197,94,0.15); color: #86efac; border: 1px solid rgba(34,197,94,0.3); }
  .item-buy-btn { width: 100%; padding: 9px; border: none; border-radius: 10px; background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; font-family: inherit; font-weight: bold; font-size: 12px; cursor: pointer; transition: 0.2s; }
  .item-buy-btn:hover { transform: scale(1.03); }
  .item-buy-btn:disabled { background: rgba(100,116,139,0.3); color: #94a3b8; cursor: not-allowed; transform: none; }
  .item-buy-btn.gem-buy { background: linear-gradient(135deg, #8b5cf6, #6b4eff); }
  .item-sold-out { position: absolute; top: 8px; left: 8px; background: rgba(239,68,68,0.9); color: #fff; padding: 2px 8px; border-radius: 6px; font-size: 9px; font-weight: bold; z-index: 2; }
  .purchase-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: var(--card); border: 1px solid var(--border); border-radius: 12px; margin-bottom: 6px; }
  .purchase-item .pi-icon { font-size: 22px; }
  .purchase-item .pi-body { flex: 1; }
  .purchase-item .pi-name { font-size: 13px; font-weight: bold; color: #fff; }
  .purchase-item .pi-meta { font-size: 10px; color: var(--muted); margin-top: 2px; }
</style>
{% endblock %}

{% block content %}
  <div class="page-head">
    <a href="/game/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>🛒 <span>فروشگاه</span></h1>
  </div>

  <div class="wallet-header">
    <div class="wallet-card wallet-coins-bg">
      <div class="wallet-icon">🪙</div>
      <div class="wallet-amount">{{ user_coins }}</div>
      <div class="wallet-label">سکه</div>
    </div>
    <div class="wallet-card wallet-gems-bg">
      <div class="wallet-icon">💎</div>
      <div class="wallet-amount">{{ user_gems }}</div>
      <div class="wallet-label">جم</div>
    </div>
  </div>

  {% if messages %}
    {% for m in messages %}<div class="flash flash-{{ m.tags }}">{{ m }}</div>{% endfor %}
  {% endif %}

  <div class="exchange-box">
    <div class="exchange-title">💱 تبدیل ارز</div>
    <form method="post" action="/accounts/shop/exchange/">
      {% csrf_token %}
      <div class="exchange-row">
        <label>جهت:</label>
        <select name="direction">
          <option value="coins_to_gems">🪙 سکه → 💎 جم</option>
          <option value="gems_to_coins">💎 جم → 🪙 سکه</option>
        </select>
      </div>
      <div class="exchange-row">
        <label>مقدار:</label>
        <input type="number" name="amount" min="1" required placeholder="10">
      </div>
      <button type="submit" class="exchange-btn">تبدیل کن</button>
      <div class="exchange-rate">۱۰۰۰ سکه = ۱۰ جم · ۱۰ جم = ۸۰۰ سکه</div>
    </form>
  </div>

  {% if categories.box %}
  <div class="cat-header"><span class="icon">🎁</span><h2>جعبه‌های شانس</h2><span class="count">{{ categories.box|length }}</span></div>
  <div class="items-grid">
    {% for item in categories.box %}
    <div class="item-card box">
      {% if item.is_sold_out %}<span class="item-sold-out">تمام شد</span>{% endif %}
      <span class="item-icon">{{ item.icon }}</span>
      <div class="item-name">{{ item.name }}</div>
      <div class="item-desc">{{ item.description }}</div>
      {% if item.price_coins %}<div class="item-price coins">🪙 {{ item.price_coins }}</div>
      {% elif item.price_gems %}<div class="item-price gems">💎 {{ item.price_gems }}</div>
      {% else %}<div class="item-price free">رایگان</div>{% endif %}
      <form method="post" action="/accounts/shop/buy/{{ item.id }}/">
        {% csrf_token %}
        {% if item.is_sold_out %}<button type="button" class="item-buy-btn" disabled>تمام شد</button>
        {% else %}<button type="submit" class="item-buy-btn {% if item.price_gems and not item.price_coins %}gem-buy{% endif %}">خرید</button>{% endif %}
      </form>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if categories.bundle %}
  <div class="cat-header"><span class="icon">💰</span><h2>بسته‌های ارز</h2><span class="count">{{ categories.bundle|length }}</span></div>
  <div class="items-grid">
    {% for item in categories.bundle %}
    <div class="item-card">
      {% if item.is_sold_out %}<span class="item-sold-out">تمام شد</span>{% endif %}
      <span class="item-icon">{{ item.icon }}</span>
      <div class="item-name">{{ item.name }}</div>
      <div class="item-desc">{{ item.description }}</div>
      {% if item.price_coins %}<div class="item-price coins">🪙 {{ item.price_coins }}</div>
      {% elif item.price_gems %}<div class="item-price gems">💎 {{ item.price_gems }}</div>
      {% else %}<div class="item-price free">رایگان</div>{% endif %}
      <form method="post" action="/accounts/shop/buy/{{ item.id }}/">
        {% csrf_token %}
        {% if item.is_sold_out %}<button type="button" class="item-buy-btn" disabled>تمام شد</button>
        {% else %}<button type="submit" class="item-buy-btn {% if item.price_gems and not item.price_coins %}gem-buy{% endif %}">خرید</button>{% endif %}
      </form>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if categories.boost %}
  <div class="cat-header"><span class="icon">⚡</span><h2>بوست‌ها</h2><span class="count">{{ categories.boost|length }}</span></div>
  <div class="items-grid">
    {% for item in categories.boost %}
    <div class="item-card">
      <span class="item-icon">{{ item.icon }}</span>
      <div class="item-name">{{ item.name }}</div>
      <div class="item-desc">{{ item.description }}</div>
      {% if item.price_coins %}<div class="item-price coins">🪙 {{ item.price_coins }}</div>
      {% elif item.price_gems %}<div class="item-price gems">💎 {{ item.price_gems }}</div>
      {% else %}<div class="item-price free">رایگان</div>{% endif %}
      <form method="post" action="/accounts/shop/buy/{{ item.id }}/">
        {% csrf_token %}
        <button type="submit" class="item-buy-btn {% if item.price_gems and not item.price_coins %}gem-buy{% endif %}">خرید</button>
      </form>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if categories.theme %}
  <div class="cat-header"><span class="icon">🎨</span><h2>تم‌ها</h2><span class="count">{{ categories.theme|length }}</span></div>
  <div class="items-grid">
    {% for item in categories.theme %}
    <div class="item-card">
      <span class="item-icon">{{ item.icon }}</span>
      <div class="item-name">{{ item.name }}</div>
      <div class="item-desc">{{ item.description }}</div>
      {% if item.price_gems %}<div class="item-price gems">💎 {{ item.price_gems }}</div>
      {% else %}<div class="item-price coins">🪙 {{ item.price_coins }}</div>{% endif %}
      <form method="post" action="/accounts/shop/buy/{{ item.id }}/">
        {% csrf_token %}
        <button type="submit" class="item-buy-btn gem-buy">خرید</button>
      </form>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if recent_purchases %}
  <div class="cat-header"><span class="icon">📜</span><h2>خریدهای اخیر</h2></div>
  {% for p in recent_purchases %}
  <div class="purchase-item">
    <div class="pi-icon">{{ p.item_icon }}</div>
    <div class="pi-body">
      <div class="pi-name">{{ p.item_name }}</div>
      <div class="pi-meta">
        {% if p.price_paid_coins %}{{ p.price_paid_coins }} سکه{% endif %}
        {% if p.price_paid_gems %} {{ p.price_paid_gems }} جم{% endif %}
        · {{ p.created_at|date:"Y/m/d H:i" }}
      </div>
    </div>
    {% if p.reward_given %}<div style="font-size:11px; color:#86efac; font-weight:bold;">{{ p.reward_given }}</div>{% endif %}
  </div>
  {% endfor %}
  {% endif %}
{% endblock %}
'''
write("accounts/templates/accounts/shop.html", SHOP_HTML)

# ============================================================
# 5) menu.html - wallet chips
# ============================================================
print("\n[5/9] Adding wallet chips to menu.html")
p = "game/templates/game/menu.html"
src = read(p)

if "wallet-chip" not in src:
    old = '<a href="/accounts/settings/" class="settings-icon" title="تنظیمات">⚙️</a>'
    new = '''<div style="display:flex; gap:8px; align-items:center;">
      <a href="/accounts/shop/" class="wallet-chip wallet-coins" title="فروشگاه">
        <span class="wc-icon">🪙</span><span class="wc-num">{{ user.coins|default:0 }}</span>
      </a>
      <a href="/accounts/shop/" class="wallet-chip wallet-gems" title="فروشگاه">
        <span class="wc-icon">💎</span><span class="wc-num">{{ user.gems|default:0 }}</span>
      </a>
      <a href="/accounts/settings/" class="settings-icon" title="تنظیمات">⚙️</a>
    </div>'''
    if old in src:
        src = src.replace(old, new, 1)
        # Add CSS
        style_end = src.find("</style>")
        if style_end > 0:
            css = '''
  .wallet-chip { display: inline-flex; align-items: center; gap: 5px; padding: 6px 12px; border-radius: 12px; text-decoration: none; font-size: 12px; font-weight: bold; font-family: monospace; transition: 0.2s; }
  .wallet-coins { background: linear-gradient(135deg, rgba(244,197,66,0.2), rgba(234,179,8,0.1)); border: 1.5px solid rgba(244,197,66,0.5); color: #fde68a; }
  .wallet-gems { background: linear-gradient(135deg, rgba(139,92,246,0.2), rgba(6,182,212,0.1)); border: 1.5px solid rgba(139,92,246,0.5); color: #c4b5fd; }
  .wallet-chip:hover { transform: scale(1.05); }
  .wallet-chip .wc-icon { font-size: 14px; }
  .wallet-chip .wc-num { color: #fff; font-size: 13px; font-weight: 900; }
'''
            src = src[:style_end] + css + src[style_end:]
        write(p, src)
        print("  ✓ wallet chips added")
    else:
        print("  ⚠ settings-icon not found")
else:
    print("  SKIP: already has wallet-chip")

# ============================================================
# 6) admin_views.py - shop admin
# ============================================================
print("\n[6/9] Adding shop management to admin_views.py")
p = "accounts/admin_views.py"
src = read(p)

if "def shop_items_list" in src:
    print("  SKIP: already exists")
else:
    src += '''

# ============================================================
# Admin — Shop Items
# ============================================================
@never_cache
def shop_items_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    from accounts.models import ShopItem
    items = ShopItem.objects.all().order_by("-created_at")
    message = request.session.pop("admin_message", None)
    return render(request, "custom_admin/shop_items.html", {"items": items, "message": message})


@never_cache
def shop_item_create(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:shop_items_list")
    from accounts.models import ShopItem
    try:
        item = ShopItem(
            name=(request.POST.get("name") or "").strip()[:60],
            description=(request.POST.get("description") or "").strip()[:200],
            icon=(request.POST.get("icon") or "🎁").strip()[:8],
            category=request.POST.get("category", "cosmetic"),
            price_coins=int(request.POST.get("price_coins") or 0),
            price_gems=int(request.POST.get("price_gems") or 0),
            reward_type=(request.POST.get("reward_type") or "").strip()[:20],
            reward_value=int(request.POST.get("reward_value") or 0),
            reward_min=int(request.POST.get("reward_min") or 0),
            reward_max=int(request.POST.get("reward_max") or 0),
            sort_order=int(request.POST.get("sort_order") or 0),
        )
        stock = (request.POST.get("stock") or "").strip()
        if stock:
            item.stock = int(stock)
        item.save()
        request.session["admin_message"] = {"type": "success", "text": f"آیتم {item.name} ساخته شد."}
    except (ValueError, TypeError) as e:
        request.session["admin_message"] = {"type": "error", "text": f"خطا: {e}"}
    return redirect("custom_admin:shop_items_list")


@never_cache
def shop_item_toggle(request, item_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:shop_items_list")
    from accounts.models import ShopItem
    try:
        item = ShopItem.objects.get(id=item_id)
        item.is_active = not item.is_active
        item.save(update_fields=["is_active"])
        request.session["admin_message"] = {"type": "success", "text": f"وضعیت {item.name} تغییر کرد."}
    except ShopItem.DoesNotExist:
        pass
    return redirect("custom_admin:shop_items_list")


@never_cache
def shop_item_delete(request, item_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:shop_items_list")
    from accounts.models import ShopItem
    try:
        ShopItem.objects.get(id=item_id).delete()
        request.session["admin_message"] = {"type": "success", "text": "آیتم حذف شد."}
    except ShopItem.DoesNotExist:
        pass
    return redirect("custom_admin:shop_items_list")
'''
    write(p, src)
    print("  ✓ shop admin views added")

# ============================================================
# 7) admin_urls.py - shop routes
# ============================================================
print("\n[7/9] Adding shop routes to admin_urls.py")
p = "accounts/admin_urls.py"
src = read(p)

if "shop_items_list" not in src:
    old = '    path("tournament/<int:tournament_id>/clear-entries/", admin_views.tournament_clear_entries, name="tournament_clear_entries"),'
    new = old + '''
    path("shop/", admin_views.shop_items_list, name="shop_items_list"),
    path("shop/create/", admin_views.shop_item_create, name="shop_item_create"),
    path("shop/<int:item_id>/toggle/", admin_views.shop_item_toggle, name="shop_item_toggle"),
    path("shop/<int:item_id>/delete/", admin_views.shop_item_delete, name="shop_item_delete"),'''
    if old in src:
        src = src.replace(old, new, 1)
    else:
        # Fallback: add before closing ]
        src = src.rsplit("]", 1)[0] + '    path("shop/", admin_views.shop_items_list, name="shop_items_list"),\n    path("shop/create/", admin_views.shop_item_create, name="shop_item_create"),\n    path("shop/<int:item_id>/toggle/", admin_views.shop_item_toggle, name="shop_item_toggle"),\n    path("shop/<int:item_id>/delete/", admin_views.shop_item_delete, name="shop_item_delete"),\n]'
    write(p, src)
    print("  ✓ routes added")
else:
    print("  SKIP: already has shop routes")

# ============================================================
# 8) custom_admin/shop_items.html + dashboard tab
# ============================================================
print("\n[8/9] Building admin shop page")
ADMIN_SHOP = '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>فروشگاه — پنل ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 1300px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; }
    .topbar h1 { font-size: 20px; color: #fca5a5; }
    .topbar a { padding: 9px 16px; border-radius: 10px; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold; }
    .admin-tabs { display: flex; gap: 6px; margin-bottom: 20px; background: #12121f; border: 1px solid rgba(148,163,184,0.15); padding: 6px; border-radius: 14px; overflow-x: auto; }
    .admin-tab { flex: 1; min-width: 90px; padding: 12px 14px; border-radius: 10px; text-align: center; text-decoration: none; font-size: 12px; font-weight: bold; color: #94a3b8; transition: 0.2s; white-space: nowrap; }
    .admin-tab:hover { background: rgba(148,163,184,0.1); color: #fff; }
    .admin-tab.active { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; box-shadow: 0 6px 20px rgba(239,68,68,0.4); }
    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }
    .card { background: #12121f; border: 1px solid rgba(148,163,184,0.15); border-radius: 16px; padding: 20px; margin-bottom: 16px; }
    .card h3 { color: #fdba74; font-size: 15px; margin-bottom: 14px; }
    details summary { cursor: pointer; font-size: 14px; font-weight: bold; color: #22c55e; padding: 10px; border-radius: 10px; background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.25); }
    details[open] summary { margin-bottom: 14px; }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
    @media (max-width: 600px) { .form-grid { grid-template-columns: 1fr; } }
    label { display: block; color: #94a3b8; font-size: 12px; margin-bottom: 4px; font-weight: bold; }
    input, select, textarea { width: 100%; padding: 10px 12px; border-radius: 10px; border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15; color: #fff; font-size: 13px; font-family: inherit; }
    button.submit { padding: 12px 24px; border: none; border-radius: 10px; background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; font-family: inherit; font-weight: bold; font-size: 14px; cursor: pointer; }
    .item-row { display: flex; align-items: center; gap: 12px; padding: 12px; background: rgba(15,23,42,0.6); border: 1px solid rgba(148,163,184,0.1); border-radius: 12px; margin-bottom: 8px; }
    .item-row.inactive { opacity: 0.5; }
    .item-row .em { font-size: 26px; width: 42px; height: 42px; border-radius: 10px; background: rgba(139,92,246,0.15); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .item-row .info { flex: 1; min-width: 0; }
    .item-row .nm { font-size: 14px; font-weight: bold; color: #fff; }
    .item-row .mt { font-size: 11px; color: #64748b; margin-top: 2px; }
    .item-row .price { font-family: monospace; font-size: 12px; color: #facc15; margin: 0 8px; }
    .btn-t { padding: 6px 12px; border: none; border-radius: 8px; font-family: inherit; font-size: 11px; font-weight: bold; cursor: pointer; }
    .btn-toggle-on { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .btn-toggle-off { background: rgba(100,116,139,0.15); color: #94a3b8; border: 1px solid rgba(100,116,139,0.3); }
    .btn-del { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
    .empty { text-align: center; padding: 40px; color: #64748b; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>🛒 مدیریت فروشگاه</h1>
    <a href="{% url 'custom_admin:logout' %}">خروج</a>
  </div>

  <div class="admin-tabs">
    <a href="/panel-admin/dashboard/" class="admin-tab">👥 کاربران</a>
    <a href="/panel-admin/alliances/" class="admin-tab">🛡️ اتحادها</a>
    <a href="/panel-admin/rooms/" class="admin-tab">🚪 اتاق‌ها</a>
    <a href="/panel-admin/rooms/active/" class="admin-tab">🎮 در حال بازی</a>
    <a href="/panel-admin/announcements/" class="admin-tab">📢 اعلان‌ها</a>
    <a href="/panel-admin/tournaments/" class="admin-tab">🏆 تورنمنت‌ها</a>
    <a href="/panel-admin/shop/" class="admin-tab active">🛒 فروشگاه</a>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <div class="card">
    <details>
      <summary>+ افزودن آیتم جدید</summary>
      <form method="post" action="/panel-admin/shop/create/">
        {% csrf_token %}
        <div class="form-grid">
          <div><label>نام</label><input type="text" name="name" required maxlength="60"></div>
          <div><label>ایموجی</label><input type="text" name="icon" value="🎁" maxlength="8"></div>
        </div>
        <div><label>توضیح</label><input type="text" name="description" maxlength="200"></div>
        <div class="form-grid" style="margin-top: 10px;">
          <div><label>دسته</label>
            <select name="category">
              <option value="box">جعبه شانس</option>
              <option value="bundle">بسته ارز</option>
              <option value="boost">بوست</option>
              <option value="theme">تم</option>
              <option value="cosmetic">ظاهری</option>
            </select>
          </div>
          <div><label>نوع جایزه</label>
            <select name="reward_type">
              <option value="">بدون جایزه</option>
              <option value="coins_fixed">سکه ثابت</option>
              <option value="gems_fixed">جم ثابت</option>
              <option value="coins_random">سکه شانسی</option>
              <option value="gems_random">جم شانسی</option>
              <option value="theme">فعال‌سازی تم</option>
              <option value="boost">فعال‌سازی بوست</option>
            </select>
          </div>
        </div>
        <div class="form-grid" style="margin-top: 10px;">
          <div><label>قیمت (سکه)</label><input type="number" name="price_coins" value="0" min="0"></div>
          <div><label>قیمت (جم)</label><input type="number" name="price_gems" value="0" min="0"></div>
        </div>
        <div class="form-grid" style="margin-top: 10px;">
          <div><label>مقدار جایزه ثابت</label><input type="number" name="reward_value" value="0"></div>
          <div><label>حداقل شانسی</label><input type="number" name="reward_min" value="0"></div>
        </div>
        <div class="form-grid" style="margin-top: 10px;">
          <div><label>حداکثر شانسی</label><input type="number" name="reward_max" value="0"></div>
          <div><label>موجودی (خالی = نامحدود)</label><input type="number" name="stock" min="0"></div>
        </div>
        <div style="margin-top: 14px;"><button type="submit" class="submit">💾 ساخت آیتم</button></div>
      </form>
    </details>
  </div>

  <div class="card">
    <h3>📦 آیتم‌ها ({{ items|length }})</h3>
    {% for item in items %}
      <div class="item-row {% if not item.is_active %}inactive{% endif %}">
        <div class="em">{{ item.icon }}</div>
        <div class="info">
          <div class="nm">{{ item.name }}</div>
          <div class="mt">{{ item.get_category_display }} · {{ item.reward_type|default:"بدون جایزه" }} · موجودی: {{ item.stock|default:"∞" }}</div>
        </div>
        <span class="price">{% if item.price_coins %}🪙{{ item.price_coins }}{% endif %}{% if item.price_gems %} 💎{{ item.price_gems }}{% endif %}</span>
        <form method="post" action="/panel-admin/shop/{{ item.id }}/toggle/" style="display:inline;">
          {% csrf_token %}
          <button type="submit" class="btn-t {% if item.is_active %}btn-toggle-on{% else %}btn-toggle-off{% endif %}">{% if item.is_active %}فعال{% else %}غیرفعال{% endif %}</button>
        </form>
        <form method="post" action="/panel-admin/shop/{{ item.id }}/delete/" style="display:inline;" onsubmit="return confirm('حذف {{ item.name }}؟');">
          {% csrf_token %}
          <button type="submit" class="btn-t btn-del">حذف</button>
        </form>
      </div>
    {% empty %}
      <div class="empty">هنوز آیتمی ساخته نشده.</div>
    {% endfor %}
  </div>
</div>
</body>
</html>
'''
write("accounts/templates/custom_admin/shop_items.html", ADMIN_SHOP)

# Add shop tab to dashboard.html
p = "accounts/templates/custom_admin/dashboard.html"
src = read(p)
if "/panel-admin/shop/" not in src:
    import re
    m = re.search(r'(<a href="/panel-admin/tournaments/"[^>]*>[^<]*تورنمنت[^<]*</a>)', src)
    if m:
        old_tab = m.group(1)
        new_tab = old_tab + '\n    <a href="/panel-admin/shop/" class="admin-tab {% if \'/panel-admin/shop/\' in request.path %}active{% endif %}">🛒 فروشگاه</a>'
        src = src.replace(old_tab, new_tab, 1)
        write(p, src)
        print("  ✓ shop tab added to dashboard")
    else:
        print("  ⚠ tournaments tab not found in dashboard")
else:
    print("  SKIP: shop tab already in dashboard")

# ============================================================
# 9) Migrations + seed + verify
# ============================================================
print("\n[9/9] Migrations + seed + verify")
for cmd in [
    [sys.executable, "manage.py", "makemigrations", "accounts", "--noinput"],
    [sys.executable, "manage.py", "migrate", "--noinput"],
]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd[1:])}")
    if r.stdout.strip(): print("   ", r.stdout.strip().replace("\n", "\n    ")[:400])
    if r.returncode != 0 and r.stderr.strip():
        print("   ERR:", r.stderr.strip()[:300])

# Seed items
print("\n[Seed] Adding default shop items")
SEED_CODE = '''
from accounts.models import ShopItem
DEFAULT_ITEMS = [
    {"name": "جعبه شانس کوچک", "icon": "🎁", "category": "box", "price_coins": 100, "reward_type": "coins_random", "reward_min": 50, "reward_max": 300, "description": "شانس! بین ۵۰ تا ۳۰۰ سکه"},
    {"name": "جعبه شانس بزرگ", "icon": "💎", "category": "box", "price_gems": 10, "reward_type": "gems_random", "reward_min": 3, "reward_max": 20, "description": "بین ۳ تا ۲۰ جم شانسی"},
    {"name": "بسته ۵۰۰ سکه", "icon": "💰", "category": "bundle", "price_gems": 10, "reward_type": "coins_fixed", "reward_value": 500, "description": "۵۰۰ سکه در ازای ۱۰ جم"},
    {"name": "بسته ۲۰۰۰ سکه", "icon": "💰", "category": "bundle", "price_gems": 35, "reward_type": "coins_fixed", "reward_value": 2000, "description": "۲۰۰۰ سکه در ازای ۳۵ جم"},
    {"name": "بسته ۵۰۰۰ سکه", "icon": "💰", "category": "bundle", "price_gems": 75, "reward_type": "coins_fixed", "reward_value": 5000, "description": "۵۰۰۰ سکه در ازای ۷۵ جم"},
    {"name": "تم طلایی", "icon": "🎨", "category": "theme", "price_gems": 50, "reward_type": "theme", "description": "رنگ طلایی ویژه"},
    {"name": "تم بنفش", "icon": "🎨", "category": "theme", "price_gems": 50, "reward_type": "theme", "description": "رنگ بنفش جادویی"},
    {"name": "تم فیروزه‌ای", "icon": "🎨", "category": "theme", "price_gems": 50, "reward_type": "theme", "description": "رنگ فیروزه‌ای"},
    {"name": "بوست ۲ برابر", "icon": "⚡", "category": "boost", "price_coins": 200, "reward_type": "boost", "description": "امتیاز دوبرابر در بازی بعدی"},
    {"name": "بوست ویژه", "icon": "🔥", "category": "boost", "price_gems": 20, "reward_type": "boost", "description": "وقت اضافه در بازی بعدی"},
]
for i, data in enumerate(DEFAULT_ITEMS):
    item, created = ShopItem.objects.get_or_create(
        name=data["name"],
        defaults={**data, "sort_order": i, "is_active": True}
    )
    if created:
        print(f"  + {data['icon']} {data['name']}")
'''
r = subprocess.run([sys.executable, "manage.py", "shell", "-c", SEED_CODE], capture_output=True, text=True)
if r.stdout.strip(): print(r.stdout.strip())
if r.returncode != 0 and r.stderr.strip(): print("  ERR:", r.stderr.strip()[:400])

# Final check
print("\n[check] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print("  ⚠ errors:")
    print(r.stderr[:1000] if r.stderr else r.stdout[:1000])

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
What was added:
  ✓ ShopItem + Purchase models
  ✓ 5 categories: boxes, bundles, boosts, themes, cosmetics
  ✓ Currency exchange (1000 coins ↔ 10 gems)
  ✓ Lucky boxes with random rewards
  ✓ Purchase history
  ✓ Wallet chips in menu top bar (🪙/💎)
  ✓ Full shop page at /accounts/shop/
  ✓ Admin: /panel-admin/shop/ with create/toggle/delete
  ✓ 10 default items seeded

Next:
  python manage.py runserver
  Hard refresh (Ctrl+Shift+R)
  
Test:
  /accounts/shop/ → buy a lucky box
  /panel-admin/shop/ → manage items
  /game/ → see wallet chips in top bar
""")
