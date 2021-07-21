import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def five_hours_hence():
    return timezone.now() + timezone.timedelta(hours=5)


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
        return f"{self.name} by {self.creator.username}"


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
        constraints = [
            models.UniqueConstraint(
                fields=["chatroom", "user"], name="unique_user_and_chatroom"
            )
        ]
        verbose_name = "Chatroom member"
        verbose_name_plural = "Chatroom members"

    def __str__(self):
        return f"{self.chatroom} members"


class ChatRoomMessage(models.Model):
    chatroom = models.ForeignKey(
        ChatRoom,
        on_delete=models.PROTECT,
        related_name="chatroom_message",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    message = models.TextField()
    edited = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chatroom message"
        verbose_name_plural = "Chatroom messages"

    def __str__(self):
        return f"{self.chatroom} messages"


class InviteLink(models.Model):
    chatroom = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="invite_link",
        limit_choices_to={"type": RoomType.PRIVATE},
    )
    email = models.EmailField()
    expires = models.DateTimeField(default=five_hours_hence)
    has_expired = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["chatroom", "email"], name="unique_email_and_chatroom"
            )
        ]
        verbose_name = "Invite"
        verbose_name_plural = "Invites"

    def __str__(self):
        return f"{self.email}'s invite"
