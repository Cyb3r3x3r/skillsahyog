import os

# Ensure the environment variable is set before importing anything from Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skillsahyog.settings")

import django
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from home.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Handles normal HTTP requests
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)  # Handles WebSockets
    ),
})
