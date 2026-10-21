#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

print("\n[1/3] Rebuilding menu.html — home page")
write("game/templates/game/menu.html", '''{% extends "base.html" %}
{% block title %}خانه{% endblock %}

{% block extra_css %}
<style>
  /* ===== Top bar ===== */
  .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
  .version-badge { display: inline-flex; align-items: center; gap: 5px; background: rgba(234, 179, 8, 0.15); color: #facc15; font-size: 10px; padding: 5px 10px; border-radius: 10px; border: 1px solid rgba(234, 179, 8, 0.3); font-weight: bold; }
  .settings-icon { width: 42px; height: 42px; border-radius: 14px; background: var(--card); border: 1.5px solid var(--border); display: flex; align-items: center; justify-content: center; text-decoration: none; font-size: 20px; transition: all 0.2s; }
  .settings-icon:hover { border-color: var(--gold); transform: rotate(45deg); }

  /* ============================================================
     PROFILE CARD (Expandable)
     ============================================================ */
  .profile-card {
    position: relative;
    padding: 18px 16px;
    background: radial-gradient(circle at 100% 0%, rgba(244,197,66,0.2), transparent 55%),
                linear-gradient(135deg, var(--card), #0f0f1e);
    border: 1.5px solid rgba(244,197,66,0.35);
    border-radius: 22px;
    margin-bottom: 16px;
    cursor: pointer;
    user-select: none;
    overflow: hidden;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .profile-card:hover {
    border-color: rgba(244,197,66,0.7);
    box-shadow: 0 12px 35px rgba(244,197,66,0.2);
  }
  .profile-card.expanded {
    padding: 24px 20px;
    border-color: var(--gold);
    box-shadow: 0 20px 50px rgba(244,197,66,0.35), 0 0 60px rgba(244,197,66,0.15);
  }
  .profile-card::before {
    content: "";
    position: absolute;
    top: -50%; right: -50%;
    width: 200%; height: 200%;
    background: conic-gradient(from 0deg, transparent, rgba(244,197,66,0.08), transparent, rgba(139,92,246,0.08), transparent);
    animation: spin 12s linear infinite;
    z-index: 0;
    opacity: 0;
    transition: opacity 0.3s;
  }
  .profile-card.expanded::before { opacity: 1; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .profile-card > * { position: relative; z-index: 1; }

  .profile-row {
    display: flex; align-items: center; gap: 14px;
  }

  .user-av-box {
    width: 56px; height: 56px;
    border-radius: 50%;
    border: 2.5px solid #f4c542;
    display: flex; align-items: center; justify-content: center;
    font-size: 28px;
    box-shadow: 0 0 22px rgba(244,197,66,0.4);
    overflow: hidden;
    flex-shrink: 0;
    transition: all 0.35s;
  }
  .profile-card.expanded .user-av-box {
    width: 76px; height: 76px;
    font-size: 40px;
    box-shadow: 0 0 40px rgba(244,197,66,0.7);
    border-width: 3px;
  }
  .user-av-box.emoji-bg { background: linear-gradient(135deg, #2a2a4a, #1a1a2e); }
  .user-av-box.image-bg { background-size: cover; background-position: center; }

  .greet-text { flex: 1; min-width: 0; }
  .greet-text .hi { font-size: 12px; color: var(--muted); margin-bottom: 2px; }
  .greet-text .name {
    font-size: 17px; font-weight: bold; color: var(--text);
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    transition: font-size 0.3s;
  }
  .profile-card.expanded .greet-text .name { font-size: 21px; }
  .greet-text .lvl-mini {
    display: inline-block;
    background: linear-gradient(135deg, #8b5cf6, #6b4eff);
    color: #fff;
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 6px;
    font-family: monospace;
    font-weight: 900;
    margin-top: 4px;
  }

  .expand-icon {
    font-size: 20px;
    color: var(--muted);
    transition: transform 0.3s;
    flex-shrink: 0;
  }
  .profile-card.expanded .expand-icon { transform: rotate(180deg); color: var(--gold); }

  /* Expanded content */
  .profile-details {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.4s ease-out;
  }
  .profile-card.expanded .profile-details { max-height: 400px; }

  .profile-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(244,197,66,0.3), transparent);
    margin: 16px 0;
  }

  .level-bar-wrap { margin-bottom: 14px; }
  .level-info {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    margin-bottom: 6px;
  }
  .level-info .lbl { color: var(--muted); }
  .level-info .val { color: var(--gold); font-family: monospace; font-weight: 900; }
  .level-bar {
    height: 8px;
    background: rgba(148,163,184,0.15);
    border-radius: 8px;
    overflow: hidden;
  }
  .level-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #8b5cf6, #f4c542);
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(139,92,246,0.6);
    transition: width 0.5s;
  }

  .mini-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 14px;
  }
  .mini-stat {
    padding: 10px 6px;
    background: rgba(15,23,42,0.6);
    border: 1px solid var(--border);
    border-radius: 12px;
    text-align: center;
  }
  .mini-stat .num {
    font-size: 16px;
    font-weight: 900;
    color: #fde68a;
    font-family: monospace;
    margin-bottom: 2px;
  }
  .mini-stat .lbl {
    font-size: 9px;
    color: var(--muted);
  }

  .profile-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px;
    border-radius: 12px;
    background: linear-gradient(135deg, #f4c542, #eab308);
    color: #1a1a1a;
    text-decoration: none;
    font-weight: 900;
    font-size: 14px;
    box-shadow: 0 8px 20px rgba(244,197,66,0.35);
    transition: 0.2s;
  }
  .profile-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 25px rgba(244,197,66,0.5);
  }

  /* ============================================================
     GAMES BUTTON (single big)
     ============================================================ */
  .games-btn {
    position: relative;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 22px 20px;
    border-radius: 22px;
    text-decoration: none;
    color: #fff;
    margin-bottom: 14px;
    overflow: hidden;
    border: 2px solid rgba(139,92,246,0.6);
    background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.5), transparent 55%),
                radial-gradient(circle at 0% 100%, rgba(236,72,153,0.3), transparent 55%),
                linear-gradient(135deg, #1a0f2e, #120824);
    box-shadow: 0 15px 45px rgba(139,92,246,0.3);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .games-btn::before {
    content: "";
    position: absolute;
    inset: -100%;
    background: conic-gradient(from 0deg, transparent, rgba(167,139,250,0.3), transparent, rgba(236,72,153,0.25), transparent);
    animation: spin 8s linear infinite;
    z-index: 0;
  }
  .games-btn:hover {
    transform: translateY(-4px) scale(1.01);
    border-color: rgba(167,139,250,0.95);
    box-shadow: 0 22px 60px rgba(139,92,246,0.5);
  }
  .games-btn:active { transform: scale(0.98); }
  .games-btn > * { position: relative; z-index: 1; }

  .games-icon {
    font-size: 46px;
    width: 76px; height: 76px;
    border-radius: 20px;
    background: rgba(255,255,255,0.1);
    border: 1.5px solid rgba(255,255,255,0.2);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    transition: transform 0.3s;
  }
  .games-btn:hover .games-icon { transform: scale(1.1) rotate(-6deg); }

  .games-body { flex: 1; }
  .games-title {
    font-size: 22px;
    font-weight: 900;
    margin-bottom: 4px;
    background: linear-gradient(135deg, #e9d5ff, #a78bfa, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .games-desc { font-size: 12.5px; color: #cbd5e1; line-height: 1.5; }
  .games-arrow { font-size: 26px; color: rgba(255,255,255,0.6); transition: 0.3s; }
  .games-btn:hover .games-arrow { transform: translateX(-6px); color: #fff; }

  .games-badge {
    position: absolute;
    top: 12px; left: 12px;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: #fff;
    font-size: 10px;
    font-weight: 900;
    padding: 3px 9px;
    border-radius: 999px;
    box-shadow: 0 4px 12px rgba(34,197,94,0.5);
    display: flex; align-items: center; gap: 4px;
  }
  .games-badge::before {
    content: "";
    width: 6px; height: 6px;
    background: #fff;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
  }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }

  /* ============================================================
     BIG CARDS (Notifications + Support + Shop)
     ============================================================ */
  .big-card {
    position: relative;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 18px 20px;
    border-radius: 20px;
    text-decoration: none;
    color: #fff;
    margin-bottom: 12px;
    transition: all 0.22s;
    overflow: hidden;
  }
  .big-card:hover { transform: translateY(-3px); }
  .big-card:active { transform: scale(0.98); }

  .big-card.notif {
    background: radial-gradient(circle at 100% 0%, rgba(139,92,246,0.35), transparent 60%),
                linear-gradient(135deg, #1a0f2e, #0f0f1e);
    border: 2px solid rgba(139,92,246,0.5);
    box-shadow: 0 8px 30px rgba(139,92,246,0.2);
  }
  .big-card.notif:hover { border-color: rgba(139,92,246,0.9); box-shadow: 0 15px 40px rgba(139,92,246,0.35); }

  .big-card.support {
    background: radial-gradient(circle at 100% 0%, rgba(6,182,212,0.35), transparent 60%),
                linear-gradient(135deg, #0a1e2a, #0f0f1e);
    border: 2px solid rgba(6,182,212,0.5);
    box-shadow: 0 8px 30px rgba(6,182,212,0.2);
  }
  .big-card.support:hover { border-color: rgba(6,182,212,0.9); box-shadow: 0 15px 40px rgba(6,182,212,0.35); }

  .big-card.shop {
    background: radial-gradient(circle at 100% 0%, rgba(100,116,139,0.3), transparent 60%),
                linear-gradient(135deg, #1a1a2e, #0f0f1e);
    border: 2px solid rgba(100,116,139,0.4);
    opacity: 0.7;
    cursor: not-allowed;
  }
  .big-card.shop:hover { transform: none; border-color: rgba(100,116,139,0.4); box-shadow: none; }

  .bc-icon {
    font-size: 38px;
    width: 60px; height: 60px;
    border-radius: 18px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    position: relative;
  }
  .notif .bc-icon { background: rgba(139,92,246,0.2); }
  .support .bc-icon { background: rgba(6,182,212,0.2); }
  .shop .bc-icon { background: rgba(100,116,139,0.2); }

  .bc-body { flex: 1; min-width: 0; }
  .bc-title { font-size: 17px; font-weight: 900; margin-bottom: 4px; }
  .bc-desc { font-size: 12px; color: #cbd5e1; }
  .bc-arrow { font-size: 22px; color: #94a3b8; }

  .bell-badge {
    position: absolute;
    top: -6px; right: -6px;
    min-width: 22px; height: 22px;
    background: #ef4444;
    color: white;
    border-radius: 50%;
    font-size: 11px;
    display: flex; align-items: center; justify-content: center;
    font-weight: bold;
    padding: 0 6px;
    box-shadow: 0 0 0 3px var(--bg);
    animation: pulseBadge 2s infinite;
  }
  @keyframes pulseBadge { 0%,100% { transform: scale(1); } 50% { transform: scale(1.15); } }

  .soon-label {
    position: absolute;
    top: 10px; left: 10px;
    background: linear-gradient(135deg, #eab308, #ca8a04);
    color: #1a1a1a;
    font-size: 9px;
    font-weight: 900;
    padding: 3px 8px;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(234,179,8,0.4);
  }

  /* ===== Guest warning ===== */
  .guest-warning {
    background: linear-gradient(135deg, rgba(234,179,8,0.15), rgba(249,115,22,0.08));
    border: 1.5px solid rgba(234,179,8,0.35);
    border-radius: 16px;
    padding: 16px 18px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 14px;
  }
  .guest-warning .gw-icon { font-size: 32px; flex-shrink: 0; }
  .guest-warning .gw-body { flex: 1; }
  .guest-warning .gw-title { font-size: 13.5px; font-weight: bold; color: #fde68a; margin-bottom: 3px; }
  .guest-warning .gw-desc { font-size: 11.5px; color: #fbbf24; line-height: 1.6; }
  .guest-warning .gw-logout { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); padding: 10px 14px; border-radius: 12px; font-size: 12px; font-weight: bold; text-decoration: none; flex-shrink: 0; }
</style>
{% endblock %}

{% block content %}

  <!-- Top bar -->
  <div class="top-bar">
    <div class="version-badge"><span>🧪</span><span>نسخه آزمایشی</span></div>
    <a href="/accounts/settings/" class="settings-icon" title="تنظیمات">⚙️</a>
  </div>

  <!-- ============================================================
       Expandable Profile Card
       ============================================================ -->
  <div class="profile-card" id="profileCard" onclick="toggleProfile(event)">
    <div class="profile-row">
      {% if user.avatar_type == "image" and user.avatar_id %}
        <div class="user-av-box image-bg" style="background-image: url('/static/avatars/images/{{ user.avatar_id|stringformat:"03d" }}.jpg');"></div>
      {% else %}
        <div class="user-av-box emoji-bg">{{ avatar_emoji }}</div>
      {% endif %}
      <div class="greet-text">
        <div class="hi">سلام 👋</div>
        <div class="name">{{ user.alias }}</div>
        <div class="lvl-mini">Lv {{ level|default:1 }}</div>
      </div>
      <div class="expand-icon">▼</div>
    </div>

    <div class="profile-details" onclick="event.stopPropagation();">
      <div class="profile-divider"></div>

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
          <div class="num">🪙 {{ user.coins|default:0 }}</div>
          <div class="lbl">سکه</div>
        </div>
      </div>

      <a href="/accounts/profile/" class="profile-btn" onclick="event.stopPropagation();">
        <span>👤</span>
        <span>مشاهده کامل پروفایل</span>
        <span>←</span>
      </a>
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

  <!-- ============================================================
       GAMES BUTTON (single, goes to /game/rooms/)
       ============================================================ -->
  <a href="/game/rooms/" class="games-btn">
    <div class="games-badge">آنلاین</div>
    <div class="games-icon">🎮</div>
    <div class="games-body">
      <div class="games-title">بازی‌ها</div>
      <div class="games-desc">۶ حالت هیجان‌انگیز — بات، پلیر، گروهی، چالش و...</div>
    </div>
    <div class="games-arrow">←</div>
  </a>

  <!-- ============================================================
       NOTIFICATIONS
       ============================================================ -->
  <a href="/social/notifications/" class="big-card notif">
    <div class="bc-icon">
      🔔
      {% if unread_notifications %}<span class="bell-badge">{{ unread_notifications }}</span>{% endif %}
    </div>
    <div class="bc-body">
      <div class="bc-title">اعلان‌ها</div>
      <div class="bc-desc">
        {% if unread_notifications %}{{ unread_notifications }} پیام جدید داری{% else %}پیام‌ها و درخواست‌ها{% endif %}
      </div>
    </div>
    <div class="bc-arrow">←</div>
  </a>

  <!-- ============================================================
       SUPPORT
       ============================================================ -->
  <a href="/support/" class="big-card support" onclick="openSupport(event)">
    <div class="bc-icon">💬</div>
    <div class="bc-body">
      <div class="bc-title">پشتیبانی</div>
      <div class="bc-desc">سوال داری؟ با ما در تماس باش</div>
    </div>
    <div class="bc-arrow">←</div>
  </a>

  <!-- ============================================================
       SHOP (Disabled but visible)
       ============================================================ -->
  <div class="big-card shop">
    <span class="soon-label">به زودی</span>
    <div class="bc-icon">🛒</div>
    <div class="bc-body">
      <div class="bc-title">فروشگاه</div>
      <div class="bc-desc">خرید آواتار و تم‌های ویژه</div>
    </div>
    <div class="bc-arrow">🔒</div>
  </div>

{% endblock %}

{% block extra_js %}
<script>
  function toggleProfile(e) {
    if (e.target.closest('a, button')) return;
    document.getElementById('profileCard').classList.toggle('expanded');
    if (window.vibrate) window.vibrate(10);
  }

  function openSupport(e) {
    e.preventDefault();
    alert('📬 راه‌های ارتباط با پشتیبانی:\\n\\n📧 ایمیل: support@esmfamil.com\\n💬 تلگرام: @esmfamil_support\\n\\n(این صفحه به زودی کامل می‌شود)');
  }
</script>
{% endblock %}
''')

