#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess, random

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
# 1) HOME PAGE — oval profile + cooler tiles + shop below top
# ============================================================
print("\n[1/6] Home page redesign")
write("game/templates/game/menu.html", '''{% extends "base.html" %}
{% block title %}خانه{% endblock %}

{% block extra_css %}
<style>
  /* ============ OVAL PROFILE BAR ============ */
  .oval-profile {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 18px;
    background: radial-gradient(ellipse at 100% 0%, rgba(244,197,66,0.3), transparent 60%),
                radial-gradient(ellipse at 0% 100%, rgba(139,92,246,0.25), transparent 60%),
                linear-gradient(135deg, var(--card), #0f0f1e);
    border: 2px solid rgba(244,197,66,0.5);
    border-radius: 999px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 25px rgba(244,197,66,0.15);
  }
  .oval-profile:hover {
    border-color: rgba(244,197,66,0.9);
    box-shadow: 0 12px 35px rgba(244,197,66,0.3);
    transform: translateY(-2px);
  }
  .oval-profile::before {
    content: "";
    position: absolute;
    inset: -100%;
    background: conic-gradient(from 0deg, transparent, rgba(244,197,66,0.15), transparent, rgba(139,92,246,0.15), transparent);
    animation: spin 15s linear infinite;
    z-index: 0;
    opacity: 0.6;
  }
  .oval-profile > * { position: relative; z-index: 1; }
  @keyframes spin { to { transform: rotate(360deg); } }

  .op-avatar {
    width: 48px; height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2a2a4a, #1a1a2e);
    display: flex; align-items: center; justify-content: center;
    font-size: 24px;
    border: 2.5px solid #f4c542;
    box-shadow: 0 0 20px rgba(244,197,66,0.5);
    overflow: hidden;
    background-size: cover;
    background-position: center;
    flex-shrink: 0;
  }
  .op-body { flex: 1; min-width: 0; text-align: right; }
  .op-name {
    font-size: 16px; font-weight: 900;
    color: #fde68a;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    margin-bottom: 2px;
  }
  .op-meta {
    font-size: 11px;
    color: #94a3b8;
    display: flex; gap: 8px; align-items: center;
  }
  .op-meta .lvl {
    background: linear-gradient(135deg, #8b5cf6, #6b4eff);
    color: #fff;
    padding: 1px 8px;
    border-radius: 8px;
    font-family: monospace;
    font-weight: 900;
  }
  .op-chevron {
    font-size: 18px;
    color: var(--gold);
    transition: transform 0.3s;
  }
  .oval-profile.expanded .op-chevron { transform: rotate(180deg); }

  /* ============ PROFILE EXPAND ============ */
  .profile-expand {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.5s cubic-bezier(0.4, 0, 0.2, 1), margin-bottom 0.4s;
    margin-bottom: 0;
  }
  .profile-expand.open { max-height: 700px; margin-bottom: 16px; }
  .pe-inner {
    padding: 20px;
    background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.2), transparent 55%),
                radial-gradient(circle at 0% 100%, rgba(139,92,246,0.15), transparent 55%),
                linear-gradient(135deg, var(--card), #0f0f1e);
    border: 1.5px solid rgba(244,197,66,0.4);
    border-radius: 22px;
    position: relative;
    overflow: hidden;
  }
  .pe-inner::before {
    content: "";
    position: absolute;
    top: -50%; right: -50%;
    width: 200%; height: 200%;
    background: conic-gradient(from 0deg, transparent, rgba(244,197,66,0.08), transparent, rgba(139,92,246,0.08), transparent);
    animation: spin 15s linear infinite;
  }
  .pe-inner > * { position: relative; z-index: 1; }

  .pe-head { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; }
  .pe-av-big {
    width: 72px; height: 72px;
    border-radius: 50%;
    border: 3px solid #f4c542;
    background: linear-gradient(135deg, #2a2a4a, #1a1a2e);
    display: flex; align-items: center; justify-content: center;
    font-size: 38px;
    box-shadow: 0 0 30px rgba(244,197,66,0.6);
    overflow: hidden;
    background-size: cover;
    background-position: center;
    flex-shrink: 0;
  }
  .pe-name-big {
    font-size: 20px; font-weight: 900;
    background: linear-gradient(135deg, #fde68a, #f4c542, #fdba74);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 3px;
  }
  .pe-username {
    font-size: 11px; color: #64748b; font-family: monospace;
  }
  .pe-level-wrap { margin-bottom: 14px; }
  .pe-level-info { display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 5px; }
  .pe-level-info .l { color: var(--muted); }
  .pe-level-info .v { color: var(--gold); font-family: monospace; font-weight: 900; }
  .pe-level-bar { height: 9px; background: rgba(148,163,184,0.15); border-radius: 9px; overflow: hidden; }
  .pe-level-fill { height: 100%; background: linear-gradient(90deg, #8b5cf6, #f4c542); border-radius: 9px; box-shadow: 0 0 10px rgba(139,92,246,0.6); }
  .pe-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 14px; }
  .pe-stat { padding: 10px 6px; background: rgba(15,23,42,0.6); border: 1px solid rgba(148,163,184,0.1); border-radius: 12px; text-align: center; }
  .pe-stat .n { font-size: 16px; font-weight: 900; color: #fde68a; font-family: monospace; margin-bottom: 2px; }
  .pe-stat .l { font-size: 9px; color: var(--muted); }
  .pe-btn {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    padding: 12px; border-radius: 12px;
    background: linear-gradient(135deg, #f4c542, #eab308);
    color: #1a1a1a; text-decoration: none;
    font-weight: 900; font-size: 14px;
    box-shadow: 0 8px 20px rgba(244,197,66,0.35);
    transition: 0.2s;
  }
  .pe-btn:hover { transform: translateY(-2px); box-shadow: 0 12px 25px rgba(244,197,66,0.5); }

  /* ============ TIP CARD ============ */
  .tip-card {
    display: flex; align-items: center; gap: 12px;
    padding: 12px 14px;
    background: linear-gradient(135deg, rgba(6,182,212,0.12), rgba(59,130,246,0.08));
    border: 1.5px solid rgba(6,182,212,0.35);
    border-radius: 14px;
    margin-bottom: 16px;
    font-size: 12px;
    color: #a5f3fc;
    line-height: 1.5;
  }
  .tip-card .ti { font-size: 22px; flex-shrink: 0; }
  .tip-card .tb { flex: 1; }
  .tip-card b { color: #67e8f9; }

  /* ============ 3 SQUARE TILES (cooler) ============ */
  .section-label {
    font-size: 11px; color: var(--muted);
    font-weight: 900; letter-spacing: 2px;
    margin: 4px 4px 12px;
    display: flex; align-items: center; gap: 8px;
    text-transform: uppercase;
  }
  .section-label::after {
    content: ""; flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(148,163,184,0.2), transparent);
  }

  .sq-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 20px;
  }
  .sq-tile {
    aspect-ratio: 1;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
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
  .sq-tile::before {
    content: "";
    position: absolute;
    inset: -100%;
    z-index: 0;
    animation: spin 8s linear infinite;
    opacity: 0.5;
  }
  .sq-tile::after {
    content: "";
    position: absolute;
    top: 0; left: -100%;
    width: 60%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
    transform: skewX(-20deg);
    animation: shine 4s infinite;
    z-index: 2;
    pointer-events: none;
  }
  @keyframes shine {
    0% { left: -100%; }
    50%,100% { left: 200%; }
  }
  .sq-tile > * { position: relative; z-index: 1; }
  .sq-tile:hover { transform: translateY(-5px) scale(1.04); }
  .sq-tile:active { transform: scale(0.97); }

  .sq-icon {
    font-size: 38px;
    line-height: 1;
    filter: drop-shadow(0 4px 12px rgba(0,0,0,0.5));
    transition: transform 0.3s;
    animation: float 3s ease-in-out infinite;
  }
  .sq-tile:nth-child(1) .sq-icon { animation-delay: 0s; }
  .sq-tile:nth-child(2) .sq-icon { animation-delay: 0.5s; }
  .sq-tile:nth-child(3) .sq-icon { animation-delay: 1s; }
  @keyframes float {
    0%,100% { transform: translateY(0); }
    50% { transform: translateY(-4px); }
  }
  .sq-tile:hover .sq-icon { transform: scale(1.2) rotate(-8deg); animation: none; }
  .sq-title { font-size: 12px; font-weight: 900; letter-spacing: 0.2px; }
  .sq-sub { font-size: 9px; opacity: 0.75; }

  /* Notif - purple */
  .sq-notif {
    background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.4), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #0f0f1e);
    border-color: rgba(139,92,246,0.6);
    box-shadow: 0 10px 30px rgba(139,92,246,0.2);
  }
  .sq-notif::before { background: conic-gradient(from 0deg, transparent, rgba(167,139,250,0.35), transparent, rgba(139,92,246,0.3), transparent); }
  .sq-notif:hover { border-color: rgba(167,139,250,0.95); box-shadow: 0 18px 45px rgba(139,92,246,0.45); }
  .sq-notif .sq-title { color: #c4b5fd; }

  /* Games - pink */
  .sq-games {
    background: radial-gradient(circle at 100% 0%, rgba(236,72,153,0.4), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #120824);
    border-color: rgba(236,72,153,0.6);
    box-shadow: 0 10px 30px rgba(236,72,153,0.2);
  }
  .sq-games::before { background: conic-gradient(from 0deg, transparent, rgba(236,72,153,0.35), transparent, rgba(139,92,246,0.3), transparent); animation-duration: 6s; }
  .sq-games:hover { border-color: rgba(236,72,153,0.95); box-shadow: 0 18px 45px rgba(236,72,153,0.45); }
  .sq-games .sq-title { color: #f9a8d4; }

  /* Support - cyan */
  .sq-support {
    background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.4), transparent 60%),
                linear-gradient(135deg, #0a1e2a, #0f0f1e);
    border-color: rgba(6,182,212,0.6);
    box-shadow: 0 10px 30px rgba(6,182,212,0.2);
  }
  .sq-support::before { background: conic-gradient(from 0deg, transparent, rgba(34,211,238,0.35), transparent, rgba(6,182,212,0.3), transparent); animation-duration: 7s; }
  .sq-support:hover { border-color: rgba(34,211,238,0.95); box-shadow: 0 18px 45px rgba(6,182,212,0.45); }
  .sq-support .sq-title { color: #a5f3fc; }

  .sq-badge {
    position: absolute;
    top: 8px; right: 8px;
    background: #ef4444; color: #fff;
    font-size: 10px; font-weight: 900;
    padding: 2px 8px;
    border-radius: 999px;
    box-shadow: 0 3px 10px rgba(239,68,68,0.6);
    animation: pulseBadge 2s infinite;
    z-index: 3;
  }
  @keyframes pulseBadge { 0%,100% { transform: scale(1); } 50% { transform: scale(1.18); } }

  /* ============ CIRCLE BUTTONS (top players + shop) ============ */
  .circle-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    padding: 4px 0;
  }
  .circle-btn {
    width: 82px; height: 82px;
    border-radius: 50%;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 2px;
    text-decoration: none;
    color: #fff;
    border: 2.5px solid;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    font-family: inherit;
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
  .circle-btn:hover { transform: translateY(-3px) scale(1.08); }

  .circle-top {
    border-color: #f4c542;
    background: radial-gradient(circle at 30% 30%, rgba(244,197,66,0.35), rgba(234,179,8,0.15));
    box-shadow: 0 0 25px rgba(244,197,66,0.4);
  }
  .circle-top::before { background: conic-gradient(from 0deg, transparent, rgba(244,197,66,0.4), transparent, rgba(249,115,22,0.3), transparent); }
  .circle-top:hover { box-shadow: 0 0 45px rgba(244,197,66,0.8); border-color: #fde68a; }
  .circle-top .ci { font-size: 32px; filter: drop-shadow(0 0 10px rgba(244,197,66,0.9)); }
  .circle-top .cl { font-size: 10px; font-weight: 900; color: #fde68a; }

  .circle-shop {
    border-color: rgba(34,197,94,0.7);
    background: radial-gradient(circle at 30% 30%, rgba(34,197,94,0.3), rgba(6,182,212,0.15));
    box-shadow: 0 0 25px rgba(34,197,94,0.35);
    opacity: 0.7;
    cursor: not-allowed;
    position: relative;
  }
  .circle-shop::before { background: conic-gradient(from 0deg, transparent, rgba(34,197,94,0.4), transparent, rgba(6,182,212,0.3), transparent); }
  .circle-shop .ci { font-size: 32px; filter: drop-shadow(0 0 10px rgba(34,197,94,0.8)); }
  .circle-shop .cl { font-size: 10px; font-weight: 900; color: #86efac; }
  .circle-shop .lock-badge {
    position: absolute;
    bottom: -4px; right: -4px;
    background: linear-gradient(135deg, #eab308, #ca8a04);
    color: #1a1a1a;
    font-size: 9px;
    font-weight: 900;
    padding: 2px 6px;
    border-radius: 6px;
    box-shadow: 0 3px 10px rgba(234,179,8,0.5);
  }
</style>
{% endblock %}

{% block content %}

  <!-- ============ OVAL PROFILE BAR ============ -->
  <div class="oval-profile" id="ovalProfile" onclick="toggleProfile()">
    {% if user.avatar_type == "image" and user.avatar_id %}
      <div class="op-avatar" style="background-image: url('/static/avatars/images/{{ user.avatar_id|stringformat:"03d" }}.jpg');"></div>
    {% else %}
      <div class="op-avatar">{{ avatar_emoji }}</div>
    {% endif %}
    <div class="op-body">
      <div class="op-name">{{ user.alias }}</div>
      <div class="op-meta">
        <span class="lvl">Lv {{ level|default:1 }}</span>
        <span>🪙 {{ user.coins|default:0 }}</span>
        <span>💎 {{ user.gems|default:0 }}</span>
      </div>
    </div>
    <div class="op-chevron">▼</div>
  </div>

  <!-- Expanded profile -->
  <div class="profile-expand" id="profileExpand">
    <div class="pe-inner">
      <div class="pe-head">
        {% if user.avatar_type == "image" and user.avatar_id %}
          <div class="pe-av-big" style="background-image: url('/static/avatars/images/{{ user.avatar_id|stringformat:"03d" }}.jpg');"></div>
        {% else %}
          <div class="pe-av-big">{{ avatar_emoji }}</div>
        {% endif %}
        <div style="flex:1;min-width:0;">
          <div class="pe-name-big">{{ user.alias }}</div>
          <div class="pe-username">@{{ user.username }}</div>
        </div>
      </div>
      <div class="pe-level-wrap">
        <div class="pe-level-info">
          <span class="l">پیشرفت</span>
          <span class="v">{{ level_progress|default:0 }} / 100</span>
        </div>
        <div class="pe-level-bar"><div class="pe-level-fill" style="width: {{ level_progress|default:0 }}%;"></div></div>
      </div>
      <div class="pe-stats">
        <div class="pe-stat"><div class="n">{{ stats.total_games|default:0 }}</div><div class="l">بازی</div></div>
        <div class="pe-stat"><div class="n">{{ stats.total_score|default:0 }}</div><div class="l">امتیاز</div></div>
        <div class="pe-stat"><div class="n">{{ user.coins|default:0 }}</div><div class="l">سکه</div></div>
      </div>
      <a href="/accounts/profile/" class="pe-btn">
        <span>👤</span>
        <span>مشاهده پروفایل کامل</span>
        <span>←</span>
      </a>
    </div>
  </div>

  <!-- ============ TIP ============ -->
  <div class="tip-card">
    <span class="ti">💡</span>
    <div class="tb"><b>نکته امروز:</b> توی بازی گروهی، با هم‌تیمی هماهنگ باش و سریع‌تر استپ بزن!</div>
  </div>

  {% if user.is_guest %}
    <div style="background: rgba(234,179,8,0.15); border: 1px solid rgba(234,179,8,0.35); border-radius: 14px; padding: 12px 16px; margin-bottom: 16px; display: flex; align-items: center; gap: 10px;">
      <span style="font-size: 24px;">🎲</span>
      <div style="flex: 1; font-size: 12px; color: #fde68a; line-height: 1.5;">
        <b>حساب مهمان</b><br>برای ذخیره دائمی، حساب بساز
      </div>
      <a href="/accounts/register/" style="background: rgba(244,197,66,0.9); color: #1a1a1a; padding: 8px 14px; border-radius: 10px; font-size: 11px; font-weight: 900; text-decoration: none; white-space: nowrap;">ثبت‌نام</a>
    </div>
  {% endif %}

  <!-- ============ 3 SQUARE TILES ============ -->
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
      <div class="sq-sub">۸ حالت</div>
    </a>

    <button class="sq-tile sq-support" onclick="openSupport()">
      <div class="sq-icon">💬</div>
      <div class="sq-title">پشتیبانی</div>
      <div class="sq-sub">در تماس باش</div>
    </button>
  </div>

  <!-- ============ CIRCLES: TOP PLAYERS + SHOP ============ -->
  <div class="section-label">🌟 سایر</div>

  <div class="circle-col">
    <a href="/game/top-players/" class="circle-btn circle-top" title="بازیکنان برتر">
      <div class="ci">⭐</div>
      <div class="cl">برتر</div>
    </a>
    <div class="circle-btn circle-shop" title="فروشگاه (به زودی)">
      <div class="ci">🛒</div>
      <div class="cl">فروش</div>
      <span class="lock-badge">🔒 به زودی</span>
    </div>
  </div>

{% endblock %}

{% block extra_js %}
<script>
  function toggleProfile() {
    const oval = document.getElementById('ovalProfile');
    const expand = document.getElementById('profileExpand');
    const isOpen = expand.classList.toggle('open');
    oval.classList.toggle('expanded', isOpen);
    if (window.vibrate) window.vibrate(8);
    if (window.soundClick) window.soundClick();
  }

  function openSupport() {
    alert('📬 پشتیبانی:\\n\\n📧 support@esmfamil.com\\n💬 @esmfamil_support');
    if (window.soundClick) window.soundClick();
  }
</script>
{% endblock %}
''')

