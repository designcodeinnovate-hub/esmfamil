# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import SupportTicket


@login_required
def support_home(request):
    if not getattr(request.user, "has_chosen_avatar", False):
        return redirect("accounts:avatar_select")

    if request.method == "POST":
        subject = (request.POST.get("subject") or "").strip()[:100]
        body = (request.POST.get("body") or "").strip()[:2000]
        category = request.POST.get("category", "general")

        if not subject or len(subject) < 3:
            messages.error(request, "موضوع باید حداقل ۳ حرف باشد.")
        elif not body or len(body) < 10:
            messages.error(request, "متن پیام باید حداقل ۱۰ حرف باشد.")
        else:
            ticket = SupportTicket.objects.create(
                user=request.user,
                subject=subject,
                body=body,
                category=category if category in ("general", "bug", "idea", "payment") else "general",
            )
            messages.success(request, f"✅ تیکت #{ticket.id} ثبت شد.")
            return redirect("support:home")

    my_tickets = SupportTicket.objects.filter(user=request.user)[:20]
    return render(request, "support/home.html", {
        "tickets": my_tickets,
        "active": "home",
    })


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    return render(request, "support/ticket.html", {
        "ticket": ticket,
        "active": "home",
    })


@login_required
def ticket_close(request, ticket_id):
    if request.method != "POST":
        return redirect("support:home")
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    if ticket.status != "closed":
        ticket.status = "closed"
        ticket.save(update_fields=["status"])
        messages.success(request, f"تیکت #{ticket.id} بسته شد.")
    return redirect("support:home")
