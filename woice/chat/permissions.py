from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import BasePermission

from .models import ChatRoom, ChatRoomMember


class ChatRoomPermission(BasePermission):
    """
    Permission check to see if user has access to certain actions
    """

    message = "Unsactioned operation!"

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if view.action == "update":
                return False
            else:
                return True
        return False


class AdminPermission(BasePermission):
    message = "Admin access only!"

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            print(request.user.username)
            try:
                chatroom = ChatRoom.objects.get(pk=request.data["chatroom_id"])
            except ObjectDoesNotExist:
                return False

            # Room creator is automatically an admin (see signals).
            # Only run this check if authenticated user is not the
            # room creator.
            if request.user != chatroom.creator:
                try:
                    other_admin = ChatRoomMember.objects.get(
                        chatroom=chatroom, user=request.user
                    )
                except ObjectDoesNotExist:
                    return False

                if not other_admin.is_admin:
                    return False
                else:
                    return True
            else:
                return True
        return False
