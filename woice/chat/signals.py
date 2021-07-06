from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ChatRoom, ChatRoomMember


@receiver(post_save, sender=ChatRoom)
def add_creator_to_members(sender, instance, created, **kwargs):
    if created:
        _ = ChatRoomMember.objects.create(
            chatroom=instance, user=instance.creator, is_admin=True
        )

    return None
