#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

print("\n[1/3] Rebuilding menu.html — square + circles")

write("game/templates/game/menu.html", '''{% extends "base.html" %}
{% block title %}خانه{% endblock %}

{% block extra_css %}
<style>
  /* ===== Top row: two circles ===== */
  .top-circles {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 18px;
    gap: 12px;
    padding: 4px 2px;
  }
  
  .circle-btn {
    width: 78px;
    height: 78px;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1px;
    text-decoration: none;
    color: #fff;
    border: 2.5px solid;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    font-family: inherit;
    padding: 0;
    flex-shrink: 0;
  }
  .circle-btn::before {
    content: "";
    position: absolute;
    inset: -100%;
    z-index: 0;
    animation: spin 10s linear infinite;
    opacity: 0.5;
  }
  .circle-btn > * { position: relative; z-index: 1; }
  @keyframes spin { to { transform: rotate(360deg); } }
  
  .circle-btn:hover {
    transform: translateY(-3px) scale(1.08);
  }
  .circle-btn:active { transform: scale(0.95); }
  
  /* ===== Top players circle (gold) ===== */
  .circle-top {
    border-color: #f4c542;
    background: radial-gradient(circle at 30% 30%, rgba(244,197,66,0.35), rgba(234,179,8,0.15));
    box-shadow: 0 0 25px rgba(244,197,66,0.4);
  }
  .circle-top::before {
    background: conic-gradient(from 0deg, transparent, rgba(244,197,66,0.4), transparent, rgba(249,115,22,0.3), transparent);
  }
  .circle-top:hover {
    box-shadow: 0 0 45px rgba(244,197,66,0.8);
    border-color: #fde68a;
  }
  .circle-top .icon {
    font-size: 32px;
    line-height: 1;
    filter: drop-shadow(0 0 10px rgba(244,197,66,0.9));
  }
  .circle-top .label {
    font-size: 10px;
    font-weight: 900;
    color: #fde68a;
    letter-spacing: 0.5px;
    text-shadow: 0 0 10px rgba(244,197,66,0.8);
  }
  
  /* ===== Profile circle (purple) ===== */
  .circle-profile {
    border-color: rgba(139,92,246,0.75);
    background: radial-gradient(circle at 30% 30%, rgba(139,92,246,0.35), rgba(6,182,212,0.15));
    box-shadow: 0 0 25px rgba(139,92,246,0.4);
  }
  .circle-profile::before {
    background: conic-gradient(from 0deg, transparent, rgba(167,139,250,0.4), transparent, rgba(6,182,212,0.3), transparent);
  }
  .circle-profile:hover {
    box-shadow: 0 0 45px rgba(139,92,246,0.8);
    border-color: rgba(196,181,253,0.95);
  }
  .circle-profile.active {
    box-shadow: 0 0 45px rgba(139,92,246,0.9);
    border-color: rgba(196,181,253,0.95);
  }
  .circle-profile .avatar-in-circle {
    width: 54px;
    height: 54px;
    border-radius: 50%;
    background: rgba(15,23,42,0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    overflow: hidden;
    background-size: cover;
    background-position: center;
    border: 1.5px solid rgba(255,255,255,0.15);
  }
  .circle-profile .label {
    font-size: 9px;
    font-weight: 900;
    color: #c4b5fd;
    margin-top: 1px;
    text-shadow: 0 0 8px rgba(139,92,246,0.8);
  }
  
  /* ============================================================
     Profile expand card
     ============================================================ */
  .profile-expand-card {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.5s cubic-bezier(0.4, 0, 0.2, 1),
                margin-bottom 0.4s,
                opacity 0.3s;
    opacity: 0;
  }
  .profile-expand-card.expanded {
    max-height: 600px;
    margin-bottom: 16px;
    opacity: 1;
  }
  .profile-inner {
    padding: 20px;
    background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.25), transparent 55%),
                radial-gradient(circle at 0% 100%, rgba(139,92,246,0.2), transparent 55%),
                linear-gradient(135deg, var(--card), #0f0f1e);
    border: 1.5px solid rgba(244,197,66,0.5);
    border-radius: 24px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 15px 40px rgba(244,197,66,0.2);
  }
  .profile-inner::before {
    content: "";
    position: absolute;
    top: -50%; right: -50%;
    width: 200%; height: 200%;
    background: conic-gradient(from 0deg, transparent, rgba(244,197,66,0.1), transparent, rgba(139,92,246,0.1), transparent);
    animation: spin 12s linear infinite;
  }
  .profile-inner > * { position: relative; z-index: 1; }
  
  .profile-head-row {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 16px;
  }
  .profile-avatar-big {
    width: 80px; height: 80px;
    border-radius: 50%;
    border: 3px solid #f4c542;
    background: linear-gradient(135deg, #2a2a4a, #1a1a2e);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 42px;
    box-shadow: 0 0 35px rgba(244,197,66,0.7);
    overflow: hidden;
    background-size: cover;
    background-position: center;
    flex-shrink: 0;
    animation: avatarPulse 2.5s ease-in-out infinite;
  }
  @keyframes avatarPulse {
    0%,100% { box-shadow: 0 0 35px rgba(244,197,66,0.7); }
    50% { box-shadow: 0 0 55px rgba(244,197,66,0.95), 0 0 20px rgba(139,92,246,0.4); }
  }
  .profile-name-big {
    font-size: 22px;
    font-weight: 900;
    background: linear-gradient(135deg, #fde68a, #f4c542, #fdba74);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 4px;
    line-height: 1.2;
  }
  .profile-username-mini {
    font-size: 11px;
    color: #64748b;
    font-family: monospace;
    margin-bottom: 6px;
  }
  .profile-lvl-badge {
    display: inline-block;
    background: linear-gradient(135deg, #8b5cf6, #6b4eff);
    color: #fff;
    font-size: 11px;
    font-weight: 900;
    padding: 3px 12px;
    border-radius: 8px;
    font-family: monospace;
    box-shadow: 0 3px 10px rgba(139,92,246,0.5);
  }
  
  .level-bar-wrap { margin-bottom: 16px; }
  .level-info {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    margin-bottom: 6px;
  }
  .level-info .lbl { color: var(--muted); }
  .level-info .val { color: var(--gold); font-family: monospace; font-weight: 900; }
  .level-bar {
    height: 10px;
    background: rgba(148,163,184,0.15);
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.05);
  }
  .level-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #8b5cf6, #f4c542);
    border-radius: 10px;
    box-shadow: 0 0 12px rgba(139,92,246,0.7);
    transition: width 0.6s;
  }
  
  .mini-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 16px;
  }
  .mini-stat {
    padding: 12px 8px;
    background: rgba(15,23,42,0.7);
    border: 1px solid rgba(148,163,184,0.1);
    border-radius: 12px;
    text-align: center;
  }
  .mini-stat .num {
    font-size: 17px;
    font-weight: 900;
    color: #fde68a;
    font-family: monospace;
    margin-bottom: 3px;
  }
  .mini-stat .lbl {
    font-size: 10px;
    color: var(--muted);
  }
  
  .profile-btn-full {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 14px;
    border-radius: 14px;
    background: linear-gradient(135deg, #f4c542, #eab308);
    color: #1a1a1a;
    text-decoration: none;
    font-weight: 900;
    font-size: 14px;
    box-shadow: 0 8px 22px rgba(244,197,66,0.4);
    transition: 0.2s;
  }
  .profile-btn-full:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 28px rgba(244,197,66,0.6);
  }
  
  /* ============================================================
     Square grid (3 cards)
     ============================================================ */
  .section-label {
    font-size: 11px;
    color: var(--muted);
    font-weight: 900;
    letter-spacing: 2px;
    margin: 4px 4px 12px;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .section-label::after {
    content: "";
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(148,163,184,0.2), transparent);
  }
  
  .square-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 16px;
  }
  .square-card {
    aspect-ratio: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 12px 8px;
    border-radius: 20px;
    text-decoration: none;
    color: #fff;
    position: relative;
    overflow: hidden;
    border: 2px solid;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    isolation: isolate;
    cursor: pointer;
    font-family: inherit;
    background: transparent;
  }
  .square-card::before {
    content: "";
    position: absolute;
    inset: -100%;
    z-index: 0;
    animation: spin 10s linear infinite;
    opacity: 0.5;
  }
  .square-card > * { position: relative; z-index: 1; }
  .square-card:hover {
    transform: translateY(-4px) scale(1.04);
  }
  .square-card:active { transform: scale(0.97); }
  
  .sq-icon {
    font-size: 34px;
    line-height: 1;
    filter: drop-shadow(0 4px 10px rgba(0,0,0,0.5));
    transition: transform 0.3s;
  }
  .square-card:hover .sq-icon { transform: scale(1.15); }
  .sq-title {
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 0.2px;
    line-height: 1.2;
  }
  .sq-sub {
    font-size: 9px;
    opacity: 0.75;
    line-height: 1.2;
  }
  
  /* Notif - purple */
  .square-card.sq-notif {
    background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.4), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #0f0f1e);
    border-color: rgba(139,92,246,0.6);
    box-shadow: 0 10px 30px rgba(139,92,246,0.2);
  }
  .square-card.sq-notif::before {
    background: conic-gradient(from 0deg, transparent, rgba(167,139,250,0.35), transparent, rgba(139,92,246,0.3), transparent);
  }
  .square-card.sq-notif:hover {
    border-color: rgba(167,139,250,0.95);
    box-shadow: 0 18px 45px rgba(139,92,246,0.45);
  }
  .sq-notif .sq-title { color: #c4b5fd; }
  
  /* Games - pink/purple */
  .square-card.sq-games {
    background: radial-gradient(circle at 100% 0%, rgba(236,72,153,0.4), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #120824);
    border-color: rgba(236,72,153,0.6);
    box-shadow: 0 10px 30px rgba(236,72,153,0.2);
  }
  .square-card.sq-games::before {
    background: conic-gradient(from 0deg, transparent, rgba(236,72,153,0.35), transparent, rgba(139,92,246,0.3), transparent);
    animation-duration: 6s;
  }
  .square-card.sq-games:hover {
    border-color: rgba(236,72,153,0.95);
    box-shadow: 0 18px 45px rgba(236,72,153,0.45);
  }
  .sq-games .sq-title { color: #f9a8d4; }
  
  /* Support - cyan */
  .square-card.sq-support {
    background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.4), transparent 60%),
                linear-gradient(135deg, #0a1e2a, #0f0f1e);
    border-color: rgba(6,182,212,0.6);
    box-shadow: 0 10px 30px rgba(6,182,212,0.2);
  }
  .square-card.sq-support::before {
    background: conic-gradient(from 0deg, transparent, rgba(34,211,238,0.35), transparent, rgba(6,182,212,0.3), transparent);
    animation-duration: 7s;
  }
  .square-card.sq-support:hover {
    border-color: rgba(34,211,238,0.95);
    box-shadow: 0 18px 45px rgba(6,182,212,0.45);
  }
  .sq-support .sq-title { color: #a5f3fc; }
  
  /* Unread badge */
  .sq-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    background: #ef4444;
    color: #fff;
    font-size: 10px;
    font-weight: 900;
    padding: 2px 8px;
    border-radius: 999px;
    box-shadow: 0 3px 10px rgba(239,68,68,0.6);
    animation: pulseBadge 2s infinite;
    z-index: 2;
    min-width: 20px;
    text-align: center;
  }
  @keyframes pulseBadge { 0%,100% { transform: scale(1); } 50% { transform: scale(1.18); } }
  
  /* ============================================================
     Shop disabled
     ============================================================ */
  .shop-disabled {
    background: linear-gradient(135deg, #1a1a2e, #0f0f1e);
    border: 2px solid rgba(100,116,139,0.3);
    border-radius: 20px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 14px;
    opacity: 0.55;
    cursor: not-allowed;
    position: relative;
  }
  .shop-disabled .sd-icon {
    font-size: 32px;
    width: 54px;
    height: 54px;
    border-radius: 14px;
    background: rgba(100,116,139,0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .shop-disabled .sd-body { flex: 1; }
  .shop-disabled .sd-title { font-size: 15px; font-weight: 900; color: #cbd5e1; margin-bottom: 3px; }
  .shop-disabled .sd-desc { font-size: 11px; color: #64748b; }
  .shop-disabled .soon-label {
    position: absolute;
    top: 8px;
    left: 8px;
    background: linear-gradient(135deg, #eab308, #ca8a04);
    color: #1a1a1a;
    font-size: 9px;
    font-weight: 900;
    padding: 3px 8px;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(234,179,8,0.4);
    z-index: 2;
  }
  
  /* ============================================================
     Guest warning
     ============================================================ */
  .guest-warning {
    background: linear-gradient(135deg, rgba(234,179,8,0.15), rgba(249,115,22,0.08));
    border: 1.5px solid rgba(234,179,8,0.35);
    border-radius: 16px;
    padding: 14px 16px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .guest-warning .gw-icon { font-size: 28px; flex-shrink: 0; }
  .guest-warning .gw-body { flex: 1; }
  .guest-warning .gw-title { font-size: 13px; font-weight: bold; color: #fde68a; margin-bottom: 2px; }
  .guest-warning .gw-desc { font-size: 11px; color: #fbbf24; line-height: 1.5; }
  .guest-warning .gw-logout {
    background: rgba(239,68,68,0.2);
    color: #fca5a5;
    border: 1px solid rgba(239,68,68,0.4);
    padding: 8px 14px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: bold;
    text-decoration: none;
    flex-shrink: 0;
  }
</style>
{% endblock %}

{% block content %}

  <!-- ===== Top row: 2 circles ===== -->
  <div class="top-circles">
    <!-- Top players (left) -->
    <a href="/game/top-players/" class="circle-btn circle-top" title="بازیکنان برتر">
      <div class="icon">⭐</div>
      <div class="label">برتر</div>
    </a>
    
    <!-- Profile (right) -->
    <button class="circle-btn circle-profile" id="profileToggleBtn" onclick="toggleProfileCircle()" title="پروفایل">
      {% if user.avatar_type == "image" and user.avatar_id %}
        <div class="avatar-in-circle" style="background-image: url('/static/avatars/images/{{ user.avatar_id|stringformat:"03d" }}.jpg');"></div>
      {% else %}
        <div class="avatar-in-circle">{{ avatar_emoji }}</div>
      {% endif %}
      <div class="label">پروفایل</div>
    </button>
  </div>

  <!-- ===== Profile expand card ===== -->
  <div class="profile-expand-card" id="profileExpand">
    <div class="profile-inner">
      <div class="profile-head-row">
        {% if user.avatar_type == "image" and user.avatar_id %}
          <div class="profile-avatar-big" style="background-image: url('/static/avatars/images/{{ user.avatar_id|stringformat:"03d" }}.jpg');"></div>
        {% else %}
          <div class="profile-avatar-big">{{ avatar_emoji }}</div>
        {% endif %}
        <div style="flex:1;min-width:0;">
          <div class="profile-name-big">{{ user.alias }}</div>
          <div class="profile-username-mini">@{{ user.username }}</div>
          <div class="profile-lvl-badge">Lv {{ level|default:1 }}</div>
        </div>
      </div>
      
      <div class="level-bar-wrap">
        <div class="level-info">
          <span class="lbl">پیشرفت تا سطح بعد</span>
          <span class="val">{{ level_progress|default:0 }} / 100</span>
        </div>
        <div class="level-bar">
          <div class="level-bar-fill" style="width: {{ level_progress|default:0 }}%;"></div>
        </div>
      </div>
      
      <div class="mini-stats">
        <div class="mini-stat">
          <div class="num">{{ stats.total_games|default:0 }}</div>
          <div class="lbl">بازی</div>
        </div>
        <div class="mini-stat">
          <div class="num">{{ stats.total_score|default:0 }}</div>
          <div class="lbl">امتیاز</div>
        </div>
        <div class="mini-stat">
          <div class="num">{{ user.coins|default:0 }}</div>
          <div class="lbl">🪙 سکه</div>
        </div>
      </div>
      
      <a href="/accounts/profile/" class="profile-btn-full">
        <span>👤</span>
        <span>مشاهده پروفایل کامل</span>
        <span>←</span>
      </a>
    </div>
  </div>

  {% if user.is_guest %}
    <div class="guest-warning">
      <span class="gw-icon">🎲</span>
      <div class="gw-body">
        <div class="gw-title">حساب مهمان</div>
        <div class="gw-desc">برای ذخیره دائمی، حساب بساز.</div>
      </div>
      <a href="/accounts/logout/" class="gw-logout" onclick="return confirm('از حساب مهمان خارج می‌شوی؟');">🚪 خروج</a>
    </div>
  {% endif %}

  <!-- ===== 3 square cards ===== -->
  <div class="section-label">📋 منو اصلی</div>
  
  <div class="square-grid">
    <!-- Notifications -->
    <a href="/social/notifications/" class="square-card sq-notif">
      {% if unread_notifications %}<span class="sq-badge">{{ unread_notifications }}</span>{% endif %}
      <div class="sq-icon">🔔</div>
      <div class="sq-title">اعلان‌ها</div>
      <div class="sq-sub">{% if unread_notifications %}{{ unread_notifications }} جدید{% else %}پیام‌ها{% endif %}</div>
    </a>
    
    <!-- Games -->
    <a href="/game/rooms/" class="square-card sq-games">
      <div class="sq-icon">🎮</div>
      <div class="sq-title">بازی‌ها</div>
      <div class="sq-sub">۶ حالت</div>
    </a>
    
    <!-- Support -->
    <button class="square-card sq-support" onclick="openSupport()">
      <div class="sq-icon">💬</div>
      <div class="sq-title">پشتیبانی</div>
      <div class="sq-sub">در تماس باش</div>
    </button>
  </div>

  <!-- ===== Shop (disabled) ===== -->
  <div class="shop-disabled">
    <span class="soon-label">به زودی</span>
    <div class="sd-icon">🛒</div>
    <div class="sd-body">
      <div class="sd-title">فروشگاه</div>
      <div class="sd-desc">خرید آواتار و تم‌های ویژه</div>
    </div>
    <div style="font-size:20px;color:#64748b;">🔒</div>
  </div>

{% endblock %}

{% block extra_js %}
<script>
  function toggleProfileCircle() {
    const card = document.getElementById('profileExpand');
    const btn = document.getElementById('profileToggleBtn');
    const isOpen = card.classList.toggle('expanded');
    btn.classList.toggle('active', isOpen);
    if (window.vibrate) window.vibrate(10);
    if (window.soundClick) window.soundClick();
  }
  
  function openSupport() {
    alert('📬 راه‌های ارتباط با پشتیبانی:\\n\\n📧 ایمیل: support@esmfamil.com\\n💬 تلگرام: @esmfamil_support\\n\\n(این صفحه به زودی کامل می‌شود)');
    if (window.soundClick) window.soundClick();
  }
</script>
{% endblock %}
''')

