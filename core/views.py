from django.shortcuts import redirect
from django.views.generic import TemplateView


class LoginRequiredPageMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.COOKIES.get("access_token"):
            return redirect("/login/")
        return super().dispatch(request, *args, **kwargs)


class AnonymousOnlyPageMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.COOKIES.get("access_token"):
            return redirect("/")
        return super().dispatch(request, *args, **kwargs)


class LoginPageView(AnonymousOnlyPageMixin, TemplateView):
    template_name = "pages/login.html"


class SignupPageView(AnonymousOnlyPageMixin, TemplateView):
    template_name = "pages/signup.html"


class MatchPageView(LoginRequiredPageMixin, TemplateView):
    template_name = "pages/match.html"


class ChatPageView(LoginRequiredPageMixin, TemplateView):
    template_name = "pages/chat.html"


class EvaluationPageView(LoginRequiredPageMixin, TemplateView):
    template_name = "pages/evaluation.html"
