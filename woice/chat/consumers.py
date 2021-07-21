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
                self.chatroom = await self.get_chatroom(self.room_id)
            except ObjectDoesNotExist:
                await self.send(
                    text_data=json.dumps({"message": "Chatroom doesn't exist!"})
                )
                await self.close()

            if self.chatroom.type == RoomType.PRIVATE:
                invite = await self.verify_invite(self.chatroom, self.user)
                if invite:
                    invite = await self.get_invite(self.chatroom, self.user)
                    await self.expire_invite(invite)
                else:
                    membership = await self.verify_membership(
                        self.chatroom, self.user
                    )
                    if not membership:
                        await self.send(
                            text_data=json.dumps(
                                {
                                    "message": "You need an invite to join this group!"
                                }
                            )
                        )
                        await self.close(code=4001)

            try:
                await self.add_member(self.chatroom, self.user)
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
        data = json.loads(text_data)
        type = data.get("type")
        message = data.get("message")
        username = data.get("username")
        message_id = data.get("message_id")

        if type == "NEW_MESSAGE":
            new_message = await self.store_message(self.chatroom, self.user, message)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "new_message",
                    "message": message,
                    "username": username,
                    "message_id": new_message.id,
                },
            )
        elif type == "EDIT_MESSAGE":
            if message_id:
                try:
                    edited = await self.get_message(message_id)
                except ObjectDoesNotExist:
                    await self.send(
                        text_data=json.dumps({"message": "Message doesn't exist!"})
                    )
                    await self.close()

                await self.replace_message(edited, message)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "edit_message",
                        "message": message,
                        "username": username,
                        "message_id": message_id,
                    },
                )
        elif type == "DELETE_MESSAGE":
            if message_id:
                print("In DELETE_MESSAGE: ", message_id)
                try:
                    await self.delete_message(message_id)
                except ObjectDoesNotExist:
                    await self.send(
                        text_data=json.dumps({"message": "Message doesn't exist!"})
                    )
                    await self.close()

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "delete_message",
                        "message": "Message deleted",
                        "username": username,
                    },
                )
        elif type == "TYPING":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing",
                    "message": message,
                    "username": username,
                },
            )
        elif type == "NOT_TYPING":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "not_typing",
                    "message": message,
                    "username": username,
                },
            )

    async def new_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "NEW_MESSAGE",
                    "message": event["message"],
                    "username": event["username"],
                    "message_id": event["message_id"],
                }
            )
        )

    async def edit_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "EDIT_MESSAGE",
                    "message": event["message"],
                    "username": event["username"],
                    "message_id": event["message_id"],
                }
            )
        )

    async def delete_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "DELETE_MESSAGE",
                    "message": event["message"],
                    "username": event["username"],
                }
            )
        )

    async def typing(self, event):
        if self.user.username != event["username"]:
            await self.send(
                text_data=json.dumps(
                    {"type": "TYPING", "message": event["message"]}
                )
            )

    async def not_typing(self, event):
        if self.user.username != event["username"]:
            await self.send(text_data=json.dumps({"type": "NOT_TYPING"}))

    @database_sync_to_async
    def get_chatroom(self, room_id):
        return ChatRoom.objects.get(pk=room_id)

    @database_sync_to_async
    def add_member(self, chatroom, user):
        return ChatRoomMember.objects.create(chatroom=chatroom, user=user)

    @database_sync_to_async
    def get_invite(self, chatroom, user):
        return InviteLink.objects.get(chatroom=chatroom, email=user.email)

    @database_sync_to_async
    def verify_invite(self, chatroom, user):
        return InviteLink.objects.filter(
            chatroom=chatroom, email=user.email, has_expired=False
        ).exists()

    @database_sync_to_async
    def verify_membership(self, chatroom, user):
        return ChatRoomMember.objects.filter(
            chatroom=chatroom, user=user
        ).exists()

    @database_sync_to_async
    def expire_invite(self, invite):
        invite.has_expired = True
        invite.save(update_fields=["has_expired"])
        return None

    @database_sync_to_async
    def store_message(self, chatroom, user, message):
        return ChatRoomMessage.objects.create(
            chatroom=chatroom, user=user, message=message
        )

    @database_sync_to_async
    def get_message(self, message_id):
        return ChatRoomMessage.objects.get(pk=message_id)

    @database_sync_to_async
    def replace_message(self, instance, message):
        instance.message = message
        instance.edited = True
        instance.save(update_fields=["message", "edited"])
        return None

    @database_sync_to_async
    def delete_message(self, message_id):
        print("In delete message: ", message_id)
        return ChatRoomMessage.objects.get(pk=message_id).delete()
