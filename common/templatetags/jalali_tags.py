# -*- coding: utf-8 -*-
"""Pure Python Jalali (Shamsi) date converter - no external deps."""
from django import template

register = template.Library()


def g2j(gy, gm, gd):
    """Gregorian -> Jalali. Returns (jy, jm, jd)."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) - 80 + gd + g_d_m[gm - 1]
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def j2g(jy, jm, jd):
    """Jalali -> Gregorian. Returns (gy, gm, gd)."""
    if jy > 979:
        gy = 1600
        jy -= 979
    else:
        gy = 621
    days = (365 * jy) + ((jy // 33) * 8) + (((jy % 33) + 3) // 4) + 78 + jd + ((jm - 1) * 31 if jm < 7 else ((jm - 7) * 30) + 186)
    gy += 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    is_leap = (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)
    sal_a = [0, 31, 29 if is_leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 1
    for i in range(1, 13):
        if gd <= sal_a[i]:
            gm = i
            break
        gd -= sal_a[i]
    return gy, gm, gd


class JDate:
    def __init__(self, jy, jm, jd, h=0, mi=0, s=0):
        self.year = jy
        self.month = jm
        self.day = jd
        self.hour = h
        self.minute = mi
        self.second = s

    def strftime(self, fmt):
        # Minimal strftime - only Y/m/d H:i:s + Persian
        out = fmt
        out = out.replace("%Y", str(self.year))
        out = out.replace("%m", str(self.month).zfill(2))
        out = out.replace("%d", str(self.day).zfill(2))
        out = out.replace("%H", str(self.hour).zfill(2))
        out = out.replace("%M", str(self.minute).zfill(2))
        out = out.replace("%S", str(self.second).zfill(2))
        # Also handle Django-style tokens
        out = out.replace("Y", str(self.year))
        out = out.replace("m", str(self.month).zfill(2))
        out = out.replace("d", str(self.day).zfill(2))
        out = out.replace("H", str(self.hour).zfill(2))
        out = out.replace("i", str(self.minute).zfill(2))
        out = out.replace("s", str(self.second).zfill(2))
        return out


@register.filter
def to_jalali(value):
    if not value:
        return None
    try:
        jy, jm, jd = g2j(value.year, value.month, value.day)
        h = getattr(value, "hour", 0)
        mi = getattr(value, "minute", 0)
        s = getattr(value, "second", 0)
        return JDate(jy, jm, jd, h, mi, s)
    except Exception:
        return None


@register.filter
def jdate(value, fmt="Y/m/d H:i"):
    if not value:
        return ""
    try:
        jy, jm, jd = g2j(value.year, value.month, value.day)
        h = getattr(value, "hour", 0)
        mi = getattr(value, "minute", 0)
        s = getattr(value, "second", 0)
        j = JDate(jy, jm, jd, h, mi, s)
        return j.strftime(fmt)
    except Exception:
        try:
            return value.strftime(fmt)
        except Exception:
            return str(value)
