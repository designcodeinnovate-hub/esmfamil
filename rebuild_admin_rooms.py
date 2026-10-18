#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix admin tabs + rebuild rooms page with categories + live game info."""
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    if not os.path.exists(p): return ""
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Fix admin tabs CSS in ALL admin templates
# ============================================================
print("\n[1/7] Fixing admin tabs CSS in all pages")

# Tabs that exist
ADMIN_TABS = [
    ("/panel-admin/dashboard/", "👥 کاربران"),
    ("/panel-admin/alliances/", "🛡️ اتحادها"),
    ("/panel-admin/rooms/", "🚪 اتاق‌ها"),
    ("/panel-admin/announcements/", "📢 اعلان‌ها"),
    ("/panel-admin/tournaments/", "🏆 تورنمنت"),
    ("/panel-admin/shop/", "🛒 فروشگاه"),
    ("/panel-admin/guest-log/", "🎲 مهمان‌ها"),
    ("/panel-admin/send-to-all/", "🎁 جایزه همه"),
]

def build_tabs_html(active_url):
    """Build consistent tabs HTML."""
    html = '<div class="admin-tabs">\n'
    for url, label in ADMIN_TABS:
        active_class = " active" if url == active_url else ""
        html += f'    <a href="{url}" class="admin-tab{active_class}">{label}</a>\n'
    html += '</div>'
    return html

# Fix CSS in all admin templates
admin_tpls = [
    "accounts/templates/custom_admin/dashboard.html",
    "accounts/templates/custom_admin/alliances.html",
    "accounts/templates/custom_admin/alliance_detail.html",
    "accounts/templates/custom_admin/rooms.html",
    "accounts/templates/custom_admin/announcements.html",
    "accounts/templates/custom_admin/tournaments.html",
    "accounts/templates/custom_admin/tournament_edit.html",
    "accounts/templates/custom_admin/shop_items.html",
    "accounts/templates/custom_admin/guest_log.html",
    "accounts/templates/custom_admin/send_to_all.html",
    "accounts/templates/custom_admin/user_detail.html",
    "accounts/templates/custom_admin/user_edit.html",
    "accounts/templates/custom_admin/user_notify.html",
]

# New improved CSS
NEW_TABS_CSS = '''
    .admin-tabs {
      display: flex;
      gap: 6px;
      margin-bottom: 20px;
      background: #12121f;
      border: 1px solid rgba(148,163,184,0.15);
      padding: 8px;
      border-radius: 14px;
      overflow-x: auto;
      overflow-y: hidden;
      white-space: nowrap;
      scrollbar-width: thin;
      scrollbar-color: rgba(139,92,246,0.5) transparent;
    }
    .admin-tabs::-webkit-scrollbar { height: 6px; }
    .admin-tabs::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.5); border-radius: 6px; }
    .admin-tabs::-webkit-scrollbar-track { background: transparent; }
    .admin-tab {
      flex: 0 0 auto;
      padding: 10px 14px;
      border-radius: 10px;
      text-align: center;
      text-decoration: none;
      font-size: 12px;
      font-weight: bold;
      color: #94a3b8;
      transition: 0.2s;
      white-space: nowrap;
    }
    .admin-tab:hover { background: rgba(148,163,184,0.1); color: #fff; }
    .admin-tab.active {
      background: linear-gradient(135deg, #ef4444, #dc2626);
      color: #fff;
      box-shadow: 0 6px 20px rgba(239,68,68,0.4);
    }
'''

