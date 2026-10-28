from django.urls import path
from . import views

app_name = "alliance"

urlpatterns = [
    path("", views.alliance_home, name="home"),
    path("create/", views.create_alliance, name="create"),
    path("join/", views.join_by_code, name="join"),
    path("join-id/<int:alliance_id>/", views.join_alliance, name="join_alliance"),
    path("<int:alliance_id>/", views.alliance_detail, name="detail"),
    path("<int:alliance_id>/edit/", views.alliance_edit, name="edit"),
    path("<int:alliance_id>/chat/", views.alliance_chat, name="chat"),
    path("<int:alliance_id>/leave/", views.leave_alliance, name="leave"),
    path("<int:alliance_id>/kick/<int:user_id>/", views.kick_member, name="kick"),

    path("<int:alliance_id>/member/<int:user_id>/promote/", views.member_promote, name="member_promote"),
    path("<int:alliance_id>/member/<int:user_id>/demote/", views.member_demote, name="member_demote"),
    path("<int:alliance_id>/member/<int:user_id>/nickname/", views.member_set_nickname, name="member_set_nickname"),
    path("<int:alliance_id>/transfer/<int:user_id>/", views.transfer_leadership, name="transfer_leadership"),
    path("<int:alliance_id>/delete/", views.alliance_delete, name="alliance_delete"),

    # Game invites
    path("<int:alliance_id>/game-invite/create/", views.game_invite_create, name="game_invite_create"),
    path("game-invite/<int:invite_id>/interested/", views.game_invite_interested, name="game_invite_interested"),
    path("game-invite/<int:invite_id>/kick/", views.game_invite_kick, name="game_invite_kick"),
    path("game-invite/<int:invite_id>/start/", views.game_invite_start, name="game_invite_start"),
]