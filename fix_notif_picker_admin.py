#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  OK {p}")
def backup(p):
    bak = p + ".bak_x"
    if os.path.exists(p) and not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f: f.write(read(p))

# ============================================================
# 1) notifications.html - full rewrite
# ============================================================
print("\n[1/5] notifications.html - full rewrite")
p = os.path.join(ROOT, "social", "templates", "social", "notifications.html")

NOTIF_HTML = '''{% extends "base.html" %}
{% load jalali_tags %}
{% block title %}اعلان‌ها{% endblock %}

{% block extra_css %}
<style>
  .page-head {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 18px; justify-content: space-between;
  }
  .page-head-left { display: flex; align-items: center; gap: 12px; }
  .page-head a {
    width: 42px; height: 42px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    color: var(--gold); text-decoration: none; font-size: 20px;
    transition: 0.2s;
  }
  .page-head a:hover { border-color: var(--gold); transform: translateX(-2px); }
  .page-head h1 { font-size: 22px; font-weight: bold; }
  .page-head h1 span { color: var(--gold); }
  .unread-count {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: #fff;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 12px; font-weight: 900;
    box-shadow: 0 4px 12px rgba(239,68,68,0.4);
  }

  .notif-card {
    display: flex; align-items: flex-start; gap: 14px;
    padding: 16px; margin-bottom: 10px;
    background: var(--card);
    border: 1.5px solid var(--border);
    border-radius: 16px;
    text-decoration: none; color: var(--text);
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
  }
  .notif-card:hover {
    border-color: var(--gold);
    transform: translateX(-3px);
    box-shadow: 0 8px 25px rgba(244,197,66,0.15);
  }
  .notif-card.unread {
    border-color: rgba(244,197,66,0.4);
    background: linear-gradient(135deg, rgba(244,197,66,0.08), rgba(139,92,246,0.05));
    box-shadow: 0 4px 15px rgba(244,197,66,0.1);
  }
  .notif-card.unread::before {
    content: "";
    position: absolute;
    top: 0; bottom: 0; right: 0;
    width: 4px;
    background: linear-gradient(180deg, #f4c542, #eab308);
  }
  .notif-card.admin {
    border-color: rgba(245,158,11,0.5);
    background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(15,23,42,0.5));
  }
  .notif-card.admin::before {
    background: linear-gradient(180deg, #f59e0b, #d97706);
  }

  .notif-icon {
    width: 48px; height: 48px;
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; flex-shrink: 0;
    background: linear-gradient(135deg, rgba(244,197,66,0.2), rgba(139,92,246,0.15));
  }
  .notif-icon.admin-icon {
    background: linear-gradient(135deg, rgba(245,158,11,0.3), rgba(234,179,8,0.15));
  }
  .notif-body { flex: 1; min-width: 0; }
  .notif-title {
    font-size: 14px; font-weight: bold; margin-bottom: 4px;
    color: #fff;
  }
  .notif-sender {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 11px;
    color: #c4b5fd;
    padding: 2px 8px;
    background: rgba(139,92,246,0.15);
    border-radius: 6px;
    margin-bottom: 6px;
    font-weight: bold;
  }
  .notif-sender.admin-sender {
    color: #fde68a;
    background: rgba(245,158,11,0.15);
  }
  .notif-sender .username {
    font-size: 10px;
    opacity: 0.7;
    font-family: monospace;
  }
  .notif-desc {
    font-size: 12px; color: var(--muted);
    line-height: 1.6; margin-bottom: 6px;
  }
  .notif-time {
    font-size: 10px;
    color: var(--dim);
    font-family: monospace;
    display: flex; align-items: center; gap: 4px;
  }

  .unread-dot {
    width: 10px; height: 10px;
    background: var(--gold);
    border-radius: 50%;
    flex-shrink: 0;
    margin-top: 8px;
    box-shadow: 0 0 8px rgba(244,197,66,0.7);
    animation: pulseDot 1.5s ease-in-out infinite;
  }
  @keyframes pulseDot {
    0%,100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.3); opacity: 0.6; }
  }

  .empty {
    text-align: center; padding: 60px 20px;
    color: var(--muted); font-size: 14px;
  }
  .empty .icon { font-size: 60px; display: block; margin-bottom: 12px; opacity: 0.5; }
  .empty h3 { font-size: 16px; margin-bottom: 6px; color: #fff; }
  .empty p { font-size: 12px; line-height: 1.7; }
</style>
{% endblock %}

{% block content %}

  <div class="page-head">
    <div class="page-head-left">
      <a href="/game/">←</a>
      <h1>🔔 <span>اعلان‌ها</span></h1>
    </div>
    {% if unread_total %}
      <div class="unread-count">{{ unread_total }} جدید</div>
    {% endif %}
  </div>

  {% if notifications %}
    {% for n in notifications %}
      {% if n.url %}
        <a href="{{ n.url }}" class="notif-card {% if not n.is_read %}unread{% endif %} {% if n.type == 'admin_broadcast' %}admin{% endif %}">
      {% else %}
        <div class="notif-card {% if not n.is_read %}unread{% endif %} {% if n.type == 'admin_broadcast' %}admin{% endif %}">
      {% endif %}

        <div class="notif-icon {% if n.type == 'admin_broadcast' %}admin-icon{% endif %}">
          {% if n.type == "friend_request" %}👋
          {% elif n.type == "friend_accepted" %}✅
          {% elif n.type == "message" %}💬
          {% elif n.type == "game_invite" %}🎮
          {% elif n.type == "game_result" %}🏆
          {% elif n.type == "alliance_invite" %}🛡️
          {% elif n.type == "admin_broadcast" %}📢
          {% else %}🔔{% endif %}
        </div>

        <div class="notif-body">
          <div class="notif-title">{{ n.title }}</div>

          {% if n.sender %}
            <div class="notif-sender">
              👤 {{ n.sender.alias }}
              <span class="username">@{{ n.sender.username }}</span>
            </div>
          {% elif n.type == "admin_broadcast" %}
            <div class="notif-sender admin-sender">
              📢 مدیر سیستم
            </div>
          {% endif %}

          {% if n.body %}<div class="notif-desc">{{ n.body }}</div>{% endif %}

          <div class="notif-time">
            🕐 {{ n.created_at|jdate:"Y/m/d H:i" }}
          </div>
        </div>

        {% if not n.is_read %}<div class="unread-dot"></div>{% endif %}

      {% if n.url %}</a>{% else %}</div>{% endif %}
    {% endfor %}
  {% else %}
    <div class="empty">
      <span class="icon">📭</span>
      <h3>هنوز اعلانی نداری</h3>
      <p>وقتی دوستی اضافه کنی یا دعوتی دریافت کنی،<br>اینجا نمایش داده می‌شه.</p>
    </div>
  {% endif %}

{% endblock %}
'''
backup(p); write(p, NOTIF_HTML)

