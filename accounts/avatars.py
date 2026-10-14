"""۱۰۰ آواتار در ۱۰ دسته ۱۰ تایی. هر آواتار یک ایموجی است."""

AVATAR_CATEGORIES = [
    {
        "key": "animals",
        "name": "حیوانات",
        "items": ["🐶", "🐱", "🦁", "🐯", "🐻", "🐼", "🐨", "🐸", "🐵", "🦊"],
    },
    {
        "key": "fantasy",
        "name": "فانتزی",
        "items": ["🧙", "🧝", "🧛", "🧚", "🦄", "🐉", "👻", "👽", "🤖", "🧜"],
    },
    {
        "key": "space",
        "name": "فضایی",
        "items": ["🚀", "🛸", "👨‍🚀", "🌟", "⭐", "🌙", "🌞", "🌍", "☄️", "🪐"],
    },
    {
        "key": "sports",
        "name": "ورزشی",
        "items": ["⚽", "🏀", "🏈", "⚾", "🎾", "🏐", "🏓", "🏸", "🥊", "🎯"],
    },
    {
        "key": "minimal",
        "name": "مینیمال",
        "items": ["◼️", "◻️", "🔵", "🔴", "🟢", "🟡", "🟣", "🟠", "⚫", "⚪"],
    },
    {
        "key": "iranian",
        "name": "ایرانی",
        "items": ["🇮🇷", "🕌", "🌷", "🍚", "🫖", "🐆", "🦅", "🌾", "🏺", "🎻"],
    },
    {
        "key": "retro",
        "name": "رترو",
        "items": ["📻", "📼", "☎️", "📟", "💾", "📀", "🎞️", "🕹️", "📠", "☂️"],
    },
    {
        "key": "nature",
        "name": "طبیعت",
        "items": ["🌳", "🌲", "🌴", "🌵", "🍁", "🌸", "🌻", "🌹", "🍄", "🌊"],
    },
    {
        "key": "objects",
        "name": "اشیا",
        "items": ["💎", "🔮", "🎩", "👑", "🎸", "🎺", "🥁", "🎨", "📚", "✏️"],
    },
    {
        "key": "abstract",
        "name": "انتزاعی",
        "items": ["🌀", "💠", "🔱", "⚛️", "♻️", "🔰", "✴️", "❇️", "✨", "💫"],
    },
]

# لیست تخت ۱۰۰ تایی برای دسترسی سریع
ALL_AVATARS = []
AVATAR_BY_ID = {}
for _cat in AVATAR_CATEGORIES:
    for _i, _emoji in enumerate(_cat["items"]):
        _avatar_id = len(ALL_AVATARS)  # 0..99
        ALL_AVATARS.append({
            "id": _avatar_id,
            "category": _cat["key"],
            "category_name": _cat["name"],
            "emoji": _emoji,
        })
        AVATAR_BY_ID[_avatar_id] = _emoji


def get_emoji(avatar_id):
    """اگر avatar_id نامعتبر بود، ایموجی پیش‌فرض برگردان."""
    if avatar_id is None:
        return "❓"
    return AVATAR_BY_ID.get(int(avatar_id), "❓")