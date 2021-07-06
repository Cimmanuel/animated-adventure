from rest_framework.permissions import BasePermission


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
