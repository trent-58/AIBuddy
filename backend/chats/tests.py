from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import AIAttempt, Chat


User = get_user_model()


class ChatsAPITests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="u1", password="pass12345")
        self.user2 = User.objects.create_user(username="u2", password="pass12345")

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_select_ai_chat_is_singleton_per_user(self):
        self._auth(self.user1)

        r1 = self.client.post("/chats/select/", {"mode": "ai"}, format="json")
        r2 = self.client.post("/chats/select/", {"mode": "ai"}, format="json")

        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r1.data["id"], r2.data["id"])
        self.assertEqual(Chat.objects.filter(kind=Chat.KIND_AI, user_a=self.user1).count(), 1)

    def test_select_direct_chat_is_singleton_for_pair(self):
        self._auth(self.user1)
        r1 = self.client.post("/chats/select/", {"mode": "person", "peer_id": self.user2.id}, format="json")
        self.assertEqual(r1.status_code, status.HTTP_200_OK)

        self._auth(self.user2)
        r2 = self.client.post("/chats/select/", {"mode": "person", "peer_id": self.user1.id}, format="json")
        self.assertEqual(r2.status_code, status.HTTP_200_OK)

        self.assertEqual(r1.data["id"], r2.data["id"])
        self.assertEqual(Chat.objects.filter(kind=Chat.KIND_DIRECT).count(), 1)

    def test_ai_commands_topic_task_answer_evaluate(self):
        self._auth(self.user1)
        select_res = self.client.post("/chats/select/", {"mode": "ai"}, format="json")
        self.assertEqual(select_res.status_code, status.HTTP_200_OK)
        chat_id = select_res.data["id"]

        topic_res = self.client.post(f"/chats/{chat_id}/messages/", {"text": "#topic"}, format="json")
        self.assertEqual(topic_res.status_code, status.HTTP_200_OK)
        self.assertEqual(topic_res.data["type"], "topic")

        task_res = self.client.post(f"/chats/{chat_id}/messages/", {"text": "#task"}, format="json")
        self.assertEqual(task_res.status_code, status.HTTP_200_OK)
        self.assertEqual(task_res.data["type"], "task")

        answer_res = self.client.post(
            f"/chats/{chat_id}/messages/",
            {"text": "#answer This is my explanation with an example because it applies in practice."},
            format="json",
        )
        self.assertEqual(answer_res.status_code, status.HTTP_200_OK)
        self.assertEqual(answer_res.data["type"], "evaluation")
        self.assertIn("score", answer_res.data["data"])

        evaluate_res = self.client.post(f"/chats/{chat_id}/messages/", {"text": "#evaluate"}, format="json")
        self.assertEqual(evaluate_res.status_code, status.HTTP_200_OK)
        self.assertEqual(evaluate_res.data["type"], "progress")
        self.assertGreaterEqual(evaluate_res.data["data"]["attempted"], 1)

        self.assertEqual(AIAttempt.objects.filter(chat_id=chat_id).count(), 1)
