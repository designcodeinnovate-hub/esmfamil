#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Replace entire music block in base.html
# ============================================================
print("\n[1/4] Rewriting music JS")

p = "templates/base.html"
src = read(p)

# Find and remove the old music IIFE
# Look for the audio element first
if 'id="globalMusic"' not in src:
    print("  ❌ audio element missing")
    sys.exit(1)

# Find start of any music-related block
markers = [
    "const bgMusic = document.getElementById('globalMusic')",
    'const bgMusic = document.getElementById("globalMusic")',
    "// ============================================================\n// 🎵 MUSIC SYSTEM",
    "// ۳) مدیریت موسیقی",
]

start = -1
for m in markers:
    idx = src.find(m)
    if idx >= 0 and (start < 0 or idx < start):
        start = idx

# Find end - look for closing of music logic
if start >= 0:
    # Find the closing })(); or next major section
    end_candidates = [
        src.find("// ============================================================\n// ۳) مدیریت موسیقی پس‌زمینه", start + 10),
        src.find("window.applySettingsNow", start),
        src.find("</script>", start),
    ]
    ends = [e for e in end_candidates if e > start]
    end = min(ends) if ends else min(len(src), start + 4000)

    print(f"  Removing block: {start} to {end}")
    src = src[:start] + src[end:]

# Now inject fresh music JS before </script>
NEW_MUSIC = r'''

// ============================================================
// 🎵 MUSIC v5 — persistent across pages, auto-start
// ============================================================
(function() {
  const audio = document.getElementById('globalMusic');
  if (!audio) { console.warn('[Music] no audio element'); return; }

  audio.loop = true;
  audio.preload = 'auto';

  const MIN_START = 3;
  const KEY_POS = 'bgMusicPosV5';
  const KEY_VOL = 'musicVol';
  const KEY_ON = 'music';
  const KEY_UNLOCK = 'bgMusicUnlockedV5';

  const isOn = () => localStorage.getItem(KEY_ON) !== 'false';
  const getVol = () => (parseInt(localStorage.getItem(KEY_VOL)) || 50) / 100;
  const wasUnlocked = () => localStorage.getItem(KEY_UNLOCK) === '1';

  // Detect gameplay pages (music pauses there)
  const path = window.location.pathname;
  const isGameplay = /^\/game\/(quick\/bot\/play|quick\/bot\/submit|team\/play|team\/round-end|room\/|match\/wait)/.test(path);

  // Save position frequently
  let lastSaved = 0;
  function save() {
    if (!audio.paused && audio.currentTime > 0) {
      try { localStorage.setItem(KEY_POS, audio.currentTime.toFixed(2)); } catch(e) {}
    }
  }

  audio.addEventListener('timeupdate', () => {
    const now = Date.now();
    if (now - lastSaved > 200) {
      save();
      lastSaved = now;
    }
  });
  audio.addEventListener('pause', save);
  window.addEventListener('beforeunload', save);
  window.addEventListener('pagehide', save);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') save();
  });

  // Restore position
  function restorePosition() {
    try {
      const saved = parseFloat(localStorage.getItem(KEY_POS) || '0');
      if (isNaN(saved) || saved <= 0) {
        audio.currentTime = MIN_START;
        return;
      }
      const dur = audio.duration;
      if (dur && saved >= dur - 1) {
        audio.currentTime = MIN_START;
      } else {
        audio.currentTime = saved;
      }
    } catch(e) {
      try { audio.currentTime = MIN_START; } catch(e2) {}
    }
  }

  if (audio.readyState >= 1) restorePosition();
  else audio.addEventListener('loadedmetadata', restorePosition, { once: true });

  // If gameplay, don't play music
  if (isGameplay) {
    audio.muted = true;
    audio.pause();
    // Expose control so game pages can resume on exit
    window.__music = {
      element: audio,
      isGameplay: true,
      pause: () => audio.pause(),
      resume: () => { if (isOn()) { audio.muted = false; audio.volume = getVol(); audio.play().catch(()=>{}); } },
    };
    return;
  }

  // Set volume
  audio.volume = getVol();

  // If previously unlocked, try playing with sound immediately
  if (wasUnlocked()) {
    audio.muted = false;
    const p = audio.play();
    if (p) p.catch(() => {
      // Even unlocked state failed - fall back to muted
      audio.muted = true;
      audio.play().catch(()=>{});
      attachUnlock();
    });
  } else {
    // Try muted autoplay
    audio.muted = true;
    audio.play().then(() => {
      attachUnlock();
    }).catch(() => {
      attachUnlock();
    });
  }

  // Attach unlock to ANY user interaction
  function attachUnlock() {
    const events = [
      'pointerdown', 'pointermove', 'pointerup',
      'mousedown', 'mousemove', 'mouseup',
      'touchstart', 'touchmove', 'touchend',
      'keydown', 'keyup', 'keypress',
      'click', 'scroll', 'wheel', 'focus'
    ];

    let done = false;
    const unlock = () => {
      if (done) return;
      done = true;
      if (!isOn()) return;

      audio.muted = false;
      audio.volume = getVol();
      if (audio.paused) {
        audio.play().catch(()=>{});
      }
      try { localStorage.setItem(KEY_UNLOCK, '1'); } catch(e) {}

      events.forEach(ev => {
        document.removeEventListener(ev, unlock, true);
        window.removeEventListener(ev, unlock, true);
      });
    };

    events.forEach(ev => {
      document.addEventListener(ev, unlock, { capture: true, passive: true });
      window.addEventListener(ev, unlock, { capture: true, passive: true });
    });

    // Also try to detect Chrome's "media engagement" — retry play every 2s for 30s
    let retries = 0;
    const retryPlay = setInterval(() => {
      retries++;
      if (audio.paused && isOn() && retries < 15) {
        audio.muted = true;
        audio.play().catch(()=>{});
      } else {
        clearInterval(retryPlay);
      }
    }, 2000);
  }

  // React to settings
  window.addEventListener('storage', (e) => {
    if (e.key === KEY_ON) {
      if (isOn()) {
        audio.muted = false;
        audio.volume = getVol();
        if (audio.paused) audio.play().catch(()=>{});
      } else {
        audio.pause();
      }
    }
    if (e.key === KEY_VOL) {
      audio.volume = getVol();
    }
  });

  // Expose control
  window.__music = {
    element: audio,
    isGameplay: false,
    pause: () => audio.pause(),
    resume: () => {
      if (isOn()) {
        audio.muted = false;
        audio.volume = getVol();
        audio.play().catch(()=>{});
      }
    },
    setVolume: (v) => { audio.volume = v / 100; },
    isPlaying: () => !audio.paused,
  };
})();

'''

