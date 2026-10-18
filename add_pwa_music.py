#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auto-play music + PWA installable app."""
import os, sys, shutil, glob, subprocess, re

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
# 1) Ensure audio file exists
# ============================================================
print("\n[1/8] Checking audio file")
audio_target = "static/audio/nature.mp3"

if os.path.exists(audio_target):
    print(f"  ✓ {audio_target} exists ({os.path.getsize(audio_target)/1024/1024:.2f} MB)")
else:
    print("  ⚠ Audio not found — searching Downloads...")
    home = os.path.expanduser("~")
    candidates = glob.glob(os.path.join(home, "Downloads", "*Nature*.mp3"))
    if candidates:
        os.makedirs("static/audio", exist_ok=True)
        shutil.copy2(candidates[0], audio_target)
        print(f"  ✓ Copied {os.path.basename(candidates[0])} → {audio_target}")
    else:
        print("  ❌ No 'Nature*.mp3' in ~/Downloads")
        print("  Please move the file there or run add_music.py first.")
        sys.exit(1)

# ============================================================
# 2) Create manifest.json
# ============================================================
print("\n[2/8] Creating manifest.json")

# Find best icon
icon_path = None
for candidate in [
    "static/avatars/generated/001.png",
    "static/avatars/images/001.jpg",
]:
    if os.path.exists(candidate):
        icon_path = "/" + candidate
        break

if not icon_path:
    print("  ⚠ No avatar icon found, using generic SVG")
    icon_path = "/static/icon.svg"

manifest = '''{
  "name": "اسم فامیل آنلاین",
  "short_name": "اسم فامیل",
  "description": "بازی نوستالژیک اسم فامیل، آنلاین و هیجان‌انگیز",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#0a0a15",
  "theme_color": "#f4c542",
  "lang": "fa",
  "dir": "rtl",
  "categories": ["games", "entertainment"],
  "icons": [
    {
      "src": "''' + icon_path + '''",
      "sizes": "300x300",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "''' + icon_path + '''",
      "sizes": "300x300",
      "type": "image/png",
      "purpose": "maskable"
    }
  ]
}
'''
write("static/manifest.json", manifest)

# ============================================================
# 3) Create service worker view
# ============================================================
print("\n[3/8] Creating service worker view")
write("config/service_worker_view.py", '''# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.views.decorators.cache import never_cache


SW_CONTENT = r"""
// Service Worker for اسم فامیل آنلاین
const CACHE_NAME = 'esmfamil-v1';
const STATIC_ASSETS = [
  '/',
  '/static/manifest.json',
  '/static/audio/nature.mp3',
];

// Install — cache essential assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('Cache addAll failed:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate — clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch — network first for HTML/API, cache first for static
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip WebSocket and non-http(s)
  if (!url.protocol.startsWith('http')) return;

  // Skip admin / panel-admin / api
  if (url.pathname.startsWith('/panel-admin/') ||
      url.pathname.startsWith('/django-admin/') ||
      url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/beta-')) {
    return;
  }

  // Static files — cache first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request).then((resp) => {
          if (resp.ok) {
            const clone = resp.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return resp;
        });
      })
    );
    return;
  }

  // HTML/other — network first, cache fallback
  event.respondWith(
    fetch(event.request).then((resp) => {
      if (resp.ok && event.request.method === 'GET') {
        const clone = resp.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
      }
      return resp;
    }).catch(() => {
      return caches.match(event.request).then((cached) => cached || new Response('offline', { status: 503 }));
    })
  );
});
"""


@never_cache
def service_worker(request):
    response = HttpResponse(SW_CONTENT, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response
''')

# ============================================================
# 4) Add route to config/urls.py
# ============================================================
print("\n[4/8] Adding /sw.js route")
p = "config/urls.py"
src = read(p)

if "service_worker" in src:
    print("  ✓ route already exists")
