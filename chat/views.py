from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatSession
from .serializers import ChatSessionSerializer, ChatMessageSerializer, TaskScoreSerializer
from .services.session_service import StudySessionService, SessionServiceError


class SessionAccessMixin:
    @staticmethod
    def _get_session_for_user(session_id: int, user):
        try:
            session = ChatSession.objects.get(id=session_id, is_active=True)
        except ChatSession.DoesNotExist:
            return None

        if session.user1_id != user.id:
            return None

        return session


class StartSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = StudySessionService.start_session(user=request.user)
        return Response(ChatSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class SessionMessagesView(APIView, SessionAccessMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = self._get_session_for_user(session_id, request.user)
        if not session:
            return Response({"error": "Session not found"}, status=404)

        data = ChatMessageSerializer(session.messages.all(), many=True).data
        return Response(data, status=200)

    def post(self, request, session_id):
        session = self._get_session_for_user(session_id, request.user)
        if not session:
            return Response({"error": "Session not found"}, status=404)

        content = request.data.get("content")
        try:
            result = StudySessionService.handle_message(
                session=session,
                user=request.user,
                content=content,
            )
        except SessionServiceError as exc:
            return Response({"error": str(exc)}, status=400)

        return Response(
            {
                "user_message": ChatMessageSerializer(result["user_message"]).data,
                "assistant_message": ChatMessageSerializer(result["assistant_message"]).data,
                "response": result["payload"],
            },
            status=201,
        )


class SessionProgressView(APIView, SessionAccessMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = self._get_session_for_user(session_id, request.user)
        if not session:
            return Response({"error": "Session not found"}, status=404)

        scores = session.scores.all()
        avg = round(sum(s.score for s in scores) / scores.count(), 2) if scores.exists() else 0.0

        return Response(
            {
                "session": ChatSessionSerializer(session).data,
                "scores": TaskScoreSerializer(scores, many=True).data,
                "stats": {
                    "total_tasks_attempted": scores.count(),
                    "average_score": avg,
                    "last_topic": session.current_topic,
                },
            },
            status=200,
        )


class SessionStateView(APIView, SessionAccessMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = self._get_session_for_user(session_id, request.user)
        if not session:
            return Response({"error": "Session not found"}, status=404)

        scores = list(session.scores.values_list("score", flat=True))
        avg = round(sum(scores) / len(scores), 2) if scores else 0.0

        return Response(
            {
                "command_state": {
                    "topic": {
                        "title": session.current_topic,
                        "explanation": "",
                    }
                    if session.current_topic
                    else None,
                    "task": {
                        "question": session.current_task,
                        "topic": session.current_topic,
                    }
                    if session.current_task
                    else None,
                    "score_history": scores,
                    "answers_count": len(scores),
                    "tasks_count": len(scores),
                    "average_score": avg,
                }
            },
            status=200,
        )
