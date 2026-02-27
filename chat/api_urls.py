from django.urls import path

from .api_views import StartSessionAPI, SessionDetailAPI, SessionMessageAPI

urlpatterns = [
    path("sessions/start", StartSessionAPI.as_view()),
    path("sessions/<int:session_id>", SessionDetailAPI.as_view()),
    path("sessions/<int:session_id>/message", SessionMessageAPI.as_view()),
]