for tpl in admin_tpls:
    src = read(tpl)
    if not src:
        continue

    # Replace existing .admin-tabs CSS
    if ".admin-tabs {" in src:
        # Find the CSS block
        pattern = re.compile(r'\s*\.admin-tabs\s*\{[^}]+\}', re.MULTILINE)
        src = pattern.sub('\n    .admin-tabs {' + '\n      display: flex;\n      gap: 6px;\n      margin-bottom: 20px;\n      background: #12121f;\n      border: 1px solid rgba(148,163,184,0.15);\n      padding: 8px;\n      border-radius: 14px;\n      overflow-x: auto;\n      overflow-y: hidden;\n      white-space: nowrap;\n      scrollbar-width: thin;\n    }', src, count=1)

        # Replace .admin-tab (single)
        pattern = re.compile(r'\s*\.admin-tab\s*\{[^}]+\}', re.MULTILINE)
        src = pattern.sub('\n    .admin-tab {\n      flex: 0 0 auto;\n      padding: 10px 14px;\n      border-radius: 10px;\n      text-align: center;\n      text-decoration: none;\n      font-size: 12px;\n      font-weight: bold;\n      color: #94a3b8;\n      transition: 0.2s;\n      white-space: nowrap;\n    }', src, count=1)

        # Replace .admin-tab.active
        pattern = re.compile(r'\s*\.admin-tab\.active\s*\{[^}]+\}', re.MULTILINE)
        src = pattern.sub('\n    .admin-tab.active {\n      background: linear-gradient(135deg, #ef4444, #dc2626);\n      color: #fff;\n      box-shadow: 0 6px 20px rgba(239,68,68,0.4);\n    }', src, count=1)

        # Replace .admin-tab:hover
        pattern = re.compile(r'\s*\.admin-tab:hover\s*\{[^}]+\}', re.MULTILINE)
        src = pattern.sub('\n    .admin-tab:hover { background: rgba(148,163,184,0.1); color: #fff; }', src, count=1)

        write(tpl, src)
        print(f"  ✓ Fixed tabs CSS: {os.path.basename(tpl)}")

# ============================================================
# 2) Rebuild admin_views.rooms_list with categorization
# ============================================================
print("\n[2/7] Rebuilding rooms_list view")

p = "accounts/admin_views.py"
src = read(p)

# Remove old rooms_list and rooms_active
old_patterns = [
    r'@never_cache\ndef rooms_list\(request\):.*?(?=\n@never_cache|\ndef |\Z)',
    r'@never_cache\ndef rooms_active\(request\):.*?(?=\n@never_cache|\ndef |\Z)',
]
for pattern in old_patterns:
    m = re.search(pattern, src, re.DOTALL)
    if m:
        src = src[:m.start()] + src[m.end():]

# Remove old _room_data if exists
m = re.search(r'def _room_to_dict[^\(]*\([^\)]*\):.*?(?=\ndef |\Z)', src, re.DOTALL)
if m:
    src = src[:m.start()] + src[m.end():]

new_rooms_code = '''

# ============================================================
# Admin — Rooms (with categorization + live game info)
# ============================================================
def _room_to_dict(g):
    """Convert Game to dict with all needed info."""
    players = []
    for p in g.players.select_related("user").all():
        players.append({
            "alias": p.user.alias,
            "username": p.user.username,
            "avatar": p.user.avatar_id,
            "score": p.score,
            "ready": p.is_ready,
            "team": p.team,
            "stopped": p.stopped_round,
        })

    active_round = g.rounds.order_by("-number").first()

    # Match description
    match_desc = ""
    if g.mode == "match" and len(players) >= 2:
        match_desc = f"⚔️ {players[0]['alias']} vs {players[1]['alias']}"
    elif g.mode == "team":
        team_a = [p["alias"] for p in players if p["team"] == "A"]
        team_b = [p["alias"] for p in players if p["team"] == "B"]
        a_str = " + ".join(team_a) if team_a else "?"
        b_str = " + ".join(team_b) if team_b else "?"
        match_desc = f"🔵 {a_str} vs 🔴 {b_str}"
    elif g.mode == "bot":
        match_desc = f"🤖 {g.host.alias} vs Bot"
    elif g.mode == "puzzle":
        match_desc = f"🎯 {g.host.alias} (معما)"
    elif g.mode == "group" and len(players) >= 1:
        names = " + ".join(p["alias"] for p in players[:3])
        if len(players) > 3:
            names += f" +{len(players) - 3}"
        match_desc = f"👥 {names}"

    return {
        "obj": g,
        "code": g.code,
        "room_name": g.room_name or "—",
        "mode": g.mode,
        "status": g.status,
        "host": g.host.alias,
        "host_username": g.host.username,
        "players": players,
        "player_count": len(players),
        "max_players": g.max_players,
        "created_at": g.created_at,
        "current_round": active_round.number if active_round else 0,
        "current_letter": active_round.letter if active_round else "—",
        "match_desc": match_desc,
    }


@never_cache
def rooms_list(request):
    if not _check_auth(request):
        return redirect("custom_admin:login")

    from game.models import Game

    all_rooms = Game.objects.all().order_by("-created_at")

    # Group by status
    in_round = [_room_to_dict(g) for g in all_rooms.filter(status="in_round")[:50]]
    round_result = [_room_to_dict(g) for g in all_rooms.filter(status="round_result")[:30]]
    waiting = [_room_to_dict(g) for g in all_rooms.filter(status="waiting")[:50]]
    finished = [_room_to_dict(g) for g in all_rooms.filter(status="finished")[:50]]

    message = request.session.pop("admin_message", None)

    return render(request, "custom_admin/rooms.html", {
        "in_round": in_round,
        "round_result": round_result,
        "waiting": waiting,
        "finished": finished,
        "count_in_round": all_rooms.filter(status="in_round").count(),
        "count_round_result": all_rooms.filter(status="round_result").count(),
        "count_waiting": all_rooms.filter(status="waiting").count(),
        "count_finished": all_rooms.filter(status="finished").count(),
        "count_total": all_rooms.count(),
        "message": message,
    })


@never_cache
def rooms_active(request):
    """Redirect to main rooms page (everything is there)."""
    return redirect("custom_admin:rooms_list")
'''

