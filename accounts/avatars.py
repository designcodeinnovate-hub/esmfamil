import random

"""۱۰۰ آواتار در ۱۰ دسته ۱۰ تایی. هر آواتار یک ایموجی است."""
AVATAR_CATEGORIES = [
    {"key": "animals", "name": "حیوانات", "items": ["🐶", "🐱", "🦁", "🐯", "🐻", "🐼", "🐨", "🐸", "🐵", "🦊"]},
    {"key": "fantasy", "name": "فانتزی", "items": ["🧙", "🧝", "🧛", "🧚", "🦄", "🐉", "👻", "👽", "🤖", "🧜"]},
    {"key": "space", "name": "فضایی", "items": ["🚀", "🛸", "👨‍🚀", "🌟", "⭐", "🌙", "🌞", "🌍", "☄️", "🪐"]},
    {"key": "sports", "name": "ورزشی", "items": ["⚽", "🏀", "🏈", "⚾", "🎾", "🏐", "🏓", "🏸", "🥊", "🎯"]},
    {"key": "minimal", "name": "مینیمال", "items": ["◼️", "◻️", "🔵", "🔴", "🟢", "🟡", "🟣", "🟠", "⚫", "⚪"]},
    {"key": "iranian", "name": "ایرانی", "items": ["🇮🇷", "🕌", "🌷", "🍚", "🫖", "🐆", "🦅", "🌾", "🏺", "🎻"]},
    {"key": "retro", "name": "رترو", "items": ["📻", "📼", "☎️", "📟", "💾", "📀", "🎞️", "🕹️", "📠", "☂️"]},
    {"key": "nature", "name": "طبیعت", "items": ["🌳", "🌲", "🌴", "🌵", "🍁", "🌸", "🌻", "🌹", "🍄", "🌊"]},
    {"key": "objects", "name": "اشیا", "items": ["💎", "🔮", "🎩", "👑", "🎸", "🎺", "🥁", "🎨", "📚", "✏️"]},
    {"key": "abstract", "name": "انتزاعی", "items": ["🌀", "💠", "🔱", "⚛️", "♻️", "🔰", "✴️", "❇️", "✨", "💫"]},
]

ALL_AVATARS = []
AVATAR_BY_ID = {}
for _cat in AVATAR_CATEGORIES:
    for _i, _emoji in enumerate(_cat["items"]):
        _avatar_id = len(ALL_AVATARS)
        ALL_AVATARS.append({"id": _avatar_id, "category": _cat["key"], "category_name": _cat["name"], "emoji": _emoji})
        AVATAR_BY_ID[_avatar_id] = _emoji

def get_emoji(avatar_id):
    if avatar_id is None: return "👤"
    try: return AVATAR_BY_ID.get(int(avatar_id), "👤")
    except (ValueError, TypeError): return "👤"

def get_image_url(avatar_id):
    if avatar_id is None: return None
    try: aid = int(avatar_id)
    except (ValueError, TypeError): return None
    if not (1 <= aid <= 44): return None
    return f"/static/avatars/images/{aid:03d}.jpg"

def get_avatar_display(user):
    if user is None: return ("emoji", "👤")
    avatar_type = getattr(user, "avatar_type", "emoji") or "emoji"
    avatar_id = getattr(user, "avatar_id", None)
    if avatar_type == "image":
        url = get_image_url(avatar_id)
        if url: return ("image", url)
        return ("emoji", "👤")
    return ("emoji", get_emoji(avatar_id))

# ۴۴ عکس لوکال
IMAGE_AVATARS = [{"id": i, "url": f"/static/avatars/images/{i:03d}.jpg"} for i in range(1, 45)]
