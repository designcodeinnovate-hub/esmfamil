#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restore beautiful home graphics + rooms"""
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) MENU.HTML — Beautiful version with all effects
# ============================================================
print("\n[1/3] Restoring beautiful menu.html")

MENU_HTML = '''{% extends "base.html" %}
{% block title %}خانه{% endblock %}

{% block extra_css %}
<style>
  /* ============ ANIMATED DOTS BACKGROUND ============ */
  .bg-pattern { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
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
  .bg-pattern::after { animation-duration: 45s; animation-direction: reverse; opacity: 0.5; }
  @keyframes dotsFloat { from { transform: translate(0, 0); } to { transform: translate(60px, 90px); } }

  .fly-dot {
    position: fixed; width: 4px; height: 4px; border-radius: 50%;
    background: #f4c542; box-shadow: 0 0 8px #f4c542;
    opacity: 0.6; z-index: 0; pointer-events: none; animation: flyUp linear infinite;
  }
  @keyframes flyUp {
    from { transform: translateY(100vh) scale(0.3); opacity: 0; }
    20% { opacity: 0.7; }
    80% { opacity: 0.5; }
    to { transform: translateY(-50px) scale(1); opacity: 0; }
  }

  /* ============ TOP BAR ============ */
  .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; position: relative; z-index: 2; }
  .version-badge { display: inline-flex; align-items: center; gap: 5px; background: rgba(234,179,8,0.15); color: #facc15; font-size: 10px; padding: 5px 10px; border-radius: 10px; border: 1px solid rgba(234,179,8,0.3); font-weight: bold; }
  .btn-settings-b { width: 42px; height: 42px; border-radius: 14px; background: rgba(30,41,59,0.9); border: 1.5px solid rgba(148,163,184,0.2); display: flex; align-items: center; justify-content: center; text-decoration: none; font-size: 20px; transition: all 0.2s; }
  .btn-settings-b:hover { border-color: #f4c542; transform: rotate(45deg); }

  /* ============ PROFILE OVAL ============ */
  .profile-wrap { position: relative; z-index: 5; margin-bottom: 18px; }
  .profile-oval {
    display: flex; align-items: center; gap: 0; padding: 6px;
    width: 62px; height: 62px; border-radius: 31px;
    background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.35), transparent 60%),
                radial-gradient(circle at 0% 100%, rgba(139,92,246,0.25), transparent 60%),
                linear-gradient(135deg, #1a1a2e, #0f0f1e);
    border: 2.5px solid rgba(244,197,66,0.6);
    cursor: pointer; transition: all 0.45s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden; margin-right: auto;
    box-shadow: 0 0 25px rgba(244,197,66,0.3);
  }
  .profile-oval:hover { border-color: #fde68a; box-shadow: 0 0 40px rgba(244,197,66,0.6); }
  .profile-oval.expanded {
    width: 100%; height: 90px; border-radius: 45px;
    padding: 14px 18px; gap: 14px;
    box-shadow: 0 15px 45px rgba(244,197,66,0.4);
  }
  .po-av {
    width: 48px; height: 48px; border-radius: 50%;
    background: linear-gradient(135deg, #2a2a4a, #1a1a2e);
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; border: 2px solid #f4c542;
    box-shadow: 0 0 15px rgba(244,197,66,0.5);
    overflow: hidden; background-size: cover; background-position: center;
    flex-shrink: 0; transition: all 0.4s;
  }
  .profile-oval.expanded .po-av { width: 62px; height: 62px; font-size: 30px; box-shadow: 0 0 25px rgba(244,197,66,0.8); }
  .po-details {
    flex: 1; min-width: 0; max-width: 0; opacity: 0; overflow: hidden;
    transition: all 0.4s; text-align: right; white-space: nowrap;
  }
  .profile-oval.expanded .po-details { max-width: 400px; opacity: 1; }
  .po-name { font-size: 16px; font-weight: 900; color: #fde68a; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; }
  .po-meta { display: flex; gap: 8px; font-size: 11px; color: #94a3b8; align-items: center; }
  .po-meta .lvl { background: linear-gradient(135deg, #8b5cf6, #6b4eff); color: #fff; padding: 2px 8px; border-radius: 8px; font-family: monospace; font-weight: 900; font-size: 10px; }
  .po-chevron { color: #f4c542; font-size: 14px; transition: transform 0.4s; flex-shrink: 0; }
  .profile-oval.expanded .po-chevron { transform: rotate(180deg); }

  /* ============ CIRCLE BUTTONS (top players + shop) ============ */
  .circle-row {
    display: flex; gap: 16px; justify-content: space-around;
    margin-bottom: 20px; position: relative; z-index: 2;
  }
  .circle-btn {
    display: flex; flex-direction: column; align-items: center; gap: 8px;
    cursor: pointer; text-decoration: none; color: #fff;
    transition: transform 0.25s;
  }
  .circle-btn:hover { transform: translateY(-4px); }
  .circle-btn:active { transform: scale(0.94); }
  .cb-circle {
    width: 76px; height: 76px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 32px; border: 3px solid;
    position: relative; overflow: hidden;
    transition: all 0.3s;
  }
  .cb-circle::before {
    content: ""; position: absolute; inset: -100%;
    background: conic-gradient(from 0deg, transparent, rgba(255,255,255,0.2), transparent);
    animation: rotate360 8s linear infinite;
    opacity: 0.6;
  }
  .cb-circle > * { position: relative; z-index: 1; }
  @keyframes rotate360 { to { transform: rotate(360deg); } }

  .cb-top {
    background: radial-gradient(circle at 30% 30%, rgba(244,197,66,0.4), rgba(234,179,8,0.15));
    border-color: rgba(244,197,66,0.7);
    box-shadow: 0 0 20px rgba(244,197,66,0.4), inset 0 0 15px rgba(244,197,66,0.2);
    filter: drop-shadow(0 0 10px rgba(244,197,66,0.6));
  }
  .circle-btn:hover .cb-top {
    box-shadow: 0 0 40px rgba(244,197,66,0.9), inset 0 0 20px rgba(244,197,66,0.4);
    border-color: #fde68a;
  }
  .cb-shop {
    background: radial-gradient(circle at 30% 30%, rgba(6,182,212,0.4), rgba(34,197,94,0.15));
    border-color: rgba(6,182,212,0.7);
    box-shadow: 0 0 20px rgba(6,182,212,0.4), inset 0 0 15px rgba(6,182,212,0.2);
  }
  .circle-btn:hover .cb-shop {
    box-shadow: 0 0 40px rgba(6,182,212,0.9), inset 0 0 20px rgba(6,182,212,0.4);
    border-color: #67e8f9;
  }
  .cb-label { font-size: 12px; font-weight: 900; letter-spacing: 0.3px; }
  .cb-top-label { color: #fde68a; }
  .cb-shop-label { color: #67e8f9; }

  /* ============ 3 SQUARE TILES ============ */
  .section-label {
    font-size: 11px; color: #94a3b8; font-weight: 900; letter-spacing: 2px;
    margin: 20px 4px 12px; display: flex; align-items: center; gap: 8px;
    text-transform: uppercase; position: relative; z-index: 2;
  }
  .section-label::after { content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, rgba(148,163,184,0.3), transparent); }

  .sq-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; position: relative; z-index: 2; }
  .sq-tile {
    aspect-ratio: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 6px;
    padding: 12px 8px; border-radius: 20px; text-decoration: none; color: #fff;
    position: relative; overflow: hidden; border: 2px solid;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer; font-family: inherit; background: transparent;
  }
  .sq-tile::before {
    content: ""; position: absolute; inset: -100%;
    background: conic-gradient(from 0deg, transparent, rgba(255,255,255,0.15), transparent);
    animation: rotate360 10s linear infinite; z-index: 0; opacity: 0.5;
  }
  .sq-tile::after {
    content: ""; position: absolute; top: 0; left: -100%;
    width: 60%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transform: skewX(-20deg); animation: shine 4s infinite;
    z-index: 2; pointer-events: none;
  }
  @keyframes shine { 0% { left: -100%; } 50%,100% { left: 200%; } }
  .sq-tile > * { position: relative; z-index: 1; }
  .sq-tile:hover { transform: translateY(-5px) scale(1.04); }
  .sq-tile:active { transform: scale(0.97); }

  .sq-icon {
    font-size: 38px; line-height: 1;
    filter: drop-shadow(0 4px 12px rgba(0,0,0,0.5));
    animation: float 3s ease-in-out infinite;
  }
  .sq-tile:nth-child(1) .sq-icon { animation-delay: 0s; }
  .sq-tile:nth-child(2) .sq-icon { animation-delay: 0.4s; }
  .sq-tile:nth-child(3) .sq-icon { animation-delay: 0.8s; }
  @keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
  .sq-tile:hover .sq-icon { transform: scale(1.2) rotate(-8deg); animation: none; }

  .sq-title { font-size: 12px; font-weight: 900; letter-spacing: 0.2px; }
  .sq-sub { font-size: 9px; opacity: 0.75; }

  /* Notif — purple */
  .sq-notif {
    background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.4), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #0f0f1e);
    border-color: rgba(139,92,246,0.6);
    box-shadow: 0 10px 30px rgba(139,92,246,0.2);
  }
  .sq-notif:hover { border-color: rgba(167,139,250,0.95); box-shadow: 0 18px 45px rgba(139,92,246,0.45); }
  .sq-notif .sq-title { color: #c4b5fd; }

  /* Games — pink */
  .sq-games {
    background: radial-gradient(circle at 100% 0%, rgba(236,72,153,0.4), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #120824);
    border-color: rgba(236,72,153,0.6);
    box-shadow: 0 10px 30px rgba(236,72,153,0.2);
  }
  .sq-games:hover { border-color: rgba(236,72,153,0.95); box-shadow: 0 18px 45px rgba(236,72,153,0.45); }
  .sq-games .sq-title { color: #f9a8d4; }

  /* Challenge — red/gold */
  .sq-challenge {
    background: radial-gradient(circle at 100% 0%, rgba(239,68,68,0.4), transparent 60%),
                linear-gradient(135deg, #2a0a0a, #1a0606);
    border-color: rgba(239,68,68,0.6);
    box-shadow: 0 10px 30px rgba(239,68,68,0.2);
  }
  .sq-challenge:hover { border-color: rgba(248,113,113,0.95); box-shadow: 0 18px 45px rgba(239,68,68,0.45); }
  .sq-challenge .sq-title { color: #fca5a5; }

  .sq-badge {
    position: absolute; top: 8px; right: 8px;
    background: #ef4444; color: #fff;
    font-size: 10px; font-weight: 900;
    padding: 2px 8px; border-radius: 999px;
    box-shadow: 0 3px 10px rgba(239,68,68,0.6);
    animation: pulseBadge 2s infinite; z-index: 3;
  }
  @keyframes pulseBadge { 0%,100% { transform: scale(1); } 50% { transform: scale(1.18); } }

  /* ============ SUPPORT BUTTON ============ */
  .support-btn {
    display: flex; align-items: center; gap: 14px;
    padding: 18px 20px;
    background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.4), transparent 60%),
                linear-gradient(135deg, #0a1e2a, #05141a);
    border: 2px solid rgba(6,182,212,0.6);
    border-radius: 20px;
    text-decoration: none; color: #fff;
    cursor: pointer; transition: all 0.3s;
    box-shadow: 0 10px 30px rgba(6,182,212,0.2);
    position: relative; z-index: 2;
    overflow: hidden;
    margin-top: 8px;
  }
  .support-btn::after {
    content: ""; position: absolute; top: 0; left: -100%;
    width: 60%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transform: skewX(-20deg); animation: shine 5s infinite;
    pointer-events: none;
  }
  .support-btn:hover {
    transform: translateY(-3px);
    border-color: rgba(34,211,238,0.95);
    box-shadow: 0 18px 45px rgba(6,182,212,0.5);
  }
  .support-btn .si { font-size: 36px; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.5)); }
  .support-btn .sb { flex: 1; text-align: right; }
  .support-btn .st { font-size: 16px; font-weight: 900; color: #a5f3fc; margin-bottom: 3px; }
  .support-btn .sd { font-size: 11px; color: #94a3b8; }
  .support-btn .sa { font-size: 22px; color: #67e8f9; }

  /* Guest warning */
  .guest-warning {
    background: linear-gradient(135deg, rgba(234,179,8,0.15), rgba(249,115,22,0.08));
    border: 1.5px solid rgba(234,179,8,0.35);
    border-radius: 14px; padding: 12px 14px; margin-bottom: 14px;
    display: flex; align-items: center; gap: 12px;
    position: relative; z-index: 2;
    font-size: 12px; color: #fde68a;
  }
  .guest-warning .gw-logout {
    background: rgba(244,197,66,0.9); color: #1a1a1a;
    padding: 6px 12px; border-radius: 8px;
    font-size: 11px; font-weight: 900; text-decoration: none;
  }
</style>
{% endblock %}

{% block content %}
  <!-- Animated background -->
  <div class="bg-pattern"></div>
  <div class="fly-dot" style="left: 10%; animation-duration: 12s;"></div>
  <div class="fly-dot" style="left: 25%; animation-duration: 15s; animation-delay: 2s; background: #8b5cf6; box-shadow: 0 0 8px #8b5cf6;"></div>
  <div class="fly-dot" style="left: 45%; animation-duration: 18s; animation-delay: 4s;"></div>
  <div class="fly-dot" style="left: 60%; animation-duration: 14s; animation-delay: 1s; background: #06b6d4; box-shadow: 0 0 8px #06b6d4;"></div>
  <div class="fly-dot" style="left: 78%; animation-duration: 16s; animation-delay: 3s;"></div>
  <div class="fly-dot" style="left: 92%; animation-duration: 13s; animation-delay: 5s; background: #8b5cf6; box-shadow: 0 0 8px #8b5cf6;"></div>

  <!-- Top bar -->
  <div class="top-bar">
    <div class="version-badge"><span>🧪</span><span>نسخه آزمایشی</span></div>
    <a href="/accounts/settings/" class="btn-settings-b">⚙️</a>
  </div>

  <!-- Profile (circle → oval) -->
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
          <span class="lvl">Lv {{ level|default:1 }}</span>
          <span>🪙 {{ user.coins|default:0 }}</span>
          <span>💎 {{ user.gems|default:0 }}</span>
        </div>
      </div>
      <div class="po-chevron">▼</div>
    </div>
  </div>

  {% if user.is_guest %}
    <div class="guest-warning">
      <span style="font-size: 22px;">🎲</span>
      <div style="flex: 1;">حساب مهمان — برای ذخیره دائمی ثبت‌نام کن</div>
      <a href="/accounts/register/" class="gw-logout">ثبت‌نام</a>
    </div>
  {% endif %}

  <!-- 2 Circle buttons: Top players + Shop -->
  <div class="circle-row">
    <a href="/game/top-players/" class="circle-btn">
      <div class="cb-circle cb-top">⭐</div>
      <div class="cb-label cb-top-label">بازیکنان برتر</div>
    </a>
    <a href="/accounts/shop/" class="circle-btn">
      <div class="cb-circle cb-shop">🛒</div>
      <div class="cb-label cb-shop-label">فروشگاه</div>
    </a>
  </div>

  <!-- Section: main menu -->
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

    <a href="/game/challenge/" class="sq-tile sq-challenge">
      <div class="sq-icon">🏆</div>
      <div class="sq-title">چالش</div>
      <div class="sq-sub">تورنمنت</div>
    </a>
  </div>

  <!-- Support -->
  <div class="section-label">💬 ارتباط با ما</div>

  <a href="/support/" class="support-btn">
    <span class="si">💬</span>
    <div class="sb">
      <div class="st">پشتیبانی</div>
      <div class="sd">سوال داری؟ با ما در تماس باش</div>
    </div>
    <span class="sa">←</span>
  </a>

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
'''
write("game/templates/game/menu.html", MENU_HTML)