# ============================================================
# 2) Ensure game/views.py home passes level + stats
# ============================================================
print("\n[2/3] Update game/views.py home context")
import re
p = "game/views.py"
with open(p, "r", encoding="utf-8") as f: src = f.read()

# Check if home already has level/stats
if '"level": level' in src and '"stats":' in src and '"level_progress": level_progress' in src:
    print("  ✓ home already has level/stats")
else:
    # Find home function
    pattern = re.compile(
        r'(@login_required\ndef home\(request\):.*?return render\(request, "game/menu\.html", \{[^}]*\}\))',
        re.DOTALL
    )
    m = pattern.search(src)
    if m:
        new_home = '''@login_required
def home(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")
    from social.notifications import unread_count
    from django.db.models import Sum

    # Player stats
    from .models import Player
    my_players = Player.objects.filter(user=request.user)
    total_games = my_players.count()
    total_score = my_players.aggregate(t=Sum("score"))["t"] or 0
    level = 1 + total_score // 100
    level_progress = total_score % 100

    return render(request, "game/menu.html", {
        "avatar_emoji": _avatar(request.user),
        "active": "home",
        "unread_notifications": unread_count(request.user),
        "level": level,
        "level_progress": level_progress,
        "stats": {
            "total_games": total_games,
            "total_score": total_score,
        },
    })'''
        src = src[:m.start()] + new_home + src[m.end():]
        with open(p, "w", encoding="utf-8") as f: f.write(src)
        print("  ✓ home updated")
    else:
        print("  ⚠ home pattern not found — trying to add via simple replace")
        old_home = '''@login_required
def home(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")
    from social.notifications import unread_count
    return render(request, "game/menu.html", {
        "avatar_emoji": _avatar(request.user),
        "active": "home",
        "unread_notifications": unread_count(request.user),
    })'''
        new_home = '''@login_required
def home(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")
    from social.notifications import unread_count
    from django.db.models import Sum
    from .models import Player
    my_players = Player.objects.filter(user=request.user)
    total_games = my_players.count()
    total_score = my_players.aggregate(t=Sum("score"))["t"] or 0
    level = 1 + total_score // 100
    level_progress = total_score % 100
    return render(request, "game/menu.html", {
        "avatar_emoji": _avatar(request.user),
        "active": "home",
        "unread_notifications": unread_count(request.user),
        "level": level,
        "level_progress": level_progress,
        "stats": {"total_games": total_games, "total_score": total_score},
    })'''
        if old_home in src:
            src = src.replace(old_home, new_home, 1)
            with open(p, "w", encoding="utf-8") as f: f.write(src)
            print("  ✓ home updated (exact match)")
        else:
            print("  ⚠ Could not update home — will need manual fix")

