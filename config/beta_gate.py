"""محافظ Beta برای دسترسی محدود در فاز آزمایشی."""

from django.shortcuts import redirect


BETA_PASSWORD = "emami_irani_esm1405"

EXEMPT_PATHS = [
    "/beta-lock/",
    "/beta-logout/",
    "/static/",
    "/favicon.ico",
]


class BetaGateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        for exempt in EXEMPT_PATHS:
            if path.startswith(exempt):
                return self.get_response(request)
        if request.session.get("beta_unlocked") is True:
            return self.get_response(request)
        return redirect(f"/beta-lock/?next={path}")
