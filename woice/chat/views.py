from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


from .models import ChatRoom, ChatRoomMember, InviteLink, RoomType
from .permissions import AdminPermission, ChatRoomPermission
from .serializers import (
    ChatRoomCreateSerializer,
    ChatRoomSerializer,
    MakeAdminSerializer,
    PrivateChatRoomInviteSerializer,
)
from .signals import invites


class ChatRoomViewSet(ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [ChatRoomPermission]
    serializer_action_classes = {
        "create": ChatRoomCreateSerializer,
        "invite": PrivateChatRoomInviteSerializer,
        "make_admin": MakeAdminSerializer,
    }
    permission_action_classes = {
        "invite": [AdminPermission],
        "make_admin": [AdminPermission],
        "join": [IsAuthenticated],
    }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "status": "success",
                "message": "Room created successfully",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=True, methods=["post"])
    def join(self, request, *args, **kwargs):
        try:
            chatroom = ChatRoom.objects.get(pk=kwargs["pk"])
        except ObjectDoesNotExist:
            return Response(
                {"status": "error", "message": "Chatroom doesn't exist!"},
                status=status.HTTP_404_NOT_FOUND,
            )

        member = ChatRoomMember.objects.filter(
            chatroom=chatroom, user=request.user
        )
        if member.exists():
            return Response(
                {"status": "success", "message": "You are already a member!"},
                status=status.HTTP_200_OK,
            )
        else:
            if chatroom.type == RoomType.PRIVATE:
                invite_link = InviteLink.objects.filter(
                    chatroom=chatroom, email=request.user.email
                )
                if invite_link.exists():
                    invite_link = invite_link.first()
                    invite_link.has_expired = True
                    invite_link.save(update_fields=["has_expired"])
                else:
                    return Response(
                        {
                            "status": "error",
                            "message": "Invalid invite link!",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

            _ = ChatRoomMember.objects.create(
                chatroom=chatroom, user=request.user
            )

            return Response(
                {
                    "status": "success",
                    "message": f"{request.user.username} joined successfully",
                },
                status=status.HTTP_200_OK,
            )

    @action(detail=True, methods=["post"])
    def invite(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipients = serializer.validated_data.get("recipients")
        try:
            chatroom = ChatRoom.objects.get(pk=kwargs["pk"])
        except ObjectDoesNotExist:
            return Response(
                {"status": "error", "message": "Chatroom doesn't exist!"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if chatroom.type != RoomType.PRIVATE:
            return Response(
                {
                    "status": "error",
                    "message": "Invites are for private rooms only!",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        emails_to_invite = []
        for recipient in set(recipients):
            invite_link = InviteLink.objects.filter(
                chatroom=chatroom, email__iexact=recipient, has_expired=False
            )
            if not invite_link.exists():
                emails_to_invite.append(recipient)

        if emails_to_invite:
            invites.send(
                sender=__class__,
                request=request,
                chatroom=chatroom,
                recipients=recipients,
            )
            state = "success"
            message = "Invite(s) sent successfully"
            status_code = status.HTTP_200_OK
        else:
            state = "error"
            message = (
                "Either emails either aren't valid or there's a pending invite!"
            )
            status_code = status.HTTP_400_BAD_REQUEST

        return Response(
            {
                "status": state,
                "message": message,
            },
            status=status_code,
        )

    @action(detail=True, methods=["post"])
    def make_admin(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data.get("user_id")
        make_admin = serializer.validated_data.get("make_admin")

        if request.user.id == user_id:
            return Response(
                {
                    "status": "error",
                    "message": "You can't grant or revoke your own admin rights!",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            chatroom = ChatRoom.objects.get(pk=kwargs["pk"])
        except ObjectDoesNotExist:
            return Response(
                {"status": "error", "message": "Chatroom doesn't exist!"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            member = ChatRoomMember.objects.get(
                chatroom=chatroom, user__id=user_id
            )
        except ObjectDoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "This user doesn't belong in this room!",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if make_admin:
            if member.is_admin:
                return Response(
                    {
                        "status": "success",
                        "message": "Member is already an admin",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                member.is_admin = True
                member.save(update_fields=["is_admin"])
                return Response(
                    {
                        "status": "success",
                        "message": "Admin rights granted successfully",
                    },
                    status=status.HTTP_200_OK,
                )
        else:
            if member.is_admin:
                member.is_admin = False
                member.save(update_fields=["is_admin"])
                return Response(
                    {
                        "status": "success",
                        "message": "Admin rights revoked successfully",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "status": "success",
                        "message": "Member is already not an admin",
                    },
                    status=status.HTTP_200_OK,
                )

    def get_permissions(self):
        try:
            return [
                permission()
                for permission in self.permission_action_classes[self.action]
            ]
        except:
            return [permission() for permission in self.permission_classes]

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super().get_serializer_class()

    def get_queryset(self):
        queryset = ChatRoom.objects.exclude(type=RoomType.PRIVATE)
        return queryset
