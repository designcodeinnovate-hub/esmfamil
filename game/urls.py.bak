from django.urls import path
from . import views

app_name = "game"

urlpatterns = [
    path("", views.home, name="home"),
    path("rooms/", views.rooms_list, name="rooms"),
    path("rooms/manage/", views.rooms_manage, name="rooms_manage"),
    path("rooms/join/<str:room_code>/", views.join_room, name="join_room"),
    path("room/<str:room_code>/", views.room, name="room"),
    path("friends/", views.friends_page, name="friends"),
    path("leaderboard/", views.leaderboard_view, name="leaderboard"),
    path("top-players/", views.top_players_view, name="top_players"),
    path("quick/", views.quick_play, name="quick_play"),
    path("quick/bot/", views.bot_setup, name="bot_setup"),
    path("quick/bot/play/<uuid:game_id>/", views.bot_play, name="bot_play"),
    path("quick/bot/submit/<uuid:game_id>/", views.bot_submit, name="bot_submit"),
    path("match/", views.match_start, name="match_start"),
    path("match/wait/", views.match_wait, name="match_wait"),
    path("match/cancel/", views.match_cancel, name="match_cancel"),
    path("match/status/", views.match_status, name="match_status"),
]