else:
    # Find import block and add
    if "from config.beta_views import" in src:
        src = src.replace(
            "from config.beta_views import beta_lock, beta_logout",
            "from config.beta_views import beta_lock, beta_logout\nfrom config.service_worker_view import service_worker",
            1
        )
    else:
        # Add at top after other imports
        src = src.replace(
            "from django.urls import include, path",
            "from django.urls import include, path\nfrom config.service_worker_view import service_worker",
            1
        )

    # Add URL pattern before the landing path
    anchor = '    # ریشه → landing'
    if anchor in src:
        insert = '    # PWA service worker\n    path("sw.js", service_worker, name="service_worker"),\n\n'
        src = src.replace(anchor, insert + anchor, 1)
        write(p, src)
        print("  ✓ /sw.js route added")
    else:
        print("  ⚠ Could not find anchor")

# ============================================================
# 5) Update base.html - autoplay + PWA meta
# ============================================================
print("\n[5/8] Updating base.html for autoplay + PWA")
p = "templates/base.html"
src = read(p)

# 5a) Update <head> — add manifest link + PWA meta + theme
if 'rel="manifest"' not in src:
    head_anchor = '  <meta name="theme-color" content="#0a0a15">'
    if head_anchor in src:
        new_meta = '''  <meta name="theme-color" content="#f4c542">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="اسم فامیل">
  <meta name="mobile-web-app-capable" content="yes">
  <link rel="manifest" href="/static/manifest.json">'''
        src = src.replace(head_anchor, new_meta, 1)
        print("  ✓ PWA meta tags added")
    else:
        print("  ⚠ theme-color meta not found")

# 5b) Update audio tag for preload
old_audio = '<audio id="globalMusic" loop preload="none">'
if old_audio in src:
    src = src.replace(old_audio, '<audio id="globalMusic" loop preload="auto">', 1)
    print("  ✓ Audio preload=auto")
elif '<audio id="globalMusic" loop preload="auto">' in src:
    print("  ✓ Audio already preload=auto")
else:
    print("  ⚠ Audio tag not found with preload=none")

# 5c) Replace _startMusic function with muted-autoplay logic
old_fn = '''function _startMusic() {
  if (_musicStarted || !bgMusic) return;
  if (!_musicOn()) return;
  bgMusic.volume = _musicVol();
  bgMusic.play().catch(() => {});
  _musicStarted = true;
}'''

new_fn = '''function _startMusic() {
  if (!bgMusic) return;
  if (!_musicOn()) return;

  // Try muted autoplay first (works around browser autoplay block)
  bgMusic.muted = true;
  bgMusic.volume = _musicVol();
  bgMusic.play().then(() => {
    _musicStarted = true;
    // Unmute on first interaction
    const unmute = () => {
      try {
        if (_musicOn()) {
          bgMusic.muted = false;
          bgMusic.volume = _musicVol();
        }
      } catch (e) {}
      document.removeEventListener('click', unmute);
      document.removeEventListener('touchstart', unmute);
      document.removeEventListener('keydown', unmute);
    };
    document.addEventListener('click', unmute);
    document.addEventListener('touchstart', unmute);
    document.addEventListener('keydown', unmute);
  }).catch(() => {
    // Even muted autoplay failed — fallback to on-interaction start
    const startReal = () => {
      try {
        if (_musicOn()) {
          bgMusic.muted = false;
          bgMusic.volume = _musicVol();
          bgMusic.play().catch(() => {});
          _musicStarted = true;
        }
      } catch (e) {}
      document.removeEventListener('click', startReal);
      document.removeEventListener('touchstart', startReal);
      document.removeEventListener('keydown', startReal);
    };
    document.addEventListener('click', startReal);
    document.addEventListener('touchstart', startReal);
    document.addEventListener('keydown', startReal);
  });
}

// Fire autoplay attempt immediately
try { _startMusic(); } catch (e) {}'''

