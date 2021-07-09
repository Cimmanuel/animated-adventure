from django.core.signals import request_started
from django.db import IntegrityError
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver
from django.utils import timezone
from templated_email import send_templated_mail

from .models import ChatRoom, ChatRoomMember, InviteLink

invites = Signal()


@receiver(post_save, sender=ChatRoom)
def add_creator_to_members(sender, instance, created, **kwargs):
    if created:
        _ = ChatRoomMember.objects.create(
            chatroom=instance, user=instance.creator, is_admin=True
        )

    return None


@receiver(invites)
def send_invite_and_create_record(request, chatroom, recipients, **kwargs):
    _ = send_templated_mail(
        template_name="chat/emails/invite",
        from_email="80cba9e67b-bb52d2@inbox.mailtrap.io",
        recipient_list=recipients,
        context={
            "id": chatroom.id,
            "host": request.get_host(),
            "scheme": request.scheme,
            "creator": chatroom.creator,
        },
    )

    for recipient in recipients:
        try:
            _ = InviteLink.objects.create(chatroom=chatroom, email=recipient)
        except IntegrityError:
            pass

    return None


@receiver(request_started)
def delete_expired_invite(sender, **kwargs):
    _ = InviteLink.objects.filter(
        Q(expires__lt=timezone.now()) | Q(has_expired=True)
    ).delete()

    return None
