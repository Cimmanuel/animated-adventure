"""
ASGI config for woice project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

# import chat.routing
# from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "woice.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        # "websocket": AuthMiddlewareStack(
        #     URLRouter(chat.routing.ws_urlpatterns)
        # ),
    }
)