if old_fn in src:
    src = src.replace(old_fn, new_fn, 1)
    print("  ✓ Autoplay logic replaced")

# 5d) Add service worker registration + install prompt
if "navigator.serviceWorker" not in src:
    sw_js = '''
<script>
// ============================================================
// Service Worker Registration (PWA)
// ============================================================
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', { scope: '/' })
      .then((reg) => console.log('[SW] registered:', reg.scope))
      .catch((err) => console.warn('[SW] error:', err));
  });
}

// ============================================================
// Install Prompt (PWA)
// ============================================================
let _deferredInstallPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  _deferredInstallPrompt = e;
  // Show install banner if not dismissed before
  if (!localStorage.getItem('installDismissed')) {
    setTimeout(() => {
      const banner = document.getElementById('pwaInstallBanner');
      if (banner) banner.classList.add('show');
    }, 3000);
  }
});

window.addEventListener('appinstalled', () => {
  localStorage.setItem('installDismissed', '1');
  const banner = document.getElementById('pwaInstallBanner');
  if (banner) banner.classList.remove('show');
});

function triggerInstall() {
  if (!_deferredInstallPrompt) return;
  _deferredInstallPrompt.prompt();
  _deferredInstallPrompt.userChoice.then((choice) => {
    if (choice.outcome === 'accepted') {
      localStorage.setItem('installDismissed', '1');
    }
    _deferredInstallPrompt = null;
    const banner = document.getElementById('pwaInstallBanner');
    if (banner) banner.classList.remove('show');
  });
}

function dismissInstall() {
  localStorage.setItem('installDismissed', '1');
  const banner = document.getElementById('pwaInstallBanner');
  if (banner) banner.classList.remove('show');
}
</script>
'''
    # Add before closing </body>
    body_end = src.rfind("</body>")
    if body_end > 0:
        src = src[:body_end] + sw_js + src[body_end:]
        print("  ✓ SW registration + install prompt added")

# 5e) Add install banner HTML + CSS
if "pwaInstallBanner" not in src:
    banner_html = '''
<!-- PWA Install Banner -->
<div class="pwa-install-banner" id="pwaInstallBanner">
  <div class="pwa-icon">📱</div>
  <div class="pwa-body">
    <div class="pwa-title">نصب اسم فامیل</div>
    <div class="pwa-desc">مثل یه اپلیکیشن نصب کن و راحت‌تر بازی کن</div>
  </div>
  <button class="pwa-install-btn" onclick="triggerInstall()">نصب</button>
  <button class="pwa-close-btn" onclick="dismissInstall()">✕</button>
</div>
'''
    css = '''
    .pwa-install-banner {
      position: fixed;
      bottom: 88px;
      left: 12px;
      right: 12px;
      max-width: 480px;
      margin: 0 auto;
      padding: 12px 14px;
      background: linear-gradient(135deg, rgba(30,41,59,0.98), rgba(15,23,42,0.98));
      border: 1.5px solid rgba(244,197,66,0.5);
      border-radius: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
      transform: translateY(120%);
      opacity: 0;
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      z-index: 999;
      box-shadow: 0 10px 40px rgba(0,0,0,0.5), 0 0 30px rgba(244,197,66,0.2);
    }
    .pwa-install-banner.show {
      transform: translateY(0);
      opacity: 1;
    }
    .pwa-icon { font-size: 32px; flex-shrink: 0; }
    .pwa-body { flex: 1; min-width: 0; }
    .pwa-title { font-size: 13px; font-weight: bold; color: #fff; margin-bottom: 2px; }
    .pwa-desc { font-size: 10px; color: #94a3b8; line-height: 1.4; }
    .pwa-install-btn {
      padding: 8px 16px;
      border-radius: 10px;
      background: linear-gradient(135deg, #f4c542, #eab308);
      color: #1a1a1a;
      border: none;
      font-family: inherit;
      font-weight: bold;
      font-size: 13px;
      cursor: pointer;
      flex-shrink: 0;
      box-shadow: 0 4px 12px rgba(244,197,66,0.4);
    }
    .pwa-close-btn {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: rgba(148,163,184,0.15);
      color: #94a3b8;
      border: none;
      cursor: pointer;
      flex-shrink: 0;
      font-size: 12px;
    }
'''
    # Add CSS before </style>
    style_end = src.find("</style>")
    if style_end > 0:
        src = src[:style_end] + css + src[style_end:]

    # Add banner before </body>
    body_end = src.rfind("</body>")
    if body_end > 0:
        src = src[:body_end] + banner_html + src[body_end:]

    print("  ✓ Install banner added")

