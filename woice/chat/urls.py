from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ChatRoomViewSet, room

router = DefaultRouter()
router.register("room", ChatRoomViewSet, "chatroom")

urlpatterns = [
    path("chatroom/<str:pk>/", room, name="room"),
] + router.urls