# ============================================================
# 2) ROOMS.HTML — Restore beautiful version
# ============================================================
print("\n[2/3] Restoring beautiful rooms.html")

ROOMS_HTML = '''{% extends "base.html" %}
{% block title %}بازی‌ها{% endblock %}

{% block extra_css %}
<style>
  .bg-pattern { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
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
  .bg-pattern::after { animation-duration: 45s; animation-direction: reverse; opacity: 0.5; }
  @keyframes dotsFloat { from { transform: translate(0, 0); } to { transform: translate(60px, 90px); } }

  .page-head { margin-bottom: 20px; display: flex; align-items: center; gap: 12px; position: relative; z-index: 2; }
  .page-head h1 { font-size: 24px; font-weight: 900; background: linear-gradient(135deg, #f4c542, #fdba74); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .page-head .count { font-size: 11px; padding: 3px 10px; background: rgba(244,197,66,0.15); color: #fde68a; border-radius: 8px; font-family: monospace; }

  .intro-text { color: #94a3b8; font-size: 13px; margin-bottom: 20px; line-height: 1.6; position: relative; z-index: 2; }

  .big {
    display: flex; align-items: center; gap: 16px;
    padding: 22px 20px; border-radius: 24px;
    text-decoration: none; color: #fff;
    margin-bottom: 14px;
    position: relative; overflow: hidden;
    border: 2px solid;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    isolation: isolate;
    z-index: 2;
  }
  .big:hover { transform: translateY(-4px) scale(1.01); }
  .big:active { transform: scale(0.98); }
  .big.soon { cursor: default; opacity: 0.7; }
  .big.soon:hover { transform: none; }

  .big::before {
    content: ""; position: absolute; inset: -150%;
    z-index: -1; animation: spin 10s linear infinite; opacity: 0.6;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .big.bot { background: linear-gradient(135deg, #2a1a0e, #1a0f08); border-color: rgba(244,197,66,0.55); box-shadow: 0 15px 40px rgba(244,197,66,0.2); }
  .big.bot::before { background: conic-gradient(from 0deg, transparent, rgba(244,197,66,0.25), transparent, rgba(249,115,22,0.25), transparent); }
  .big.bot:hover { border-color: rgba(251,211,77,0.95); box-shadow: 0 20px 60px rgba(244,197,66,0.4); }

  .big.player { background: linear-gradient(135deg, #0a1a2a, #080f18); border-color: rgba(59,130,246,0.55); box-shadow: 0 15px 40px rgba(59,130,246,0.2); }
  .big.player::before { background: conic-gradient(from 0deg, transparent, rgba(96,165,250,0.3), transparent, rgba(139,92,246,0.25), transparent); }
  .big.player:hover { border-color: rgba(96,165,250,0.95); box-shadow: 0 20px 60px rgba(59,130,246,0.4); }

  .big.group { background: linear-gradient(135deg, #1a0f2e, #120824); border-color: rgba(139,92,246,0.6); box-shadow: 0 15px 40px rgba(139,92,246,0.25); }
  .big.group::before { background: conic-gradient(from 0deg, transparent, rgba(167,139,250,0.3), transparent, rgba(236,72,153,0.25), transparent); }
  .big.group:hover { border-color: rgba(167,139,250,0.95); box-shadow: 0 20px 60px rgba(139,92,246,0.45); }

  .big.speed { background: linear-gradient(135deg, #0a1e2a, #05141a); border-color: rgba(6,182,212,0.6); box-shadow: 0 15px 40px rgba(6,182,212,0.25); }
  .big.speed::before { background: conic-gradient(from 0deg, transparent, rgba(34,211,238,0.3), transparent, rgba(6,182,212,0.25), transparent); animation-duration: 5s; }
  .big.speed:hover { border-color: rgba(34,211,238,0.95); box-shadow: 0 20px 60px rgba(6,182,212,0.45); }

  .big.puzzle { background: linear-gradient(135deg, #0a2a1a, #051a0f); border-color: rgba(34,197,94,0.6); box-shadow: 0 15px 40px rgba(34,197,94,0.25); }
  .big.puzzle::before { background: conic-gradient(from 0deg, transparent, rgba(74,222,128,0.3), transparent, rgba(16,185,129,0.25), transparent); animation-duration: 8s; }
  .big.puzzle:hover { border-color: rgba(74,222,128,0.95); box-shadow: 0 20px 60px rgba(34,197,94,0.45); }

  .big.guess { background: linear-gradient(135deg, #0a1e2a, #05141a); border-color: rgba(6,182,212,0.6); box-shadow: 0 15px 40px rgba(6,182,212,0.25); }
  .big.guess::before { background: conic-gradient(from 0deg, transparent, rgba(34,211,238,0.3), transparent, rgba(59,130,246,0.25), transparent); animation-duration: 6s; }
  .big.guess:hover { border-color: rgba(34,211,238,0.95); box-shadow: 0 20px 60px rgba(6,182,212,0.45); }

  .big.memory { background: linear-gradient(135deg, #1a0f2e, #0f0f1e); border-color: rgba(167,139,250,0.6); box-shadow: 0 15px 40px rgba(139,92,246,0.25); }
  .big.memory::before { background: conic-gradient(from 0deg, transparent, rgba(167,139,250,0.3), transparent, rgba(139,92,246,0.25), transparent); animation-duration: 7s; }
  .big.memory:hover { border-color: rgba(196,181,253,0.95); box-shadow: 0 20px 60px rgba(139,92,246,0.45); }

  .big > * { position: relative; z-index: 1; }

  .bic {
    font-size: 42px; width: 72px; height: 72px;
    border-radius: 20px; background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    border: 1.5px solid rgba(255,255,255,0.15);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; transition: transform 0.3s;
    box-shadow: 0 8px 20px rgba(0,0,0,0.3);
  }
  .big:hover .bic { transform: scale(1.1) rotate(-6deg); }

  .bbody { flex: 1; }
  .btitle { font-size: 19px; font-weight: 900; margin-bottom: 4px; letter-spacing: -0.2px; }
  .big.bot .btitle { color: #fde68a; }
  .big.player .btitle { color: #bfdbfe; }
  .big.group .btitle { color: #e9d5ff; }
  .big.speed .btitle { color: #a5f3fc; }
  .big.puzzle .btitle { color: #bbf7d0; }
  .big.guess .btitle { color: #a5f3fc; }
  .big.memory .btitle { color: #c4b5fd; }
  .bdesc { font-size: 12px; color: rgba(255,255,255,0.7); line-height: 1.5; }

  .btags { display: flex; gap: 5px; flex-wrap: wrap; margin-top: 8px; }
  .btag { font-size: 9.5px; font-weight: bold; padding: 3px 8px; border-radius: 6px; background: rgba(255,255,255,0.1); color: #e2e8f0; border: 1px solid rgba(255,255,255,0.15); }

  .barrow { font-size: 22px; color: rgba(255,255,255,0.5); transition: 0.3s; }
  .big:hover .barrow { transform: translateX(-4px); color: rgba(255,255,255,0.9); }

  .badge-live { position: absolute; top: 12px; left: 12px; background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; font-size: 10px; font-weight: 900; padding: 3px 9px; border-radius: 999px; z-index: 2; box-shadow: 0 4px 12px rgba(34,197,94,0.5); animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.7; } }
  .badge-team { position: absolute; top: 12px; left: 12px; background: linear-gradient(135deg, #ec4899, #8b5cf6); color: #fff; font-size: 10px; font-weight: 900; padding: 3px 9px; border-radius: 999px; z-index: 2; }
  .badge-new { position: absolute; top: 12px; left: 12px; background: linear-gradient(135deg, #f4c542, #eab308); color: #1a1a1a; font-size: 10px; font-weight: 900; padding: 3px 9px; border-radius: 999px; z-index: 2; animation: pulse 2s infinite; }
</style>
{% endblock %}
{% block content %}
  <div class="bg-pattern"></div>

  <div class="page-head">
    <h1>🎮 بازی‌ها</h1>
    <span class="count">۷ حالت</span>
  </div>

  <p class="intro-text">یه حالت رو انتخاب کن و شروع کن! هر بازی یه تجربه‌ی خاص داره.</p>

  <a href="/game/quick/" class="big bot">
    <div class="badge-live">⚡ آنی</div>
    <div class="bic">⚡</div>
    <div class="bbody">
      <div class="btitle">بازی با بات</div>
      <div class="bdesc">رقیب هوشمند، سه سطح سختی</div>
      <div class="btags">
        <span class="btag">🎯 ۳ سطح</span>
        <span class="btag">🚀 بدون انتظار</span>
      </div>
    </div>
    <div class="barrow">←</div>
  </a>

  <a href="/game/match/" class="big player">
    <div class="badge-live">🌐 آنلاین</div>
    <div class="bic">⚔️</div>
    <div class="bbody">
      <div class="btitle">بازی با پلیر</div>
      <div class="bdesc">رقابت آنی با یک حریف واقعی</div>
      <div class="btags">
        <span class="btag">🎯 1v1</span>
        <span class="btag">🌍 سراسر ایران</span>
      </div>
    </div>
    <div class="barrow">←</div>
  </a>

  <a href="/game/team/start/" class="big group">
    <div class="badge-team">👥 ۴ نفره</div>
    <div class="bic">🛡️</div>
    <div class="bbody">
      <div class="btitle">بازی گروهی</div>
      <div class="bdesc">۴ نفره · دو تیم ۲ نفره · ۳ راند</div>
      <div class="btags">
        <span class="btag">👥 2v2</span>
        <span class="btag">🏆 جایزه برنده</span>
      </div>
    </div>
    <div class="barrow">←</div>
  </a>

  <a href="/game/quick/bot/?mode=speed" class="big speed">
    <div class="bic">⏱️</div>
    <div class="bbody">
      <div class="btitle">بازی سرعتی</div>
      <div class="bdesc">فقط ۲۰ ثانیه فرصت داری!</div>
      <div class="btags">
        <span class="btag">⚡ سریع</span>
        <span class="btag">🎲 حرف رندوم</span>
      </div>
    </div>
    <div class="barrow">←</div>
  </a>

  <a href="/game/puzzle/" class="big puzzle">
    <div class="badge-new">🆕 جدید</div>
    <div class="bic">🎯</div>
    <div class="bbody">
      <div class="btitle">بازی معما</div>
      <div class="bdesc">حروف رو مرتب کن، کلمه رو بساز</div>
      <div class="btags">
        <span class="btag">🧩 ۵ کلمه</span>
        <span class="btag">⏱ زمان محدود</span>
      </div>
    </div>
    <div class="barrow">←</div>
  </a>

  <a href="/game/guess/" class="big guess">
    <div class="badge-new">🆕 جدید</div>
    <div class="bic">🎲</div>
    <div class="bbody">
      <div class="btitle">بازی ۰ تا ۱۰۰</div>
      <div class="bdesc">عدد پنهان رو حدس بزن</div>
      <div class="btags">
        <span class="btag">🔢 اعداد</span>
        <span class="btag">🎯 ۷ تلاش</span>
      </div>
    </div>
    <div class="barrow">←</div>
  </a>

  <a href="/game/memory/" class="big memory">
    <div class="badge-new">🆕 جدید</div>
    <div class="bic">🧠</div>
    <div class="bbody">
      <div class="btitle">بازی حافظه</div>
      <div class="bdesc">جفت کارت‌های یکسان رو پیدا کن</div>
      <div class="btags">
        <span class="btag">🧠 ۸ جفت</span>
        <span class="btag">🎯 سرعت + حافظه</span>
      </div>
    </div>
    <div class="barrow">←</div>
  </a>

{% endblock %}
'''
write("game/templates/game/rooms.html", ROOMS_HTML)

