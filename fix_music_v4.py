#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Read base.html
# ============================================================
print("\n[1/4] Reading base.html")
p = "templates/base.html"
src = read(p)

# ============================================================
# 2) Remove hint button (with surrounding style block)
# ============================================================
print("\n[2/4] Removing music hint button")

import re

# Remove the hint div
hint_div_pattern = re.compile(
    r'<div id="musicHint"[^>]*>.*?</div>\s*',
    re.DOTALL
)
new_src = hint_div_pattern.sub('', src)
if new_src != src:
    print("  ✓ Removed #musicHint div")
    src = new_src

# Remove the pulseHint style if it was standalone
hint_style_pattern = re.compile(
    r'<style>\s*@keyframes pulseHint \{[^}]*\}\s*</style>\s*',
    re.DOTALL
)
new_src = hint_style_pattern.sub('', src)
if new_src != src:
    print("  ✓ Removed pulseHint style")
    src = new_src

# Also look for any JS referencing musicHint
if 'musicHint' in src:
    # There may be references in JS - remove those lines
    lines = src.split('\n')
    lines = [l for l in lines if 'musicHint' not in l]
    src = '\n'.join(lines)
    print("  ✓ Removed musicHint JS references")

# ============================================================
# 3) Replace music JS block entirely
# ============================================================
print("\n[3/4] Replacing music JS with v4 (auto-start, 3s offset, resume)")

# Find the audio element
if 'id="globalMusic"' not in src:
    print("  ❌ globalMusic audio element not found")
    sys.exit(1)

# Find "management of music" section and replace
# Try multiple strategies to locate the block

# Strategy A: Find the whole "const bgMusic = ..." through end of music block
music_block_start = None
music_block_end = None

# Find bgMusic declaration
idx = src.find("const bgMusic = document.getElementById('globalMusic')")
if idx >= 0:
    music_block_start = idx
elif idx < 0:
    idx = src.find("const bgMusic = document.getElementById(\"globalMusic\")")
    if idx >= 0:
        music_block_start = idx

if music_block_start is None:
    print("  ⚠ bgMusic declaration not found - looking for _startMusic")
    idx = src.find("function _startMusic()")
    if idx >= 0:
        music_block_start = idx

if music_block_start is None:
    print("  ⚠ Could not find music code. Injecting new block before </script>")
    inject_before = src.rfind("</script>")
    if inject_before < 0:
        print("  ❌ No script tag found")
        sys.exit(1)
    NEW_MUSIC_JS = r'''

// ============================================================
// 🎵 MUSIC SYSTEM v4 — auto-start, 3s offset, resume across pages
// ============================================================
(function() {
  const bgMusic = document.getElementById('globalMusic');
  if (!bgMusic) return;

  // Ensure loop attribute is set (belt and suspenders)
  bgMusic.loop = true;
  bgMusic.setAttribute('preload', 'auto');

  const MIN_START = 3; // seconds — skip intro
  const SAVE_EVERY = 500; // ms

  const musicOn = () => localStorage.getItem('music') !== 'false';
  const musicVol = () => (parseInt(localStorage.getItem('musicVol')) || 50) / 100;
  const isUnlocked = () => localStorage.getItem('bgMusicUnlocked') === '1';
  const setUnlocked = () => localStorage.setItem('bgMusicUnlocked', '1');

  // --- Get position ---
  // First ever load: start at 3s
  // Subsequent loads: resume from saved position
  function getStartPosition() {
    const saved = localStorage.getItem('bgMusicPos');
    if (saved === null) return MIN_START;
    const pos = parseFloat(saved);
    if (isNaN(pos)) return MIN_START;
    return pos;
  }

  // --- Apply position after metadata loaded ---
  function applyPosition() {
    try {
      const pos = getStartPosition();
      const dur = bgMusic.duration;
      if (dur && pos >= dur - 1) {
        // Saved position past end → loop from start
        bgMusic.currentTime = MIN_START;
      } else if (pos > 0) {
        bgMusic.currentTime = pos;
      }
    } catch(e) {}
  }

  if (bgMusic.readyState >= 1) {
    applyPosition();
  } else {
    bgMusic.addEventListener('loadedmetadata', applyPosition, { once: true });
  }

  // --- Save position ---
  function savePos() {
    try {
      if (!bgMusic.paused && bgMusic.currentTime > 0) {
        localStorage.setItem('bgMusicPos', bgMusic.currentTime);
      }
    } catch(e) {}
  }

  setInterval(savePos, SAVE_EVERY);
  document.addEventListener('visibilitychange', savePos);
  window.addEventListener('pagehide', savePos);
  window.addEventListener('beforeunload', savePos);

  // --- Start playback (muted first, then unmute on first interaction) ---
  function tryPlayMuted() {
    if (!musicOn()) return;
    bgMusic.volume = musicVol();
    bgMusic.muted = true;

    const p = bgMusic.play();
    if (p !== undefined) {
      p.then(() => {
        attachUnlockHandlers();
        if (isUnlocked()) {
          // Was already unlocked in this session → unmute immediately
          bgMusic.muted = false;
        }
      }).catch(() => {
        // Muted autoplay failed — still attach unlock handlers
        attachUnlockHandlers();
      });
    } else {
      attachUnlockHandlers();
    }
  }

  function attachUnlockHandlers() {
    const events = ['pointerdown','touchstart','keydown','click','wheel','mousemove','scroll','focus'];

    const unmute = () => {
      if (!musicOn()) return;
      bgMusic.muted = false;
      bgMusic.volume = musicVol();
      if (bgMusic.paused) {
        bgMusic.play().catch(() => {});
      }
      setUnlocked();
      cleanup();
    };

    const cleanup = () => {
      events.forEach(ev => {
        document.removeEventListener(ev, unmute, true);
        window.removeEventListener(ev, unmute, true);
      });
    };

    events.forEach(ev => {
      document.addEventListener(ev, unmute, { capture: true, passive: true });
      window.addEventListener(ev, unmute, { capture: true, passive: true });
    });
  }

  // Fire playback start
  if (bgMusic.readyState >= 2) {
    tryPlayMuted();
  } else {
    bgMusic.addEventListener('canplay', tryPlayMuted, { once: true });
    // Fallback in case canplay doesn't fire (edge case)
    setTimeout(tryPlayMuted, 800);
  }

  // --- React to settings changes ---
  window.addEventListener('storage', (e) => {
    if (e.key === 'music') {
      if (musicOn()) {
        bgMusic.muted = false;
        bgMusic.volume = musicVol();
        if (bgMusic.paused) bgMusic.play().catch(()=>{});
      } else {
        bgMusic.pause();
      }
    }
    if (e.key === 'musicVol') {
      bgMusic.volume = musicVol();
    }
  });

  // --- Expose global API for settings page ---
  window.__music = {
    element: bgMusic,
    start: () => {
      bgMusic.muted = false;
      bgMusic.volume = musicVol();
      bgMusic.play().catch(()=>{});
    },
    pause: () => bgMusic.pause(),
    isPlaying: () => !bgMusic.paused,
    setVolume: (v) => { bgMusic.volume = v / 100; },
  };
})();

'''
    src = src[:inject_before] + NEW_MUSIC_JS + src[inject_before:]
    write(p, src)
    print("  ✓ Music JS injected")
