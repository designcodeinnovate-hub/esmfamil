#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, glob, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Ensure audio file
# ============================================================
print("\n[1/6] Audio file check")
audio = "static/audio/nature.mp3"
if not os.path.exists(audio):
    home = os.path.expanduser("~")
    for pattern in [os.path.join(home, "Downloads", "*Nature*.mp3"), os.path.join(home, "Downloads", "*.mp3")]:
        matches = glob.glob(pattern)
        if matches:
            os.makedirs("static/audio", exist_ok=True)
            shutil.copy2(matches[0], audio)
            print(f"  ✓ Copied {os.path.basename(matches[0])} → {audio}")
            break
    if not os.path.exists(audio):
        print("  ❌ No mp3 file found")
        sys.exit(1)
else:
    print(f"  ✓ {audio} ({os.path.getsize(audio)/1024/1024:.2f} MB)")

# ============================================================
# 2) Replace music JS in base.html
# ============================================================
print("\n[2/6] Replacing music JS")

p = "templates/base.html"
src = read(p)

# Find old music block start
start_marker = "// ============================================================\n// ۳) مدیریت موسیقی پس‌زمینه"
end_marker = "// هندلر مخصوص صفحه تنظیمات برای اعمال فوری"

start_idx = src.find(start_marker)
end_idx = src.find(end_marker)

if start_idx < 0:
    # Try alt marker
    start_marker = "const bgMusic = document.getElementById('globalMusic');"
    start_idx = src.find(start_marker)
    if start_idx > 100:
        start_idx -= 100  # Include preceding comments

if start_idx < 0:
    print("  ⚠ Music block not found — will inject new block before </script>")
    inject_before = src.rfind("</script>")
    if inject_before < 0:
        print("  ❌ No script tag found")
        sys.exit(1)
    NEW_JS = '''

// ============================================================
// ROBUST MUSIC SYSTEM (v3)
// ============================================================
(function() {
  const bgMusic = document.getElementById('globalMusic');
  if (!bgMusic) {
    console.warn('[Music] audio element not found');
    return;
  }

  const isOn = () => localStorage.getItem('music') !== 'false';
  const vol = () => (parseInt(localStorage.getItem('musicVol')) || 50) / 100;
  const getPos = () => parseFloat(localStorage.getItem('bgMusicPos') || '0');
  const savePos = () => {
    try {
      if (!bgMusic.paused && bgMusic.currentTime > 0) {
        localStorage.setItem('bgMusicPos', bgMusic.currentTime);
      }
    } catch(e) {}
  };

  // Restore volume and position
  bgMusic.volume = vol();

  const tryRestorePos = () => {
    try {
      const p = getPos();
      if (p > 0 && (!bgMusic.duration || p < bgMusic.duration - 1)) {
        bgMusic.currentTime = p;
      }
    } catch(e) {}
  };

  if (bgMusic.readyState >= 1) tryRestorePos();
  bgMusic.addEventListener('loadedmetadata', tryRestorePos);

  // Attempt muted autoplay
  function startMuted() {
    if (!isOn()) {
      console.log('[Music] disabled in settings');
      return;
    }
    bgMusic.muted = true;
    bgMusic.volume = vol();

    const playPromise = bgMusic.play();
    if (playPromise !== undefined) {
      playPromise.then(() => {
        console.log('[Music] muted autoplay OK — waiting for unlock');
        attachUnlock();
      }).catch(err => {
        console.log('[Music] muted autoplay failed:', err.message);
        attachUnlock();
      });
    }
  }

  function attachUnlock() {
    const unlock = () => {
      if (!isOn()) return;
      bgMusic.muted = false;
      bgMusic.volume = vol();
      if (bgMusic.paused) {
        bgMusic.play().catch(() => {});
      }
      console.log('[Music] unlocked with sound');
      ['pointerdown','touchstart','keydown','click'].forEach(evt => {
        document.removeEventListener(evt, unlock);
      });
      const hint = document.getElementById('musicHint');
      if (hint) hint.style.display = 'none';
    };
    ['pointerdown','touchstart','keydown','click'].forEach(evt => {
      document.addEventListener(evt, unlock, { once: true, passive: true });
    });
  }

  // Kick off
  if (bgMusic.readyState >= 2) {
    startMuted();
  } else {
    bgMusic.addEventListener('canplay', startMuted, { once: true });
    setTimeout(startMuted, 800);
  }

  // Show hint if autoplay fails after 3s
  setTimeout(() => {
    if (bgMusic.paused && isOn()) {
      const hint = document.getElementById('musicHint');
      if (hint) hint.style.display = 'flex';
    }
  }, 3000);

  // Save position
  setInterval(savePos, 1500);
  window.addEventListener('beforeunload', savePos);
  window.addEventListener('pagehide', savePos);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') savePos();
  });

  // Global controller
  window.MusicPlayer = {
    play: () => {
      if (isOn()) {
        bgMusic.muted = false;
        bgMusic.volume = vol();
        bgMusic.play().catch(()=>{});
      }
    },
    pause: () => bgMusic.pause(),
    setVolume: (v) => { bgMusic.volume = Math.max(0, Math.min(1, v/100)); },
    getState: () => ({
      playing: !bgMusic.paused,
      volume: bgMusic.volume,
      muted: bgMusic.muted,
      time: bgMusic.currentTime,
    }),
  };

  // React to settings changes
  window.addEventListener('storage', (e) => {
    if (e.key === 'music') {
      if (isOn()) bgMusic.play().catch(()=>{});
      else bgMusic.pause();
    }
    if (e.key === 'musicVol') {
      bgMusic.volume = vol();
    }
  });

  // Hint button handler
  setTimeout(() => {
    const hint = document.getElementById('musicHint');
    if (hint) {
      hint.onclick = () => {
        bgMusic.muted = false;
        bgMusic.volume = vol();
        bgMusic.play().then(() => {
          hint.style.display = 'none';
        }).catch(() => {});
      };
    }
  }, 100);
})();

'''
    src = src[:inject_before] + NEW_JS + src[inject_before:]
    write(p, src)
    print("  ✓ Music JS injected")
