# -*- coding: utf-8 -*-
import random
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import ShopItem, Purchase


@login_required
def shop_home(request):
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    items = ShopItem.objects.filter(is_active=True)
    categories = {"box": [], "boost": [], "theme": [], "bundle": [], "cosmetic": []}
    for item in items:
        if item.category in categories:
            item.is_sold_out = (item.stock is not None and item.stock <= 0)
            categories[item.category].append(item)

    recent = Purchase.objects.filter(user=request.user)[:8]

    return render(request, "accounts/shop.html", {
        "categories": categories,
        "recent_purchases": recent,
        "active": "profile",
        "user_coins": request.user.coins or 0,
        "user_gems": request.user.gems or 0,
    })


@login_required
def shop_buy(request, item_id):
    if request.method != "POST":
        return redirect("accounts:shop")
    if not request.user.has_chosen_avatar:
        return redirect("accounts:avatar_select")

    item = get_object_or_404(ShopItem, id=item_id, is_active=True)

    if item.stock is not None and item.stock <= 0:
        messages.error(request, "این آیتم تمام شده.")
        return redirect("accounts:shop")
    if item.price_coins and (request.user.coins or 0) < item.price_coins:
        messages.error(request, f"سکه کافی نداری (نیاز: {item.price_coins}).")
        return redirect("accounts:shop")
    if item.price_gems and (request.user.gems or 0) < item.price_gems:
        messages.error(request, f"جم کافی نداری (نیاز: {item.price_gems}).")
        return redirect("accounts:shop")

    if item.price_coins: request.user.coins -= item.price_coins
    if item.price_gems: request.user.gems -= item.price_gems

    reward_text = ""
    if item.reward_type == "coins_fixed":
        request.user.coins += item.reward_value
        reward_text = f"+{item.reward_value} سکه"
    elif item.reward_type == "gems_fixed":
        request.user.gems += item.reward_value
        reward_text = f"+{item.reward_value} جم"
    elif item.reward_type == "coins_random":
        amount = random.randint(max(1, item.reward_min or 50), max(item.reward_min or 50, item.reward_max or 300))
        request.user.coins += amount
        reward_text = f"🎉 +{amount} سکه!"
    elif item.reward_type == "gems_random":
        amount = random.randint(max(1, item.reward_min or 1), max(item.reward_min or 1, item.reward_max or 15))
        request.user.gems += amount
        reward_text = f"🎉 +{amount} جم!"
    elif item.reward_type == "theme":
        reward_text = "🎨 تم فعال شد"
    elif item.reward_type == "boost":
        reward_text = "⚡ بوست فعال شد"

    request.user.save(update_fields=["coins", "gems"])

    if item.stock is not None:
        item.stock = max(0, item.stock - 1)
        item.save(update_fields=["stock"])

    Purchase.objects.create(
        user=request.user, item=item,
        item_name=item.name, item_icon=item.icon,
        price_paid_coins=item.price_coins,
        price_paid_gems=item.price_gems,
        reward_given=reward_text,
    )
    messages.success(request, f"{item.icon} {item.name} خریداری شد! {reward_text}")
    return redirect("accounts:shop")


@login_required
def shop_exchange(request):
    if request.method != "POST":
        return redirect("accounts:shop")
    try:
        amount = int(request.POST.get("amount") or 0)
        direction = request.POST.get("direction", "coins_to_gems")
    except (ValueError, TypeError):
        messages.error(request, "مقدار نامعتبر.")
        return redirect("accounts:shop")
    if amount <= 0:
        messages.error(request, "مقدار باید بیشتر از صفر باشد.")
        return redirect("accounts:shop")

    if direction == "coins_to_gems":
        needed = amount * 100
        if (request.user.coins or 0) < needed:
            messages.error(request, f"سکه کافی نداری (نیاز: {needed}).")
            return redirect("accounts:shop")
        request.user.coins -= needed
        request.user.gems += amount
        request.user.save(update_fields=["coins", "gems"])
        messages.success(request, f"تبدیل شد! -{needed} سکه → +{amount} جم")
    else:
        if (request.user.gems or 0) < amount:
            messages.error(request, f"جم کافی نداری (نیاز: {amount}).")
            return redirect("accounts:shop")
        reward = amount * 80
        request.user.gems -= amount
        request.user.coins += reward
        request.user.save(update_fields=["coins", "gems"])
        messages.success(request, f"تبدیل شد! -{amount} جم → +{reward} سکه")

    return redirect("accounts:shop")
