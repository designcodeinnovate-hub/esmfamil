#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ارتقای UI: بازی‌ها در خانه + گرافیک خفن + پروفایل نمونه در landing"""
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
# 1) menu.html — بازی‌ها به خانه اضافه بشه + گرافیک خفن
# ============================================================
print("\n[1/4] menu.html — بازی‌ها به خانه")
write("game/templates/game/menu.html", '''{% extends "base.html" %}
{% block title %}خانه{% endblock %}

{% block extra_css %}
<style>
  /* ===== Top bar ===== */
  .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
  .version-badge { display: inline-flex; align-items: center; gap: 5px; background: rgba(234, 179, 8, 0.15); color: #facc15; font-size: 10px; padding: 5px 10px; border-radius: 10px; border: 1px solid rgba(234, 179, 8, 0.3); font-weight: bold; }
  .settings-icon { width: 42px; height: 42px; border-radius: 14px; background: var(--card); border: 1.5px solid var(--border); display: flex; align-items: center; justify-content: center; text-decoration: none; font-size: 20px; transition: all 0.2s; }
  .settings-icon:hover { border-color: var(--gold); transform: rotate(45deg); }

  /* ===== User row ===== */
  .user-row { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
  .user-av-box { width: 50px; height: 50px; border-radius: 50%; border: 2px solid #f4c542; display: flex; align-items: center; justify-content: center; font-size: 26px; box-shadow: 0 0 22px rgba(244, 197, 66, 0.3); overflow: hidden; flex-shrink: 0; }
  .user-av-box.emoji-bg { background: linear-gradient(135deg, #2a2a4a, #1a1a2e); }
  .user-av-box.image-bg { background-size: cover; background-position: center; }
  .greet-text { flex: 1; min-width: 0; }
  .greet-text .hi { font-size: 12px; color: var(--muted); margin-bottom: 2px; }
  .greet-text .name { font-size: 16px; font-weight: bold; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  /* ===== Quick action circles ===== */
  .round-row { display: flex; gap: 10px; justify-content: flex-end; margin-bottom: 14px; }
  .round-btn { position: relative; width: 66px; height: 66px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; text-decoration: none; border: 2px solid; transition: all 0.22s; flex-shrink: 0; gap: 2px; box-shadow: 0 6px 18px rgba(0,0,0,0.3); cursor: pointer; }
  .round-btn:hover { transform: translateY(-3px) scale(1.06); box-shadow: 0 12px 28px rgba(0,0,0,0.45); }
  .round-btn .rb-icon { font-size: 24px; line-height: 1; }
  .round-btn .rb-label { font-size: 9px; font-weight: bold; line-height: 1; }
  .round-top { background: linear-gradient(135deg, rgba(244,197,66,0.3), rgba(234,179,8,0.1)); border-color: rgba(244,197,66,0.55); }
  .round-top .rb-label { color: #fde68a; }
  .round-shop { background: linear-gradient(135deg, rgba(34,197,94,0.3), rgba(6,182,212,0.1)); border-color: rgba(34,197,94,0.55); }
  .round-shop .rb-label { color: #86efac; }
  .round-alliance { background: linear-gradient(135deg, rgba(139,92,246,0.3), rgba(6,182,212,0.15)); border-color: rgba(139,92,246,0.55); }
  .round-alliance .rb-label { color: #c4b5fd; }

  /* ============================================================
     🎮 GAMES SECTION — super awesome graphics
     ============================================================ */
  .section-title { font-size: 13px; color: var(--muted); font-weight: bold; margin: 22px 0 12px; letter-spacing: 1.5px; text-transform: uppercase; display: flex; align-items: center; gap: 8px; }
  .section-title::after { content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, rgba(148,163,184,0.2), transparent); }

  .games-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px; }
  @media (max-width: 380px) { .games-grid { grid-template-columns: 1fr; } }

  .game-tile {
    position: relative;
    display: flex; flex-direction: column;
    padding: 16px 14px;
    border-radius: 20px;
    text-decoration: none;
    color: #fff;
    overflow: hidden;
    border: 1.5px solid;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    isolation: isolate;
    min-height: 130px;
  }
  .game-tile:hover { transform: translateY(-4px) scale(1.02); }
  .game-tile:active { transform: scale(0.97); }
  .game-tile.soon { cursor: default; opacity: 0.75; }
  .game-tile.soon:hover { transform: none; }

  /* Rotating glow behind */
  .game-tile::before {
    content: "";
    position: absolute;
    inset: -100%;
    z-index: 0;
    opacity: 0.4;
    animation: spin 10s linear infinite;
    pointer-events: none;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Bot — gold */
  .game-tile.bot {
    background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.4), transparent 55%),
                linear-gradient(135deg, #2a1a0e, #1a0f08);
    border-color: rgba(244,197,66,0.5);
    box-shadow: 0 10px 30px rgba(244,197,66,0.15);
  }
  .game-tile.bot::before {
    background: conic-gradient(from 0deg, transparent 0deg, rgba(244,197,66,0.2) 90deg, transparent 180deg, rgba(249,115,22,0.2) 270deg, transparent 360deg);
  }
  .game-tile.bot:hover { border-color: rgba(251,211,77,0.95); box-shadow: 0 16px 40px rgba(244,197,66,0.35); }

  /* Player — blue */
  .game-tile.player {
    background: radial-gradient(circle at 100% 0%, rgba(59,130,246,0.4), transparent 55%),
                linear-gradient(135deg, #0a1a2a, #080f18);
    border-color: rgba(59,130,246,0.5);
    box-shadow: 0 10px 30px rgba(59,130,246,0.15);
  }
  .game-tile.player::before {
    background: conic-gradient(from 0deg, transparent 0deg, rgba(96,165,250,0.25) 90deg, transparent 180deg, rgba(139,92,246,0.2) 270deg, transparent 360deg);
  }
  .game-tile.player:hover { border-color: rgba(96,165,250,0.95); box-shadow: 0 16px 40px rgba(59,130,246,0.35); }

  /* Group — purple/pink */
  .game-tile.group {
    background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.45), transparent 55%),
                linear-gradient(135deg, #1a0f2e, #120824);
    border-color: rgba(139,92,246,0.55);
    box-shadow: 0 10px 30px rgba(139,92,246,0.2);
  }
  .game-tile.group::before {
    background: conic-gradient(from 0deg, transparent 0deg, rgba(167,139,250,0.25) 90deg, transparent 180deg, rgba(236,72,153,0.2) 270deg, transparent 360deg);
  }
  .game-tile.group:hover { border-color: rgba(167,139,250,0.95); box-shadow: 0 16px 40px rgba(139,92,246,0.4); }

  /* Challenge — red */
  .game-tile.challenge {
    background: radial-gradient(circle at 100% 0%, rgba(239,68,68,0.4), transparent 55%),
                linear-gradient(135deg, #2a0a0a, #1a0606);
    border-color: rgba(239,68,68,0.55);
    box-shadow: 0 10px 30px rgba(239,68,68,0.2);
  }
  .game-tile.challenge::before {
    background: conic-gradient(from 0deg, transparent 0deg, rgba(248,113,113,0.25) 90deg, transparent 180deg, rgba(249,115,22,0.2) 270deg, transparent 360deg);
    animation-duration: 4s;
  }
  .game-tile.challenge:hover { border-color: rgba(248,113,113,0.95); box-shadow: 0 16px 40px rgba(239,68,68,0.4); }

  /* Speed — cyan */
  .game-tile.speed {
    background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.45), transparent 55%),
                linear-gradient(135deg, #0a1e2a, #05141a);
    border-color: rgba(6,182,212,0.55);
    box-shadow: 0 10px 30px rgba(6,182,212,0.2);
  }
  .game-tile.speed::before {
    background: conic-gradient(from 0deg, transparent 0deg, rgba(34,211,238,0.25) 90deg, transparent 180deg, rgba(6,182,212,0.2) 270deg, transparent 360deg);
    animation-duration: 5s;
  }
  .game-tile.speed:hover { border-color: rgba(34,211,238,0.95); box-shadow: 0 16px 40px rgba(6,182,212,0.4); }

  /* Puzzle — green, soon */
  .game-tile.puzzle {
    background: radial-gradient(circle at 100% 0%, rgba(34,197,94,0.35), transparent 55%),
                linear-gradient(135deg, #0a2a1a, #051a0f);
    border-color: rgba(34,197,94,0.5);
  }
  .game-tile.puzzle::before {
    background: conic-gradient(from 0deg, transparent 0deg, rgba(74,222,128,0.2) 90deg, transparent 180deg, rgba(16,185,129,0.15) 270deg, transparent 360deg);
    animation-duration: 8s;
  }

  /* Tile content */
  .game-tile > * { position: relative; z-index: 1; }
  .game-tile-icon {
    font-size: 42px;
    margin-bottom: 10px;
    filter: drop-shadow(0 6px 12px rgba(0,0,0,0.4));
    transition: transform 0.3s;
  }
  .game-tile:hover .game-tile-icon { transform: scale(1.15) rotate(-8deg); }
  .game-tile-title { font-size: 16px; font-weight: 900; margin-bottom: 4px; }
  .game-tile.bot .game-tile-title { color: #fde68a; }
  .game-tile.player .game-tile-title { color: #bfdbfe; }
  .game-tile.group .game-tile-title { color: #e9d5ff; }
  .game-tile.challenge .game-tile-title { color: #fca5a5; }
  .game-tile.speed .game-tile-title { color: #a5f3fc; }
  .game-tile.puzzle .game-tile-title { color: #bbf7d0; }
  .game-tile-desc { font-size: 11px; color: rgba(255,255,255,0.7); line-height: 1.5; }
  .game-tile-badge {
    position: absolute;
    top: 10px; left: 10px;
    padding: 3px 9px;
    border-radius: 999px;
    font-size: 9px;
    font-weight: 900;
    z-index: 2;
  }
  .game-tile-badge.live {
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: #fff;
    box-shadow: 0 4px 12px rgba(34,197,94,0.5);
    animation: pulse 1.5s infinite;
  }
  .game-tile-badge.team {
    background: linear-gradient(135deg, #ec4899, #8b5cf6);
    color: #fff;
    box-shadow: 0 4px 12px rgba(236,72,153,0.5);
  }
  .game-tile-badge.soon {
    background: linear-gradient(135deg, #eab308, #ca8a04);
    color: #1a1a1a;
    box-shadow: 0 4px 12px rgba(234,179,8,0.5);
  }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.7; } }

  /* ===== Guest warning ===== */
  .guest-warning { background: linear-gradient(135deg, rgba(234,179,8,0.15), rgba(249,115,22,0.08)); border: 1.5px solid rgba(234,179,8,0.35); border-radius: 16px; padding: 16px 18px; margin-bottom: 16px; display: flex; align-items: center; gap: 14px; }
  .guest-warning .gw-icon { font-size: 32px; flex-shrink: 0; }
  .guest-warning .gw-body { flex: 1; }
  .guest-warning .gw-title { font-size: 13.5px; font-weight: bold; color: #fde68a; margin-bottom: 3px; }
  .guest-warning .gw-desc { font-size: 11.5px; color: #fbbf24; line-height: 1.6; }
  .guest-warning .gw-logout { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); padding: 10px 14px; border-radius: 12px; font-size: 12px; font-weight: bold; text-decoration: none; flex-shrink: 0; }

  /* ===== Notifications ===== */
  .notif-btn { position: relative; display: flex; align-items: center; gap: 16px; padding: 18px 20px; background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.35), transparent 60%), linear-gradient(135deg, #1a0f2e, #0f0f1e); border: 2px solid rgba(139,92,246,0.5); border-radius: 20px; text-decoration: none; color: #fff; transition: all 0.22s; margin-bottom: 14px; box-shadow: 0 8px 30px rgba(139,92,246,0.2); }
  .notif-btn:hover { transform: translateY(-3px); border-color: rgba(139,92,246,0.9); box-shadow: 0 15px 40px rgba(139,92,246,0.35); }
  .notif-btn .nb-icon { font-size: 38px; width: 60px; height: 60px; border-radius: 18px; background: rgba(139,92,246,0.2); display: flex; align-items: center; justify-content: center; flex-shrink: 0; position: relative; }
  .notif-btn .nb-body { flex: 1; }
  .notif-btn .nb-title { font-size: 17px; font-weight: 900; margin-bottom: 4px; }
  .notif-btn .nb-desc { font-size: 12px; color: #cbd5e1; }
  .notif-btn .nb-arrow { font-size: 22px; color: #94a3b8; }
  .bell-badge { position: absolute; top: -6px; right: -6px; min-width: 22px; height: 22px; background: #ef4444; color: white; border-radius: 50%; font-size: 11px; display: flex; align-items: center; justify-content: center; font-weight: bold; padding: 0 6px; box-shadow: 0 0 0 3px var(--bg); animation: pulseBadge 2s infinite; }
  @keyframes pulseBadge { 0%,100% { transform: scale(1); } 50% { transform: scale(1.15); } }
</style>
{% endblock %}

{% block content %}

  <div class="top-bar">
    <div class="version-badge"><span>🧪</span><span>نسخه آزمایشی</span></div>
    <a href="/accounts/settings/" class="settings-icon" title="تنظیمات">⚙️</a>
  </div>

  <div class="user-row">
    {% if user.avatar_type == "image" and user.avatar_id %}
      <div class="user-av-box image-bg" style="background-image: url('/static/avatars/images/{{ user.avatar_id|stringformat:"03d" }}.jpg');"></div>
    {% else %}
      <div class="user-av-box emoji-bg">{{ avatar_emoji }}</div>
    {% endif %}
    <div class="greet-text">
      <div class="hi">سلام 👋</div>
      <div class="name">{{ user.alias }}</div>
    </div>
  </div>

  {% if user.is_guest %}
    <div class="guest-warning">
      <span class="gw-icon">🎲</span>
      <div class="gw-body">
        <div class="gw-title">حساب مهمان</div>
        <div class="gw-desc">با خروج، امتیازها از بین می‌ره. برای ذخیره دائمی، حساب بساز.</div>
      </div>
      <a href="/accounts/logout/" class="gw-logout" onclick="return confirm('از حساب مهمان خارج می‌شوی؟');">🚪 خروج</a>
    </div>
  {% endif %}

  <div class="round-row">
    <a href="/alliance/" class="round-btn round-alliance" title="اتحاد">
      <span class="rb-icon">🛡️</span>
      <span class="rb-label">اتحاد</span>
    </a>
    <a href="/game/top-players/" class="round-btn round-top" title="بازیکنان برتر">
      <span class="rb-icon">⭐</span>
      <span class="rb-label">برتر</span>
    </a>
    <a href="/accounts/shop/" class="round-btn round-shop" title="فروشگاه">
      <span class="rb-icon">🛒</span>
      <span class="rb-label">فروشگاه</span>
    </a>
  </div>

  <!-- ============================================================
       🎮 GAMES SECTION
       ============================================================ -->
  <div class="section-title">🎮 بازی‌ها</div>

  <div class="games-grid">
    <a href="/game/quick/" class="game-tile bot">
      <div class="game-tile-badge live">⚡ آنی</div>
      <div class="game-tile-icon">⚡</div>
      <div class="game-tile-title">بازی با بات</div>
      <div class="game-tile-desc">رقیب هوشمند، ۳ سطح سختی</div>
    </a>

    <a href="/game/match/" class="game-tile player">
      <div class="game-tile-badge live">🌐 آنلاین</div>
      <div class="game-tile-icon">⚔️</div>
      <div class="game-tile-title">بازی با پلیر</div>
      <div class="game-tile-desc">رقابت آنی با حریف واقعی</div>
    </a>

    <a href="/game/team/start/" class="game-tile group">
      <div class="game-tile-badge team">👥 ۴ نفره</div>
      <div class="game-tile-icon">🛡️</div>
      <div class="game-tile-title">بازی گروهی</div>
      <div class="game-tile-desc">تیم ۲v۲، ۳ راند هیجان</div>
    </a>

    <a href="/game/challenge/" class="game-tile challenge">
      <div class="game-tile-icon">🏆</div>
      <div class="game-tile-title">چالش</div>
      <div class="game-tile-desc">تورنمنت هفتگی و روزانه</div>
    </a>

    <a href="/game/quick/bot/?mode=speed" class="game-tile speed">
      <div class="game-tile-icon">⏱️</div>
      <div class="game-tile-title">سرعتی</div>
      <div class="game-tile-desc">فقط ۲۰ ثانیه!</div>
    </a>

    <div class="game-tile puzzle soon" onclick="alert('🎯 بازی معما به زودی!')">
      <div class="game-tile-badge soon">⏳ به زودی</div>
      <div class="game-tile-icon">🎯</div>
      <div class="game-tile-title">معما</div>
      <div class="game-tile-desc">حدس کلمه از سرنخ</div>
    </div>
  </div>

  <div class="section-title">📬 سایر</div>

  <a href="/social/notifications/" class="notif-btn">
    <div class="nb-icon">
      🔔
      {% if unread_notifications %}<span class="bell-badge">{{ unread_notifications }}</span>{% endif %}
    </div>
    <div class="nb-body">
      <div class="nb-title">اعلان‌ها</div>
      <div class="nb-desc">{% if unread_notifications %}{{ unread_notifications }} پیام جدید{% else %}پیام‌ها و درخواست‌ها{% endif %}</div>
    </div>
    <div class="nb-arrow">←</div>
  </a>

{% endblock %}
''')

