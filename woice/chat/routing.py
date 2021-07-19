from django.urls import path
from .consumers import ChatRoomConsumer


websocket_urlpatterns = [
    path("ws/chat/<str:pk>/", ChatRoomConsumer.as_asgi()),
]
