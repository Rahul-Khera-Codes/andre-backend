"""
ASGI config for andre project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""



import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from microsoft.websocket_urls import websocket_urlpatterns
from microsoft.authentication import CustomJWTMiddleware


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'andre.settings')

django_asgi_application = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_application,
    "websocket": AllowedHostsOriginValidator(
        CustomJWTMiddleware(URLRouter(websocket_urlpatterns))
    )
})