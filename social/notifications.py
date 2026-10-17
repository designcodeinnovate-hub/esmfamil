from .models import Notification


def notify(user, ntype, title, body="", url=""):
    """ساخت اعلان جدید."""
    try:
        return Notification.objects.create(
            user=user, type=ntype, title=title, body=body, url=url,
        )
    except Exception:
        return None


def unread_count(user):
    if not user.is_authenticated:
        return 0
    return Notification.objects.filter(user=user, is_read=False).count()
