from django.urls import path

from .views import FindMatchView

urlpatterns = [
    path("find/", FindMatchView.as_view()),

    # Backward-compatible old route
    path("match/", FindMatchView.as_view()),
]
