from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .api_serializers import SessionSerializer, MessageSerializer
from .services.session_service import SessionService, SessionServiceError


class StartSessionAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = SessionService.start_session(request.user)
        return Response(SessionSerializer(session).data, status=201)


class SessionDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        try:
            session = SessionService.get_session_for_user(session_id=session_id, user=request.user)
        except SessionServiceError as exc:
            return Response({"detail": str(exc)}, status=404)

        messages = session.messages.order_by("-created_at")[:20]
        messages_data = MessageSerializer(list(reversed(messages)), many=True).data

        return Response(
            {
                "session": SessionSerializer(session).data,
                "messages": messages_data,
            },
            status=200,
        )


class SessionMessageAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        try:
            session = SessionService.get_session_for_user(session_id=session_id, user=request.user)
        except SessionServiceError as exc:
            return Response(
                {
                    "type": "error",
                    "data": {"message": str(exc)},
                    "session_state": {"current_topic_title": None, "has_task": False},
                },
                status=404,
            )

        message_text = request.data.get("message", "")
        try:
            result = SessionService.process_message(
                session=session,
                user=request.user,
                message_text=message_text,
            )
        except SessionServiceError as exc:
            return Response(
                {
                    "type": "error",
                    "data": {"message": str(exc)},
                    "session_state": SessionService.session_state_payload(session),
                },
                status=400,
            )

        return Response(result, status=200)
