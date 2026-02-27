from django.urls import path

from .views import (
    InterestOptionListView,
    LoginView,
    LogoutView,
    RegisterCompleteView,
    RegisterEmailView,
    RegisterSetPasswordView,
    RegisterVerifyCodeView,
)

urlpatterns = [
    path("interests", InterestOptionListView.as_view()),
    path("interests/", InterestOptionListView.as_view()),
    path("register/email", RegisterEmailView.as_view()),
    path("register/email/", RegisterEmailView.as_view()),
    path("register/verify", RegisterVerifyCodeView.as_view()),
    path("register/verify/", RegisterVerifyCodeView.as_view()),
    path("register/password", RegisterSetPasswordView.as_view()),
    path("register/password/", RegisterSetPasswordView.as_view()),
    path("register/complete", RegisterCompleteView.as_view()),
    path("register/complete/", RegisterCompleteView.as_view()),
    path("login", LoginView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout", LogoutView.as_view()),
    path("logout/", LogoutView.as_view()),
]