src = src.rstrip() + new_rooms_code + "\n"
write(p, src)
print("  ✓ rooms_list rebuilt")

# ============================================================
# 3) Rebuild rooms.html admin template
# ============================================================
print("\n[3/7] Rebuilding rooms.html admin template")

# Load jalali tags
ROOMS_HTML = '''{% load jalali_tags %}<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>اتاق‌ها — پنل ادمین</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, sans-serif; min-height: 100vh; background: #0a0a15; color: #e2e8f0; padding: 20px 16px 40px; }
    .container { max-width: 1400px; margin: 0 auto; }

    .topbar { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #1e1b4b, #0f0f1e); border: 1px solid rgba(239,68,68,0.3); padding: 16px 22px; border-radius: 16px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
    .topbar h1 { font-size: 20px; color: #fca5a5; }
    .topbar a { padding: 9px 16px; border-radius: 10px; background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; text-decoration: none; font-size: 13px; font-weight: bold; }

    .admin-tabs {
      display: flex; gap: 6px; margin-bottom: 20px;
      background: #12121f; border: 1px solid rgba(148,163,184,0.15);
      padding: 8px; border-radius: 14px;
      overflow-x: auto; overflow-y: hidden;
      white-space: nowrap; scrollbar-width: thin;
    }
    .admin-tabs::-webkit-scrollbar { height: 6px; }
    .admin-tabs::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.5); border-radius: 6px; }
    .admin-tab {
      flex: 0 0 auto; padding: 10px 14px; border-radius: 10px;
      text-align: center; text-decoration: none;
      font-size: 12px; font-weight: bold; color: #94a3b8;
      transition: 0.2s; white-space: nowrap;
    }
    .admin-tab:hover { background: rgba(148,163,184,0.1); color: #fff; }
    .admin-tab.active { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; box-shadow: 0 6px 20px rgba(239,68,68,0.4); }

    .msg { padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 16px; }
    .msg-success { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .msg-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.35); }

    /* Stats overview */
    .stats-overview { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 24px; }
    @media (max-width: 700px) { .stats-overview { grid-template-columns: 1fr 1fr; } }
    .stat-card { padding: 16px; border-radius: 14px; text-align: center; }
    .stat-card.live { background: linear-gradient(135deg, rgba(34,197,94,0.2), rgba(15,23,42,0.6)); border: 1.5px solid rgba(34,197,94,0.4); }
    .stat-card.waiting { background: linear-gradient(135deg, rgba(234,179,8,0.2), rgba(15,23,42,0.6)); border: 1.5px solid rgba(234,179,8,0.4); }
    .stat-card.result { background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(15,23,42,0.6)); border: 1.5px solid rgba(59,130,246,0.4); }
    .stat-card.finished { background: linear-gradient(135deg, rgba(100,116,139,0.2), rgba(15,23,42,0.6)); border: 1.5px solid rgba(100,116,139,0.4); }
    .stat-val { font-size: 28px; font-weight: 900; font-family: monospace; color: #fff; margin-bottom: 4px; }
    .stat-lbl { font-size: 11px; color: #94a3b8; font-weight: bold; }

    /* Section */
    .section { margin-bottom: 28px; }
    .section-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid rgba(148,163,184,0.1); }
    .section-head h2 { font-size: 16px; font-weight: 900; color: #fff; }
    .section-head .badge-count { padding: 3px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; font-family: monospace; }
    .section-head.live .badge-count { background: rgba(34,197,94,0.2); color: #4ade80; }
    .section-head.waiting .badge-count { background: rgba(234,179,8,0.2); color: #fde68a; }
    .section-head.result .badge-count { background: rgba(59,130,246,0.2); color: #93c5fd; }
    .section-head.finished .badge-count { background: rgba(100,116,139,0.2); color: #cbd5e1; }
    .live-pulse { display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 10px #4ade80; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.4); opacity: 0.5; } }

    /* Room card */
    .room-card {
      background: #12121f; border: 1.5px solid rgba(148,163,184,0.15);
      border-radius: 14px; padding: 16px; margin-bottom: 10px;
      transition: 0.2s;
    }
    .room-card.live { border-color: rgba(34,197,94,0.4); background: linear-gradient(135deg, rgba(34,197,94,0.05), #12121f); }
    .room-card.waiting { border-color: rgba(234,179,8,0.4); background: linear-gradient(135deg, rgba(234,179,8,0.05), #12121f); }
    .room-card.result { border-color: rgba(59,130,246,0.4); }
    .room-card.finished {
      opacity: 0.4;
      background: #0a0a15;
      border-color: rgba(100,116,139,0.2);
    }
    .room-card.finished:hover { opacity: 0.6; }

    .room-top { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
    .room-code { font-family: monospace; font-size: 18px; font-weight: 900; color: #facc15; padding: 4px 10px; background: rgba(250,204,21,0.1); border-radius: 8px; border: 1px solid rgba(250,204,21,0.3); }
    .room-name { font-size: 15px; font-weight: bold; color: #fff; }
    .room-mode { padding: 3px 10px; border-radius: 6px; font-size: 10px; font-weight: bold; background: rgba(139,92,246,0.15); color: #c4b5fd; font-family: monospace; }
    .room-status { padding: 3px 10px; border-radius: 6px; font-size: 10px; font-weight: bold; }
    .status-live { background: rgba(34,197,94,0.2); color: #4ade80; }
    .status-waiting { background: rgba(234,179,8,0.2); color: #fde68a; }
    .status-result { background: rgba(59,130,246,0.2); color: #93c5fd; }
    .status-finished { background: rgba(100,116,139,0.2); color: #cbd5e1; }

    .room-match { padding: 10px 14px; background: rgba(15,23,42,0.6); border-radius: 10px; margin-bottom: 10px; font-size: 13px; color: #e2e8f0; font-weight: bold; }

    .room-info { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; margin-bottom: 10px; }
    .info-item { padding: 8px 10px; background: rgba(15,23,42,0.4); border-radius: 8px; font-size: 11px; }
    .info-item .lbl { color: #64748b; font-size: 10px; margin-bottom: 2px; }
    .info-item .val { color: #fff; font-weight: bold; font-family: monospace; }

    .room-players { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
    .player-chip { padding: 6px 12px; background: rgba(139,92,246,0.15); border: 1px solid rgba(139,92,246,0.3); border-radius: 20px; font-size: 11px; color: #c4b5fd; font-weight: bold; }
    .player-chip.host { background: rgba(250,204,21,0.15); border-color: rgba(250,204,21,0.4); color: #facc15; }
    .player-chip.ready { background: rgba(34,197,94,0.15); border-color: rgba(34,197,94,0.4); color: #4ade80; }
    .player-chip.team-a { background: rgba(59,130,246,0.15); border-color: rgba(59,130,246,0.4); color: #93c5fd; }
    .player-chip.team-b { background: rgba(239,68,68,0.15); border-color: rgba(239,68,68,0.4); color: #fca5a5; }

    .room-actions { display: flex; gap: 8px; margin-top: 10px; }
    .btn-del { padding: 8px 16px; background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); border-radius: 8px; font-family: inherit; font-size: 11px; font-weight: bold; cursor: pointer; }
    .btn-del:hover { background: rgba(239,68,68,0.3); }

    .empty-state { text-align: center; padding: 30px 20px; color: #64748b; font-size: 13px; }
    .empty-state .icon { font-size: 40px; display: block; margin-bottom: 8px; opacity: 0.4; }
  </style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <h1>🚪 مدیریت اتاق‌ها و بازی‌های فعال</h1>
    <a href="{% url 'custom_admin:logout' %}">خروج</a>
  </div>

  <div class="admin-tabs">
    <a href="/panel-admin/dashboard/" class="admin-tab">👥 کاربران</a>
    <a href="/panel-admin/alliances/" class="admin-tab">🛡️ اتحادها</a>
    <a href="/panel-admin/rooms/" class="admin-tab active">🚪 اتاق‌ها</a>
    <a href="/panel-admin/announcements/" class="admin-tab">📢 اعلان‌ها</a>
    <a href="/panel-admin/tournaments/" class="admin-tab">🏆 تورنمنت</a>
    <a href="/panel-admin/shop/" class="admin-tab">🛒 فروشگاه</a>
    <a href="/panel-admin/guest-log/" class="admin-tab">🎲 مهمان‌ها</a>
    <a href="/panel-admin/send-to-all/" class="admin-tab">🎁 جایزه همه</a>
  </div>

  {% if message %}<div class="msg msg-{{ message.type }}">{{ message.text }}</div>{% endif %}

  <div class="stats-overview">
    <div class="stat-card live">
      <div class="stat-val">{{ count_in_round }}</div>
      <div class="stat-lbl"><span class="live-pulse"></span> در حال بازی</div>
    </div>
    <div class="stat-card waiting">
      <div class="stat-val">{{ count_waiting }}</div>
      <div class="stat-lbl">در انتظار</div>
    </div>
    <div class="stat-card result">
      <div class="stat-val">{{ count_round_result }}</div>
      <div class="stat-lbl">نتیجه راند</div>
    </div>
    <div class="stat-card finished">
      <div class="stat-val">{{ count_finished }}</div>
      <div class="stat-lbl">تمام‌شده</div>
    </div>
  </div>

  <!-- ==================== LIVE GAMES ==================== -->
  <div class="section">
    <div class="section-head live">
      <span class="live-pulse"></span>
      <h2>🔴 در حال بازی (Live)</h2>
      <span class="badge-count">{{ count_in_round }}</span>
    </div>
    {% if in_round %}
      {% for r in in_round %}
      <div class="room-card live">
        <div class="room-top">
          <span class="room-code">{{ r.code }}</span>
          <span class="room-name">{{ r.room_name }}</span>
          <span class="room-mode">{{ r.mode }}</span>
          <span class="room-status status-live">● در حال بازی</span>
        </div>
        {% if r.match_desc %}
        <div class="room-match">🎮 {{ r.match_desc }}</div>
        {% endif %}
        <div class="room-info">
          <div class="info-item"><div class="lbl">میزبان</div><div class="val">{{ r.host }}</div></div>
          <div class="info-item"><div class="lbl">بازیکنان</div><div class="val">{{ r.player_count }} / {{ r.max_players }}</div></div>
          <div class="info-item"><div class="lbl">راند</div><div class="val">{{ r.current_round }}</div></div>
          <div class="info-item"><div class="lbl">حرف</div><div class="val" style="color:#facc15; font-size:16px;">{{ r.current_letter }}</div></div>
          <div class="info-item"><div class="lbl">شروع</div><div class="val" style="font-size:10px;">{{ r.created_at|jdate:"H:i" }}</div></div>
        </div>
        <div class="room-players">
          {% for p in r.players %}
            <span class="player-chip {% if p.username == r.host_username %}host{% endif %} {% if p.team == 'A' %}team-a{% elif p.team == 'B' %}team-b{% endif %} {% if p.ready %}ready{% endif %}">
              {% if p.username == r.host_username %}👑 {% endif %}{{ p.alias }} ({{ p.score }})
            </span>
          {% endfor %}
        </div>
        <div class="room-actions">
          <form method="post" action="{% url 'custom_admin:room_delete' r.obj.id %}" onsubmit="return confirm('حذف اتاق {{ r.code }}؟');">
            {% csrf_token %}
            <button type="submit" class="btn-del">🗑️ حذف اتاق</button>
          </form>
        </div>
      </div>
      {% endfor %}
    {% else %}
      <div class="empty-state"><span class="icon">🎮</span>هیچ بازی در حال اجرا نیست.</div>
    {% endif %}
  </div>

  <!-- ==================== WAITING ROOMS ==================== -->
  <div class="section">
    <div class="section-head waiting">
      <h2>⏳ اتاق‌های در انتظار</h2>
      <span class="badge-count">{{ count_waiting }}</span>
    </div>
    {% if waiting %}
      {% for r in waiting %}
      <div class="room-card waiting">
        <div class="room-top">
          <span class="room-code">{{ r.code }}</span>
          <span class="room-name">{{ r.room_name }}</span>
          <span class="room-mode">{{ r.mode }}</span>
          <span class="room-status status-waiting">در انتظار بازیکنان</span>
        </div>
        {% if r.match_desc %}
        <div class="room-match">{{ r.match_desc }}</div>
        {% endif %}
        <div class="room-info">
          <div class="info-item"><div class="lbl">میزبان</div><div class="val">{{ r.host }}</div></div>
          <div class="info-item"><div class="lbl">بازیکنان</div><div class="val">{{ r.player_count }} / {{ r.max_players }}</div></div>
          <div class="info-item"><div class="lbl">شروع</div><div class="val" style="font-size:10px;">{{ r.created_at|jdate:"H:i" }}</div></div>
        </div>
        <div class="room-players">
          {% for p in r.players %}
            <span class="player-chip {% if p.username == r.host_username %}host{% endif %} {% if p.ready %}ready{% endif %}">
              {% if p.username == r.host_username %}👑 {% endif %}{{ p.alias }}{% if p.ready %} ✓{% endif %}
            </span>
          {% empty %}
            <span style="color:#64748b; font-size:11px;">هیچ بازیکنی داخل نیست</span>
          {% endfor %}
        </div>
        <div class="room-actions">
          <form method="post" action="{% url 'custom_admin:room_delete' r.obj.id %}" onsubmit="return confirm('حذف اتاق {{ r.code }}؟');">
            {% csrf_token %}
            <button type="submit" class="btn-del">🗑️ حذف اتاق</button>
          </form>
        </div>
      </div>
      {% endfor %}
    {% else %}
      <div class="empty-state"><span class="icon">⏳</span>هیچ اتاقی در انتظار نیست.</div>
    {% endif %}
  </div>

  <!-- ==================== ROUND RESULT ==================== -->
  {% if count_round_result > 0 %}
  <div class="section">
    <div class="section-head result">
      <h2>📊 در حال نمایش نتیجه</h2>
      <span class="badge-count">{{ count_round_result }}</span>
    </div>
    {% for r in round_result %}
    <div class="room-card result">
      <div class="room-top">
        <span class="room-code">{{ r.code }}</span>
        <span class="room-name">{{ r.room_name }}</span>
        <span class="room-status status-result">نتیجه راند {{ r.current_round }}</span>
      </div>
      {% if r.match_desc %}<div class="room-match">{{ r.match_desc }}</div>{% endif %}
      <div class="room-players">
        {% for p in r.players %}
          <span class="player-chip {% if p.username == r.host_username %}host{% endif %}">{{ p.alias }} ({{ p.score }})</span>
        {% endfor %}
      </div>
      <div class="room-actions">
        <form method="post" action="{% url 'custom_admin:room_delete' r.obj.id %}" onsubmit="return confirm('حذف اتاق {{ r.code }}؟');">
          {% csrf_token %}
          <button type="submit" class="btn-del">🗑️ حذف اتاق</button>
        </form>
      </div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <!-- ==================== FINISHED (GRAYED) ==================== -->
  <div class="section">
    <div class="section-head finished">
      <h2>🏁 اتاق‌های بسته شده</h2>
      <span class="badge-count">{{ count_finished }}</span>
    </div>
    {% if finished %}
      {% for r in finished %}
      <div class="room-card finished">
        <div class="room-top">
          <span class="room-code">{{ r.code }}</span>
          <span class="room-name">{{ r.room_name }}</span>
          <span class="room-mode">{{ r.mode }}</span>
          <span class="room-status status-finished">🏁 تمام‌شده</span>
        </div>
        {% if r.match_desc %}<div class="room-match">{{ r.match_desc }}</div>{% endif %}
        <div class="room-info">
          <div class="info-item"><div class="lbl">میزبان</div><div class="val">{{ r.host }}</div></div>
          <div class="info-item"><div class="lbl">بازیکنان</div><div class="val">{{ r.player_count }}</div></div>
          <div class="info-item"><div class="lbl">تاریخ</div><div class="val" style="font-size:10px;">{{ r.created_at|jdate:"Y/m/d H:i" }}</div></div>
        </div>
        <div class="room-players">
          {% for p in r.players %}
            <span class="player-chip" style="opacity:0.7;">{{ p.alias }} ({{ p.score }})</span>
          {% endfor %}
        </div>
        <div class="room-actions">
          <form method="post" action="{% url 'custom_admin:room_delete' r.obj.id %}" onsubmit="return confirm('حذف دائمی این اتاق؟');">
            {% csrf_token %}
            <button type="submit" class="btn-del">🗑️ حذف دائمی</button>
          </form>
        </div>
      </div>
      {% endfor %}
    {% else %}
      <div class="empty-state"><span class="icon">🏁</span>هیچ اتاق بسته‌ای وجود ندارد.</div>
    {% endif %}
  </div>

</div>
</body>
</html>
'''

