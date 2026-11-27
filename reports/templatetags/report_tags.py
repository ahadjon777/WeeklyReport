from django import template

from ..periods import MONTHS_UZ, WEEKDAYS_UZ

register = template.Library()


@register.filter
def uzdate(d):
    """23.11.2026, Dushanba"""
    return f"{d:%d.%m.%Y}, {WEEKDAYS_UZ[d.weekday()]}"


@register.filter
def uzshort(d):
    """Dush 23"""
    return f"{WEEKDAYS_UZ[d.weekday()][:3]} {d.day}"


@register.filter
def initials(user):
    name = (user.get_full_name() or user.username).split()
    return "".join(p[0] for p in name[:2]).upper() or "?"


@register.filter
def fullname(user):
    return user.get_full_name() or user.username


@register.filter
def avclass(user):
    return f"av{user.pk % 6}"


@register.filter
def hrs(value):
    """4.0 -> 4, 4.5 -> 4.5"""
    if value in (None, ""):
        return ""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return value
    return f"{v:g}"
