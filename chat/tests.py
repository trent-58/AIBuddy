from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from chat.models import Session, Attempt


User = get_user_model()


class SessionApiTests(APITestCase):
    def setUp(self):
        self.password = "StrongPass123"
        self.user = User.objects.create_user(
            username="alice",
            password=self.password,
            interests=["python", "ml"],
        )
        token_resp = self.client.post(
            "/auth/login",
            {"username": "alice", "password": self.password},
            format="json",
        )
        self.token = token_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def start_session(self):
        resp = self.client.post("/sessions/start", {}, format="json")
        self.assertEqual(resp.status_code, 201)
        return resp.data["id"]

    @patch("chat.services.session_service.openai_tutor")
    def test_topic_task_answer_flow(self, tutor_mock):
        tutor_mock.generate_topic.return_value = {
            "topic_title": "Python Basics",
            "explanation": "Intro topic",
        }
        tutor_mock.generate_task.return_value = {
            "task": "What is list comprehension?",
            "task_type": "conceptual",
            "expected_answer_hint": "Explain syntax and use-case",
        }
        tutor_mock.evaluate_answer.return_value = {
            "score": 71,
            "feedback": "Good but missing edge cases",
            "improvement": "Add complexity analysis",
            "common_mistakes": ["No complexity analysis"],
        }

        session_id = self.start_session()

        r1 = self.client.post(f"/sessions/{session_id}/message", {"message": "#topic"}, format="json")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.data["type"], "topic")

        r2 = self.client.post(f"/sessions/{session_id}/message", {"message": "#task"}, format="json")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["type"], "task")

        r3 = self.client.post(
            f"/sessions/{session_id}/message",
            {"message": "#answer My answer is ..."},
            format="json",
        )
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.data["type"], "evaluation")

        session = Session.objects.get(id=session_id)
        self.assertEqual(session.current_topic_title, "Python Basics")
        self.assertEqual(session.current_task_text, "What is list comprehension?")
        self.assertEqual(Attempt.objects.filter(session=session).count(), 1)

    @patch("chat.services.session_service.openai_tutor")
    def test_help_and_progress(self, tutor_mock):
        tutor_mock.generate_topic.return_value = {
            "topic_title": "ML",
            "explanation": "Topic text",
        }
        tutor_mock.generate_task.return_value = {
            "task": "Define overfitting",
            "task_type": "conceptual",
            "expected_answer_hint": "Train vs test performance",
        }
        tutor_mock.give_hint.return_value = {
            "hint": "Think about train vs unseen data",
            "next_step_question": "What happens on new data?",
        }
        tutor_mock.summarize_progress.return_value = {
            "attempted": 0,
            "avg_score": 0.0,
            "last_topic": "ML",
            "strengths": [],
            "weaknesses": ["practice"],
            "next_recommendation": "Solve 1 more task",
        }

        session_id = self.start_session()
        self.client.post(f"/sessions/{session_id}/message", {"message": "#topic"}, format="json")
        self.client.post(f"/sessions/{session_id}/message", {"message": "#task"}, format="json")

        h = self.client.post(f"/sessions/{session_id}/message", {"message": "#help"}, format="json")
        self.assertEqual(h.status_code, 200)
        self.assertEqual(h.data["type"], "hint")

        p = self.client.post(f"/sessions/{session_id}/message", {"message": "#progress"}, format="json")
        self.assertEqual(p.status_code, 200)
        self.assertEqual(p.data["type"], "progress")

    @patch("chat.services.session_service.openai_tutor")
    def test_normal_chat_and_state_errors(self, tutor_mock):
        tutor_mock.chat_reply.return_value = {"reply": "Let's break this down."}

        session_id = self.start_session()

        r = self.client.post(
            f"/sessions/{session_id}/message",
            {"message": "Explain recursion simply"},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["type"], "chat")

        err = self.client.post(f"/sessions/{session_id}/message", {"message": "#task"}, format="json")
        self.assertEqual(err.status_code, 200)
        self.assertEqual(err.data["type"], "error")
        self.assertIn("#topic", err.data["data"]["message"])

        unknown = self.client.post(
            f"/sessions/{session_id}/message",
            {"message": "#unknown"},
            format="json",
        )
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(unknown.data["type"], "error")
        self.assertIn("available_commands", unknown.data["data"])
