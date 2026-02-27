from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user.models import User


class FindMatchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        current_user = request.user
        my_interests = current_user.interests or []

        queryset = User.objects.exclude(id=current_user.id)
        matched_user = queryset.filter(interests__overlap=my_interests).first()

        if matched_user:
            return Response(
                {
                    "is_solo": False,
                    "matched_user_id": matched_user.id,
                    "username": matched_user.username,
                    "interests": matched_user.interests,
                },
                status=200,
            )

        return Response(
            {
                "is_solo": True,
                "matched_user_id": None,
                "username": None,
                "interests": [],
                "detail": "No matching partner found. You can start solo chat with AI.",
            },
            status=200,
        )
