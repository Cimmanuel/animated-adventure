from accounts.serializers import UserSerializer
from django.db import IntegrityError
from rest_framework.serializers import (
    BooleanField,
    EmailField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    UUIDField,
    ValidationError,
)

from .models import ChatRoom
from .utils import strip_str


class ChatRoomSerializer(ModelSerializer):
    creator = UserSerializer()

    class Meta:
        model = ChatRoom
        fields = "__all__"
        extra_kwargs = {
            "creator": {"read_only": True},
        }


class ChatRoomCreateSerializer(ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ["id", "name", "type", "created"]

    def create(self, validated_data):
        try:
            validated_data["creator"] = self.context["request"].user
            return super().create(validated_data)
        except IntegrityError:
            message = f"You already created a room with the name \
                `{validated_data['name']}`"
            raise ValidationError(
                {
                    "status": "error",
                    "message": strip_str(message, "normal"),
                }
            )


class PrivateChatRoomInviteSerializer(Serializer):
    chatroom_id = UUIDField()
    recipients = ListField(child=EmailField(), allow_empty=False)


class MakeAdminSerializer(Serializer):
    user_id = IntegerField()
    chatroom_id = UUIDField()
    make_admin = BooleanField(default=False)