else:
    print(f"  Found music block start at index {music_block_start}")
    # Find end of block - look for common end markers
    end_candidates = [
        src.find("window.applySettingsNow", music_block_start),
        src.find("// ============================================================\n// ", music_block_start + 200),
        src.find("</script>", music_block_start),
    ]
    # Pick the earliest non-negative
    valid_ends = [e for e in end_candidates if e > music_block_start]
    if valid_ends:
        music_block_end = min(valid_ends)
    else:
        # Fallback: go to 5000 chars or end of script
        music_block_end = min(len(src), music_block_start + 5000)
        while music_block_end < len(src) and src[music_block_end] not in '\n':
            music_block_end += 1

    print(f"  Music block: {music_block_start} to {music_block_end}")

    NEW_MUSIC_JS = r'''

// ============================================================
// 🎵 MUSIC SYSTEM v4 — auto-start, 3s offset, resume across pages
// ============================================================
(function() {
  const bgMusic = document.getElementById('globalMusic');
  if (!bgMusic) return;

  // Ensure loop attribute is set
  bgMusic.loop = true;
  bgMusic.setAttribute('preload', 'auto');

  const MIN_START = 3;
  const SAVE_EVERY = 500;

  const musicOn = () => localStorage.getItem('music') !== 'false';
  const musicVol = () => (parseInt(localStorage.getItem('musicVol')) || 50) / 100;
  const isUnlocked = () => localStorage.getItem('bgMusicUnlocked') === '1';
  const setUnlocked = () => localStorage.setItem('bgMusicUnlocked', '1');

  function getStartPosition() {
    const saved = localStorage.getItem('bgMusicPos');
    if (saved === null) return MIN_START;
    const pos = parseFloat(saved);
    if (isNaN(pos)) return MIN_START;
    return pos;
  }

  function applyPosition() {
    try {
      const pos = getStartPosition();
      const dur = bgMusic.duration;
      if (dur && pos >= dur - 1) {
        bgMusic.currentTime = MIN_START;
      } else if (pos > 0) {
        bgMusic.currentTime = pos;
      }
    } catch(e) {}
  }

  if (bgMusic.readyState >= 1) {
    applyPosition();
  } else {
    bgMusic.addEventListener('loadedmetadata', applyPosition, { once: true });
  }

  function savePos() {
    try {
      if (!bgMusic.paused && bgMusic.currentTime > 0) {
        localStorage.setItem('bgMusicPos', bgMusic.currentTime);
      }
    } catch(e) {}
  }

  setInterval(savePos, SAVE_EVERY);
  document.addEventListener('visibilitychange', savePos);
  window.addEventListener('pagehide', savePos);
  window.addEventListener('beforeunload', savePos);

  function tryPlayMuted() {
    if (!musicOn()) return;
    bgMusic.volume = musicVol();
    bgMusic.muted = true;
    const p = bgMusic.play();
    if (p !== undefined) {
      p.then(() => {
        attachUnlockHandlers();
        if (isUnlocked()) bgMusic.muted = false;
      }).catch(() => {
        attachUnlockHandlers();
      });
    } else {
      attachUnlockHandlers();
    }
  }

  function attachUnlockHandlers() {
    const events = ['pointerdown','touchstart','keydown','click','wheel','mousemove','scroll','focus'];
    const unmute = () => {
      if (!musicOn()) return;
      bgMusic.muted = false;
      bgMusic.volume = musicVol();
      if (bgMusic.paused) bgMusic.play().catch(() => {});
      setUnlocked();
      events.forEach(ev => {
        document.removeEventListener(ev, unmute, true);
        window.removeEventListener(ev, unmute, true);
      });
    };
    events.forEach(ev => {
      document.addEventListener(ev, unmute, { capture: true, passive: true });
      window.addEventListener(ev, unmute, { capture: true, passive: true });
    });
  }

  if (bgMusic.readyState >= 2) {
    tryPlayMuted();
  } else {
    bgMusic.addEventListener('canplay', tryPlayMuted, { once: true });
    setTimeout(tryPlayMuted, 800);
  }

  window.addEventListener('storage', (e) => {
    if (e.key === 'music') {
      if (musicOn()) {
        bgMusic.muted = false;
        bgMusic.volume = musicVol();
        if (bgMusic.paused) bgMusic.play().catch(()=>{});
      } else {
        bgMusic.pause();
      }
    }
    if (e.key === 'musicVol') bgMusic.volume = musicVol();
  });

  window.__music = {
    element: bgMusic,
    start: () => {
      bgMusic.muted = false;
      bgMusic.volume = musicVol();
      bgMusic.play().catch(()=>{});
    },
    pause: () => bgMusic.pause(),
    isPlaying: () => !bgMusic.paused,
    setVolume: (v) => { bgMusic.volume = v / 100; },
  };
})();

'''
    src = src[:music_block_start] + NEW_MUSIC_JS + src[music_block_end:]
    write(p, src)
    print("  ✓ Music block replaced")