write("accounts/templates/custom_admin/rooms.html", ROOMS_HTML)
print("  ✓ rooms.html rebuilt")

# ============================================================
# 4) Remove "همه بازی‌ها" bot-btn from menu.html
# ============================================================
print("\n[4/7] Removing 'همه بازی‌ها' from menu.html")

p = "game/templates/game/menu.html"
src = read(p)

# Remove bot-btn with "همه بازی‌ها"
pattern = re.compile(
    r'<!-- همه بازی‌ها -->\s*<a href="/game/rooms/"[^>]*class="bot-btn"[^>]*>.*?</a>\s*',
    re.DOTALL
)
src = pattern.sub('', src, count=1)

# Also try without comment
pattern2 = re.compile(
    r'<a href="/game/rooms/"[^>]*class="bot-btn"[^>]*>.*?</a>\s*',
    re.DOTALL
)
src = pattern2.sub('', src, count=1)

write(p, src)
print("  ✓ 'همه بازی‌ها' removed")

# ============================================================
# 5) Fix all admin templates' tabs CSS + ensure links work
# ============================================================
print("\n[5/7] Fixing tabs in all admin pages")

# Rebuild dashboard.html tabs
for tpl_name in ["dashboard.html", "alliances.html", "announcements.html", "tournaments.html", "shop_items.html", "guest_log.html", "send_to_all.html"]:
    tpl_path = f"accounts/templates/custom_admin/{tpl_name}"
    if not os.path.exists(tpl_path):
        continue

    src = read(tpl_path)

    # Determine current active by checking which has 'active' class near the tab
    active_url = "/panel-admin/dashboard/"
    if "/panel-admin/alliances/" in src and 'href="/panel-admin/alliances/" class="admin-tab active"' in src:
        active_url = "/panel-admin/alliances/"
    elif "/panel-admin/rooms/" in src and 'href="/panel-admin/rooms/" class="admin-tab active"' in src:
        active_url = "/panel-admin/rooms/"
    elif "/panel-admin/announcements/" in src and 'href="/panel-admin/announcements/" class="admin-tab active"' in src:
        active_url = "/panel-admin/announcements/"
    elif "/panel-admin/tournaments/" in src and 'href="/panel-admin/tournaments/" class="admin-tab active"' in src:
        active_url = "/panel-admin/tournaments/"
    elif "/panel-admin/shop/" in src and 'href="/panel-admin/shop/" class="admin-tab active"' in src:
        active_url = "/panel-admin/shop/"
    elif "/panel-admin/guest-log/" in src and 'href="/panel-admin/guest-log/" class="admin-tab active"' in src:
        active_url = "/panel-admin/guest-log/"
    elif "/panel-admin/send-to-all/" in src and 'href="/panel-admin/send-to-all/" class="admin-tab active"' in src:
        active_url = "/panel-admin/send-to-all/"

    # Replace entire admin-tabs div
    pattern = re.compile(r'<div class="admin-tabs">.*?</div>\s*(?=<div class="stats"|<div class="stats-mini"|<div class="search"|<!--|<form|<div class="card"|$)',
                         re.DOTALL)
    m = pattern.search(src)
    if m:
        new_tabs = build_tabs_html(active_url)
        src = src[:m.start()] + new_tabs + "\n\n  " + src[m.end():]
        write(tpl_path, src)
        print(f"  ✓ Rebuilt tabs in {tpl_name}")

