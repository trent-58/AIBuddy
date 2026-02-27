from django.urls import path

from .api_views import StartSessionAPI, SessionDetailAPI, SessionMessageAPI
from .compat_views import (
    CreateChatSessionCompatView,
    ChatMessagesCompatView,
    SendMessageCompatView,
    SessionStateCompatView,
)

urlpatterns = [
    # Required API
    path("sessions/start", StartSessionAPI.as_view()),
    path("sessions/<int:session_id>", SessionDetailAPI.as_view()),
    path("sessions/<int:session_id>/message", SessionMessageAPI.as_view()),

    # Compatibility routes
    path("sessions/start/", StartSessionAPI.as_view()),
    path("sessions/<int:session_id>/", SessionDetailAPI.as_view()),
    path("sessions/<int:session_id>/message/", SessionMessageAPI.as_view()),
    path("sessions/", CreateChatSessionCompatView.as_view()),
    path("sessions/<int:chat_id>/messages/", ChatMessagesCompatView.as_view()),
    path("sessions/<int:chat_id>/send/", SendMessageCompatView.as_view()),
    path("sessions/<int:chat_id>/state/", SessionStateCompatView.as_view()),
]
