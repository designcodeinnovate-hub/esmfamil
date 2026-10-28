# -*- coding: utf-8 -*-
"""Custom middleware for the accounts app."""
from django.utils import timezone
from django.contrib.auth import get_user_model


class LastSeenMiddleware:
    """
    Update user.last_seen on every authenticated request,
    throttled to once per `UPDATE_INTERVAL` seconds to avoid
    a DB hit on every asset request.
    """

    UPDATE_INTERVAL = 60  # seconds

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            now = timezone.now()
            last = getattr(user, "last_seen", None)
            needs_update = (
                last is None
                or (now - last).total_seconds() > self.UPDATE_INTERVAL
            )
            if needs_update:
                try:
                    User = get_user_model()
                    User.objects.filter(pk=user.pk).update(last_seen=now)
                    # keep the in-memory instance consistent
                    user.last_seen = now
                except Exception:
                    # never let presence break a request
                    pass
        return self.get_response(request)