# ============================================================
# 6) Fix admin_urls.py to include all routes
# ============================================================
print("\n[6/7] Verifying admin_urls.py")

p = "accounts/admin_urls.py"
src = read(p)

# Make sure all routes exist
required_routes = [
    ('path("", admin_views.admin_login, name="login"),', "login"),
    ('path("dashboard/", admin_views.dashboard, name="dashboard"),', "dashboard"),
    ('path("logout/", admin_views.admin_logout, name="logout"),', "logout"),
    ('path("rooms/", admin_views.rooms_list, name="rooms_list"),', "rooms_list"),
    ('path("rooms/active/", admin_views.rooms_active, name="rooms_active"),', "rooms_active"),
    ('path("send-to-all/", admin_views.send_to_all, name="send_to_all"),', "send_to_all"),
]

for route, name in required_routes:
    if route not in src:
        # Add before closing ]
        src = src.rsplit("]", 1)[0] + route + "\n]"
        print(f"  + Added missing route: {name}")

write(p, src)
print("  ✓ admin_urls.py verified")

# ============================================================
# 7) Final check + test
# ============================================================
print("\n[7/7] Final check + test")

r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:600]}")

# Test pages
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

tu, created = User.objects.get_or_create(
    username="__admin_test_final__",
    defaults={"alias": "admin-test", "is_active": True, "is_staff": True, "has_chosen_avatar": True, "has_completed_registration": True}
)
if created:
    tu.set_password("x")
    tu.save()

