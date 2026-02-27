from django.contrib import admin
from django.urls import include, path
from user.views import RegisterView, LoginView

from .views import (
    LoginPageView,
    SignupPageView,
    MatchPageView,
    ChatPageView,
    EvaluationPageView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # API
    path("auth/register", RegisterView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("", include("chat.api_urls")),
    path("user/", include("user.urls")),
    path("matching/", include("matching.urls")),
    path("chat/", include("chat.urls")),
    path("ai/", include("AI.urls")),

    # Public auth pages
    path("login/", LoginPageView.as_view(), name="page-login"),
    path("signup/", SignupPageView.as_view(), name="page-signup"),

    # Protected pages
    path("", MatchPageView.as_view(), name="page-match"),
    path("app/chat/", ChatPageView.as_view(), name="page-chat"),
    path("app/evaluation/", EvaluationPageView.as_view(), name="page-evaluation"),
]
