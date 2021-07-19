import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from .models import (
    ChatRoom,
    ChatRoomMember,
    ChatRoomMessage,
    InviteLink,
    RoomType,
)


class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["pk"]
        self.room_group_name = self.room_id

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )

        if self.user.is_authenticated:
            await self.accept()
            try:
                invite = await self.verify_invite(self.room_id, self.user)
                await self.expire_invite(invite)
            except ObjectDoesNotExist:
                await self.send(
                    text_data=json.dumps(
                        {"message": "Invite is either invalid or expired!"}
                    )
                )
                await self.close(code=4001)
            else:
                try:
                    await self.add_member(self.room_id, self.user)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "join",
                            "message": f"{self.user.username} joined",
                        },
                    )
                except IntegrityError:
                    await self.send(
                        text_data=json.dumps({"message": "Welcome back!"})
                    )
        else:
            await self.accept()
            await self.send(
                text_data=json.dumps({"message": "You must login to continue!"})
            )
            await self.close(code=4001)

    async def join(self, event):
        await self.send(text_data=json.dumps({"message": event["message"]}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):
        json_text_data = json.loads(text_data)
        message = json_text_data["message"]
        username = json_text_data["username"]

        await self.store_message(self.room_id, self.user, message)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chatroom_message",
                "message": message,
                "username": username,
            },
        )

    async def chatroom_message(self, event):
        await self.send(
            text_data=json.dumps(
                {"message": event["message"], "username": event["username"]}
            )
        )

    @database_sync_to_async
    def add_member(self, room_id, user):
        chatroom = ChatRoom.objects.get(pk=room_id)
        return ChatRoomMember.objects.create(chatroom=chatroom, user=user)

    @database_sync_to_async
    def verify_invite(self, room_id, user):
        chatroom = ChatRoom.objects.get(pk=room_id)
        if chatroom.type == RoomType.PRIVATE:
            return InviteLink.objects.get(
                chatroom=chatroom, email=user.email, has_expired=False
            )

    @database_sync_to_async
    def expire_invite(self, invite):
        invite.has_expired = True
        invite.save(update_fields=["has_expired"])
        return None

    @database_sync_to_async
    def store_message(self, room_id, user, message):
        chatroom = ChatRoom.objects.get(pk=room_id)
        return ChatRoomMessage.objects.create(
            chatroom=chatroom, user=user, message=message
        )