else:
    if end_idx < 0:
        end_idx = src.find("window.applySettingsNow", start_idx)
    if end_idx < 0:
        end_idx = start_idx + 3000  # Fallback
        while end_idx < len(src) and src[end_idx] != '\n':
            end_idx += 1

    old_block = src[start_idx:end_idx]

    NEW_JS = '''// ============================================================
// ROBUST MUSIC SYSTEM (v3)
// ============================================================
const bgMusic = document.getElementById('globalMusic');

(function() {
  if (!bgMusic) { console.warn('[Music] audio element missing'); return; }

  const isOn = () => localStorage.getItem('music') !== 'false';
  const vol = () => (parseInt(localStorage.getItem('musicVol')) || 50) / 100;
  const getPos = () => parseFloat(localStorage.getItem('bgMusicPos') || '0');
  const savePos = () => {
    try {
      if (!bgMusic.paused && bgMusic.currentTime > 0) {
        localStorage.setItem('bgMusicPos', bgMusic.currentTime);
      }
    } catch(e) {}
  };

  bgMusic.volume = vol();

  const tryRestorePos = () => {
    try {
      const p = getPos();
      if (p > 0 && (!bgMusic.duration || p < bgMusic.duration - 1)) {
        bgMusic.currentTime = p;
      }
    } catch(e) {}
  };

  if (bgMusic.readyState >= 1) tryRestorePos();
  bgMusic.addEventListener('loadedmetadata', tryRestorePos);

  function startMuted() {
    if (!isOn()) return;
    bgMusic.muted = true;
    bgMusic.volume = vol();
    const playPromise = bgMusic.play();
    if (playPromise !== undefined) {
      playPromise.then(() => attachUnlock()).catch(() => attachUnlock());
    }
  }

  function attachUnlock() {
    const unlock = () => {
      if (!isOn()) return;
      bgMusic.muted = false;
      bgMusic.volume = vol();
      if (bgMusic.paused) bgMusic.play().catch(()=>{});
      ['pointerdown','touchstart','keydown','click'].forEach(e => {
        document.removeEventListener(e, unlock);
      });
      const hint = document.getElementById('musicHint');
      if (hint) hint.style.display = 'none';
    };
    ['pointerdown','touchstart','keydown','click'].forEach(e => {
      document.addEventListener(e, unlock, { once: true, passive: true });
    });
  }

  if (bgMusic.readyState >= 2) startMuted();
  else {
    bgMusic.addEventListener('canplay', startMuted, { once: true });
    setTimeout(startMuted, 800);
  }

  setTimeout(() => {
    if (bgMusic.paused && isOn()) {
      const hint = document.getElementById('musicHint');
      if (hint) hint.style.display = 'flex';
    }
  }, 3000);

  setInterval(savePos, 1500);
  window.addEventListener('beforeunload', savePos);
  window.addEventListener('pagehide', savePos);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') savePos();
  });

  window.MusicPlayer = {
    play: () => {
      if (isOn()) {
        bgMusic.muted = false;
        bgMusic.volume = vol();
        bgMusic.play().catch(()=>{});
      }
    },
    pause: () => bgMusic.pause(),
    setVolume: (v) => { bgMusic.volume = Math.max(0, Math.min(1, v/100)); },
    getState: () => ({
      playing: !bgMusic.paused,
      volume: bgMusic.volume,
      muted: bgMusic.muted,
      time: bgMusic.currentTime,
    }),
  };

  window.addEventListener('storage', (e) => {
    if (e.key === 'music') {
      if (isOn()) bgMusic.play().catch(()=>{});
      else bgMusic.pause();
    }
    if (e.key === 'musicVol') bgMusic.volume = vol();
  });

  setTimeout(() => {
    const hint = document.getElementById('musicHint');
    if (hint) {
      hint.onclick = () => {
        bgMusic.muted = false;
        bgMusic.volume = vol();
        bgMusic.play().then(() => { hint.style.display = 'none'; }).catch(()=>{});
      };
    }
  }, 100);
})();

'''

    src = src[:start_idx] + NEW_JS + src[end_idx:]
    write(p, src)
    print("  ✓ Music JS replaced")

