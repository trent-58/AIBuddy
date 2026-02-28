from django.urls import path

from .views import (
    FindMatchView,
    IncomingInviteListView,
    InviteAcceptView,
    InviteCreateView,
    InviteRejectView,
    MatchCandidatesView,
    OutgoingInviteListView,
)

urlpatterns = [
    path("candidates/", MatchCandidatesView.as_view()),
    path("match/", FindMatchView.as_view()),
    path("invites/", InviteCreateView.as_view()),
    path("invites/incoming/", IncomingInviteListView.as_view()),
    path("invites/outgoing/", OutgoingInviteListView.as_view()),
    path("invites/<int:invite_id>/accept/", InviteAcceptView.as_view()),
    path("invites/<int:invite_id>/reject/", InviteRejectView.as_view()),
]
