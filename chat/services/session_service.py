from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any

from django.db import transaction

from chat.models import Attempt, Message, Session

from .command_parser import parse_command
from .openai_client import OpenAIClient, OpenAIClientError
from .tutor_service import TutorService


@dataclass
class MessageResult:
    response_type: str
    data: dict[str, Any]


class SessionServiceError(Exception):
    pass


class _FallbackTutorService:
    @staticmethod
    def _normalize_interests(interests):
        if interests is None:
            return []
        if isinstance(interests, str):
            return [x.strip() for x in interests.split(",") if x.strip()]
        if isinstance(interests, dict):
            values = []
            for v in interests.values():
                if isinstance(v, (list, tuple)):
                    values.extend(v)
                else:
                    values.append(v)
            return [str(x).strip() for x in values if str(x).strip()]
        if isinstance(interests, (list, tuple, set)):
            return [str(x).strip() for x in interests if str(x).strip()]
        return [str(interests).strip()] if str(interests).strip() else []

    def generate_topic(self, interests):
        norm = self._normalize_interests(interests)
        base = random.choice(norm) if norm else "general learning"
        angles = [
            "beginner essentials",
            "real-world use cases",
            "common mistakes",
            "practical workflow",
            "problem-solving mindset",
        ]
        angle = random.choice(angles)
        return {
            "topic_title": f"{base.title()} - {angle.title()}",
            "explanation": (
                f"What it is: this topic introduces {base} from a {angle} perspective.\n"
                f"Why it matters: understanding {base} helps you solve practical tasks faster and with better decision-making.\n"
                "Key points: start from fundamentals, identify common mistakes, and connect concepts to outcomes.\n"
                f"Real-world example: use {base} in a small project scenario and compare different solution approaches.\n"
                "How to start: study one concept, implement a tiny example, then explain your result in your own words."
            ),
        }

    def generate_task(self, current_topic):
        return {
            "task": f"Explain '{current_topic}' and provide one practical example.",
            "task_type": "conceptual",
            "expected_answer_hint": "Define clearly, provide example, mention limitations.",
        }

    def evaluate_answer(self, *, current_task, user_answer, expected_answer_hint):
        score = max(0, min(100, 45 + min(50, len(user_answer) // 2)))
        return {
            "score": score,
            "feedback": "Good attempt. Some parts are correct, but the reasoning can be deeper.",
            "improvement": "Add clearer structure and a concrete example aligned with the task.",
            "common_mistakes": ["Too generic explanation"],
        }

    def give_hint(self, current_task):
        return {
            "hint": "Start from the core definition, then connect it to one realistic scenario.",
            "next_step_question": "Which key concept is central to this task?",
        }

    def summarize_progress(self, *, attempted, avg_score, last_topic, feedback_summaries):
        return {
            "attempted": attempted,
            "avg_score": avg_score,
            "last_topic": last_topic,
            "strengths": ["Consistency"] if attempted else [],
            "weaknesses": ["Depth of explanation"] if attempted else ["No attempts yet"],
            "next_recommendation": "Try one more task and focus on structured reasoning.",
        }

    def chat_reply(self, *, history, user_message, current_topic, current_task):
        return {"reply": "Good question. Let's split it into definition, mechanism, and real-world example."}


try:
    openai_tutor = TutorService(OpenAIClient())
except OpenAIClientError:
    openai_tutor = _FallbackTutorService()


class SessionService:
    @staticmethod
    def start_session(user) -> Session:
        # Bu yerda user uchun yangi session ochyapmiz
        return Session.objects.create(user=user)

    @staticmethod
    def get_session_for_user(*, session_id: int, user) -> Session:
        try:
            session = Session.objects.get(id=session_id, user=user)
        except Session.DoesNotExist as exc:
            raise SessionServiceError("Session not found") from exc
        return session

    @staticmethod
    def session_state_payload(session: Session) -> dict[str, Any]:
        return {
            "current_topic_title": session.current_topic_title,
            "has_task": bool(session.current_task_text),
        }

    @staticmethod
    def _history_text(session: Session, limit: int = 20) -> str:
        rows = []
        for msg in session.messages.order_by("-created_at")[:limit][::-1]:
            rows.append(f"{msg.role}: {msg.content}")
        return "\n".join(rows)

    @staticmethod
    def _save_user_message(session: Session, text: str) -> Message:
        # Bu yerda user xabarini DB ga saqlayapmiz
        return Message.objects.create(session=session, role=Message.ROLE_USER, content=text)

    @staticmethod
    def _save_assistant_message(session: Session, text: str, role: str = Message.ROLE_ASSISTANT) -> Message:
        # Bu yerda assistant/system javobini DB ga saqlayapmiz
        return Message.objects.create(session=session, role=role, content=text)

    @staticmethod
    def _assistant_text(response_type: str, data: dict[str, Any]) -> str:
        if response_type == "topic":
            return f"Topic: {data.get('topic_title', '-')}\n{data.get('explanation', '')}".strip()
        if response_type == "task":
            return (
                f"Task ({data.get('task_type', 'conceptual')}): {data.get('task', '')}\n"
                f"Hint baseline: {data.get('expected_answer_hint', '')}"
            ).strip()
        if response_type == "evaluation":
            return (
                f"Score: {data.get('score', 0)}/100\n"
                f"Feedback: {data.get('feedback', '')}\n"
                f"Improvement: {data.get('improvement', '')}"
            ).strip()
        if response_type == "hint":
            return f"Hint: {data.get('hint', '')}\nQuestion: {data.get('next_step_question', '')}".strip()
        if response_type == "progress":
            return (
                f"Attempted: {data.get('attempted', 0)}, Avg: {data.get('avg_score', 0)}\n"
                f"Last topic: {data.get('last_topic', '-')}\n"
                f"Next: {data.get('next_recommendation', '')}"
            ).strip()
        if response_type == "chat":
            return data.get("reply", "")
        return data.get("message") or "Unknown result"

    @classmethod
    def _handle_topic(cls, *, session: Session, user, command_arg: str) -> MessageResult:
        # Bu yerda #topic commandini ishlayapmiz
        interests = getattr(user, "interests", [])
        if isinstance(interests, str):
            interests = [x.strip() for x in interests.split(",") if x.strip()]
        elif isinstance(interests, dict):
            values = []
            for v in interests.values():
                if isinstance(v, (list, tuple)):
                    values.extend(v)
                else:
                    values.append(v)
            interests = [str(x).strip() for x in values if str(x).strip()]
        elif isinstance(interests, (list, tuple, set)):
            interests = [str(x).strip() for x in interests if str(x).strip()]
        else:
            interests = [str(interests).strip()] if str(interests).strip() else []

        topic_data = openai_tutor.generate_topic(interests=interests)

        session.current_topic_title = topic_data["topic_title"]
        session.current_topic_explanation = topic_data["explanation"]
        session.current_task_text = None
        session.current_task_type = None
        session.current_task_hint = None
        session.last_command = "#topic"
        session.save(
            update_fields=[
                "current_topic_title",
                "current_topic_explanation",
                "current_task_text",
                "current_task_type",
                "current_task_hint",
                "last_command",
            ]
        )

        return MessageResult(response_type="topic", data=topic_data)

    @classmethod
    def _handle_task(cls, *, session: Session) -> MessageResult:
        # Bu yerda #task commandini ishlayapmiz
        if not session.current_topic_title:
            return MessageResult(
                response_type="error",
                data={"message": "Send #topic first."},
            )

        task_data = openai_tutor.generate_task(current_topic=session.current_topic_title)
        session.current_task_text = task_data["task"]
        session.current_task_type = task_data["task_type"]
        session.current_task_hint = task_data["expected_answer_hint"]
        session.last_command = "#task"
        session.save(update_fields=["current_task_text", "current_task_type", "current_task_hint", "last_command"])

        return MessageResult(response_type="task", data=task_data)

    @classmethod
    def _handle_answer(cls, *, session: Session, command_arg: str) -> MessageResult:
        # Bu yerda #answer commandini ishlayapmiz
        if not session.current_task_text:
            return MessageResult(
                response_type="error",
                data={"message": "Send #task first."},
            )

        answer_text = (command_arg or "").strip()
        if not answer_text:
            return MessageResult(
                response_type="error",
                data={"message": "Use format: #answer <your answer>"},
            )

        eval_data = openai_tutor.evaluate_answer(
            current_task=session.current_task_text,
            user_answer=answer_text,
            expected_answer_hint=session.current_task_hint or "",
        )

        # Bu yerda attempt natijasini DB ga yozib qo'yamiz
        Attempt.objects.create(
            session=session,
            task_text=session.current_task_text,
            user_answer=answer_text,
            score=eval_data["score"],
            feedback=eval_data["feedback"],
            improvement=eval_data["improvement"],
        )

        session.last_command = "#answer"
        session.save(update_fields=["last_command"])

        # Tanlov: current_task saqlanib qoladi (clear qilinmaydi)
        return MessageResult(response_type="evaluation", data=eval_data)

    @classmethod
    def _handle_help(cls, *, session: Session) -> MessageResult:
        # Bu yerda #help commandini ishlayapmiz
        if not session.current_task_text:
            return MessageResult(
                response_type="error",
                data={"message": "Send #task first."},
            )

        hint_data = openai_tutor.give_hint(current_task=session.current_task_text)
        session.last_command = "#help"
        session.save(update_fields=["last_command"])

        return MessageResult(response_type="hint", data=hint_data)

    @classmethod
    def _handle_progress(cls, *, session: Session) -> MessageResult:
        # Bu yerda #progress commandini ishlaymiz va DB statistikani yig'amiz
        attempts = list(session.attempts.order_by("-created_at"))
        attempted = len(attempts)
        avg_score = round(sum(x.score for x in attempts) / attempted, 2) if attempted else 0.0
        feedback_summaries = [a.feedback[:180] for a in attempts[:5]]

        progress_data = openai_tutor.summarize_progress(
            attempted=attempted,
            avg_score=avg_score,
            last_topic=session.current_topic_title or "",
            feedback_summaries=feedback_summaries,
        )

        # DB statistikani aniq qiymat bilan override qilamiz
        progress_data["attempted"] = attempted
        progress_data["avg_score"] = avg_score
        progress_data["last_topic"] = session.current_topic_title or ""

        session.last_command = "#progress"
        session.save(update_fields=["last_command"])

        return MessageResult(response_type="progress", data=progress_data)

    @classmethod
    def _handle_normal_chat(cls, *, session: Session, text: str) -> MessageResult:
        chat_data = openai_tutor.chat_reply(
            history=cls._history_text(session),
            user_message=text,
            current_topic=session.current_topic_title or "",
            current_task=session.current_task_text or "",
        )
        return MessageResult(response_type="chat", data=chat_data)

    @classmethod
    @transaction.atomic
    def process_message(cls, *, session: Session, user, message_text: str) -> dict[str, Any]:
        text = (message_text or "").strip()
        if not text:
            raise SessionServiceError("message is required")

        cls._save_user_message(session, text)
        parsed = parse_command(text)

        try:
            if parsed is None:
                result = cls._handle_normal_chat(session=session, text=text)

            elif parsed.name == "unknown":
                result = MessageResult(
                    response_type="error",
                    data={
                        "message": "Unknown command.",
                        "available_commands": ["#topic", "#task", "#answer", "#help", "#progress"],
                    },
                )

            elif parsed.name == "topic":
                result = cls._handle_topic(session=session, user=user, command_arg=parsed.argument)

            elif parsed.name == "task":
                result = cls._handle_task(session=session)

            elif parsed.name == "answer":
                result = cls._handle_answer(session=session, command_arg=parsed.argument)

            elif parsed.name == "help":
                result = cls._handle_help(session=session)

            elif parsed.name == "progress":
                result = cls._handle_progress(session=session)

            else:
                result = MessageResult(
                    response_type="error",
                    data={"message": "Unsupported command."},
                )

        except (OpenAIClientError, ValueError) as exc:
            result = MessageResult(response_type="error", data={"message": str(exc)})

        assistant_text = cls._assistant_text(result.response_type, result.data)
        role = Message.ROLE_SYSTEM if result.response_type == "error" else Message.ROLE_ASSISTANT
        cls._save_assistant_message(session, assistant_text, role=role)

        session_state = cls.session_state_payload(session)
        return {
            "type": result.response_type,
            "data": result.data,
            "session_state": session_state,
        }
