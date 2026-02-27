from django.db.models import Count, Q
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from user.models import Interest, User
from .serializers import MatchResponseSerializer


class FindMatchView(GenericAPIView):
    serializer_class = MatchResponseSerializer
    permission_classes = [IsAuthenticated]

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
