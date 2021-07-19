from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from jwt import decode as jwt_decode
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken


class JWTAuthMiddleware:
    """
    Custom JWT authentication middleware
    """

    def __init__(self, application):
        self.application = application

    async def __call__(self, scope, receive, send):
        close_old_connections()
        token = parse_qs(scope["query_string"].decode("utf8"))["token"][0]
        try:
            UntypedToken(token)
        except (InvalidToken, TokenError) as e:
            return None
        else:
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            scope["user"] = await self.get_user(decoded_data)
        return await self.application(scope, receive, send)

    @database_sync_to_async
    def get_user(self, data):
        try:
            user = get_user_model().objects.get(id=data["user_id"])
        except ObjectDoesNotExist:
            user = AnonymousUser()
        return user
