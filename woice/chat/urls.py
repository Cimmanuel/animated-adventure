from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ChatRoomViewSet, MemberSearchView, MessageListView, room

router = DefaultRouter()
router.register("room", ChatRoomViewSet, "chatroom")

urlpatterns = [
    path("chatroom/<str:pk>/", room, name="room"),
    path(
        "room/<str:pk>/search/",
        MemberSearchView.as_view(),
        name="member-search",
    ),
    path(
        "room/<str:pk>/messages/",
        MessageListView.as_view(),
        name="messages",
    ),
] + router.urls
