from django.contrib import admin

from .models import ChatRoom, ChatRoomMember


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "creator", "type", "created", "updated"]
    list_filter = ["creator", "type"]


@admin.register(ChatRoomMember)
class ChatRoomMemberAdmin(admin.ModelAdmin):
    list_display = ["user", "chatroom", "is_admin"]
    list_filter = ["is_admin"]
