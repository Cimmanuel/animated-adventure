from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from templated_email import send_templated_mail

from .models import ChatRoom, RoomType
from .permissions import ChatRoomPermission
from .serializers import (
    ChatRoomCreateSerializer,
    ChatRoomSerializer,
    PrivateChatRoomInviteSerializer,
)


class ChatRoomViewSet(ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [ChatRoomPermission]
    serializer_action_classes = {
        "create": ChatRoomCreateSerializer,
        "invite": PrivateChatRoomInviteSerializer,
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
