from django.urls import path

from . import views

app_name = "game"

urlpatterns = [
    path("", views.home, name="home"),
    path("rooms/", views.rooms_list, name="rooms"),
    path("friends/", views.friends_page, name="friends"),
    path("quick/", views.quick_play, name="quick_play"),
    path("quick/bot/", views.bot_setup, name="bot_setup"),
    path("quick/bot/play/<uuid:game_id>/", views.bot_play, name="bot_play"),
    path("quick/bot/submit/<uuid:game_id>/", views.bot_submit, name="bot_submit"),
    path("create/", views.create_room, name="create"),
    path("join/", views.join_room, name="join"),
    path("room/<str:room_code>/", views.room, name="room"),
]