c = Client()
c.session["custom_admin_logged_in"] = True
c.session["beta_unlocked"] = True
c.session.save()

admin_urls = [
    "/panel-admin/dashboard/",
    "/panel-admin/alliances/",
    "/panel-admin/rooms/",
    "/panel-admin/announcements/",
    "/panel-admin/tournaments/",
    "/panel-admin/shop/",
    "/panel-admin/guest-log/",
    "/panel-admin/send-to-all/",
]

print("\n  Admin pages test:")
for url in admin_urls:
    try:
        r = c.get(url, follow=False)
        mark = "✓" if r.status_code == 200 else ("→" if r.status_code in (301, 302) else "✗")
        print(f"    {mark} {url:35s} → {r.status_code}")
    except Exception as e:
        print(f"    ✗ {url:35s} → {type(e).__name__}")

# Test menu page
c2 = Client()
c2.force_login(tu)
c2.session["beta_unlocked"] = True
c2.session.save()

print("\n  Player pages test:")
for url in ["/game/", "/game/rooms/", "/game/rooms/manage/"]:
    try:
        r = c2.get(url, follow=False)
        mark = "✓" if r.status_code == 200 else ("→" if r.status_code in (301, 302) else "✗")
        print(f"    {mark} {url:35s} → {r.status_code}")
    except Exception as e:
        print(f"    ✗ {url:35s} → {type(e).__name__}")

if created:
    tu.delete()

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
What was fixed:

  1. Admin tabs CSS — flex: 0 0 auto (no more squishing)
     + horizontal scroll (scrolls nicely on small screens)
     + consistent across all admin pages

  2. Rooms page reorganized into 4 sections:
     🔴 در حال بازی (Live) — pulsing green dot
     ⏳ اتاق‌های در انتظار (Waiting) — yellow
     📊 در حال نمایش نتیجه (Round Result) — blue
     🏁 اتاق‌های بسته شده (Finished) — GRAYED OUT

  3. Live match info shows:
     ⚔️ User A vs User B (for match mode)
     🔵 Team A vs 🔴 Team B (for team mode)
     🤖 Host vs Bot (for bot mode)
     🎯 Host (معما) (for puzzle mode)
     👥 Player list (for group mode)

  4. Player chips show:
     👑 Host, team color, ready state, score

  5. Removed "همه بازی‌ها" card from menu.html

Next:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)

Open /panel-admin/rooms/ to see the new layout.
""")