# ============================================================
# 3) Verify
# ============================================================
print("\n[3/3] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True, timeout=30)
if r.returncode == 0:
    print("  ✓ PASSED")
else:
    print(f"  ⚠ {r.stderr[:300] if r.stderr else r.stdout[:300]}")

print("\n" + "="*60)
print("✅ گرافیک زیبا برگشت")
print("="*60)
print("""
چه چیزایی برگشت:

  🏠 خانه:
     ✓ پس‌زمینه نقطه‌ای متحرک
     ✓ ذرات طلایی/بنفش شناور
     ✓ پروفایل دایره → کلیک → بیضی (به چپ)
     ✓ ⚙️ تنظیمات (بالا چپ)
     ✓ ⭐ بازیکنان برتر + 🛒 فروشگاه (دایره‌ای، بالا)
     ✓ 🔔 اعلان‌ها (بنفش) + 🎮 بازی‌ها (صورتی) + 🏆 چالش (قرمز)
     ✓ 💬 پشتیبانی (مستطیل فیروزه‌ای، پایین)
     ✓ همه با shine + float + pulse animation

  🎮 بازی‌ها:
     ✓ ۷ کارت رنگی
     ✓ rotating glow پشت هر کارت
     ✓ آیکون‌های ۷۲px با hover rotate
     ✓ badge های live/new/team
     ✓ تگ‌های اطلاعات

  قابلیت‌های جدید همه سر جاشون:
     ✓ قفل آواتار (50 سکه)
     ✓ فروشگاه فعال
     ✓ پشتیبانی

حالا:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R

تست:
  http://127.0.0.1:8000/game/
  http://127.0.0.1:8000/game/rooms/
""")