write(p, src)

# ============================================================
# 6) Create an SVG icon fallback (in case icon path is SVG)
# ============================================================
print("\n[6/8] Creating fallback icon.svg")
write("static/icon.svg", '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#f4c542"/>
      <stop offset="1" stop-color="#ca8a04"/>
    </linearGradient>
  </defs>
  <rect width="300" height="300" rx="60" fill="#0a0a15"/>
  <circle cx="150" cy="150" r="110" fill="url(#g)" opacity="0.15"/>
  <text x="150" y="200" font-size="180" text-anchor="middle" font-family="Tahoma">👑</text>
</svg>
''')

# ============================================================
# 7) Collect static + migrate
# ============================================================
print("\n[7/8] Collecting static files")
for cmd in [
    [sys.executable, "manage.py", "collectstatic", "--noinput", "--clear"],
]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd[1:])}")
    if r.returncode == 0:
        print(f"  ✓ {r.stdout.strip().split(chr(10))[-1] if r.stdout else 'done'}")
    else:
        print(f"  ⚠ {r.stderr.strip()[:300] if r.stderr else 'error'}")

# ============================================================
# 8) Final check
# ============================================================
print("\n[8/8] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print("  ⚠ Errors:")
    print(r.stderr[:1500] if r.stderr else r.stdout[:1500])
    sys.exit(1)

# Verify files
print("\n[Verify] Files:")
for f in [
    "static/audio/nature.mp3",
    "static/manifest.json",
    "static/icon.svg",
    "config/service_worker_view.py",
]:
    status = "✓" if os.path.exists(f) else "✗"
    size = f" ({os.path.getsize(f)/1024:.1f} KB)" if os.path.exists(f) else ""
    print(f"  {status} {f}{size}")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
What was added:

  🎵 MUSIC AUTOPLAY:
     - Tries muted autoplay on page load
     - Unmutes on first user click/tap/key
     - Loops forever (loop attribute)
     - Respects settings (music toggle + volume)
     - Works across all pages

  📱 PWA (installable app):
     - static/manifest.json (name, icons, theme)
     - /sw.js service worker (caches assets, offline support)
     - Meta tags for iOS + Android
     - Chrome install prompt appears after some interaction
     - Custom install banner at bottom
     - Auto-registers SW on page load
     - appinstalled event dismissed the banner

How to install on Chrome/Edge:
  Desktop:
    1. Open http://127.0.0.1:8000/
    2. Click the install icon in the address bar (⊕ or computer icon)
    3. Or click the "نصب" button in the banner
    4. App opens in its own window

  Android Chrome:
    1. Menu (⋮) → "Add to Home screen" or "Install app"
    2. Launches like a native app

  iPhone Safari:
    1. Share button → "Add to Home Screen"

Note: PWA install only works on:
  - localhost / 127.0.0.1 (dev)
  - HTTPS domain (production)
  - NOT on http://192.168.x.x or public HTTP

Next:
  python manage.py runserver
  Ctrl+Shift+R to hard refresh
  
Test:
  1. Open /game/  → music starts silently
  2. Click anywhere → sound comes on
  3. Look for install icon in Chrome address bar
  4. Or wait 3s → install banner appears at bottom
""")
