from django.urls import path
from . import views

app_name = "support"

urlpatterns = [
    path("", views.support_home, name="home"),
    path("<int:ticket_id>/", views.ticket_detail, name="ticket"),
    path("<int:ticket_id>/close/", views.ticket_close, name="close"),
]
