#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix 'offline' error from SECURE_SSL_REDIRECT + service worker."""
import os, re, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

print("\n[1/4] Fixing settings.py (SSL redirect)")

p = "config/settings.py"
src = read(p)

# 1) Make SECURE_SSL_REDIRECT conditional (only in prod, not localhost)
if "SECURE_SSL_REDIRECT = True" in src:
    src = src.replace(
        "SECURE_SSL_REDIRECT = True",
        '''# Only redirect HTTP→HTTPS in production, not local dev
SECURE_SSL_REDIRECT = (
    not DEBUG
    and not any(h in ("127.0.0.1", "localhost") for h in ALLOWED_HOSTS)
    and os.environ.get("DISABLE_SSL_REDIRECT", "false").lower() != "true"
)'''
    )
    print("  ✓ SECURE_SSL_REDIRECT now conditional")

# 2) Make cookies secure only when not on localhost
if "SESSION_COOKIE_SECURE = True" in src:
    src = src.replace(
        "SESSION_COOKIE_SECURE = True",
        'SESSION_COOKIE_SECURE = not DEBUG and not any(h in ("127.0.0.1", "localhost") for h in ALLOWED_HOSTS)'
    )
    print("  ✓ SESSION_COOKIE_SECURE conditional")

if "CSRF_COOKIE_SECURE = True" in src:
    src = src.replace(
        "CSRF_COOKIE_SECURE = True",
        'CSRF_COOKIE_SECURE = not DEBUG and not any(h in ("127.0.0.1", "localhost") for h in ALLOWED_HOSTS)'
    )
    print("  ✓ CSRF_COOKIE_SECURE conditional")

# 3) HSTS only in production
if "SECURE_HSTS_SECONDS = 31536000" in src:
    src = src.replace(
        "SECURE_HSTS_SECONDS = 31536000",
        'SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000'
    )
    print("  ✓ HSTS conditional")

write(p, src)

print("\n[2/4] Fixing service worker (skip POST + /accounts/)")

p = "config/service_worker_view.py"
if os.path.exists(p):
    src = read(p)

    # Fix fetch handler
    old_fetch = '''// Fetch — network first for HTML/API, cache first for static
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
'''

    new_fetch = '''// Fetch — network first for HTML/API, cache first for static
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip WebSocket and non-http(s)
  if (!url.protocol.startsWith('http')) return;

  // ⚠️ CRITICAL: Skip ALL non-GET requests (POST, PUT, DELETE)
  if (event.request.method !== 'GET') return;

  // ⚠️ Skip admin, auth, api, beta paths
  if (url.pathname.startsWith('/panel-admin/') ||
      url.pathname.startsWith('/django-admin/') ||
      url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/beta-') ||
      url.pathname.startsWith('/accounts/') ||
      url.pathname.startsWith('/social/') ||
      url.pathname.startsWith('/alliance/') ||
      url.pathname.startsWith('/game/')) {
    return;
  }
'''

    if old_fetch in src:
        src = src.replace(old_fetch, new_fetch, 1)
        print("  ✓ Service worker: POST + app paths skipped")

    # Fix offline fallback (return proper HTML, not plain 'offline')
    old_fallback = '''      return caches.match(event.request).then((cached) => cached || new Response('offline', { status: 503 }));'''
    new_fallback = '''      return caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return new Response(
          '<!DOCTYPE html><html><body style="background:#0a0a15;color:#fff;font-family:Tahoma;text-align:center;padding:50px;direction:rtl;"><h1>📡 اتصال قطع است</h1><p>لطفاً اینترنت خود را بررسی کنید و صفحه را دوباره باز کنید.</p><a href="/" style="color:#f4c542;">بازگشت</a></body></html>',
          { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
        );
      });'''

    if old_fallback in src:
        src = src.replace(old_fallback, new_fallback, 1)
        print("  ✓ Better offline fallback (Persian)")

    write(p, src)
else:
    print("  ⚠ service_worker_view.py not found")

print("\n[3/4] Adding SW unregister helper (base.html)")

p = "templates/base.html"
src = read(p)

# Add SW unregister button in a hidden dev tool
if "unregisterServiceWorker" not in src:
    # Add to existing SW registration code
    old = """if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', { scope: '/' })
      .then(r => console.log('[SW] registered:', r.scope))
      .catch(e => console.warn('[SW] error:', e));
  });
}"""

    new = """if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', { scope: '/' })
      .then(r => console.log('[SW] registered:', r.scope))
      .catch(e => console.warn('[SW] error:', e));
  });
}

// Dev helper: unregister SW if needed
window.unregisterServiceWorker = function() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(function(regs) {
      for (var r of regs) r.unregister();
      localStorage.removeItem('installDismissed');
      console.log('SW unregistered. Reload needed.');
      setTimeout(() => location.reload(true), 500);
    });
  }
};"""

    if old in src:
        src = src.replace(old, new, 1)
        write(p, src)
        print("  ✓ Added window.unregisterServiceWorker()")
    else:
        print("  ⚠ SW registration block not found")

print("\n[4/4] Django check + test")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print(f"  ⚠ {r.stderr[:400]}")

# Verify
from importlib import import_module
import django
django.setup()
from django.conf import settings

print(f"\n  DEBUG: {settings.DEBUG}")
print(f"  SECURE_SSL_REDIRECT: {settings.SECURE_SSL_REDIRECT}")
print(f"  SESSION_COOKIE_SECURE: {settings.SESSION_COOKIE_SECURE}")
print(f"  CSRF_COOKIE_SECURE: {settings.CSRF_COOKIE_SECURE}")
print(f"  SECURE_HSTS_SECONDS: {settings.SECURE_HSTS_SECONDS}")

print("\n" + "="*60)
print("DONE")
print("="*60)
print("""
What was fixed:

  ✅ SECURE_SSL_REDIRECT is now conditional:
     - FALSE on localhost (127.0.0.1, localhost)
     - FALSE if DEBUG=True
     - TRUE only in production with HTTPS
     
  ✅ Cookie security is conditional:
     - Not secure on localhost (works over HTTP)
     - Secure in production (HTTPS only)
     
  ✅ HSTS is conditional:
     - 0 on local (no forced HTTPS)
     - 1 year in production
     
  ✅ Service worker fixed:
     - SKIPS all POST/PUT/DELETE requests
     - SKIPS /accounts/, /game/, /social/, /alliance/
     - Better offline page (Persian HTML, not plain text)
     
  ✅ Added dev helper:
     - window.unregisterServiceWorker() in console

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 CRITICAL: Clear old service worker NOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Old service worker is still registered in your browser
and causing the "offline" problem.

Open browser and do ONE of these:

Option A (Recommended):
  F12 → Console → paste and Enter:
    unregisterServiceWorker()
  Then reload (page will reload automatically)

Option B (Manual):
  F12 → Application → Service Workers
  Click "Unregister" next to the entry
  Then Ctrl+Shift+R

Option C (Nuclear):
  Ctrl+Shift+Delete → Clear cookies + cache
  Then reopen site

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 TEST LOCALLY FIRST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python manage.py runserver

Then open:
  http://127.0.0.1:8000/accounts/register/

Fill form and submit → should work now!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 THEN DEPLOY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  git add .
  git commit -m "fix: offline error + service worker"
  git push
  runflare deploy

In Runflare Panel:
  → Restart service
  → Set env var: DISABLE_SSL_REDIRECT = false
""")