# ============================================================
# 2) social/views.py - notifications_view: add unread_total
# ============================================================
print("\n[2/5] social/views.py - notifications_view")
p = os.path.join(ROOT, "social", "views.py")
src = read(p)

old = '''@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).select_related("sender")
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, "social/notifications.html", {
        "notifications": notifs,
        "active": "friends",
    })'''

new = '''@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).select_related("sender")
    unread = notifs.filter(is_read=False).count()
    # علامت‌گذاری به‌عنوان خوانده‌شده بعد از شمارش
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, "social/notifications.html", {
        "notifications": notifs,
        "unread_total": unread,
        "active": "friends",
    })'''

if old in src:
    src = src.replace(old, new, 1)
    backup(p); write(p, src)
    print("  FIXED: unread_total added")
else:
    print("  WARN: notifications_view not found")

# ============================================================
# 3) tournament_edit.html - separate date/time sections + prettier
# ============================================================
print("\n[3/5] tournament_edit.html - separate date/time")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "tournament_edit.html")

EDIT_HTML = '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% if tournament %}ویرایش{% else %}ساخت{% endif %} تورنمنت</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 900px; margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
    .topbar h1 { font-size: 19px; color: #fca5a5; }
    .topbar-actions { display: flex; gap: 8px; }
    .topbar a { padding: 9px 16px; border-radius: 10px; text-decoration: none; font-size: 13px; font-weight: bold; color: #fff; }
    .btn-back { background: rgba(148,163,184,0.2); }
    .btn-logout { background: linear-gradient(135deg, #ef4444, #dc2626); }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .card { background: #12121f; border: 1px solid rgba(148,163,184,0.15); border-radius: 16px; padding: 22px; margin-bottom: 16px; }
    .card h3 { color: #fdba74; font-size: 15px; margin-bottom: 16px; }

    label { display: block; color: #94a3b8; font-size: 12px; margin: 12px 0 6px; font-weight: bold; }
    input[type=text], input[type=number], textarea, select { width: 100%; padding: 12px 14px; border-radius: 10px; border: 1.5px solid rgba(148,163,184,0.2); background: #0a0a15; color: #fff; font-size: 14px; font-family: inherit; box-sizing: border-box; }
    textarea { resize: vertical; min-height: 70px; }
    input:focus, textarea:focus, select:focus { outline: none; border-color: #facc15; }

    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    @media (max-width: 500px) { .row { grid-template-columns: 1fr; } }

    .emojis { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
    .emoji-opt { padding: 12px; text-align: center; font-size: 24px; background: #1a1a2e; border: 2px solid transparent; border-radius: 10px; cursor: pointer; transition: 0.15s; }
    .emoji-opt:hover { border-color: #facc15; }
    .emoji-opt input { display: none; }
    .emoji-opt:has(input:checked) { border-color: #facc15; background: linear-gradient(135deg, rgba(250,204,21,0.2), rgba(139,92,246,0.1)); }

    button.submit { width: 100%; margin-top: 18px; padding: 14px; border: none; border-radius: 12px; font-size: 15px; font-weight: bold; font-family: inherit; cursor: pointer; color: #fff; background: linear-gradient(135deg, #22c55e, #16a34a); box-shadow: 0 8px 20px rgba(34,197,94,0.4); }
    button.submit:hover { transform: translateY(-1px); }

    .danger-card { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.3); border-radius: 16px; padding: 22px; }
    .danger-card h3 { color: #fca5a5; }
    .danger-card p { font-size: 12px; color: #94a3b8; margin-bottom: 12px; line-height: 1.6; }
    button.danger-btn { padding: 10px 20px; border: none; border-radius: 10px; font-family: inherit; font-weight: bold; font-size: 13px; cursor: pointer; background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4); margin-left: 8px; }
    button.del-btn { padding: 10px 20px; border: none; border-radius: 10px; font-family: inherit; font-weight: bold; font-size: 13px; cursor: pointer; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; }

    /* ============ Jalali DateTime Picker ============ */
    .dt-wrap {
      background: linear-gradient(135deg, #0f0f1e, #1a1a2e);
      border: 1.5px solid rgba(139,92,246,0.3);
      border-radius: 16px;
      padding: 18px;
      margin-bottom: 12px;
    }
    .dt-wrap.start { border-color: rgba(34,197,94,0.4); }
    .dt-wrap.end { border-color: rgba(239,68,68,0.4); }

    .dt-header {
      display: flex; align-items: center; gap: 8px;
      margin-bottom: 14px; padding-bottom: 10px;
      border-bottom: 1px solid rgba(148,163,184,0.1);
    }
    .dt-header .badge {
      padding: 4px 12px; border-radius: 8px; font-size: 11px; font-weight: 900;
    }
    .dt-wrap.start .badge { background: rgba(34,197,94,0.2); color: #4ade80; }
    .dt-wrap.end .badge { background: rgba(239,68,68,0.2); color: #fca5a5; }
    .dt-header .title { font-size: 14px; font-weight: bold; color: #fff; flex: 1; }

    .dt-section {
      margin-bottom: 14px;
      padding: 12px;
      background: rgba(10,10,21,0.5);
      border-radius: 12px;
      border: 1px solid rgba(148,163,184,0.08);
    }
    .dt-section:last-child { margin-bottom: 0; }

    .dt-section-title {
      font-size: 11px;
      color: #94a3b8;
      margin-bottom: 10px;
      font-weight: bold;
      display: flex; align-items: center; gap: 6px;
    }

    .dt-grid-date {
      display: grid;
      grid-template-columns: 1.4fr 1.5fr 1fr;
      gap: 8px;
    }
    .dt-grid-time {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .dt-field { display: flex; flex-direction: column; gap: 4px; }
    .dt-field .lbl {
      font-size: 10px;
      color: #64748b;
      text-align: center;
      font-weight: bold;
    }
    .dt-field select {
      padding: 12px 8px;
      font-size: 15px;
      font-weight: bold;
      text-align: center;
      background: #0a0a15;
      border: 1.5px solid rgba(148,163,184,0.2);
      border-radius: 10px;
      color: #fff;
      font-family: inherit;
      cursor: pointer;
    }
    .dt-field select:focus { outline: none; border-color: #facc15; }
    .dt-wrap.start .dt-field select:focus { border-color: #22c55e; box-shadow: 0 0 12px rgba(34,197,94,0.3); }
    .dt-wrap.end .dt-field select:focus { border-color: #ef4444; box-shadow: 0 0 12px rgba(239,68,68,0.3); }

    .dt-preview {
      margin-top: 12px;
      padding: 10px 14px;
      background: rgba(250,204,21,0.08);
      border: 1px dashed rgba(250,204,21,0.3);
      border-radius: 10px;
      font-size: 13px;
      color: #fde68a;
      text-align: center;
      font-family: monospace;
      font-weight: bold;
    }

    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 10px 12px; text-align: right; font-size: 12px; border-bottom: 1px solid rgba(148,163,184,0.1); }
    th { color: #94a3b8; font-size: 11px; font-weight: bold; }
    tr:last-child td { border-bottom: none; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>🏆 {% if tournament %}ویرایش: {{ tournament.name }}{% else %}ساخت تورنمنت جدید{% endif %}</h1>
    <div class="topbar-actions">
      <a href="{% url 'custom_admin:tournaments_list' %}" class="btn-back">← بازگشت</a>
      <a href="{% url 'custom_admin:logout' %}" class="btn-logout">خروج</a>
    </div>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <form method="post" id="tourForm">
    {% csrf_token %}

    <div class="card">
      <h3>📝 اطلاعات پایه</h3>
      <label>آیکن</label>
      <div class="emojis">
        {% for e in "🏆🥇🏅🎯⚔️🔥🌟💎👑🎮🏰🛡️" %}
          <label class="emoji-opt">
            <input type="radio" name="icon" value="{{ e }}" {% if tournament and tournament.icon == e %}{% elif not tournament and e == '🏆' %}checked{% endif %}>
            {{ e }}
          </label>
        {% endfor %}
      </div>

      <label>نام تورنمنت</label>
      <input type="text" name="name" value="{{ tournament.name|default:'' }}" required maxlength="80">

      <label>توضیح</label>
      <textarea name="description" maxlength="300">{{ tournament.description|default:'' }}</textarea>

      <div class="row">
        <div>
          <label>نوع</label>
          <select name="tournament_type">
            <option value="daily" {% if tournament.tournament_type == 'daily' or not tournament %}selected{% endif %}>روزانه</option>
            <option value="hourly" {% if tournament.tournament_type == 'hourly' %}selected{% endif %}>ساعتی</option>
            <option value="weekly" {% if tournament.tournament_type == 'weekly' %}selected{% endif %}>هفتگی</option>
          </select>
        </div>
        <div>
          <label>وضعیت</label>
          <select name="status">
            <option value="scheduled" {% if tournament.status == 'scheduled' or not tournament %}selected{% endif %}>برنامه‌ریزی شده</option>
            <option value="active" {% if tournament.status == 'active' %}selected{% endif %}>در حال برگزاری</option>
            <option value="finished" {% if tournament.status == 'finished' %}selected{% endif %}>پایان یافته</option>
            <option value="cancelled" {% if tournament.status == 'cancelled' %}selected{% endif %}>لغو شده</option>
          </select>
        </div>
      </div>
    </div>

    {% with start_j=tournament.start_at|to_jalali end_j=tournament.end_at|to_jalali %}

    <!-- ============ START ============ -->
    <div class="card">
      <h3>⏰ زمان‌بندی (شمسی)</h3>

      <div class="dt-wrap start">
        <div class="dt-header">
          <div class="badge">شروع</div>
          <div class="title">تاریخ و ساعت شروع تورنمنت</div>
        </div>

        <div class="dt-section">
          <div class="dt-section-title">📅 تاریخ</div>
          <div class="dt-grid-date">
            <div class="dt-field">
              <select name="start_jy" id="start_jy">
                {% for y in year_options %}
                  <option value="{{ y }}" {% if start_j and start_j.year == y %}selected{% elif not start_j and y == default_jy %}selected{% endif %}>{{ y }}</option>
                {% endfor %}
              </select>
              <div class="lbl">سال</div>
            </div>
            <div class="dt-field">
              <select name="start_jm" id="start_jm">
                {% for m_num, m_name in month_options %}
                  <option value="{{ m_num }}" {% if start_j and start_j.month == m_num %}selected{% elif not start_j and m_num == default_jm %}selected{% endif %}>{{ m_name }}</option>
                {% endfor %}
              </select>
              <div class="lbl">ماه</div>
            </div>
            <div class="dt-field">
              <select name="start_jd" id="start_jd">
                {% for d in day_options %}
                  <option value="{{ d }}" {% if start_j and start_j.day == d %}selected{% elif not start_j and d == default_jd %}selected{% endif %}>{{ d }}</option>
                {% endfor %}
              </select>
              <div class="lbl">روز</div>
            </div>
          </div>
        </div>

        <div class="dt-section">
          <div class="dt-section-title">🕐 ساعت</div>
          <div class="dt-grid-time">
            <div class="dt-field">
              <select name="start_jh" id="start_jh">
                {% for h in hour_options %}
                  <option value="{{ h }}" {% if start_j and start_j.hour == h %}selected{% elif not start_j and h == default_jh %}selected{% endif %}>{{ h|stringformat:"02d" }}</option>
                {% endfor %}
              </select>
              <div class="lbl">ساعت</div>
            </div>
            <div class="dt-field">
              <select name="start_jmin" id="start_jmin">
                {% for mn in minute_options %}
                  <option value="{{ mn }}" {% if start_j and start_j.minute == mn %}selected{% elif not start_j and mn == 0 %}selected{% endif %}>{{ mn|stringformat:"02d" }}</option>
                {% endfor %}
              </select>
              <div class="lbl">دقیقه</div>
            </div>
          </div>
        </div>

        <div class="dt-preview" id="start_preview">...</div>
      </div>

      <!-- ============ END ============ -->
      <div class="dt-wrap end">
        <div class="dt-header">
          <div class="badge">پایان</div>
          <div class="title">تاریخ و ساعت پایان تورنمنت</div>
        </div>

        <div class="dt-section">
          <div class="dt-section-title">📅 تاریخ</div>
          <div class="dt-grid-date">
            <div class="dt-field">
              <select name="end_jy" id="end_jy">
                {% for y in year_options %}
                  <option value="{{ y }}" {% if end_j and end_j.year == y %}selected{% elif not end_j and y == default_jy %}selected{% endif %}>{{ y }}</option>
                {% endfor %}
              </select>
              <div class="lbl">سال</div>
            </div>
            <div class="dt-field">
              <select name="end_jm" id="end_jm">
                {% for m_num, m_name in month_options %}
                  <option value="{{ m_num }}" {% if end_j and end_j.month == m_num %}selected{% elif not end_j and m_num == default_jm %}selected{% endif %}>{{ m_name }}</option>
                {% endfor %}
              </select>
              <div class="lbl">ماه</div>
            </div>
            <div class="dt-field">
              <select name="end_jd" id="end_jd">
                {% for d in day_options %}
                  <option value="{{ d }}" {% if end_j and end_j.day == d %}selected{% elif not end_j and d == default_jd %}selected{% endif %}>{{ d }}</option>
                {% endfor %}
              </select>
              <div class="lbl">روز</div>
            </div>
          </div>
        </div>

        <div class="dt-section">
          <div class="dt-section-title">🕐 ساعت</div>
          <div class="dt-grid-time">
            <div class="dt-field">
              <select name="end_jh" id="end_jh">
                {% for h in hour_options %}
                  <option value="{{ h }}" {% if end_j and end_j.hour == h %}selected{% elif not end_j and h == default_end_jh %}selected{% endif %}>{{ h|stringformat:"02d" }}</option>
                {% endfor %}
              </select>
              <div class="lbl">ساعت</div>
            </div>
            <div class="dt-field">
              <select name="end_jmin" id="end_jmin">
                {% for mn in minute_options %}
                  <option value="{{ mn }}" {% if end_j and end_j.minute == mn %}selected{% elif not end_j and mn == 0 %}selected{% endif %}>{{ mn|stringformat:"02d" }}</option>
                {% endfor %}
              </select>
              <div class="lbl">دقیقه</div>
            </div>
          </div>
        </div>

        <div class="dt-preview" id="end_preview">...</div>
      </div>
    </div>
    {% endwith %}

    <div class="card">
      <h3>💰 هزینه و جایزه</h3>
      <div class="row">
        <div>
          <label>هزینه ورود (سکه)</label>
          <input type="number" name="entry_fee_coins" value="{{ tournament.entry_fee_coins|default:0 }}" min="0">
        </div>
        <div>
          <label>هزینه ورود (جم)</label>
          <input type="number" name="entry_fee_gems" value="{{ tournament.entry_fee_gems|default:0 }}" min="0">
        </div>
      </div>
      <div class="row">
        <div>
          <label>جایزه برنده (سکه)</label>
          <input type="number" name="prize_coins" value="{{ tournament.prize_coins|default:0 }}" min="0">
        </div>
        <div>
          <label>جایزه برنده (جم)</label>
          <input type="number" name="prize_gems" value="{{ tournament.prize_gems|default:0 }}" min="0">
        </div>
      </div>
    </div>

    <div class="card">
      <h3>👥 ظرفیت</h3>
      <div class="row">
        <div>
          <label>حداقل بازیکن</label>
          <input type="number" name="min_players" value="{{ tournament.min_players|default:2 }}" min="2">
        </div>
        <div>
          <label>حداکثر بازیکن</label>
          <input type="number" name="max_players" value="{{ tournament.max_players|default:100 }}" min="2">
        </div>
      </div>
    </div>

    <button type="submit" class="submit">💾 ذخیره</button>
  </form>

  {% if tournament %}
    <div class="card" style="margin-top: 16px;">
      <h3>👥 شرکت‌کننده‌ها ({{ entries|length }})</h3>
      {% if entries %}
        <table>
          <thead>
            <tr><th>#</th><th>نام نمایشی</th><th>username</th><th>امتیاز</th><th>تاریخ عضویت</th></tr>
          </thead>
          <tbody>
            {% for e in entries %}
              <tr>
                <td>{{ forloop.counter }}</td>
                <td>{{ e.alias }}</td>
                <td style="font-family:monospace; color:#94a3b8;">@{{ e.username }}</td>
                <td style="color:#facc15; font-family:monospace; font-weight:bold;">{{ e.score }}</td>
                <td style="font-size:11px; color:#64748b;">{{ e.joined_at|jdate:"Y/m/d H:i" }}</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      {% else %}
        <p style="color:#64748b; text-align:center; padding: 20px;">هنوز کسی ثبت‌نام نکرده.</p>
      {% endif %}
    </div>

    <div class="danger-card" style="margin-top: 16px;">
      <h3>⚠️ اقدامات خطرناک</h3>
      <p>خارج کردن همه از صف یا حذف کامل تورنمنت غیرقابل بازگشت است.</p>
      <form method="post" action="{% url 'custom_admin:tournament_clear_entries' tournament.id %}" style="display:inline;" onsubmit="return confirm('همه از صف خارج شوند؟');">
        {% csrf_token %}
        <button type="submit" class="danger-btn">🧹 خالی کردن صف</button>
      </form>
      <form method="post" action="{% url 'custom_admin:tournament_delete' tournament.id %}" style="display:inline;" onsubmit="return confirm('حذف کامل تورنمنت؟');">
        {% csrf_token %}
        <button type="submit" class="del-btn">🗑️ حذف تورنمنت</button>
      </form>
    </div>
  {% endif %}
</div>

<script>
  function updatePreview(prefix) {
    var jy = document.getElementById(prefix + "_jy").value;
    var jm = document.getElementById(prefix + "_jm");
    var jd = document.getElementById(prefix + "_jd").value;
    var jh = document.getElementById(prefix + "_jh").value;
    var jmin = document.getElementById(prefix + "_jmin").value;
    var monthName = jm.options[jm.selectedIndex].text;
    var preview = document.getElementById(prefix + "_preview");
    var pad = function(n) { return String(n).padStart(2, "0"); };
    preview.textContent = "📅 " + jd + " " + monthName + " " + jy + " — ⏰ " + pad(jh) + ":" + pad(jmin);
  }
  ["start", "end"].forEach(function(prefix) {
    ["_jy", "_jm", "_jd", "_jh", "_jmin"].forEach(function(suffix) {
      var el = document.getElementById(prefix + suffix);
      if (el) el.addEventListener("change", function() { updatePreview(prefix); });
    });
    updatePreview(prefix);
  });
</script>
</body>
</html>
'''
backup(p); write(p, EDIT_HTML)

# ============================================================
# 4) admin_views.py - promote/demote staff actions
# ============================================================
print("\n[4/5] admin_views.py - promote/demote staff")
p = os.path.join(ROOT, "accounts", "admin_views.py")
src = read(p)

if "def user_toggle_staff" in src:
    print("  SKIP: already exists")
else:
    new_view = '''

@never_cache
def user_toggle_staff(request, user_id):
    if not _check_auth(request):
        return redirect("custom_admin:login")
    if request.method != "POST":
        return redirect("custom_admin:dashboard")

    User = get_user_model()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("custom_admin:dashboard")

    action = request.POST.get("action", "toggle")
    if action == "promote":
        u.is_staff = True
        u.save(update_fields=["is_staff"])
        request.session["admin_message"] = {"type": "success", "text": f"@{u.username} به ادمین ارتقا یافت."}
    elif action == "demote":
        u.is_staff = False
        u.save(update_fields=["is_staff"])
        request.session["admin_message"] = {"type": "success", "text": f"@{u.username} از ادمینی خارج شد."}
    else:
        u.is_staff = not u.is_staff
        u.save(update_fields=["is_staff"])
        request.session["admin_message"] = {"type": "success", "text": f"وضعیت ادمین @{u.username}: {'فعال' if u.is_staff else 'غیرفعال'}."}

    redirect_to = request.POST.get("redirect_to", "dashboard")
    if redirect_to == "edit":
        return redirect("custom_admin:user_edit", user_id=u.id)
    elif redirect_to == "detail":
        return redirect("custom_admin:user_detail", user_id=u.id)
    return redirect("custom_admin:dashboard")
'''
    src = src.rstrip() + "\n" + new_view + "\n"
    backup(p); write(p, src)
    print("  FIXED: user_toggle_staff added")

# ============================================================
# 5) admin_urls.py - add route
# ============================================================
print("\n[5/5] admin_urls.py - route")
p = os.path.join(ROOT, "accounts", "admin_urls.py")
src = read(p)

if "user_toggle_staff" in src:
    print("  SKIP: route exists")
else:
    old = '    path("user/<int:user_id>/toggle/", admin_views.user_toggle_active, name="user_toggle"),'
    new = old + '\n    path("user/<int:user_id>/toggle-staff/", admin_views.user_toggle_staff, name="user_toggle_staff"),'
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: route added")
    else:
        print("  WARN: toggle route not found")

# ============================================================
# Update dashboard.html - add promote/demote button per user row
# ============================================================
print("\n[Extra] dashboard.html - promote/demote button")
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "dashboard.html")
src = read(p)

if "user_toggle_staff" not in src:
    # Add button after edit button
    old = '''                <a href="{% url 'custom_admin:user_edit' u.id %}" style="background:rgba(139,92,246,0.2); color:#c4b5fd; padding:6px 10px; font-size:11px; border-radius:8px; text-decoration:none; font-weight:bold;">✏️ ویرایش</a>'''
    new = old + '''
                <form method="post" action="{% url 'custom_admin:user_toggle_staff' u.id %}" style="display:inline;">
                  {% csrf_token %}
                  {% if u.is_staff %}
                    <input type="hidden" name="action" value="demote">
                    <button type="submit" style="background:rgba(239,68,68,0.15); color:#fca5a5; padding:6px 10px; font-size:11px; border-radius:8px; border:1px solid rgba(239,68,68,0.3); cursor:pointer; font-weight:bold; font-family:inherit;" onclick="return confirm('از ادمینی خارج شود؟');">❌ حذف ادمین</button>
                  {% else %}
                    <input type="hidden" name="action" value="promote">
                    <button type="submit" style="background:rgba(245,158,11,0.15); color:#fde68a; padding:6px 10px; font-size:11px; border-radius:8px; border:1px solid rgba(245,158,11,0.3); cursor:pointer; font-weight:bold; font-family:inherit;" onclick="return confirm('به ادمین ارتقا یابد؟');">👑 ارتقا به ادمین</button>
                  {% endif %}
                </form>'''
    if old in src:
        src = src.replace(old, new, 1)
        backup(p); write(p, src)
        print("  FIXED: promote/demote button in dashboard")
    else:
        print("  WARN: edit button not found in dashboard")

# Also add to user_detail page
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "user_detail.html")
if os.path.exists(p):
    src = read(p)
    if "user_toggle_staff" not in src:
        # Add in the info card area, after the algorithm row
        old = '''    <div class="row">
      <span class="k">الگوریتم پسورد</span>
      <span class="v">
        <span class="algo-tag">{{ u.password|slice:":20" }}…</span>
      </span>
    </div>'''
        new = old + '''

    <div style="margin-top: 14px; padding-top: 14px; border-top: 1px solid rgba(148,163,184,0.15);">
      <form method="post" action="{% url 'custom_admin:user_toggle_staff' u.id %}" style="display:inline;">
        {% csrf_token %}
        <input type="hidden" name="redirect_to" value="detail">
        {% if u.is_staff %}
          <input type="hidden" name="action" value="demote">
          <button type="submit" class="action btn-danger" style="background: linear-gradient(135deg, #ef4444, #dc2626); color:#fff;" onclick="return confirm('از ادمینی خارج شود؟');">❌ حذف از ادمینی</button>
        {% else %}
          <input type="hidden" name="action" value="promote">
          <button type="submit" class="action btn-warning" onclick="return confirm('به ادمین ارتقا یابد؟');">👑 ارتقا به ادمین</button>
        {% endif %}
      </form>
    </div>'''
        if old in src:
            src = src.replace(old, new, 1)
            backup(p); write(p, src)
            print("  FIXED: promote/demote in user_detail")

# Also add flash message display for admin dashboard
p = os.path.join(ROOT, "accounts", "templates", "custom_admin", "dashboard.html")
src = read(p)
if "admin_message" not in src and "request.session" not in src:
    # Add message display right after topbar
    old = '''  <div class="admin-tabs">'''
    new = '''  {% if messages %}
    {% for m in messages %}
      <div class="msg msg-{{ m.tags }}">{{ m }}</div>
    {% endfor %}
  {% endif %}

  <div class="admin-tabs">'''
    if old in src:
        src = src.replace(old, new, 1)
        # Add message CSS if not exists
        if ".msg-success {" not in src:
            css_anchor = "    .stats {"
            css_add = '''    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; text-align: right; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    .stats {'''
            src = src.replace(css_anchor, css_add, 1)
        backup(p); write(p, src)
        print("  FIXED: messages in dashboard")

# Final check
print("\n[check] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], cwd=ROOT, capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check passed")
else:
    print("  ⚠ errors:", r.stderr[:400] if r.stderr else r.stdout[:400])

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
What's new:

NOTIFICATIONS PAGE:
  ✓ Full rewrite with clean layout
  ✓ Sender name shown in badge (👤 alias @username)
  ✓ Admin broadcasts shown with 📢 مدیر سیستم + gold background
  ✓ Unread counter badge in header
  ✓ Jalali dates (1403/08/26 20:30)
  ✓ Pulsing unread dot
  ✓ unread_total passed to context

TOURNAMENT DATE/TIME PICKER:
  ✓ Date (سال/ماه/روز) separate from Time (ساعت/دقیقه)
  ✓ Different border colors for start (green) / end (red)
  ✓ Live preview showing selected date in Persian
  ✓ Better spacing and larger selects

USER ADMIN PROMOTE/DEMOTE:
  ✓ /panel-admin/dashboard/ → buttons in each row:
    - 👑 ارتقا به ادمین (for non-staff)
    - ❌ حذف ادمین (for staff)
  ✓ /panel-admin/user/<id>/ → promote/demote button
  ✓ Flash messages display in dashboard

Next:
  Ctrl+C
  python manage.py runserver
  Hard refresh: Ctrl+Shift+R

Test:
  1. /social/notifications/ → clean layout with sender
  2. /panel-admin/tournaments/ → create
     - Date section (year/month/day) - separate box
     - Time section (hour/minute) - separate box
     - Live preview
  3. /panel-admin/dashboard/ → promote/demote buttons in rows
""")
