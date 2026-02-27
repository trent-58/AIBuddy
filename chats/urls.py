from django.urls import path

from .views import ChatDetailView, ChatListView, ChatMessageView, ChatSelectView


urlpatterns = [
    path("select/", ChatSelectView.as_view()),
    path("", ChatListView.as_view()),
    path("<int:chat_id>/", ChatDetailView.as_view()),
    path("<int:chat_id>/messages/", ChatMessageView.as_view()),
]
