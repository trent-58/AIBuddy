from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Session, Message
from .services.session_service import SessionService, SessionServiceError


class CompatAccessMixin:
    @staticmethod
    def _get_session(session_id: int, user):
        try:
            return Session.objects.get(id=session_id, user=user)
        except Session.DoesNotExist:
            return None


class CreateChatSessionCompatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = SessionService.start_session(request.user)
        return Response(
            {
                "id": session.id,
                "is_solo": True,
                "topic": session.current_topic_title or "",
            },
            status=201,
        )


class ChatMessagesCompatView(APIView, CompatAccessMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        session = self._get_session(chat_id, request.user)
        if not session:
            return Response({"error": "Chat not found"}, status=404)

        data = []
        for msg in session.messages.order_by("created_at"):
            if msg.role == Message.ROLE_USER:
                sender_type = "user"
                sender_username = request.user.username
            else:
                sender_type = "ai"
                sender_username = "AI Tutor"

            data.append(
                {
                    "id": msg.id,
                    "chat": session.id,
                    "sender_type": sender_type,
                    "sender_username": sender_username,
                    "content": msg.content,
                    "created_at": msg.created_at,
                }
            )

        return Response(data, status=200)


class SendMessageCompatView(APIView, CompatAccessMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        session = self._get_session(chat_id, request.user)
        if not session:
            return Response({"error": "Chat not found"}, status=404)

        content = request.data.get("content", "")
        try:
            result = SessionService.process_message(
                session=session,
                user=request.user,
                message_text=content,
            )
        except SessionServiceError as exc:
            return Response({"error": str(exc)}, status=400)

        return Response(
            {
                "ai_triggered": result.get("type") != "error",
                "response": result,
            },
            status=201,
        )


class SessionStateCompatView(APIView, CompatAccessMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        session = self._get_session(chat_id, request.user)
        if not session:
            return Response({"error": "Chat not found"}, status=404)

        score_history = list(session.attempts.order_by("created_at").values_list("score", flat=True))

        return Response(
            {
                "command_state": {
                    "topic": {
                        "title": session.current_topic_title,
                        "explanation": session.current_topic_explanation,
                    }
                    if session.current_topic_title
                    else None,
                    "task": {
                        "question": session.current_task_text,
                        "topic": session.current_topic_title,
                    }
                    if session.current_task_text
                    else None,
                    "score_history": score_history,
                    "answers_count": len(score_history),
                    "tasks_count": len(score_history),
                }
            },
            status=200,
        )
