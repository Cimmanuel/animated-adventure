from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ChatRoomViewSet

router = DefaultRouter()
router.register("room", ChatRoomViewSet, "chatroom")

urlpatterns = [] + router.urls
