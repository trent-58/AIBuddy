from django.urls import path
from .views import (
    AISoloChatView,
    GenerateTaskView,
    SubmitDiscussionView,
    EvaluateDiscussionView,
)

urlpatterns = [
    path("solo/", AISoloChatView.as_view()),  # #topic #task #answer
    path("chat/<int:chat_id>/task/", GenerateTaskView.as_view()),
    path("chat/<int:chat_id>/submit/", SubmitDiscussionView.as_view()),
    path("chat/<int:chat_id>/evaluate/", EvaluateDiscussionView.as_view()),
]