# ============================================================
# 3) Django check
# ============================================================
print("\n[3/3] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ PASSED")
else:
    print(f"  ⚠ {r.stderr[:500]}")

print("\n" + "="*60)
print("✅ صفحه خانه بازطراحی شد")
print("="*60)
print("""
طراحی جدید:

  ┌─────────────────────────────────┐
  │  [⭐ برتر]          [👤 پروفایل] │
  │                                  │
  │  (کلیک پروفایل → کارت باز شه)  │
  │                                  │
  │  📋 منو اصلی                    │
  │  ┌────┐ ┌────┐ ┌────┐          │
  │  │🔔  │ │🎮  │ │💬  │          │
  │  │اعلان│ │بازی│ │پشتیب│          │
  │  └────┘ └────┘ └────┘          │
  │                                  │
  │  [🛒 فروشگاه - به زودی] 🔒     │
  └─────────────────────────────────┘

  ⭐ برتر: دایره طلایی با فونت درخشان
  👤 پروفایل: دایره بنفش با آواتار
  🔔 اعلان: مربع بنفش
  🎮 بازی‌ها: مربع صورتی
  💬 پشتیبانی: مربع فیروزه‌ای
  🛒 فروشگاه: نوار خاکستری غیرفعال

حالا:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R

بعد:
  http://127.0.0.1:8000/game/
""")
