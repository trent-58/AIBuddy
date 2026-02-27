from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import ChatSession
from .models import AITask, Submission, AIEvaluation
from .serializers import AITaskSerializer, SubmissionSerializer, AIEvaluationSerializer
from .services import AIService


class ChatAccessMixin:
    @staticmethod
    def is_participant(chat, user):
        return chat.user1_id == user.id or chat.user2_id == user.id


class AISoloChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = (request.data.get("message") or "").strip()
        context = request.data.get("context", "")

        if not message:
            return Response({"error": "Message is required"}, status=400)

        ai_response = AIService.process_command(message, context)

        return Response({"mode": "solo_ai", "response": ai_response}, status=200)


class GenerateTaskView(APIView, ChatAccessMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        try:
            chat = ChatSession.objects.get(id=chat_id, is_active=True)
        except ChatSession.DoesNotExist:
            return Response({"error": "Chat not found"}, status=404)

        if not self.is_participant(chat, request.user):
            return Response({"error": "Access denied"}, status=403)

        if hasattr(chat, "ai_task"):
            return Response(AITaskSerializer(chat.ai_task).data, status=200)

        interests = []
        if getattr(chat.user1, "interests", None):
            interests.extend(chat.user1.interests)
        if getattr(chat, "user2", None) and getattr(chat.user2, "interests", None):
            interests.extend(chat.user2.interests)
        if not interests and getattr(request.user, "interests", None):
            interests = request.user.interests

        task_data = AIService.generate_duo_task(interests)

        task = AITask.objects.create(
            chat=chat,
            title=task_data.get("title", "Discussion Task"),
            description=task_data.get("description", "Discuss together."),
        )

        return Response(AITaskSerializer(task).data, status=201)


class SubmitDiscussionView(APIView, ChatAccessMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        content = (request.data.get("content") or "").strip()

        if not content:
            return Response({"error": "Content required"}, status=400)

        try:
            chat = ChatSession.objects.get(id=chat_id, is_active=True)
        except ChatSession.DoesNotExist:
            return Response({"error": "Chat not found"}, status=404)

        if not self.is_participant(chat, request.user):
            return Response({"error": "Access denied"}, status=403)

        submission = Submission.objects.create(chat=chat, user=request.user, content=content)

        return Response(SubmissionSerializer(submission).data, status=201)


class EvaluateDiscussionView(APIView, ChatAccessMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        try:
            chat = ChatSession.objects.get(id=chat_id, is_active=True)
        except ChatSession.DoesNotExist:
            return Response({"error": "Chat not found"}, status=404)

        if not self.is_participant(chat, request.user):
            return Response({"error": "Access denied"}, status=403)

        submissions = chat.submissions.all()

        if not submissions.exists():
            return Response({"error": "No discussion found"}, status=400)

        if hasattr(chat, "evaluation"):
            return Response(AIEvaluationSerializer(chat.evaluation).data, status=200)

        result = AIService.evaluate_discussion(submissions)

        score = result.get("score", 6)
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = 6.0
        score = min(10.0, max(0.0, score))

        evaluation = AIEvaluation.objects.create(
            chat=chat,
            score=score,
            explanation=result.get("explanation", "Good discussion."),
        )

        return Response(AIEvaluationSerializer(evaluation).data, status=201)
