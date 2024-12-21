import os

# Set DJANGO_SETTINGS_MODULE before importing Django or Channels components
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizio.settings")

# Import necessary components after settings are loaded
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

asgi_application = get_asgi_application()
from ai_quiz.consumers.routing import websocket_urlpatterns
# ASGI application # Import the consumer you will create

application = ProtocolTypeRouter(
    {
        "http": asgi_application,  # Handles regular HTTP requests
        "websocket": AuthMiddlewareStack(  # Handles WebSocket requests
            URLRouter(websocket_urlpatterns)
        ),
    }
)
