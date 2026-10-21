from django.urls import path
from . import admin_views

app_name = "custom_admin"

urlpatterns = [
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
    path("user/<int:user_id>/reset-password/", admin_views.user_reset_password, name="user_reset_password"),
    path("user/<int:user_id>/change-alias/", admin_views.user_change_alias, name="user_change_alias"),

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
    path("announcement/toggle-read/", admin_views.announcement_toggle_read, name="announcement_toggle_read"),

    # Tournaments
    path("tournaments/", admin_views.tournaments_list, name="tournaments_list"),
    path("tournament/create/", admin_views.tournament_create, name="tournament_create"),
    path("tournament/<int:tournament_id>/", admin_views.tournament_edit, name="tournament_edit"),
    path("tournament/<int:tournament_id>/delete/", admin_views.tournament_delete, name="tournament_delete"),
    path("tournament/<int:tournament_id>/clear-entries/", admin_views.tournament_clear_entries, name="tournament_clear_entries"),
    path("shop/", admin_views.shop_items_list, name="shop_items_list"),
    path("support/", admin_views.support_list, name="support_list"),
    path("support/<int:ticket_id>/", admin_views.support_detail, name="support_detail"),
    path("shop/create/", admin_views.shop_item_create, name="shop_item_create"),
    path("shop/<int:item_id>/toggle/", admin_views.shop_item_toggle, name="shop_item_toggle"),
    path("shop/<int:item_id>/delete/", admin_views.shop_item_delete, name="shop_item_delete"),
    path("guest-log/", admin_views.guest_log_list, name="guest_log_list"),
    path("send-to-all/", admin_views.send_to_all, name="send_to_all"),
    path("support/", admin_views.support_tickets_list, name="support_tickets_list"),
    path("support/<int:ticket_id>/", admin_views.support_ticket_admin, name="support_ticket_admin"),
    path("guest-log/clear/", admin_views.guest_log_clear, name="guest_log_clear"),
]
