from django.urls import path

from .views import FindMatchView

urlpatterns = [
    path("match/", FindMatchView.as_view()),
]
