import uuid

from django.conf import settings
from django.db import models


class RoomType(models.TextChoices):
    PUBLIC = "public", "Public"
    PRIVATE = "private", "Private"


class ChatRoom(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, unique=True, editable=False
    )
    name = models.CharField(max_length=100)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="chatroom",
    )
    type = models.CharField(
        max_length=10, choices=RoomType.choices, default=RoomType.PUBLIC
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "creator"], name="unique_name_and_creator"
            )
        ]
        verbose_name = "Chatroom"
        verbose_name_plural = "Chatrooms"

    def __str__(self):
        return f"{self.creator.username}'s {self.name} room"


class ChatRoomMember(models.Model):
    chatroom = models.ForeignKey(
        ChatRoom,
        on_delete=models.PROTECT,
        related_name="chatroom_member",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    is_admin = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Chatroom member"
        verbose_name_plural = "Chatroom members"

    def __str__(self):
        return f"{self.chatroom} members"
