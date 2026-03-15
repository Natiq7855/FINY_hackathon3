from django.urls import path
from django.shortcuts import redirect
from . import views


def redirect_to_general(request, community_id):
    return redirect("chat_room", community_id=community_id, channel="general")


urlpatterns = [
    # Redirect bare /chat/<id>/ → /chat/<id>/general/
    path("<int:community_id>/", redirect_to_general, name="chat_room_root"),
    # Channel-aware routes
    path("<int:community_id>/<slug:channel>/", views.chat_room, name="chat_room"),
    path("<int:community_id>/<slug:channel>/messages/", views.messages_api, name="chat_messages_api"),
    path("<int:community_id>/<slug:channel>/send/", views.send_message, name="chat_send"),
]