# ============================================================
# 2) landing.html — پروفایل نمونه با آواتار و نام
# ============================================================
print("\n[2/4] landing.html — پروفایل نمونه")
write("accounts/templates/accounts/landing.html", '''<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <meta name="theme-color" content="#0a0a15">
  <title>اسم فامیل آنلاین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { height: 100%; overflow-y: auto; overflow-x: hidden; }
    body { font-family: Tahoma, sans-serif; background: radial-gradient(circle at 20% 10%, #1e1b4b 0%, #0f0f1e 45%, #060608 100%); color: #e2e8f0; min-height: 100vh; }
    .glow { position: fixed; width: 400px; height: 400px; border-radius: 50%; filter: blur(130px); z-index: 0; pointer-events: none; }
    .glow-1 { top: -100px; right: -100px; background: #8b5cf6; opacity: 0.28; }
    .glow-2 { bottom: -100px; left: -100px; background: #f4c542; opacity: 0.18; }
    .glow-3 { top: 40%; left: -100px; background: #06b6d4; opacity: 0.15; }

    .content { position: relative; z-index: 10; display: flex; flex-direction: column; align-items: center; padding: 30px 20px; min-height: 100vh; }

    .logo-wrap { text-align: center; margin-top: 10px; margin-bottom: 6px; }
    .logo-name { font-size: 44px; font-weight: 900; background: linear-gradient(180deg, #fde68a 0%, #f4c542 50%, #ca8a04 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .logo-crown { font-size: 40px; display: inline-block; transform: translateY(-10px) rotate(-8deg); filter: drop-shadow(0 6px 20px rgba(244,197,66,0.6)); }
    .tagline { color: #94a3b8; font-size: 13px; text-align: center; margin-bottom: 22px; letter-spacing: 1.5px; }

    /* ============================================================
       👤 SAMPLE PROFILE CARD
       ============================================================ */
    .sample-profile {
      position: relative;
      width: 340px;
      max-width: 92vw;
      padding: 24px 20px 20px;
      background: linear-gradient(135deg, rgba(30,41,59,0.85), rgba(15,23,42,0.95));
      border: 1.5px solid rgba(244,197,66,0.4);
      border-radius: 24px;
      margin-bottom: 26px;
      text-align: center;
      overflow: hidden;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 40px rgba(244,197,66,0.1);
      animation: cardFloat 4s ease-in-out infinite;
    }
    @keyframes cardFloat {
      0%,100% { transform: translateY(0); }
      50% { transform: translateY(-6px); }
    }
    .sample-profile::before {
      content: "";
      position: absolute;
      inset: -50%;
      background: conic-gradient(from 0deg, transparent 0deg, rgba(244,197,66,0.15) 90deg, transparent 180deg, rgba(139,92,246,0.15) 270deg, transparent 360deg);
      animation: spin 12s linear infinite;
      z-index: 0;
      pointer-events: none;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .sample-profile > * { position: relative; z-index: 1; }

    .sample-label {
      display: inline-block;
      background: rgba(244,197,66,0.15);
      color: #fde68a;
      padding: 3px 12px;
      border-radius: 999px;
      font-size: 10px;
      font-weight: 900;
      margin-bottom: 12px;
      letter-spacing: 0.5px;
    }

    .sample-avatar {
      width: 88px; height: 88px;
      margin: 0 auto 12px;
      border-radius: 50%;
      background: linear-gradient(135deg, rgba(139,92,246,0.3), rgba(6,182,212,0.2));
      border: 3px solid #f4c542;
      display: flex; align-items: center; justify-content: center;
      font-size: 48px;
      box-shadow: 0 0 30px rgba(244,197,66,0.5), inset 0 0 20px rgba(0,0,0,0.3);
      animation: avatarPulse 2.5s ease-in-out infinite;
    }
    @keyframes avatarPulse {
      0%,100% { box-shadow: 0 0 30px rgba(244,197,66,0.5), inset 0 0 20px rgba(0,0,0,0.3); }
      50% { box-shadow: 0 0 50px rgba(244,197,66,0.8), 0 0 20px rgba(139,92,246,0.5), inset 0 0 20px rgba(0,0,0,0.3); }
    }

    .sample-name {
      font-size: 20px;
      font-weight: 900;
      background: linear-gradient(135deg, #fde68a, #f4c542, #fdba74);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 4px;
    }
    .sample-username {
      font-size: 11px;
      color: #64748b;
      font-family: monospace;
      letter-spacing: 1px;
      margin-bottom: 12px;
    }

    .sample-level-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      background: rgba(15,23,42,0.7);
      border-radius: 12px;
      margin-top: 12px;
    }
    .sample-level-badge {
      background: linear-gradient(135deg, #8b5cf6, #6b4eff);
      color: #fff;
      font-size: 11px;
      font-weight: 900;
      padding: 3px 10px;
      border-radius: 8px;
      font-family: monospace;
      flex-shrink: 0;
    }
    .sample-progress {
      flex: 1;
      height: 6px;
      background: rgba(148,163,184,0.2);
      border-radius: 6px;
      overflow: hidden;
    }
    .sample-progress-fill {
      height: 100%;
      width: 68%;
      background: linear-gradient(90deg, #8b5cf6, #f4c542);
      border-radius: 6px;
      box-shadow: 0 0 8px rgba(139,92,246,0.6);
      animation: progressShine 2s ease-in-out infinite;
    }
    @keyframes progressShine {
      0%,100% { opacity: 1; }
      50% { opacity: 0.75; }
    }

    .sample-stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 6px;
      margin-top: 12px;
    }
    .sample-stat {
      padding: 8px 4px;
      background: rgba(15,23,42,0.5);
      border-radius: 10px;
      border: 1px solid rgba(148,163,184,0.1);
    }
    .sample-stat .v {
      font-size: 14px;
      font-weight: 900;
      color: #fde68a;
      font-family: monospace;
      margin-bottom: 2px;
    }
    .sample-stat .l {
      font-size: 9px;
      color: #64748b;
    }

    /* ============================================================
       Options
       ============================================================ */
    .options { display: flex; flex-direction: column; gap: 12px; width: 340px; max-width: 92vw; }
    .btn-opt { display: flex; align-items: center; gap: 14px; padding: 16px 20px; border-radius: 18px; font-size: 16px; font-weight: bold; text-decoration: none; border: 1.5px solid; transition: all 0.2s; color: #e2e8f0; }
    .btn-opt:hover { transform: translateY(-3px); }
    .btn-opt .icon { font-size: 26px; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; background: rgba(15, 23, 42, 0.6); border-radius: 12px; flex-shrink: 0; }
    .btn-opt .label { flex: 1; text-align: right; }
    .btn-register { background: linear-gradient(135deg, #f4c542, #eab308); color: #1a1a1a; border-color: transparent; padding: 20px 22px; font-size: 18px; box-shadow: 0 14px 40px rgba(244,197,66,0.45); }
    .btn-register .icon { background: rgba(0,0,0,0.15); font-size: 28px; width: 48px; height: 48px; }
    .btn-account { background: rgba(30, 41, 59, 0.75); border-color: rgba(6, 182, 212, 0.3); }
    .btn-account:hover { border-color: #06b6d4; background: rgba(30, 41, 59, 0.95); }
    .btn-guest { background: rgba(30, 41, 59, 0.6); color: #cbd5e1; border-color: rgba(148, 163, 184, 0.2); }
    .btn-guest:hover { border-color: #94a3b8; background: rgba(30, 41, 59, 0.85); }
    .divider { display: flex; align-items: center; gap: 10px; margin: 6px 0; color: #475569; font-size: 11px; }
    .divider::before, .divider::after { content: ""; flex: 1; height: 1px; background: rgba(148, 163, 184, 0.15); }
    .footer { margin-top: 30px; margin-bottom: 20px; text-align: center; color: #475569; font-size: 11px; line-height: 1.8; }
  </style>
</head>
<body>
  <div class="glow glow-1"></div>
  <div class="glow glow-2"></div>
  <div class="glow glow-3"></div>

  <div class="content">
    <div class="logo-wrap">
      <span class="logo-crown">👑</span>
      <span class="logo-name">اسم فامیل</span>
    </div>
    <div class="tagline">بازی نوستالژیک، حال و آنلاین</div>

    <!-- ============================================================
         Sample Profile Card
         ============================================================ -->
    <div class="sample-profile">
      <div class="sample-label">✨ نمونه پروفایل</div>
      <div class="sample-avatar">🦁</div>
      <div class="sample-name">آرش</div>
      <div class="sample-username">@arash_1403</div>

      <div class="sample-level-bar">
        <span class="sample-level-badge">Lv 5</span>
        <div class="sample-progress">
          <div class="sample-progress-fill"></div>
        </div>
      </div>

      <div class="sample-stats">
        <div class="sample-stat">
          <div class="v">12</div>
          <div class="l">بازی</div>
        </div>
        <div class="sample-stat">
          <div class="v">480</div>
          <div class="l">امتیاز</div>
        </div>
        <div class="sample-stat">
          <div class="v">3</div>
          <div class="l">پیروزی</div>
        </div>
      </div>
    </div>

    <div class="options">
      <a class="btn-opt btn-register" href="/accounts/register/">
        <span class="icon">✨</span>
        <span class="label">ساخت حساب جدید</span>
        <span>←</span>
      </a>
      <div class="divider">یا</div>
      <a class="btn-opt btn-account" href="/accounts/login/">
        <span class="icon">🔐</span>
        <span class="label">ورود با حساب کاربری</span>
        <span>←</span>
      </a>
      <a class="btn-opt btn-guest" href="/accounts/guest/">
        <span class="icon">🎲</span>
        <span class="label">ورود مهمان</span>
        <span>←</span>
      </a>
    </div>

    <div class="footer">
      <div>اسم فامیل آنلاین</div>
      <div>v3.0</div>
    </div>
  </div>
</body>
</html>
''')

