from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from templated_email import send_templated_mail

from .models import ChatRoom, ChatRoomMember, RoomType
from .permissions import ChatRoomPermission
from .serializers import (
    ChatRoomCreateSerializer,
    ChatRoomSerializer,
    MakeAdminSerializer,
    PrivateChatRoomInviteSerializer,
)


class ChatRoomViewSet(ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [ChatRoomPermission]
    serializer_action_classes = {
        "create": ChatRoomCreateSerializer,
        "invite": PrivateChatRoomInviteSerializer,
        "make_admin": MakeAdminSerializer,
    }
    permission_action_classes = {}

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
    def invite(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipients = serializer.validated_data.get("recipients")
        try:
            chatroom = ChatRoom.objects.get(
                pk=kwargs["pk"], creator=request.user, type=RoomType.PRIVATE
            )
        except ObjectDoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "You need creator access to invite into this room!",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        _ = send_templated_mail(
            template_name="chat/emails/invite",
            from_email="80cba9e67b-bb52d2@inbox.mailtrap.io",
            recipient_list=recipients,
            context={
                "id": chatroom.id,
                "creator": chatroom.creator,
            },
        )

        return Response(
            {
                "status": "error",
                "message": "Invites sent successfully",
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def make_admin(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data.get("user_id")
        make_admin = serializer.validated_data.get("make_admin")
        chatroom_id = serializer.validated_data.get("chatroom_id")

        try:
            chatroom = ChatRoom.objects.get(pk=chatroom_id)
        except ObjectDoesNotExist:
            return Response(
                {"status": "error", "message": "Chatroom doesn't exist!"},
                status=status.HTTP_404_BAD_REQUEST,
            )

        # Room creator is automatically an admin (see signals). Only run this
        # check if authenticated user is not the room creator.
        if request.user != chatroom.creator:
            try:
                other_admin = ChatRoomMember.objects.get(
                    chatroom=chatroom, user=request.user
                )
            except ObjectDoesNotExist:
                return Response(
                    {
                        "status": "error",
                        "message": "You are not a member of this room!",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            if not other_admin.is_admin:
                return Response(
                    {
                        "status": "error",
                        "message": "You have to be admin to make other users admin!",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
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
        queryset = ChatRoom.objects.filter(creator=self.request.user)
        return queryset
