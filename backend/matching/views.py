from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from chats.models import Chat
from user.models import Interest

from .models import ChatInvite
from .serializers import (
    InviteCreateSerializer,
    InviteSerializer,
    MatchCandidateSerializer,
    MatchResponseSerializer,
)


User = get_user_model()


class FindMatchView(GenericAPIView):
    serializer_class = MatchResponseSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Find Best Match",
        description="Returns one best matching user by shared interests, otherwise solo fallback.",
        responses={200: MatchResponseSerializer},
    )
    def get(self, request):
        current_user = request.user
        my_interest_ids = list(
            Interest.objects.filter(user=current_user).values_list("name_id", flat=True)
        )

        if not my_interest_ids:
            payload = {
                "is_solo": True,
                "matched_user_id": None,
                "username": None,
                "interests": [],
                "detail": "No interests selected. You can start solo chat with AI.",
            }
            return Response(self.get_serializer(payload).data, status=200)

        queryset = User.objects.exclude(id=current_user.id)
        matched_user = (
            queryset.annotate(
                shared_interests=Count(
                    "interest",
                    filter=Q(interest__name_id__in=my_interest_ids),
                    distinct=True,
                )
            )
            .filter(shared_interests__gt=0)
            .order_by("-shared_interests", "id")
            .first()
        )

        if matched_user:
            matched_interests = list(
                Interest.objects.filter(user=matched_user)
                .select_related("name")
                .values_list("name__name", flat=True)
            )
            payload = {
                "is_solo": False,
                "matched_user_id": matched_user.id,
                "username": matched_user.username,
                "interests": matched_interests,
            }
            return Response(self.get_serializer(payload).data, status=200)

        payload = {
            "is_solo": True,
            "matched_user_id": None,
            "username": None,
            "interests": [],
            "detail": "No matching partner found. You can start solo chat with AI.",
        }
        return Response(self.get_serializer(payload).data, status=200)


class MatchCandidatesView(GenericAPIView):
    serializer_class = MatchCandidateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Match Candidates",
        description="List similar-interest users who do not already have a direct chat with current user.",
        responses={200: MatchCandidateSerializer(many=True)},
    )
    def get(self, request):
        user = request.user
        my_interest_ids = list(Interest.objects.filter(user=user).values_list("name_id", flat=True))
        if not my_interest_ids:
            return Response([], status=status.HTTP_200_OK)

        chat_pairs = Chat.objects.filter(kind=Chat.KIND_DIRECT).filter(Q(user_a=user) | Q(user_b=user)).values_list(
            "user_a_id", "user_b_id"
        )
        existing_peer_ids = set()
        for a_id, b_id in chat_pairs:
            peer_id = b_id if a_id == user.id else a_id
            existing_peer_ids.add(peer_id)

        candidates_qs = (
            User.objects.exclude(id=user.id)
            .exclude(id__in=existing_peer_ids)
            .annotate(
                shared_interests=Count(
                    "interest",
                    filter=Q(interest__name_id__in=my_interest_ids),
                    distinct=True,
                )
            )
            .filter(shared_interests__gt=0)
            .order_by("-shared_interests", "id")
        )

        rows = []
        for candidate in candidates_qs:
            candidate_interests = list(
                Interest.objects.filter(user=candidate)
                .select_related("name")
                .values_list("name__name", flat=True)
            )
            rows.append(
                {
                    "user_id": candidate.id,
                    "username": candidate.username,
                    "shared_interests": candidate.shared_interests,
                    "interests": candidate_interests,
                }
            )

        return Response(self.get_serializer(rows, many=True).data, status=status.HTTP_200_OK)


