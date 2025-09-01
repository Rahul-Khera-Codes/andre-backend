from django.urls import path

from .consumers.chat_llm import ChatLLMConsumer

websocket_urlpatterns = [
    path("chat-llm/", ChatLLMConsumer.as_asgi()),
]