# ============================================================
# 3) rooms.html — گرافیک خفن‌تر برای صفحه بازی‌ها
# ============================================================
print("\n[3/4] rooms.html — گرافیک خفن")
write("game/templates/game/rooms.html", '''{% extends "base.html" %}
{% block title %}بازی‌ها{% endblock %}
{% block extra_css %}
<style>
  .page-head { margin-bottom: 20px; display: flex; align-items: center; gap: 12px; }
  .page-head h1 { font-size: 24px; font-weight: 900; background: linear-gradient(135deg, #f4c542, #fdba74); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .page-head .count { font-size: 11px; padding: 3px 10px; background: rgba(244,197,66,0.15); color: #fde68a; border-radius: 8px; font-family: monospace; }

  .intro-text { color: var(--muted); font-size: 13px; margin-bottom: 20px; line-height: 1.6; }

  .big {
    display: flex; align-items: center; gap: 16px;
    padding: 22px 20px; border-radius: 24px;
    text-decoration: none; color: #fff;
    margin-bottom: 14px;
    position: relative; overflow: hidden;
    border: 2px solid;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    isolation: isolate;
  }
  .big:hover { transform: translateY(-4px) scale(1.01); }
  .big:active { transform: scale(0.98); }
  .big.soon { cursor: default; opacity: 0.7; }
  .big.soon:hover { transform: none; }

  /* rotating glow */
  .big::before {
    content: "";
    position: absolute;
    inset: -150%;
    z-index: -1;
    animation: spin 10s linear infinite;
    opacity: 0.6;
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

  .big.challenge { background: linear-gradient(135deg, #2a0a0a, #1a0606); border-color: rgba(239,68,68,0.6); box-shadow: 0 15px 40px rgba(239,68,68,0.25); }
  .big.challenge::before { background: conic-gradient(from 0deg, transparent, rgba(248,113,113,0.3), transparent, rgba(249,115,22,0.25), transparent); animation-duration: 4s; }
  .big.challenge:hover { border-color: rgba(248,113,113,0.95); box-shadow: 0 20px 60px rgba(239,68,68,0.45); }

  .big.speed { background: linear-gradient(135deg, #0a1e2a, #05141a); border-color: rgba(6,182,212,0.6); box-shadow: 0 15px 40px rgba(6,182,212,0.25); }
  .big.speed::before { background: conic-gradient(from 0deg, transparent, rgba(34,211,238,0.3), transparent, rgba(6,182,212,0.25), transparent); animation-duration: 5s; }
  .big.speed:hover { border-color: rgba(34,211,238,0.95); box-shadow: 0 20px 60px rgba(6,182,212,0.45); }

  .big.puzzle { background: linear-gradient(135deg, #0a2a1a, #051a0f); border-color: rgba(34,197,94,0.5); }
  .big.puzzle::before { background: conic-gradient(from 0deg, transparent, rgba(74,222,128,0.2), transparent, rgba(16,185,129,0.2), transparent); animation-duration: 8s; }

  .big > * { position: relative; z-index: 1; }

  .bic {
    font-size: 42px;
    width: 72px; height: 72px;
    border-radius: 20px;
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    border: 1.5px solid rgba(255,255,255,0.15);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    transition: transform 0.3s;
    box-shadow: 0 8px 20px rgba(0,0,0,0.3);
  }
  .big:hover .bic { transform: scale(1.1) rotate(-6deg); }

  .bbody { flex: 1; }
  .btitle { font-size: 19px; font-weight: 900; margin-bottom: 4px; letter-spacing: -0.2px; }
  .big.bot .btitle { color: #fde68a; }
  .big.player .btitle { color: #bfdbfe; }
  .big.group .btitle { color: #e9d5ff; }
  .big.challenge .btitle { color: #fca5a5; }
  .big.speed .btitle { color: #a5f3fc; }
  .big.puzzle .btitle { color: #bbf7d0; }
  .bdesc { font-size: 12px; color: rgba(255,255,255,0.7); line-height: 1.5; }

  .btags { display: flex; gap: 5px; flex-wrap: wrap; margin-top: 8px; }
  .btag { font-size: 9.5px; font-weight: bold; padding: 3px 8px; border-radius: 6px; background: rgba(255,255,255,0.1); color: #e2e8f0; border: 1px solid rgba(255,255,255,0.15); }

  .barrow { font-size: 22px; color: rgba(255,255,255,0.5); transition: 0.3s; }
  .big:hover .barrow { transform: translateX(-4px); color: rgba(255,255,255,0.9); }

  .soon-badge { position: absolute; top: 12px; left: 12px; background: linear-gradient(135deg, #eab308, #ca8a04); color: #1a1a1a; font-size: 10px; font-weight: 900; padding: 3px 9px; border-radius: 999px; z-index: 2; box-shadow: 0 4px 12px rgba(234,179,8,0.5); }
  .live-badge { position: absolute; top: 12px; left: 12px; background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; font-size: 10px; font-weight: 900; padding: 3px 9px; border-radius: 999px; z-index: 2; box-shadow: 0 4px 12px rgba(34,197,94,0.5); animation: pulse 1.5s infinite; display: flex; align-items: center; gap: 4px; }
  .live-badge::before { content: ""; width: 6px; height: 6px; background: #fff; border-radius: 50%; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.7; } }
  .team-badge { position: absolute; top: 12px; left: 12px; background: linear-gradient(135deg, #ec4899, #8b5cf6); color: #fff; font-size: 10px; font-weight: 900; padding: 3px 9px; border-radius: 999px; z-index: 2; box-shadow: 0 4px 12px rgba(236,72,153,0.5); }
</style>
{% endblock %}
{% block content %}

  <div class="page-head">
    <h1>🎮 بازی‌ها</h1>
    <span class="count">۶ حالت</span>
  </div>

  <p class="intro-text">یه حالت رو انتخاب کن و شروع کن! هر بازی یه تجربه‌ی خاص داره.</p>

  <a href="/game/quick/" class="big bot">
    <div class="live-badge">⚡ آنی</div>
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
    <div class="live-badge">🌐 آنلاین</div>
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
    <div class="team-badge">👥 ۴ نفره</div>
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

  <div class="big puzzle soon" onclick="alert('🎯 بازی معما به زودی فعال می‌شود!')">
    <span class="soon-badge">⏳ به زودی</span>
    <div class="bic">🎯</div>
    <div class="bbody">
      <div class="btitle">بازی معما</div>
      <div class="bdesc">حدس کلمه از روی سرنخ</div>
      <div class="btags">
        <span class="btag">🧩 پازل</span>
        <span class="btag">🤔 سرنخ</span>
      </div>
    </div>
    <div class="barrow">←</div>
  </div>

{% endblock %}
''')