print("\n[2/3] Update game/views.py — add level/stats to home context")
p = "game/views.py"
with open(p, "r", encoding="utf-8") as f: src = f.read()

# Find home view and update it
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
    from django.db.models import Sum, Count

    # Get player stats
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

if old_home in src:
    src = src.replace(old_home, new_home, 1)
    with open(p, "w", encoding="utf-8") as f: f.write(src)
    print("  ✓ home view updated with stats")
else:
    print("  ⚠ home view pattern not found - trying loose match")
    # Loose match
    import re
    pattern = re.compile(
        r'@login_required\ndef home\(request\):.*?return render\(request, "game/menu\.html", \{[^}]*\}\)',
        re.DOTALL
    )
    m = pattern.search(src)
    if m:
        src = src[:m.start()] + new_home + src[m.end():]
        with open(p, "w", encoding="utf-8") as f: f.write(src)
        print("  ✓ home view updated (loose)")
    else:
        print("  ✗ Could not find home view")

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
چه چیزایی تغییر کرد:

  👤 پروفایل (بالای صفحه):
     ✓ کارت قابل کلیک — کلیک = بزرگ‌تر می‌شه
     ✓ نمایش آواتار + نام + Lv (کوچیک)
     ✓ کلیک → باز می‌شه:
        • نوار پیشرفت Lv
        • آمار (بازی، امتیاز، سکه)
        • دکمه "مشاهده کامل پروفایل"

  🎮 بازی‌ها:
     ✓ فقط یه دکمه بزرگ (نه ۶ تا)
     ✓ کلیک → می‌ره /game/rooms/
     ✓ گرافیک بنفش/صورتی با چرخش

  🔔 اعلان‌ها:
     ✓ مثل قبل با badge

  💬 پشتیبانی (جدید):
     ✓ گرافیک مثل اعلان‌ها (فیروزه‌ای)
     ✓ کلیک → پیام با راه‌های ارتباط

  🛒 فروشگاه:
     ✓ نمایش هست ولی غیرفعال (opacity + cursor)
     ✓ بج "به زودی"
     ✓ کلیک نمی‌شه

  ❌ اتحاد از خانه حذف شد

حالا:
  pkill -9 -f "manage.py runserver"
  python manage.py runserver
  Ctrl+Shift+R

بعد:
  http://127.0.0.1:8000/game/
""")
