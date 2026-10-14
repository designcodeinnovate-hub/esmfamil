# game/bot.py
"""موتور بات: پاسخ‌دهی هوشمند با زمان‌بندی متغیر بر اساس سختی و حرف."""

import random

from .bot_data import words_for, LETTER_DIFFICULTY

HARD_LETTERS = {"ث", "ض", "ظ", "ژ", "ط", "غ", "ذ"}
MEDIUM_LETTERS = {"ح", "خ", "ص", "ق", "ع", "ک", "گ", "چ", "پ", "ش", "ز", "و", "ه"}

ALL_LETTERS = list(LETTER_DIFFICULTY.keys())


def letter_weight(letter):
    if letter in HARD_LETTERS:
        return 1.4
    if letter in MEDIUM_LETTERS:
        return 1.2
    return 1.0


def bot_pick_letter(difficulty):
    """بات یک حرف بر اساس سختی بازی انتخاب می‌کند."""
    if difficulty == "easy":
        pool = [l for l in ALL_LETTERS if LETTER_DIFFICULTY[l] == 1]
    elif difficulty == "medium":
        pool = [l for l in ALL_LETTERS if LETTER_DIFFICULTY[l] <= 2]
    else:
        pool = ALL_LETTERS[:]
    return random.choice(pool)


def bot_answer_for(category, letter, difficulty):
    """بات یک کلمه برای دسته و حرف انتخاب می‌کند. اگر نتوانست، خالی."""
    words = words_for(category, letter)
    if not words:
        return ""
    fail_rate = {"easy": 0.35, "medium": 0.18, "hard": 0.07}.get(difficulty, 0.18)
    if random.random() < fail_rate:
        return ""
    return random.choice(words)


def bot_answers_for_round(categories, letter, difficulty, max_seconds):
    """پاسخ‌های بات + زمان صرف شده."""
    base_ratio = {"easy": 0.85, "medium": 0.60, "hard": 0.35}.get(difficulty, 0.60)
    ratio = base_ratio * letter_weight(letter)
    ratio = max(0.15, min(0.9, ratio))
    elapsed = max_seconds * ratio * random.uniform(0.85, 1.15)

    answers = {}
    used = 0.0
    per_word = elapsed / max(len(categories), 1)
    for cat in categories:
        if used + per_word > elapsed:
            answers[cat] = ""
        else:
            answers[cat] = bot_answer_for(cat, letter, difficulty)
            used += per_word
    return answers, elapsed