# ============================================================
# 4) تست + جمع‌بندی
# ============================================================
print("\n[4/4] تست")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:300]}")

print("\n" + "="*60)
print("✅ ارتقا تموم شد")
print("="*60)
print("""
چه چیزایی اضافه شد:

  🎮 menu.html (خانه):
     ✓ بخش بازی‌ها با ۶ tile خفن
     ✓ آیکن‌های رنگارنگ + انیمیشن چرخشی پشت
     ✓ badge: آنی / آنلاین / ۴ نفره / به زودی
     ✓ آواتار بالای صفحه با نام

  👤 landing.html (صفحه اصلی):
     ✓ پروفایل نمونه با آواتار 🦁
     ✓ نام "آرش" + username @arash_1403
     ✓ نوار Lv 5 با پیشرفت
     ✓ آمار: 12 بازی، 480 امتیاز، 3 پیروزی
     ✓ کارت با انیمیشن float

  🎨 rooms.html (بازی‌ها):
     ✓ کارت‌های بزرگ با rotating glow
     ✓ badge های رنگی
     ✓ تگ‌های اطلاعات
     ✓ آیکن‌های بزرگ‌تر با hover animation
     ✓ توضیحات غنی‌تر

حالا:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)

بعد:
  http://127.0.0.1:8000/          ← پروفایل نمونه
  http://127.0.0.1:8000/game/     ← بازی‌ها در خانه
""")