class InviteCreateView(GenericAPIView):
    serializer_class = InviteCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Send Invite",
        description="Send a direct chat invite to another user.",
        request=InviteCreateSerializer,
        responses={201: InviteSerializer},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from_user = request.user
        to_user_id = serializer.validated_data["to_user_id"]

        if to_user_id == from_user.id:
            return Response({"detail": "Cannot invite yourself"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        pair_key = Chat.build_pair_key(kind=Chat.KIND_DIRECT, user_a_id=from_user.id, user_b_id=to_user.id)
        if Chat.objects.filter(kind=Chat.KIND_DIRECT, pair_key=pair_key).exists():
            return Response({"detail": "Chat already exists with this user"}, status=status.HTTP_400_BAD_REQUEST)

        pending_exists = ChatInvite.objects.filter(
            Q(from_user=from_user, to_user=to_user, status="pending")
            | Q(from_user=to_user, to_user=from_user, status="pending")
        ).exists()
        if pending_exists:
            return Response({"detail": "Pending invite already exists"}, status=status.HTTP_400_BAD_REQUEST)

        invite = ChatInvite.objects.create(from_user=from_user, to_user=to_user, status="pending")
        return Response(InviteSerializer(invite).data, status=status.HTTP_201_CREATED)


class IncomingInviteListView(GenericAPIView):
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Incoming Invites",
        description="List pending invites received by current user.",
        responses={200: InviteSerializer(many=True)},
    )
    def get(self, request):
        invites = ChatInvite.objects.filter(to_user=request.user, status="pending").order_by("-created_at")
        return Response(self.get_serializer(invites, many=True).data, status=status.HTTP_200_OK)


class OutgoingInviteListView(GenericAPIView):
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Outgoing Invites",
        description="List pending invites sent by current user.",
        responses={200: InviteSerializer(many=True)},
    )
    def get(self, request):
        invites = ChatInvite.objects.filter(from_user=request.user, status="pending").order_by("-created_at")
        return Response(self.get_serializer(invites, many=True).data, status=status.HTTP_200_OK)


class InviteAcceptView(GenericAPIView):
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Accept Invite",
        description="Accept invite and create/get direct chat with inviter.",
        responses={200: OpenApiTypes.OBJECT},
    )
    @transaction.atomic
    def post(self, request, invite_id):
        try:
            invite = ChatInvite.objects.select_for_update().get(id=invite_id, to_user=request.user)
        except ChatInvite.DoesNotExist:
            return Response({"detail": "Invite not found"}, status=status.HTTP_404_NOT_FOUND)

        if invite.status != "pending":
            return Response({"detail": "Invite already processed"}, status=status.HTTP_400_BAD_REQUEST)

        invite.status = "accepted"
        invite.save(update_fields=["status"])

        pair_key = Chat.build_pair_key(
            kind=Chat.KIND_DIRECT,
            user_a_id=invite.from_user_id,
            user_b_id=invite.to_user_id,
        )
        chat = Chat.objects.filter(kind=Chat.KIND_DIRECT, pair_key=pair_key).first()
        if chat is None:
            low, high = sorted([invite.from_user, invite.to_user], key=lambda x: x.id)
            chat = Chat.objects.create(kind=Chat.KIND_DIRECT, user_a=low, user_b=high)

        return Response(
            {
                "detail": "Invite accepted",
                "invite": InviteSerializer(invite).data,
                "chat_id": chat.id,
            },
            status=status.HTTP_200_OK,
        )


class InviteRejectView(GenericAPIView):
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Reject Invite",
        description="Reject an incoming invite.",
        responses={200: OpenApiTypes.OBJECT},
    )
    @transaction.atomic
    def post(self, request, invite_id):
        try:
            invite = ChatInvite.objects.select_for_update().get(id=invite_id, to_user=request.user)
        except ChatInvite.DoesNotExist:
            return Response({"detail": "Invite not found"}, status=status.HTTP_404_NOT_FOUND)

        if invite.status != "pending":
            return Response({"detail": "Invite already processed"}, status=status.HTTP_400_BAD_REQUEST)

        invite.status = "rejected"
        invite.save(update_fields=["status"])

        return Response(
            {
                "detail": "Invite rejected",
                "invite": InviteSerializer(invite).data,
            },
            status=status.HTTP_200_OK,
        )
