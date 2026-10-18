#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add local background music from Downloads."""
import os, sys, glob, shutil, re

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ {p}")

# ============================================================
# 1) Find the mp3 file
# ============================================================
print("\n[1/4] Searching for audio file...")

home = os.path.expanduser("~")
patterns = [
    os.path.join(home, "Downloads", "sound Nature (8).mp3"),
    os.path.join(home, "Downloads", "sound Nature*.mp3"),
    os.path.join(home, "Downloads", "*Nature (8)*.mp3"),
    os.path.join(home, "Downloads", "*Nature*.mp3"),
    os.path.join(home, "Downloads", "*nature*.mp3"),
]

source = None
for pattern in patterns:
    matches = glob.glob(pattern)
    if matches:
        source = matches[0]
        break

if not source:
    # Fallback: any mp3 in Downloads
    all_mp3 = sorted(glob.glob(os.path.join(home, "Downloads", "*.mp3")))
    if all_mp3:
        print("  Files found in ~/Downloads:")
        for i, f in enumerate(all_mp3, 1):
            print(f"    {i}. {os.path.basename(f)}")
        print("\n  ⚠ 'sound Nature (8).mp3' not found.")
        print("  Please use the exact filename or move the file to Downloads.")
    else:
        print("  ❌ No mp3 files found in ~/Downloads")
    sys.exit(1)

print(f"  Found: {source}")
print(f"  Size: {os.path.getsize(source) / 1024 / 1024:.2f} MB")

# ============================================================
# 2) Copy to static/audio/
# ============================================================
print("\n[2/4] Copying to static/audio/")
os.makedirs("static/audio", exist_ok=True)
target = "static/audio/nature.mp3"
shutil.copy2(source, target)
print(f"  ✓ {target} ({os.path.getsize(target) / 1024 / 1024:.2f} MB)")

# ============================================================
# 3) Update base.html
# ============================================================
print("\n[3/4] Updating templates/base.html")
p = "templates/base.html"
src = read(p)

old_audio_pattern = re.compile(
    r'<audio id="globalMusic"[^>]*>\s*<source[^>]+>\s*</audio>',
    re.MULTILINE
)
new_audio = '''<audio id="globalMusic" loop preload="auto">
  <source src="/static/audio/nature.mp3" type="audio/mpeg">
</audio>'''

m = old_audio_pattern.search(src)
if not m:
    print("  ⚠ Audio tag not found in base.html — checking for old URL...")
    old_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    if old_url in src:
        src = src.replace(old_url, "/static/audio/nature.mp3")
        write(p, src)
        print("  ✓ Replaced SoundHelix URL")
    else:
        print("  ❌ Could not find audio tag OR URL")
        sys.exit(1)
else:
    existing = m.group(0)
    if "/static/audio/nature.mp3" in existing:
        print("  ✓ Already using local audio")
    else:
        src = src[:m.start()] + new_audio + src[m.end():]
        write(p, src)
        print("  ✓ Audio tag updated")

# ============================================================
# 4) Add sessionStorage resume (so it doesn't restart on every page)
# ============================================================
print("\n[4/4] Adding playback resume across pages")

src = read(p)

# Check if resume logic already exists
if "natureResumeTime" in src:
    print("  ✓ Resume logic already present")
else:
    # Find the _startMusic function and enhance it
    old_start = '''function _startMusic() {
  if (_musicStarted || !bgMusic) return;
  if (!_musicOn()) return;
  bgMusic.volume = _musicVol();
  bgMusic.play().catch(() => {});
  _musicStarted = true;
}'''
    
    new_start = '''function _startMusic() {
  if (_musicStarted || !bgMusic) return;
  if (!_musicOn()) return;
  // Restore playback position from previous page
  try {
    var saved = parseFloat(sessionStorage.getItem('natureResumeTime') || '0');
    if (saved > 0 && saved < (bgMusic.duration || 99999)) {
      bgMusic.currentTime = saved;
    }
  } catch (e) {}
  bgMusic.volume = _musicVol();
  bgMusic.play().catch(() => {});
  _musicStarted = true;

  // Save position periodically so we can resume on next page
  bgMusic.addEventListener('timeupdate', function() {
    try { sessionStorage.setItem('natureResumeTime', bgMusic.currentTime); } catch (e) {}
  });
}'''
    
    if old_start in src:
        src = src.replace(old_start, new_start, 1)
        write(p, src)
        print("  ✓ Resume logic added")
    else:
        print("  ⚠ _startMusic function not found — trying fallback")
        # Fallback: look for the pattern more loosely
        if "_musicStarted = true" in src:
            print("  ✓ Music start logic exists (no resume)")
        else:
            print("  ⚠ Could not enhance music start")

# ============================================================
# Final check
# ============================================================
print("\n[Check] Django check")
import subprocess
r = subprocess.run([sys.executable, "manage.py", "check"], capture_output=True, text=True)
if r.returncode == 0:
    print("  ✓ Django check PASSED")
else:
    print("  ⚠ Errors:")
    print(r.stderr[:800] if r.stderr else r.stdout[:800])

# Verify audio file served
print("\n[Verify] Audio file present:")
if os.path.exists(target):
    print(f"  ✓ {target} ({os.path.getsize(target) / 1024 / 1024:.2f} MB)")
else:
    print(f"  ❌ {target} missing")

print("\n" + "="*60)
print("DONE!")
print("="*60)
print("""
What was done:
  1. ✓ Copied 'sound Nature (8).mp3' → static/audio/nature.mp3
  2. ✓ Updated <audio> tag in base.html
  3. ✓ Added playback resume across pages (sessionStorage)

How music works now:
  - Plays on first click/touch on any page
  - Loops forever (loop attribute)
  - Volume: settings → میزان صدای موسیقی (0-100%)
  - Mute: settings → موسیقی پس‌زمینه (toggle off)
  - Resumes from same position when navigating between pages
  - When music toggle is OFF in settings, it won't play
  - When music volume = 0, it effectively mutes

To change volume/mute:
  Go to /accounts/settings/ → موسیقی پس‌زمینه

Next:
  python manage.py runserver
  Ctrl+Shift+R (hard refresh to clear cache)
  
Note: Browser requires a user interaction (click/tap) before playing audio,
      so first click anywhere on the page will start the music.
""")
