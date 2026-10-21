# -*- coding: utf-8 -*-
"""Context processor to expose FORCE_GUEST_MODE to all templates."""
from django.conf import settings


def force_guest_mode(request):
    return {
        "force_guest_mode": getattr(settings, "FORCE_GUEST_MODE", False),
    }