# ============================================================
# 2) ADMIN LIVE GAMES — better view
# ============================================================
print("\n[2/6] Admin live games redesign")
write("accounts/templates/custom_admin/rooms.html", '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>اتاق‌ها — پنل ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 1400px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; }
    .topbar h1 { font-size: 20px; color: #fca5a5; }
    .topbar a { padding: 9px 16px; border-radius: 10px; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold; }

    .admin-tabs { display: flex; gap: 6px; margin-bottom: 20px; background: #12121f; border: 1px solid rgba(148,163,184,0.15); padding: 6px; border-radius: 14px; overflow-x: auto; }
    .admin-tab { flex: 1; min-width: 100px; padding: 12px 14px; border-radius: 10px; text-align: center; text-decoration: none; font-size: 12px; font-weight: bold; color: #94a3b8; transition: 0.2s; white-space: nowrap; }
    .admin-tab:hover { background: rgba(148,163,184,0.1); color: #fff; }
    .admin-tab.active { background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; box-shadow: 0 6px 20px rgba(34,197,94,0.4); }

    /* LIVE HEADER */
    .live-header {
      background: linear-gradient(135deg, rgba(34,197,94,0.15), rgba(6,182,212,0.1));
      border: 2px solid rgba(34,197,94,0.4);
      border-radius: 20px;
      padding: 22px 24px;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      position: relative;
      overflow: hidden;
    }
    .live-header::before {
      content: "";
      position: absolute;
      top: 0; left: -100%; width: 100%; height: 100%;
      background: linear-gradient(90deg, transparent, rgba(34,197,94,0.15), transparent);
      animation: sweep 3s infinite;
    }
    @keyframes sweep { 0% { left: -100%; } 100% { left: 100%; } }
    .live-header > * { position: relative; z-index: 1; }
    .live-dot-pulse {
      width: 14px; height: 14px;
      border-radius: 50%;
      background: #22c55e;
      box-shadow: 0 0 15px #22c55e;
      animation: pulse 1.5s infinite;
      flex-shrink: 0;
    }
    @keyframes pulse { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.4); opacity: 0.6; } }
    .live-title { font-size: 18px; font-weight: 900; color: #4ade80; margin-bottom: 3px; }
    .live-sub { font-size: 12px; color: #86efac; }
    .live-count { margin-right: auto; font-size: 28px; font-weight: 900; color: #4ade80; font-family: monospace; }

    /* LIVE CARDS */
    .live-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 16px;
    }
    .live-card {
      background: linear-gradient(135deg, #12121f, #1a1a2e);
      border: 1.5px solid rgba(34,197,94,0.35);
      border-radius: 18px;
      padding: 18px;
      position: relative;
      overflow: hidden;
      transition: 0.2s;
    }
    .live-card:hover {
      border-color: rgba(34,197,94,0.8);
      transform: translateY(-3px);
      box-shadow: 0 15px 40px rgba(34,197,94,0.2);
    }
    .live-card::before {
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, #22c55e, #4ade80, #22c55e);
      animation: glow 2s infinite;
    }
    @keyframes glow { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }

    .lc-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
    .lc-icon { width: 50px; height: 50px; border-radius: 14px; background: linear-gradient(135deg, rgba(34,197,94,0.3), rgba(6,182,212,0.2)); display: flex; align-items: center; justify-content: center; font-size: 26px; flex-shrink: 0; border: 1px solid rgba(34,197,94,0.3); }
    .lc-info { flex: 1; min-width: 0; }
    .lc-title { font-size: 15px; font-weight: 900; color: #fff; margin-bottom: 3px; }
    .lc-meta { font-size: 11px; color: #94a3b8; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
    .lc-code { font-family: monospace; background: rgba(34,197,94,0.15); color: #4ade80; padding: 2px 8px; border-radius: 6px; font-weight: bold; }

    /* Players in live game */
    .players-live {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
      padding: 10px;
      background: rgba(15,23,42,0.6);
      border-radius: 12px;
    }
    .player-chip {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 5px 10px;
      background: rgba(34,197,94,0.12);
      border: 1px solid rgba(34,197,94,0.3);
      border-radius: 999px;
      font-size: 11px;
      font-weight: bold;
    }
    .player-chip .pc-av {
      width: 20px; height: 20px;
      border-radius: 50%;
      background: rgba(15,23,42,0.7);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      background-size: cover;
      background-position: center;
    }
    .player-chip .pc-name { color: #fff; }
    .player-chip .pc-score { color: #4ade80; font-family: monospace; font-weight: 900; }

    /* Game stats */
    .live-stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin-bottom: 12px;
    }
    .ls-item {
      padding: 8px 6px;
      background: rgba(15,23,42,0.5);
      border-radius: 10px;
      text-align: center;
    }
    .ls-item .l { font-size: 9px; color: #64748b; margin-bottom: 2px; }
    .ls-item .v { font-size: 14px; font-weight: 900; color: #facc15; font-family: monospace; }
    .ls-item .v.green { color: #4ade80; }
    .ls-item .v.red { color: #f87171; }

    /* Letter + Timer */
    .letter-box {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      background: linear-gradient(135deg, rgba(244,197,66,0.15), rgba(234,179,8,0.08));
      border: 1px solid rgba(244,197,66,0.3);
      border-radius: 12px;
      margin-bottom: 12px;
    }
    .letter-box .lr-letter {
      width: 44px; height: 44px;
      border-radius: 12px;
      background: radial-gradient(circle, rgba(244,197,66,0.4), rgba(234,179,8,0.15));
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      font-weight: 900;
      color: #fde68a;
      font-family: monospace;
      box-shadow: 0 0 15px rgba(244,197,66,0.4);
    }
    .letter-box .lr-info { flex: 1; }
    .letter-box .lr-title { font-size: 11px; color: #94a3b8; margin-bottom: 2px; }
    .letter-box .lr-round { font-size: 14px; font-weight: 900; color: #fde68a; }

    /* Actions */
    .lc-actions { display: flex; gap: 8px; }
    .lc-actions a, .lc-actions button { flex: 1; padding: 9px; border-radius: 9px; border: none; font-family: inherit; font-weight: bold; font-size: 12px; cursor: pointer; text-align: center; text-decoration: none; }
    .btn-kill { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3) !important; }
    .btn-kill:hover { background: rgba(239,68,68,0.3); }

    /* EMPTY STATE */
    .empty-live {
      text-align: center;
      padding: 80px 20px;
      background: linear-gradient(135deg, #12121f, #1a1a2e);
      border: 2px dashed rgba(148,163,184,0.2);
      border-radius: 20px;
    }
    .empty-live .icon { font-size: 80px; margin-bottom: 16px; display: block; opacity: 0.5; }
    .empty-live h3 { font-size: 20px; color: #94a3b8; margin-bottom: 8px; }
    .empty-live p { font-size: 13px; color: #64748b; line-height: 1.6; }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }

    /* OTHER ROOMS (when not live tab) */
    .table-wrap { background: #12121f; border: 1px solid rgba(148,163,184,0.12); border-radius: 16px; overflow: auto; }
    table { width: 100%; border-collapse: collapse; min-width: 950px; }
    th { background: rgba(30,41,59,0.7); padding: 14px 12px; text-align: right; font-size: 12px; color: #94a3b8; font-weight: bold; white-space: nowrap; border-bottom: 1px solid rgba(148,163,184,0.15); }
    td { padding: 12px; text-align: right; font-size: 13px; border-bottom: 1px solid rgba(148,163,184,0.08); white-space: nowrap; }
    tr:hover td { background: rgba(244,197,66,0.03); }
    .code-txt { font-family: monospace; font-weight: bold; color: #facc15; }
    .username { font-family: monospace; color: #94a3b8; }
    .status-badge { padding: 3px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; }
    .st-waiting { background: rgba(234,179,8,0.15); color: #fde68a; }
    .st-in_round { background: rgba(34,197,94,0.15); color: #4ade80; animation: pulse 2s infinite; }
    .st-finished { background: rgba(100,116,139,0.15); color: #cbd5e1; }
    .btn-del-small { padding: 6px 10px; border-radius: 6px; background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); font-family: inherit; font-size: 11px; font-weight: bold; cursor: pointer; }
    .filter-row { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
    .filter-row input, .filter-row select { padding: 12px 16px; border-radius: 12px; border: 1px solid rgba(148,163,184,0.2); background: #1a1a2e; color: #fff; font-size: 14px; font-family: inherit; }
    .filter-row input { flex: 1; min-width: 200px; }
    .filter-row button { padding: 12px 22px; border-radius: 12px; border: none; background: linear-gradient(135deg, #facc15, #eab308); color: #1a1a1a; font-weight: bold; font-size: 14px; font-family: inherit; cursor: pointer; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>🚪 مدیریت اتاق‌ها</h1>
    <a href="{% url 'custom_admin:logout' %}">خروج</a>
  </div>

  <div class="admin-tabs">
    <a href="/panel-admin/dashboard/" class="admin-tab">👥 کاربران</a>
    <a href="/panel-admin/alliances/" class="admin-tab">🛡️ اتحادها</a>
    <a href="/panel-admin/rooms/" class="admin-tab {% if status_filter != 'in_round' %}active{% endif %}">🚪 اتاق‌ها</a>
    <a href="/panel-admin/rooms/active/" class="admin-tab {% if status_filter == 'in_round' %}active{% endif %}">🎮 در حال بازی</a>
    <a href="/panel-admin/announcements/" class="admin-tab">📢 اعلان‌ها</a>
    <a href="/panel-admin/tournaments/" class="admin-tab">🏆 تورنمنت‌ها</a>
    <a href="/panel-admin/shop/" class="admin-tab">🛒 فروشگاه</a>
  </div>

  {% if message %}<div class="msg msg-success">{{ message.text }}</div>{% endif %}

  {% if status_filter == 'in_round' %}
    <!-- LIVE VIEW -->
    <div class="live-header">
      <div class="live-dot-pulse"></div>
      <div>
        <div class="live-title">بازی‌های زنده</div>
        <div class="live-sub">در حال حاضر این بازی‌ها در جریان هستند</div>
      </div>
      <div class="live-count">{{ rooms|length }}</div>
    </div>

    {% if rooms %}
      <div class="live-grid">
        {% for r in rooms %}
          <div class="live-card">
            <div class="lc-head">
              <div class="lc-icon">🎮</div>
              <div class="lc-info">
                <div class="lc-title">{{ r.room_name }}</div>
                <div class="lc-meta">
                  <span class="lc-code">#{{ r.code }}</span>
                  <span>{{ r.mode }}</span>
                </div>
              </div>
            </div>

            {% if r.players %}
              <div class="players-live">
                {% for p in r.players %}
                  <div class="player-chip">
                    <div class="pc-av">{{ p.avatar }}</div>
                    <span class="pc-name">{{ p.alias }}</span>
                    <span class="pc-score">{{ p.score }}</span>
                  </div>
                {% endfor %}
              </div>
            {% endif %}

            <div class="live-stats">
              <div class="ls-item">
                <div class="l">بازیکنان</div>
                <div class="v">{{ r.players_count }}/{{ r.max_players }}</div>
              </div>
              <div class="ls-item">
                <div class="l">راند</div>
                <div class="v">{{ r.current_round|default:"-" }}</div>
              </div>
              <div class="ls-item">
                <div class="l">حرف</div>
                <div class="v">{{ r.current_letter|default:"-" }}</div>
              </div>
            </div>

            {% if r.current_round %}
              <div class="letter-box">
                <div class="lr-letter">{{ r.current_letter }}</div>
                <div class="lr-info">
                  <div class="lr-title">راند فعلی</div>
                  <div class="lr-round">{{ r.current_round }}</div>
                </div>
              </div>
            {% endif %}

            <div class="lc-actions">
              <form method="post" action="{% url 'custom_admin:room_delete' r.id %}" style="display:contents;" onsubmit="return confirm('حذف بازی {{ r.code }}؟');">
                {% csrf_token %}
                <button type="submit" class="btn-kill">🗑️ حذف اتاق</button>
              </form>
            </div>
          </div>
        {% endfor %}
      </div>
    {% else %}
      <div class="empty-live">
        <span class="icon">🎮</span>
        <h3>هیچ بازی زنده‌ای نیست</h3>
        <p>وقتی بازی‌ای شروع بشه، اینجا نمایش داده می‌شه</p>
      </div>
    {% endif %}
  {% else %}
    <!-- LIST ALL ROOMS -->
    <div class="filter-row">
      <form method="get" class="filter-row" style="flex:1; margin:0;">
        <input type="text" name="q" value="{{ search }}" placeholder="جستجو...">
        <select name="status">
          <option value="">همه</option>
          <option value="waiting" {% if status_filter == "waiting" %}selected{% endif %}>در انتظار</option>
          <option value="in_round" {% if status_filter == "in_round" %}selected{% endif %}>در حال بازی</option>
          <option value="finished" {% if status_filter == "finished" %}selected{% endif %}>تمام‌شده</option>
        </select>
        <button type="submit">🔍 فیلتر</button>
      </form>
    </div>

    {% if rooms %}
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>#</th><th>کد</th><th>اسم</th><th>حالت</th><th>وضعیت</th><th>میزبان</th><th>بازیکنان</th><th>تاریخ</th><th>عملیات</th></tr>
          </thead>
          <tbody>
            {% for r in rooms %}
              <tr>
                <td>{{ forloop.counter }}</td>
                <td><span class="code-txt">{{ r.code }}</span></td>
                <td>{{ r.room_name }}</td>
                <td>{{ r.mode }}</td>
                <td><span class="status-badge st-{{ r.status }}">{{ r.status }}</span></td>
                <td>{{ r.host }} <span class="username">@{{ r.host_username }}</span></td>
                <td>{{ r.players_count }}/{{ r.max_players }}</td>
                <td style="font-size:11px; color:#64748b;">{{ r.created_at|jdate:"Y/m/d H:i" }}</td>
                <td>
                  <form method="post" action="{% url 'custom_admin:room_delete' r.id %}" style="display:inline;" onsubmit="return confirm('حذف؟');">
                    {% csrf_token %}
                    <button type="submit" class="btn-del-small">🗑️</button>
                  </form>
                </td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    {% else %}
      <div class="empty-live">
        <span class="icon">🚪</span>
        <h3>هیچ اتاقی نیست</h3>
      </div>
    {% endif %}
  {% endif %}
</div>
</body>
</html>
''')

# Update rooms_active view to include player info
print("\n[2b/6] Update rooms_active to include players")
p = "accounts/admin_views.py"
src = read(p)

if "def rooms_active(request):" in src:
    import re
    old = re.search(r'@never_cache\ndef rooms_active\(request\):.*?(?=\n@never_cache|\ndef |\Z)', src, re.DOTALL)
    if old:
        new_fn = '''@never_cache
def rooms_active(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    from game.models import Game
    from accounts.avatars import get_emoji

    qs = Game.objects.filter(status="in_round").order_by("-created_at")
    data = []
    for g in qs:
        active_round = g.rounds.order_by("-number").first()
        # Get players with their scores
        players = []
        for p in g.players.select_related("user").all():
            players.append({
                "alias": p.user.alias,
                "avatar": get_emoji(p.user.avatar_id),
                "score": p.score,
                "username": p.user.username,
            })
        data.append({
            "id": str(g.id),
            "code": g.code,
            "room_name": g.room_name or "—",
            "mode": g.mode,
            "status": g.status,
            "host": g.host.alias,
            "host_username": g.host.username,
            "players_count": g.players.count(),
            "max_players": g.max_players,
            "created_at": g.created_at,
            "has_password": bool(g.password),
            "current_round": active_round.number if active_round else None,
            "current_letter": active_round.letter if active_round else None,
            "players": players,
        })
    return render(request, "custom_admin/rooms.html", {
        "rooms": data, "search": "", "status_filter": "in_round", "message": None,
    })
'''
        src = src[:old.start()] + new_fn + src[old.end():]
        write(p, src)
        print("  ✓ rooms_active view updated")

# ============================================================
# 3) PUZZLE GAME — append views + url + template
# ============================================================
print("\n[3/6] Puzzle game")

p = "game/views.py"
src = read(p)

if "def puzzle_home" not in src:
    PUZZLE_CODE = '''

# ============================================================
# Puzzle Game — guess the word from clue
# ============================================================
import random as _rand
from django.http import JsonResponse as _JsonResponse

_PUZZLE_WORDS = [
    {"word": "خورشید", "clue": "تو آسمون می‌درخشه، روز رو روشن می‌کنه", "cat": "طبیعت"},
    {"word": "کتاب", "clue": "صفحات داره، کلمه‌ها توشه، می‌خونیمش", "cat": "اشیا"},
    {"word": "پروانه", "clue": "بال داره، رنگی رنگی، روی گل‌ها می‌شینه", "cat": "حیوان"},
    {"word": "باران", "clue": "از آسمون میاد، زمین رو خیس می‌کنه", "cat": "طبیعت"},
    {"word": "آینه", "clue": "تصویرت رو نشون می‌ده، شیشه‌ایه", "cat": "اشیا"},
    {"word": "ماهی", "clue": "توی آب زندگی می‌کنه، شنا می‌کنه", "cat": "حیوان"},
    {"word": "درخت", "clue": "تنه داره، برگ داره، سایه می‌ندازه", "cat": "طبیعت"},
    {"word": "آبشار", "clue": "از بلندی می‌ریزه، صدای شلپ شلپ", "cat": "طبیعت"},
    {"word": "ستاره", "clue": "شب‌ها می‌درخشه، توی آسمون", "cat": "طبیعت"},
    {"word": "قلب", "clue": "داخل سینه، می‌تپه، قرمز", "cat": "بدن"},
    {"word": "پرواز", "clue": "بالا رفتن توی هوا، هواپیما می‌کنه", "cat": "عمل"},
    {"word": "ساعت", "clue": "عقربه داره، زمان رو نشون می‌ده", "cat": "اشیا"},
    {"word": "آشپز", "clue": "غذا درست می‌کنه، آشپزخونه کارشه", "cat": "شغل"},
    {"word": "کوه", "clue": "بلنده، سنگه، صعود سخت", "cat": "طبیعت"},
    {"word": "شیرین", "clue": "مزه‌ی عسل و شکره", "cat": "مزه"},
]

@login_required
def puzzle_home(request):
    check = _require_complete(request.user)
    if check:
        return check

    if request.method == "POST":
        # New puzzle
        puzzle = _rand.choice(_PUZZLE_WORDS)
        request.session["puzzle_word"] = puzzle["word"]
        request.session["puzzle_clue"] = puzzle["clue"]
        request.session["puzzle_cat"] = puzzle["cat"]
        request.session["puzzle_tries"] = 0
        request.session["puzzle_max"] = 5
        request.session["puzzle_finished"] = False
        return redirect("game:puzzle")

    # If no puzzle yet, start one
    if "puzzle_word" not in request.session:
        puzzle = _rand.choice(_PUZZLE_WORDS)
        request.session["puzzle_word"] = puzzle["word"]
        request.session["puzzle_clue"] = puzzle["clue"]
        request.session["puzzle_cat"] = puzzle["cat"]
        request.session["puzzle_tries"] = 0
        request.session["puzzle_max"] = 5
        request.session["puzzle_finished"] = False

    return render(request, "game/puzzle.html", {
        "clue": request.session.get("puzzle_clue"),
        "cat": request.session.get("puzzle_cat"),
        "tries": request.session.get("puzzle_tries", 0),
        "max_tries": request.session.get("puzzle_max", 5),
        "finished": request.session.get("puzzle_finished", False),
        "won": request.session.get("puzzle_won", False),
        "word": request.session.get("puzzle_word", "") if request.session.get("puzzle_finished") else "",
        "active": "games",
    })


@login_required
def puzzle_guess(request):
    check = _require_complete(request.user)
    if check:
        return check

    if request.method != "POST":
        return redirect("game:puzzle")

    guess = (request.POST.get("guess") or "").strip().replace("ي", "ی").replace("ك", "ک")
    word = request.session.get("puzzle_word", "").replace("ي", "ی").replace("ك", "ک")

    if not guess or not word:
        return redirect("game:puzzle")

    tries = request.session.get("puzzle_tries", 0) + 1
    max_tries = request.session.get("puzzle_max", 5)

    if guess == word:
        request.session["puzzle_won"] = True
        request.session["puzzle_finished"] = True
        request.session["puzzle_tries"] = tries
        messages.success(request, f"🎉 آفرین! توی {tries} تلاش درست حدس زدی.")
    elif tries >= max_tries:
        request.session["puzzle_won"] = False
        request.session["puzzle_finished"] = True
        request.session["puzzle_tries"] = tries
        messages.error(request, f"❌ تموم شد! کلمه «{word}» بود.")
    else:
        request.session["puzzle_tries"] = tries
        messages.info(request, f"❌ نه! {max_tries - tries} تلاش دیگه داری.")

    return redirect("game:puzzle")
'''
    src = src.rstrip() + PUZZLE_CODE + "\n"
    write(p, src)
    print("  ✓ puzzle views added")

# Add routes
p = "game/urls.py"
src = read(p)
if "puzzle" not in src:
    if '    path("challenge/", views.challenge_home, name="challenge"),' in src:
        src = src.replace(
            '    path("challenge/", views.challenge_home, name="challenge"),',
            '    path("challenge/", views.challenge_home, name="challenge"),\n    path("puzzle/", views.puzzle_home, name="puzzle"),\n    path("puzzle/guess/", views.puzzle_guess, name="puzzle_guess"),'
        )
    write(p, src)
    print("  ✓ puzzle routes added")

# Puzzle template
write("game/templates/game/puzzle.html", '''{% extends "base.html" %}
{% block title %}بازی معما{% endblock %}
{% block extra_css %}
<style>
  .head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
  .head h1 { font-size: 24px; font-weight: 900; background: linear-gradient(135deg, #4ade80, #16a34a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  
  .clue-box {
    background: radial-gradient(circle at 100% 0%, rgba(34,197,94,0.3), transparent 60%),
                linear-gradient(135deg, #0a2a1a, #0f0f1e);
    border: 2px solid rgba(34,197,94,0.5);
    border-radius: 22px;
    padding: 26px 22px;
    margin-bottom: 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 15px 40px rgba(34,197,94,0.15);
  }
  .clue-box::before {
    content: "";
    position: absolute;
    inset: -100%;
    background: conic-gradient(from 0deg, transparent, rgba(74,222,128,0.15), transparent, rgba(16,185,129,0.15), transparent);
    animation: spin 10s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .clue-box > * { position: relative; z-index: 1; }
  .clue-cat {
    display: inline-block;
    background: rgba(34,197,94,0.2);
    color: #86efac;
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 900;
    margin-bottom: 12px;
    border: 1px solid rgba(34,197,94,0.4);
  }
  .clue-icon { font-size: 56px; margin-bottom: 8px; }
  .clue-text {
    font-size: 17px;
    color: #fff;
    line-height: 1.8;
    font-weight: bold;
  }
  
  .tries-info {
    display: flex;
    justify-content: center;
    gap: 6px;
    margin-top: 18px;
  }
  .tries-dot {
    width: 24px; height: 8px;
    border-radius: 4px;
    background: rgba(148,163,184,0.2);
  }
  .tries-dot.used { background: linear-gradient(90deg, #ef4444, #dc2626); box-shadow: 0 0 8px rgba(239,68,68,0.5); }
  .tries-dot.left { background: linear-gradient(90deg, #22c55e, #16a34a); box-shadow: 0 0 8px rgba(34,197,94,0.5); }
  
  .guess-form {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 16px;
  }
  .guess-input {
    width: 100%;
    padding: 18px;
    border-radius: 14px;
    border: 2px solid rgba(34,197,94,0.4);
    background: rgba(15,23,42,0.8);
    color: #fff;
    font-size: 20px;
    font-family: inherit;
    text-align: center;
    font-weight: bold;
    margin-bottom: 12px;
    box-sizing: border-box;
  }
  .guess-input:focus { outline: none; border-color: #4ade80; box-shadow: 0 0 20px rgba(34,197,94,0.3); }
  
  .btn-guess {
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 14px;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: #fff;
    font-size: 17px;
    font-weight: 900;
    font-family: inherit;
    cursor: pointer;
    box-shadow: 0 10px 30px rgba(34,197,94,0.4);
    transition: 0.2s;
  }
  .btn-guess:hover { transform: translateY(-2px); }
  
  .finished-box {
    text-align: center;
    padding: 30px 20px;
    border-radius: 20px;
    margin-bottom: 16px;
  }
  .finished-box.won { background: rgba(34,197,94,0.15); border: 2px solid rgba(34,197,94,0.4); }
  .finished-box.lost { background: rgba(239,68,68,0.15); border: 2px solid rgba(239,68,68,0.4); }
  .finished-box .fi { font-size: 60px; margin-bottom: 10px; }
  .finished-box .ft { font-size: 20px; font-weight: 900; margin-bottom: 6px; }
  .finished-box.won .ft { color: #4ade80; }
  .finished-box.lost .ft { color: #f87171; }
  .finished-box .fw { font-size: 15px; color: #fff; font-family: monospace; letter-spacing: 2px; }
  
  .btn-new {
    display: block;
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 14px;
    background: linear-gradient(135deg, #f4c542, #eab308);
    color: #1a1a1a;
    font-size: 16px;
    font-weight: 900;
    font-family: inherit;
    cursor: pointer;
    text-decoration: none;
    text-align: center;
    box-shadow: 0 10px 30px rgba(244,197,66,0.4);
    margin-top: 12px;
  }
</style>
{% endblock %}
{% block content %}
  <div class="head">
    <a href="/game/rooms/" class="back-btn"><span class="arrow-icon">→</span></a>
    <h1>🎯 بازی معما</h1>
  </div>

  <div class="clue-box">
    <div class="clue-cat">{{ cat }}</div>
    <div class="clue-icon">🎯</div>
    <div class="clue-text">{{ clue }}</div>
    <div class="tries-info">
      {% for i in "12345" %}
        {% if forloop.counter0 < tries %}
          <div class="tries-dot used"></div>
        {% elif not finished %}
          <div class="tries-dot left"></div>
        {% else %}
          <div class="tries-dot"></div>
        {% endif %}
      {% endfor %}
    </div>
  </div>

  {% if finished %}
    <div class="finished-box {% if won %}won{% else %}lost{% endif %}">
      <div class="fi">{% if won %}🎉{% else %}😢{% endif %}</div>
      <div class="ft">{% if won %}آفرین! درست حدس زدی{% else %}تموم شد!{% endif %}</div>
      <div class="fw">کلمه: {{ word }}</div>
    </div>
    <form method="post">
      {% csrf_token %}
      <button type="submit" class="btn-new">🔄 معمای جدید</button>
    </form>
  {% else %}
    <form method="post" action="/game/puzzle/guess/" class="guess-form">
      {% csrf_token %}
      <input type="text" name="guess" class="guess-input" placeholder="کلمه رو حدس بزن..." autocomplete="off" autofocus maxlength="30">
      <button type="submit" class="btn-guess">🎯 حدس بزن</button>
    </form>
  {% endif %}
{% endblock %}
''')

# ============================================================
# 4) 0-100 GAME — bot mode
# ============================================================
print("\n[4/6] 0-100 game")

p = "game/views.py"
src = read(p)

if "def guess_home" not in src:
    GUESS_CODE = '''

# ============================================================
# 0-100 Guess Game
# ============================================================
@login_required
def guess_home(request):
    check = _require_complete(request.user)
    if check:
        return check

    # Start new game
    if request.method == "POST" and request.POST.get("action") == "new":
        _start_guess_game(request)
        return redirect("game:guess")

    # Start if none
    if "guess_number" not in request.session:
        _start_guess_game(request)

    return render(request, "game/guess.html", {
        "tries": request.session.get("guess_tries", 0),
        "max_tries": request.session.get("guess_max", 7),
        "finished": request.session.get("guess_finished", False),
        "won": request.session.get("guess_won", False),
        "number": request.session.get("guess_number") if request.session.get("guess_finished") else None,
        "history": request.session.get("guess_history", []),
        "active": "games",
    })


def _start_guess_game(request):
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
    src = src.rstrip() + GUESS_CODE + "\n"
    write(p, src)
    print("  ✓ guess views added")

# Routes
p = "game/urls.py"
src = read(p)
if "guess" not in src:
    if '    path("puzzle/", views.puzzle_home, name="puzzle"),' in src:
        src = src.replace(
            '    path("puzzle/", views.puzzle_home, name="puzzle"),\n    path("puzzle/guess/", views.puzzle_guess, name="puzzle_guess"),',
            '    path("puzzle/", views.puzzle_home, name="puzzle"),\n    path("puzzle/guess/", views.puzzle_guess, name="puzzle_guess"),\n    path("guess/", views.guess_home, name="guess"),\n    path("guess/attempt/", views.guess_attempt, name="guess_attempt"),'
        )
    write(p, src)
    print("  ✓ guess routes added")

# Guess template
write("game/templates/game/guess.html", '''{% extends "base.html" %}
{% block title %}بازی ۰ تا ۱۰۰{% endblock %}
{% block extra_css %}
<style>
  .head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
  .head h1 { font-size: 24px; font-weight: 900; background: linear-gradient(135deg, #06b6d4, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }

  .hero {
    background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.3), transparent 60%),
                linear-gradient(135deg, #0a1e2a, #0f0f1e);
    border: 2px solid rgba(6,182,212,0.5);
    border-radius: 22px;
    padding: 26px 22px;
    margin-bottom: 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 15px 40px rgba(6,182,212,0.15);
  }
  .hero::before {
    content: "";
    position: absolute;
    inset: -100%;
    background: conic-gradient(from 0deg, transparent, rgba(34,211,238,0.15), transparent, rgba(6,182,212,0.15), transparent);
    animation: spin 12s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .hero > * { position: relative; z-index: 1; }
  .hero-icon { font-size: 64px; margin-bottom: 10px; filter: drop-shadow(0 0 20px rgba(6,182,212,0.6)); }
  .hero-title { font-size: 20px; font-weight: 900; color: #a5f3fc; margin-bottom: 6px; }
  .hero-desc { font-size: 13px; color: #94a3b8; line-height: 1.6; }

  .tries-info {
    display: flex; justify-content: center; gap: 6px;
    margin-top: 18px;
  }
  .tries-dot {
    width: 24px; height: 8px; border-radius: 4px;
    background: rgba(148,163,184,0.2);
  }
  .tries-dot.used { background: linear-gradient(90deg, #ef4444, #dc2626); box-shadow: 0 0 8px rgba(239,68,68,0.5); }
  .tries-dot.left { background: linear-gradient(90deg, #22c55e, #16a34a); box-shadow: 0 0 8px rgba(34,197,94,0.5); }

  .history {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 16px;
    max-height: 220px;
    overflow-y: auto;
  }
  .history-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-radius: 10px;
    margin-bottom: 6px;
    background: rgba(15,23,42,0.5);
    border: 1px solid rgba(148,163,184,0.1);
    font-size: 13px;
  }
  .history-item .num {
    font-family: monospace;
    font-weight: 900;
    color: #fff;
    width: 40px;
    text-align: center;
  }
  .history-item .arrow { font-size: 18px; }
  .history-item.low { border-color: rgba(34,197,94,0.3); background: rgba(34,197,94,0.08); }
  .history-item.low .arrow { color: #4ade80; }
  .history-item.high { border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.08); }
  .history-item.high .arrow { color: #f87171; }
  .history-item.win { border-color: rgba(244,197,66,0.5); background: rgba(244,197,66,0.15); }
  .history-item.win .arrow { color: #fde68a; }
  .history-item .hint { font-size: 11px; color: #94a3b8; }

  .input-form {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 22px;
  }
  .input-form input[type=number] {
    width: 100%;
    padding: 20px;
    border-radius: 14px;
    border: 2px solid rgba(6,182,212,0.4);
    background: rgba(15,23,42,0.8);
    color: #fff;
    font-size: 32px;
    font-family: monospace;
    text-align: center;
    font-weight: 900;
    margin-bottom: 14px;
    box-sizing: border-box;
    -moz-appearance: textfield;
  }
  .input-form input[type=number]::-webkit-outer-spin-button,
  .input-form input[type=number]::-webkit-inner-spin-button {
    -webkit-appearance: none; margin: 0;
  }
  .input-form input:focus { outline: none; border-color: #22d3ee; box-shadow: 0 0 25px rgba(6,182,212,0.3); }
  .btn-guess {
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 14px;
    background: linear-gradient(135deg, #06b6d4, #3b82f6);
    color: #fff;
    font-size: 17px;
    font-weight: 900;
    font-family: inherit;
    cursor: pointer;
    box-shadow: 0 10px 30px rgba(6,182,212,0.4);
    transition: 0.2s;
  }
  .btn-guess:hover { transform: translateY(-2px); }

  .finished-box {
    text-align: center;
    padding: 30px 20px;
    border-radius: 20px;
    margin-bottom: 16px;
  }
  .finished-box.won { background: rgba(34,197,94,0.15); border: 2px solid rgba(34,197,94,0.4); }
  .finished-box.lost { background: rgba(239,68,68,0.15); border: 2px solid rgba(239,68,68,0.4); }
  .finished-box .fi { font-size: 60px; margin-bottom: 10px; }
  .finished-box .ft { font-size: 20px; font-weight: 900; margin-bottom: 6px; }
  .finished-box.won .ft { color: #4ade80; }
  .finished-box.lost .ft { color: #f87171; }
  .finished-box .fw { font-size: 16px; color: #fff; font-family: monospace; }

  .btn-new {
    display: block; width: 100%; padding: 16px;
    border: none; border-radius: 14px;
    background: linear-gradient(135deg, #f4c542, #eab308);
    color: #1a1a1a; font-size: 16px; font-weight: 900;
    font-family: inherit; cursor: pointer;
    text-decoration: none; text-align: center;
    box-shadow: 0 10px 30px rgba(244,197,66,0.4);
    margin-top: 12px;
  }
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
        {% if forloop.counter0 < tries %}
          <div class="tries-dot used"></div>
        {% elif not finished %}
          <div class="tries-dot left"></div>
        {% else %}
          <div class="tries-dot"></div>
        {% endif %}
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
            <div class="arrow">
              {% if h.result == 'win' %}🎯{% elif h.result == 'low' %}⬆️{% else %}⬇️{% endif %}
            </div>
            <div class="hint">
              {% if h.result == 'win' %}درسته!
              {% elif h.result == 'low' %}برو بالاتر
              {% else %}بیا پایین‌تر{% endif %}
            </div>
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

# ============================================================
# 5) Update rooms.html to add puzzle + guess
# ============================================================
print("\n[5/6] Update rooms.html to add new games")
p = "game/templates/game/rooms.html"
src = read(p)

if "/game/puzzle/" not in src or "/game/guess/" not in src:
    # Rebuild rooms.html
    write(p, '''{% extends "base.html" %}
{% block title %}بازی‌ها{% endblock %}
{% block extra_css %}
<style>
  .head { margin-bottom: 20px; }
  .head h1 { font-size: 24px; font-weight: 900; background: linear-gradient(135deg, #f4c542, #fdba74); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .big { display: flex; align-items: center; gap: 16px; padding: 22px 20px; border-radius: 24px; text-decoration: none; color: #fff; margin-bottom: 14px; position: relative; overflow: hidden; border: 2px solid; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); isolation: isolate; }
  .big::before { content: ""; position: absolute; inset: -150%; z-index: -1; animation: spin 10s linear infinite; opacity: 0.6; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .big:hover { transform: translateY(-4px) scale(1.01); }
  .big:active { transform: scale(0.98); }
  .big.bot { background: linear-gradient(135deg, #2a1a0e, #1a0f08); border-color: rgba(244,197,66,0.55); box-shadow: 0 15px 40px rgba(244,197,66,0.2); }
  .big.bot::before { background: conic-gradient(from 0deg, transparent, rgba(244,197,66,0.25), transparent, rgba(249,115,22,0.25), transparent); }
  .big.bot:hover { border-color: rgba(251,211,77,0.95); box-shadow: 0 20px 60px rgba(244,197,66,0.4); }
  .big.player { background: linear-gradient(135deg, #0a1a2a, #080f18); border-color: rgba(59,130,246,0.55); box-shadow: 0 15px 40px rgba(59,130,246,0.2); }
  .big.player::before { background: conic-gradient(from 0deg, transparent, rgba(96,165,250,0.3), transparent, rgba(139,92,246,0.25), transparent); }
  .big.player:hover { border-color: rgba(96,165,250,0.95); box-shadow: 0 20px 60px rgba(59,130,246,0.4); }
  .big.group { background: linear-gradient(135deg, #1a0f2e, #120824); border-color: rgba(139,92,246,0.6); box-shadow: 0 15px 40px rgba(139,92,246,0.25); }
  .big.group::before { background: conic-gradient(from 0deg, transparent, rgba(167,139,250,0.3), transparent, rgba(236,72,153,0.25), transparent); }
  .big.group:hover { border-color: rgba(167,139,250,0.95); box-shadow: 0 20px 60px rgba(139,92,246,0.45); }
  .big.challenge { background: linear-gradient(135deg, #2a0a0a, #1a0606); border-color: rgba(239,68,68,0.6); box-shadow: 0 15px 40px rgba(239,68,68,0.25); }
  .big.challenge::before { background: conic-gradient(from 0deg, transparent, rgba(248,113,113,0.3), transparent, rgba(249,115,22,0.25), transparent); animation-duration: 4s; }
  .big.challenge:hover { border-color: rgba(248,113,113,0.95); box-shadow: 0 20px 60px rgba(239,68,68,0.45); }
  .big.speed { background: linear-gradient(135deg, #0a1e2a, #05141a); border-color: rgba(6,182,212,0.6); box-shadow: 0 15px 40px rgba(6,182,212,0.25); }
  .big.speed::before { background: conic-gradient(from 0deg, transparent, rgba(34,211,238,0.3), transparent, rgba(6,182,212,0.25), transparent); animation-duration: 5s; }
  .big.speed:hover { border-color: rgba(34,211,238,0.95); box-shadow: 0 20px 60px rgba(6,182,212,0.45); }
  .big.puzzle { background: linear-gradient(135deg, #0a2a1a, #051a0f); border-color: rgba(34,197,94,0.6); box-shadow: 0 15px 40px rgba(34,197,94,0.25); }
  .big.puzzle::before { background: conic-gradient(from 0deg, transparent, rgba(74,222,128,0.3), transparent, rgba(16,185,129,0.25), transparent); animation-duration: 8s; }
  .big.puzzle:hover { border-color: rgba(74,222,128,0.95); box-shadow: 0 20px 60px rgba(34,197,94,0.45); }
  .big.guess { background: linear-gradient(135deg, #0a1e2a, #05141a); border-color: rgba(6,182,212,0.6); box-shadow: 0 15px 40px rgba(6,182,212,0.25); }
  .big.guess::before { background: conic-gradient(from 0deg, transparent, rgba(34,211,238,0.3), transparent, rgba(59,130,246,0.25), transparent); animation-duration: 6s; }
  .big.guess:hover { border-color: rgba(34,211,238,0.95); box-shadow: 0 20px 60px rgba(6,182,212,0.45); }
  .big > * { position: relative; z-index: 1; }
  .bic { font-size: 42px; width: 72px; height: 72px; border-radius: 20px; background: rgba(255,255,255,0.08); backdrop-filter: blur(10px); border: 1.5px solid rgba(255,255,255,0.15); display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: transform 0.3s; box-shadow: 0 8px 20px rgba(0,0,0,0.3); }
  .big:hover .bic { transform: scale(1.1) rotate(-6deg); }
  .bbody { flex: 1; }
  .btitle { font-size: 19px; font-weight: 900; margin-bottom: 4px; }
  .big.bot .btitle { color: #fde68a; }
  .big.player .btitle { color: #bfdbfe; }
  .big.group .btitle { color: #e9d5ff; }
  .big.challenge .btitle { color: #fca5a5; }
  .big.speed .btitle { color: #a5f3fc; }
  .big.puzzle .btitle { color: #bbf7d0; }
  .big.guess .btitle { color: #a5f3fc; }
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
  <div class="head"><h1>🎮 بازی‌ها</h1></div>

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

  <a href="/game/challenge/" class="big challenge">
    <div class="bic">🏆</div>
    <div class="bbody">
      <div class="btitle">چالش</div>
      <div class="bdesc">تورنمنت هفتگی، روزانه و ساعتی</div>
      <div class="btags">
        <span class="btag">⚔️ رقابتی</span>
        <span class="btag">🎁 جوایز</span>
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
      <div class="bdesc">حدس کلمه از روی سرنخ</div>
      <div class="btags">
        <span class="btag">🧩 پازل</span>
        <span class="btag">🤔 ۵ تلاش</span>
      </div>
    </div>
    <div class="barrow">←</div>
  </a>

  <a href="/game/guess/" class="big guess">
    <div class="badge-new">🆕 جدید</div>
    <div class="bic">🎲</div>
    <div class="bbody">
      <div class="btitle">بازی ۰ تا ۱۰۰</div>
      <div class="bdesc">حدس عدد بین ۰ تا ۱۰۰</div>
      <div class="btags">
        <span class="btag">🔢 اعداد</span>
        <span class="btag">🎯 ۷ تلاش</span>
      </div>
    </div>
    <div class="barrow">←</div>
  </a>
{% endblock %}
''')
    print("  ✓ rooms.html updated with puzzle + guess")

# ============================================================
# 6) Django check + migrate + test
# ============================================================
print("\n[6/6] Check + migrate")

# Make sure messages is imported in game/views.py
p = "game/views.py"
src = read(p)
if "from django.contrib import messages" not in src:
    # Add at top
    src = src.replace(
        "from django.contrib.auth.decorators import login_required",
        "from django.contrib import messages\nfrom django.contrib.auth.decorators import login_required",
        1
    )
    write(p, src)
    print("  ✓ messages imported")

# Make sure _rand is imported
if "import random as _rand" not in src:
    src = read(p)
    if "import random" in src:
        # Already imported regular random, so just alias
        if "as _rand" not in src:
            src = src.replace("import random\n", "import random\nimport random as _rand\n", 1)
            write(p, src)
            print("  ✓ _rand alias added")

# Check
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:500]}")

r = subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Migrate OK")

print("\n" + "="*60)
print("✅ همه چیز ارتقا یافت")
print("="*60)
print("""
چه چیزایی:

  🏠 خانه (menu.html):
     ✓ پنل بیضی پروفایل (بالا) — کلیک → باز می‌شه
     ✓ ۳ مربع خفن‌تر با shine + float animation
     ✓ کارت نکته روز
     ✓ ⭐ برتر (بالا) + 🛒 فروش (پایین، به زودی)
     ✓ آمار کامل تو پروفایل باز شده

  👑 پنل ادمین (/panel-admin/rooms/active/):
     ✓ نمایش زنده بازی‌های در حال انجام
     ✓ آواتار + نام + امتیاز همه بازیکنان
     ✓ راند فعلی + حرف
     ✓ کارت‌های خفن با انیمیشن پالس
     ✓ دکمه حذف

  🎯 بازی معما (/game/puzzle/):
     ✓ ۱۵ کلمه با سرنخ
     ✓ ۵ تلاش
     ✓ حروف فارسی نرمال می‌شن
     ✓ نمایش آمار تلاش‌ها

  🎲 بازی ۰ تا ۱۰۰ (/game/guess/):
     ✓ عدد تصادفی ۰-۱۰۰
     ✓ ۷ تلاش
     ✓ هیستوری حدس‌ها با high/low
     ✓ گرافیک فیروزه‌ای

حالا:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R

تست:
  http://127.0.0.1:8000/game/                    ← خانه جدید
  http://127.0.0.1:8000/game/rooms/              ← ۷ بازی
  http://127.0.0.1:8000/game/puzzle/             ← معما
  http://127.0.0.1:8000/game/guess/              ← ۰ تا ۱۰۰
  http://127.0.0.1:8000/panel-admin/rooms/active/  ← بازی زنده
""")