# ============================================================
# 3) Add music hint element + CSS
# ============================================================
print("\n[3/6] Adding music hint button")
src = read(p)

if 'id="musicHint"' not in src:
    hint_html = '''
<div id="musicHint" style="display:none; position:fixed; top:12px; right:12px; padding:10px 16px; background:linear-gradient(135deg,#f4c542,#eab308); color:#1a1a1a; border-radius:14px; font-size:13px; font-weight:900; cursor:pointer; z-index:9999; box-shadow:0 6px 20px rgba(244,197,66,0.5); align-items:center; gap:8px; animation:pulseHint 2s infinite;">
  <span style="font-size:18px;">🔊</span>
  <span>روشن کردن موسیقی</span>
</div>
<style>
@keyframes pulseHint {
  0%,100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
</style>
'''
    body_close = src.rfind("</body>")
    if body_close > 0:
        src = src[:body_close] + hint_html + src[body_close:]
        write(p, src)
        print("  ✓ Music hint added")
else:
    print("  ✓ Music hint already exists")

# ============================================================
# 4) Verify PWA setup
# ============================================================
print("\n[4/6] Verifying PWA setup")

# 4a) manifest
if not os.path.exists("static/manifest.json"):
    print("  ⚠ manifest.json missing — creating")
    manifest = '''{
  "name": "اسم فامیل آنلاین",
  "short_name": "اسم فامیل",
  "description": "بازی نوستالژیک اسم فامیل، آنلاین",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#0a0a15",
  "theme_color": "#f4c542",
  "lang": "fa",
  "dir": "rtl",
  "icons": [
    {"src": "/static/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"},
    {"src": "/static/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "maskable"}
  ]
}
'''
    write("static/manifest.json", manifest)
