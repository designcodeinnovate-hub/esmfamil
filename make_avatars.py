import os
import ssl
import time
import random
import urllib.request

out_dir = "static/avatars/generated"
os.makedirs(out_dir, exist_ok=True)

# SSL context که به خطاها حساس نباشه
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# پارامترها
tops = ["ShortHairShortFlat", "ShortHairShortRound", "ShortHairTheCaesar",
        "LongHairBob", "LongHairBun", "LongHairCurly", "LongHairStraight",
        "LongHairFro", "LongHairMiaWallace", "LongHairNotTooLong",
        "Hijab", "Turban", "Hat", "WinterHat1", "WinterHat2",
        "NoHair", "ShortHairDreads01", "ShortHairFrizzle"]
facial = ["Blank", "BeardMedium", "BeardLight", "BeardMajestic",
          "MoustacheFancy", "MoustacheMagnum"]
access = ["Blank", "Round", "Sunglasses", "Wayfarers", "Prescription01"]
skin = ["edb98a", "d08b5b", "614335", "ffdbb4", "ae5d29", "fd9841", "f8d25c"]
hair_c = ["2c1b18", "4a312c", "724133", "a55728", "b58143",
          "c93305", "d6b370", "e8e1e1", "f59797"]
cloth_c = ["262e33", "65c9ff", "5199e4", "25557c", "e6e6e6",
           "929598", "3c4f5c", "b1e2ff", "a7ffc4", "ffafb9"]
cloth_t = ["BlazerShirt", "Hoodie", "ShirtCrewNeck", "ShirtVNeck", "Overall"]
eyes = ["Default", "Happy", "Side", "Squint", "Wink", "Surprised"]
mouth = ["Smile", "Serious", "Default", "Twinkle", "Grimace"]

random.seed(42)
seen = set()
combos = []
while len(combos) < 100:
    key = (random.choice(tops), random.choice(facial), random.choice(access), random.choice(skin))
    if key not in seen:
        seen.add(key)
        combos.append(key)

def build_url(t, f, a, s):
    return (
        f"https://api.dicebear.com/7.x/avataaars/png?"
        f"topType={t}&accessoriesType={a}&hairColor={random.choice(hair_c)}"
        f"&facialHairType={f}&clotheType={random.choice(cloth_t)}"
        f"&clotheColor={random.choice(cloth_c)}&eyeType={random.choice(eyes)}"
        f"&eyebrowType=Default&mouthType={random.choice(mouth)}"
        f"&skinColor={s}&size=300&radius=50"
    )

def try_download(url, path, max_retries=5):
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=20, context=ctx).read()
            if len(data) > 200:
                with open(path, "wb") as fp:
                    fp.write(data)
                return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1 + attempt)  # وقفه پیش‌رونده
                continue
        return False
    return False

print("Downloading 100 avatars...")
ok = 0
fail_list = []

for i, (t, f, a, s) in enumerate(combos, 1):
    path = f"{out_dir}/{i:03d}.png"

    # اگه قبلاً دانلود شده، رد شو
    if os.path.exists(path) and os.path.getsize(path) > 200:
        ok += 1
        print(f"  {i}/100 ⏭ (already)")
        continue

    url = build_url(t, f, a, s)
    if try_download(url, path):
        ok += 1
        print(f"  {i}/100 ✓")
    else:
        fail_list.append(i)
        print(f"  {i}/100 ✗")

print(f"\n✅ {ok}/100 دانلود شد")

if fail_list:
    print(f"\n⚠️ {len(fail_list)} تا ناموفق — دوباره اجرا کن:")
    print("   python3 make_avatars.py")