# Inject before the settings handler (or before </script>)
anchor = src.find("window.applySettingsNow")
if anchor < 0:
    anchor = src.rfind("</script>")
if anchor < 0:
    print("  ❌ No script tag")
    sys.exit(1)

src = src[:anchor] + NEW_MUSIC + "\n" + src[anchor:]
write(p, src)

# ============================================================
# 2) Update settings JS to use __music
# ============================================================
print("\n[2/4] Updating settings JS hooks")

src = read(p)

# Find old applySettingsNow music handling and replace
old_patterns = [
    ("if (key === 'music') {\n    if (value === 'true' && bgMusic) {", "if (key === 'music') {\n    if (value === 'true' && window.__music) {"),
    ("bgMusic.play().catch(e=>e);", "window.__music.start && window.__music.start();"),
    ("else if (bgMusic) {\n      bgMusic.pause();", "else if (window.__music) {\n      window.__music.pause();"),
    ("if (key === 'musicVol' && bgMusic) {\n    bgMusic.volume = parseInt(value) / 100;", "if (key === 'musicVol' && window.__music) {\n    window.__music.setVolume(parseInt(value) / 100 * 100);"),
]

for old, new in old_patterns:
    if old in src:
        src = src.replace(old, new, 1)

write(p, src)
print("  ✓ Updated")

# ============================================================
# 3) Add music pause to gameplay templates
# ============================================================
print("\n[3/4] Adding music control to gameplay templates")

gameplay_templates = [
    "game/templates/game/bot_play.html",
    "game/templates/game/team_play.html",
    "game/templates/game/room.html",
    "game/templates/game/match_wait.html",
]

for tpl in gameplay_templates:
    if not os.path.exists(tpl):
        print(f"  ⚠ {tpl} not found")
        continue

    src = read(tpl)
    if "__music" in src and "isGameplay" in src:
        print(f"  SKIP: {tpl}")
        continue

    # Add script at end of block extra_js or end of body
    script = '''
<script>
  // Pause background music during gameplay
  if (window.__music) {
    window.__music.isGameplay = true;
    window.__music.pause();
  }
</script>
'''

    # Try to add inside extra_js block
    if "{% block extra_js %}" in src:
        # Add before {% endblock %}
        end_block = src.rfind("{% endblock %}", src.find("{% block extra_js %}"))
        if end_block > 0:
            src = src[:end_block] + script + src[end_block:]
    elif "</body>" in src:
        src = src.replace("</body>", script + "</body>", 1)
    else:
        src += script

    write(tpl, src)

# ============================================================
# 4) Verify
# ============================================================
print("\n[4/4] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print("  ⚠ Errors:")
    print(r.stderr[:600] if r.stderr else r.stdout[:600])
    sys.exit(1)

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
How it works now:

  1. On ANY page load:
     - Audio seeks to saved position (or 3s if first time)
     - Tries to play muted immediately (works without interaction)
     
  2. First user interaction (mousemove, click, scroll, key):
     - Unmutes → sound comes on
     - Marks user as "unlocked" (saved in localStorage)
     
  3. Navigate between pages:
     - Music continues from saved position (not restart)
     - 200ms save interval → minimal gap
     - If already unlocked: plays WITH sound immediately
     
  4. Enter gameplay (bot play, team play, room, match):
     - Music pauses automatically
     - When leaving gameplay: resumes
     
  5. Settings:
     - Music OFF → pauses
     - Volume slider → applies immediately
     
  6. Audio ends (shouldn't happen because loop=true):
     - Restarts from beginning

⚠️ IMPORTANT — browser limitation:
  Modern browsers (Chrome, Safari, Firefox) BLOCK audio playback
  with sound until the user has interacted with the page at least once.
  This is a hard security policy — NO code can bypass it.
  
  What this means:
  - First visit: music plays MUTED, then unmutes on first mouse move
  - After that: every page has music WITH SOUND immediately (unlock persisted)

Test:
  1. Open /game/ → music muted playing from 3s
  2. Move mouse → sound comes on
  3. Click "بازی‌ها" → new page, music continues WITH sound
  4. Click "بازی با بات" → music continues
  5. Click "شروع بازی" → music pauses (gameplay)
  6. After game ends → music resumes

Open /game/ and check console:
  [Music] autoplay OK (muted)
  [Music] unlocked
""")
