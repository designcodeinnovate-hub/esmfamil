from django.urls import path
from . import admin_views

app_name = "custom_admin"

urlpatterns = [
    # Auth
    path("", admin_views.admin_login, name="login"),
    path("dashboard/", admin_views.dashboard, name="dashboard"),
    path("logout/", admin_views.admin_logout, name="logout"),

    # Users
    path("user/<int:user_id>/", admin_views.user_detail, name="user_detail"),
    path("user/<int:user_id>/edit/", admin_views.user_edit, name="user_edit"),
    path("user/<int:user_id>/notify/", admin_views.user_notify, name="user_notify"),
    path("user/<int:user_id>/notify/<int:notif_id>/delete/", admin_views.user_notify_delete, name="user_notify_delete"),
    path("user/<int:user_id>/notify/clear/", admin_views.user_notify_clear, name="user_notify_clear"),
    path("user/<int:user_id>/notify/<int:notif_id>/toggle-read/", admin_views.user_notify_toggle_read, name="user_notify_toggle_read"),
    path("user/<int:user_id>/update/", admin_views.user_update, name="user_update"),
    path("user/<int:user_id>/toggle/", admin_views.user_toggle_active, name="user_toggle"),
    path("user/<int:user_id>/toggle-staff/", admin_views.user_toggle_staff, name="user_toggle_staff"),
    path("user/<int:user_id>/delete/", admin_views.user_delete, name="user_delete"),

    # Alliances
    path("alliances/", admin_views.alliances_list, name="alliances_list"),
    path("alliance/<int:alliance_id>/", admin_views.alliance_manage, name="alliance_manage"),

    # Rooms
    path("rooms/", admin_views.rooms_list, name="rooms_list"),
    path("rooms/active/", admin_views.rooms_active, name="rooms_active"),
    path("room/<uuid:game_id>/delete/", admin_views.room_delete, name="room_delete"),

    # Announcements
    path("announcements/", admin_views.announcements_list, name="announcements_list"),
    path("announcement/create/", admin_views.announcement_create, name="announcement_create"),
    path("announcement/delete/", admin_views.announcement_delete, name="announcement_delete"),

    # Challenge (was "tournaments" — renamed)
    path("challenges/", admin_views.challenges_list, name="challenges_list"),
    path("challenge/create/", admin_views.challenge_create, name="challenge_create"),
    path("challenge/<int:challenge_id>/", admin_views.challenge_edit, name="challenge_edit"),
    path("challenge/<int:challenge_id>/delete/", admin_views.challenge_delete, name="challenge_delete"),
    path("challenge/<int:challenge_id>/clear-entries/", admin_views.challenge_clear_entries, name="challenge_clear_entries"),

    # Shop
    path("shop/", admin_views.shop_items_list, name="shop_items_list"),
    path("shop/create/", admin_views.shop_item_create, name="shop_item_create"),
    path("shop/<int:item_id>/toggle/", admin_views.shop_item_toggle, name="shop_item_toggle"),
    path("shop/<int:item_id>/delete/", admin_views.shop_item_delete, name="shop_item_delete"),

    # Support
    path("support/", admin_views.support_list, name="support_list"),
    path("support/<int:ticket_id>/", admin_views.support_detail, name="support_detail"),

    # Guest log
    path("guest-log/", admin_views.guest_log_list, name="guest_log_list"),
    path("guest-log/clear/", admin_views.guest_log_clear, name="guest_log_clear"),

    # Send to all
    path("send-to-all/", admin_views.send_to_all, name="send_to_all"),

    # APIs
    path("api/live-games/", admin_views.api_live_games, name="api_live_games"),
    path("api/support-tickets/", admin_views.api_support_tickets, name="api_support_tickets"),
    path("api/users/", admin_views.api_users, name="api_users"),
]