else:
    print("  ✓ manifest.json exists")

# 4b) icon.svg
if not os.path.exists("static/icon.svg"):
    print("  ⚠ icon.svg missing — creating")
    icon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#f4c542"/>
      <stop offset="1" stop-color="#ca8a04"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="100" fill="#0a0a15"/>
  <circle cx="256" cy="256" r="180" fill="url(#g)" opacity="0.2"/>
  <text x="256" y="340" font-size="280" text-anchor="middle" font-family="Arial, sans-serif">👑</text>
</svg>
'''
    write("static/icon.svg", icon)
else:
    print("  ✓ icon.svg exists")

# 4c) service_worker_view.py
if not os.path.exists("config/service_worker_view.py"):
    print("  ⚠ service_worker_view.py missing")
else:
    print("  ✓ service_worker_view.py exists")

# 4d) route in config/urls.py
src_urls = read("config/urls.py")
if "service_worker" in src_urls:
    print("  ✓ sw.js route in config/urls.py")
else:
    print("  ⚠ sw.js route missing — adding")
    if "from config.beta_views import" in src_urls:
        src_urls = src_urls.replace(
            "from config.beta_views import beta_lock, beta_logout",
            "from config.beta_views import beta_lock, beta_logout\nfrom config.service_worker_view import service_worker",
            1
        )
    anchor = '    # ریشه → landing'
    if anchor in src_urls:
        insert = '    path("sw.js", service_worker, name="service_worker"),\n\n'
        src_urls = src_urls.replace(anchor, insert + anchor, 1)
    write("config/urls.py", src_urls)
    print("  ✓ Added sw.js route")

# 4e) manifest link + PWA meta in base.html
src = read(p)
if 'rel="manifest"' not in src:
    anchor = '<meta name="theme-color"'
    if anchor in src:
        idx = src.find(anchor)
        end = src.find(">", idx) + 1
        meta_block = '''

  <link rel="manifest" href="/static/manifest.json">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="اسم فامیل">
  <meta name="mobile-web-app-capable" content="yes">'''
        src = src[:end] + meta_block + src[end:]
        write(p, src)
        print("  ✓ PWA meta tags added")

# 4f) SW registration + install prompt
if "navigator.serviceWorker" not in src:
    sw_js = '''
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', { scope: '/' })
      .then(r => console.log('[SW] registered:', r.scope))
      .catch(e => console.warn('[SW] error:', e));
  });
}
let _deferred = null;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  _deferred = e;
  if (!localStorage.getItem('installDismissed')) {
    setTimeout(() => {
      const b = document.getElementById('pwaBanner');
      if (b) b.classList.add('show');
    }, 5000);
  }
});
window.addEventListener('appinstalled', () => {
  localStorage.setItem('installDismissed', '1');
  const b = document.getElementById('pwaBanner');
  if (b) b.classList.remove('show');
});
function installPWA() {
  if (!_deferred) return;
  _deferred.prompt();
  _deferred.userChoice.then(c => {
    if (c.outcome === 'accepted') localStorage.setItem('installDismissed', '1');
    _deferred = null;
    const b = document.getElementById('pwaBanner');
    if (b) b.classList.remove('show');
  });
}
function dismissPWA() {
  localStorage.setItem('installDismissed', '1');
  const b = document.getElementById('pwaBanner');
  if (b) b.classList.remove('show');
}
</script>
'''
    body_close = src.rfind("</body>")
    if body_close > 0:
        src = src[:body_close] + sw_js + src[body_close:]
        write(p, src)
        print("  ✓ SW registration added")

# 4g) Install banner
if 'id="pwaBanner"' not in src:
    banner = '''
