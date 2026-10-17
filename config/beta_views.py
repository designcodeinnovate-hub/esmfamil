"""صفحات Beta Gate."""

from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from .beta_gate import BETA_PASSWORD


@csrf_exempt
def beta_lock(request):
    if request.session.get("beta_unlocked") is True:
        next_url = request.GET.get("next", "/") or "/"
        return redirect(next_url)

    error = None
    next_url = request.GET.get("next", "/") or "/"

    if request.method == "POST":
        entered = (request.POST.get("password") or "").strip()
        next_url = request.POST.get("next", "/") or "/"

        if entered == BETA_PASSWORD:
            request.session["beta_unlocked"] = True
            request.session.set_expiry(60 * 60 * 24 * 7)
            return redirect(next_url)
        else:
            error = "رمز اشتباه است. دوباره تلاش کن."

    return render(request, "beta_lock.html", {"error": error, "next": next_url})


def beta_logout(request):
    request.session.pop("beta_unlocked", None)
    return redirect("beta_lock")
