from django.urls import path
from . import views

urlpatterns = [
    path("create_chat_room/", views.CreateChatRoom.as_view(), name="create_chat-room"),
]