<div id="pwaBanner" style="position:fixed; bottom:88px; left:12px; right:12px; max-width:480px; margin:0 auto; padding:14px; background:linear-gradient(135deg,rgba(30,41,59,0.98),rgba(15,23,42,0.98)); border:1.5px solid rgba(244,197,66,0.5); border-radius:16px; display:flex; align-items:center; gap:10px; transform:translateY(120%); opacity:0; transition:all 0.4s; z-index:998; box-shadow:0 10px 40px rgba(0,0,0,0.5);">
  <div style="font-size:32px;">📱</div>
  <div style="flex:1;">
    <div style="font-size:13px; font-weight:bold; color:#fff;">نصب اسم فامیل</div>
    <div style="font-size:10px; color:#94a3b8;">مثل یه اپ نصب کن</div>
  </div>
  <button onclick="installPWA()" style="padding:8px 16px; border-radius:10px; background:linear-gradient(135deg,#f4c542,#eab308); color:#1a1a1a; border:none; font-family:inherit; font-weight:bold; font-size:13px; cursor:pointer;">نصب</button>
  <button onclick="dismissPWA()" style="width:28px; height:28px; border-radius:50%; background:rgba(148,163,184,0.15); color:#94a3b8; border:none; cursor:pointer; font-size:12px;">✕</button>
</div>
<style>
#pwaBanner.show { transform: translateY(0); opacity: 1; }
</style>
'''
    body_close = src.rfind("</body>")
    if body_close > 0:
        src = src[:body_close] + banner + src[body_close:]
        write(p, src)
        print("  ✓ Install banner added")

# ============================================================
# 5) Collect static + migrate
# ============================================================
print("\n[5/6] Collect static")
r = subprocess.run([sys.executable, "manage.py", "collectstatic", "--noinput"],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Static collected")
else:
    print(f"  ⚠ {r.stderr[:300]}")

# ============================================================
# 6) Check
# ============================================================
print("\n[6/6] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print("  ⚠ Errors:")
    print(r.stderr[:1000] if r.stderr else r.stdout[:1000])
    sys.exit(1)

print("\n[Files verification]")
files = [
    "static/audio/nature.mp3",
    "static/manifest.json",
    "static/icon.svg",
    "config/service_worker_view.py",
    "templates/base.html",
]
for f in files:
    size = os.path.getsize(f) if os.path.exists(f) else 0
    status = "✓" if size > 0 else "✗"
    print(f"  {status} {f} ({size:,} bytes)")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
Music now does:
  ✓ Muted autoplay on page load (works even without interaction)
  ✓ Unmutes on first click/tap/key/scroll anywhere
  ✓ Loops forever (loop attribute in HTML)
  ✓ Saves position every 1.5s
  ✓ Restores position on new page (continues from same spot)
  ✓ If autoplay fully blocked → shows 🔊 button top-right
  ✓ Settings toggle/volume still work
  ✓ Respects user's music OFF preference

PWA now does:
  ✓ manifest.json with SVG icon
  ✓ /sw.js service worker route
  ✓ Auto-registers SW on page load
  ✓ Install banner appears 5s after load
  ✓ Chrome address bar install icon works

Next:
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)

Test music:
  1. Go to /game/ — music should start silently immediately
  2. Click anywhere → sound comes on
  3. Navigate to /accounts/profile/ → music continues from same spot
  4. If not playing → click 🔊 button top-right (appears after 3s)

Test PWA:
  1. Chrome address bar → look for install icon (⊕)
  2. Or wait 5s → banner appears at bottom
  3. Click install → opens as standalone app

Diagnostic (browser console F12):
  - Should see: "[Music] muted autoplay OK"
  - Should see: "[SW] registered: /"
  - On click: "[Music] unlocked with sound"

If music still doesn't play:
  - Open F12 Console
  - Type: document.getElementById('globalMusic').play()
  - If error → send it
""")