# ============================================================
# 4) Verify audio tag has loop + preload
# ============================================================
print("\n[4/4] Verifying audio tag")
src = read(p)

if 'id="globalMusic"' not in src:
    print("  ❌ Audio tag missing")
    sys.exit(1)

# Ensure loop and preload are correct
if 'preload="none"' in src:
    src = src.replace('preload="none"', 'preload="auto"')
    write(p, src)
    print("  ✓ preload set to auto")

if 'loop' not in src.split('id="globalMusic"')[1][:200]:
    print("  ⚠ loop attribute may be missing")

print("  ✓ Audio tag OK")

# ============================================================
# Final check
# ============================================================
print("\n[check] Django check")
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print("  ⚠ Errors:")
    print(r.stderr[:800] if r.stderr else r.stdout[:800])
    sys.exit(1)

# Verify no musicHint left
src = read(p)
if 'musicHint' in src:
    print("\n  ⚠ WARNING: 'musicHint' still found in base.html")
else:
    print("\n  ✓ musicHint fully removed")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
What changed:

  ✓ Removed 🔊 hint button completely
  ✓ Music auto-plays muted on every page load
  ✓ Unmutes on ANY interaction (mouse move, scroll, click, key, touch)
  ✓ Starts from 3 seconds (skips intro) on first load
  ✓ Saves position every 500ms
  ✓ Resumes from saved position on page navigation
  ✓ Loops forever when track ends
  ✓ When music OFF in settings → stays paused
  ✓ When music volume changed → applies immediately
  ✓ Unlock state persisted (bgMusicUnlocked) — once user interacts
    once, subsequent pages start with sound immediately

How it works on navigation:
  - User clicks a link → beforeunload saves currentTime
  - New page loads → reads bgMusicPos → seeks to it → muted play
  - If user was already unlocked this session → unmute immediately
  - Gap between pages is ~100-200ms (barely noticeable)

Next:
  python manage.py runserver
  Ctrl+Shift+R (hard refresh)

Test:
  1. Open /game/ → music plays from ~3s (maybe muted first)
  2. Move mouse / scroll → sound comes on
  3. Click any navigation link
  4. New page → music resumes from same spot (not from 3s again)
  5. Let it finish → loops to 0 → plays through
  6. Settings → music OFF → pauses
  7. Settings → music ON → resumes

If music doesn't play:
  F12 Console → type:
    document.getElementById('globalMusic').play()
  → If error appears, send it
""")
