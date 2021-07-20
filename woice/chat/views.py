from django.contrib.postgres.search import TrigramSimilarity
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import (
    ChatRoom,
    ChatRoomMember,
    ChatRoomMessage,
    InviteLink,
    RoomType,
)
from .permissions import AdminPermission, ChatRoomPermission
from .serializers import (
    ChatRoomCreateSerializer,
    ChatRoomMemberSerializer,
    ChatRoomMessageSerializer,
    ChatRoomSerializer,
    MakeAdminSerializer,
    PrivateChatRoomInviteSerializer,
)
from .signals import invites


def room(request, pk):
    return render(request, "chat/chatroom.html", {"pk": pk})


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


class MemberSearchView(ListAPIView):
    serializer_class = ChatRoomMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        q = self.request.query_params.get("q")

        if q:
            try:
                chatroom = ChatRoom.objects.get(pk=self.kwargs["pk"])
            except ObjectDoesNotExist:
                return Response(
                    {
                        "status": "error",
                        "message": "Chatroom doesn't exist",
                    }
                )

            queryset = ChatRoomMember.objects.annotate(
                similarity=TrigramSimilarity("user__username", q)
            ).filter(chatroom=chatroom, similarity__gt=0.3)
        else:
            queryset = ChatRoomMember.objects.none()
        return queryset


class MessageListView(ListAPIView):
    serializer_class = ChatRoomMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            chatroom = ChatRoom.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "Chatroom doesn't exist",
                }
            )

        queryset = ChatRoomMessage.objects.filter(chatroom=chatroom)
        return queryset.order_by("-created")
