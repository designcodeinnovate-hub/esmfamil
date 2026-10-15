from django.urls import path
from . import views

app_name = "social"

urlpatterns = [
    path("", views.friends_home, name="friends_home"),
    path("search/", views.search_user, name="search_user"),
    path("add/<int:user_id>/", views.send_request, name="send_request"),
    path("accept/<int:req_id>/", views.accept_request, name="accept_request"),
    path("reject/<int:req_id>/", views.reject_request, name="reject_request"),
    path("remove/<int:user_id>/", views.remove_friend, name="remove_friend"),
    path("chat/<int:user_id>/", views.chat_view, name="chat"),
]
