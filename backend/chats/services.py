from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.db.utils import OperationalError, ProgrammingError
from django.db.models import Avg, Q

from user.models import Interest

from .models import AIAttempt, Chat, ChatMessage, ChatTopic


class ChatsServiceError(Exception):
    pass


@dataclass
class SendResult:
    response_type: str
    payload: dict


class _FallbackTutor:
    @staticmethod
    def topic(
        *,
        interests: list[str],
        previous_topic: str = "",
        covered_topics: list[str] | None = None,
        requested_topic: str = "",
    ) -> dict[str, Any]:
        covered_set = {x.strip().lower() for x in (covered_topics or []) if x.strip()}

        if requested_topic:
            topic = requested_topic.strip()
            base = topic
        else:
            candidates = [
                "variables",
                "data types",
                "operators",
                "conditionals",
                "loops",
                "functions",
                "lists",
                "tuples",
                "dictionaries",
                "sets",
                "strings",
                "file handling",
                "exceptions",
                "modules",
                "object-oriented programming",
                "inheritance",
                "decorators",
                "generators",
                "context managers",
                "testing",
                "debugging",
                "algorithms",
            ]
            if interests:
                candidates = [*candidates, *interests]
            unseen = [topic for topic in candidates if topic.strip().lower() not in covered_set]
            pool = unseen or candidates
            base = random.choice(pool) if pool else "General Learning"
            topic = base

        if previous_topic and topic.strip().lower() == previous_topic.strip().lower() and not requested_topic:
            topic = f"{topic} ({random.randint(1, 99)})"

        return {
            "topic": topic,
            "explanation": f"Let's discuss {base}. Focus on concept, examples, and common mistakes.",
        }

    @staticmethod
    def task(*, topic: str) -> dict[str, Any]:
        return {
            "task": f"Explain '{topic}' with one real-world example.",
            "hint_baseline": "Define clearly, then give one practical scenario.",
        }

    @staticmethod
    def hint(*, task: str, hint_baseline: str) -> dict[str, Any]:
        hint = hint_baseline or "Break your answer into definition, mechanism, and one example."
        return {"hint": hint}

    @staticmethod
    def evaluate(*, task: str, answer: str, hint_baseline: str) -> dict[str, Any]:
        score = min(100, max(0, 30 + len(answer) // 4))
        if any(word in answer.lower() for word in ["because", "example", "therefore"]):
            score = min(100, score + 10)
        return {
            "score": score,
            "feedback": "Good structure. Add more precision and concrete details.",
        }

    @staticmethod
    def chat_reply(*, text: str, current_topic: str, current_task: str) -> dict[str, Any]:
        reply = (
            "Use #topic for a new topic, #task for a task, #hint for help, "
            "#answer <text> to submit, and #evaluate for progress."
        )
        if current_topic:
            reply = f"Current topic: {current_topic}. {reply}"
        return {"reply": reply}

    @staticmethod
    def progress(*, attempted: int, avg_score: float, best_score: int, current_topic: str) -> dict[str, Any]:
        return {
            "attempted": attempted,
            "avg_score": round(float(avg_score), 2),
            "best_score": int(best_score),
            "current_topic": current_topic,
            "summary": "Keep practicing with focused examples to improve consistency.",
        }


class _OpenAITutor:
    def __init__(self):
        try:
            from openai import OpenAI
        except Exception as exc:
            raise RuntimeError("openai package is not available") from exc

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        self.client = OpenAI(api_key=api_key, timeout=30.0)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def _json_call(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> dict[str, Any]:
        completion = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        content = completion.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned empty content")
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise RuntimeError("OpenAI returned non-object JSON")
        return payload

    def topic(
        self,
        *,
        interests: list[str],
        previous_topic: str = "",
        covered_topics: list[str] | None = None,
        requested_topic: str = "",
    ) -> dict[str, Any]:
        interests_text = ", ".join(interests) if interests else "general learning"
        covered_text = ", ".join(covered_topics or []) if covered_topics else "none"
        data = self._json_call(
            system_prompt="You are a concise learning assistant. Return valid JSON only.",
            user_prompt=(
                "Generate a new learning topic and short explanation.\n"
                f"User interests: {interests_text}. "
                f"Previously covered topics in this chat: {covered_text}. "
                f"Previous topic to avoid repeating: {previous_topic or 'none'}. "
                f"Requested topic override from user (if any): {requested_topic or 'none'}. "
                "If requested topic exists, use that exact topic.\n"
                "Otherwise, choose a topic not in covered topics when possible.\n"
                'Return JSON: {"topic":"...","explanation":"..."}'
            ),
            temperature=0.4,
        )
        topic = str(data.get("topic", "")).strip()
        explanation = str(data.get("explanation", "")).strip()
        if not topic:
            raise RuntimeError("Missing topic")
        if not explanation:
            explanation = "Start with fundamentals, then apply with a practical example."
        return {"topic": topic, "explanation": explanation}

    def task(self, *, topic: str) -> dict[str, Any]:
        data = self._json_call(
            system_prompt="You are a tutor. Return valid JSON only.",
            user_prompt=(
                f"Create one task for topic: {topic}. "
                'Return JSON: {"task":"...","hint_baseline":"..."}'
            ),
            temperature=0.3,
        )
        task = str(data.get("task", "")).strip()
        hint = str(data.get("hint_baseline", "")).strip()
        if not task:
            raise RuntimeError("Missing task")
        if not hint:
            hint = "Break your answer into core idea and one concrete example."
        return {"task": task, "hint_baseline": hint}

    def hint(self, *, task: str, hint_baseline: str) -> dict[str, Any]:
        data = self._json_call(
            system_prompt="You are a tutor. Give a hint only, no full solution. Return JSON.",
            user_prompt=(
                f"Task: {task}\nHint baseline: {hint_baseline}\n"
                'Return JSON: {"hint":"..."}'
            ),
            temperature=0.2,
        )
        hint = str(data.get("hint", "")).strip()
        if not hint:
            hint = hint_baseline or "Focus on definitions first, then show one practical example."
        return {"hint": hint}

    def evaluate(self, *, task: str, answer: str, hint_baseline: str) -> dict[str, Any]:
        data = self._json_call(
            system_prompt="You are a strict but fair tutor. Score 0..100. Return JSON.",
            user_prompt=(
                f"Task: {task}\nExpected hint baseline: {hint_baseline}\nStudent answer: {answer}\n"
                'Return JSON: {"score":0,"feedback":"..."}'
            ),
            temperature=0.1,
        )
        try:
            score = int(float(data.get("score", 0)))
        except (TypeError, ValueError):
            score = 0
        score = max(0, min(100, score))
        feedback = str(data.get("feedback", "")).strip() or "Answer reviewed. Add clearer reasoning and examples."
        return {"score": score, "feedback": feedback}

    def chat_reply(self, *, text: str, current_topic: str, current_task: str) -> dict[str, Any]:
        data = self._json_call(
            system_prompt="You are a concise tutor assistant. Return JSON.",
            user_prompt=(
                f"Current topic: {current_topic}\nCurrent task: {current_task}\n"
                f"User message: {text}\n"
                'Return JSON: {"reply":"..."}'
            ),
            temperature=0.5,
        )
        reply = str(data.get("reply", "")).strip()
        if not reply:
            reply = "Let's break your question into smaller parts and solve step-by-step."
        return {"reply": reply}

    def progress(self, *, attempted: int, avg_score: float, best_score: int, current_topic: str) -> dict[str, Any]:
        data = self._json_call(
            system_prompt="You summarize learning progress from metrics. Return JSON.",
            user_prompt=(
                f"attempted={attempted}, avg_score={avg_score}, best_score={best_score}, current_topic={current_topic}\n"
                'Return JSON: {"summary":"..."}'
            ),
            temperature=0.2,
        )
        summary = str(data.get("summary", "")).strip() or "Progress is stable; keep practicing with focused feedback."
        return {
            "attempted": attempted,
            "avg_score": round(float(avg_score), 2),
            "best_score": int(best_score),
            "current_topic": current_topic,
            "summary": summary,
        }


class _TutorFacade:
    def __init__(self):
        self._fallback = _FallbackTutor()
        self._openai: _OpenAITutor | None = None

    def _client(self):
        if self._openai is None:
            self._openai = _OpenAITutor()
        return self._openai

    def _call(self, method_name: str, **kwargs):
        try:
            return getattr(self._client(), method_name)(**kwargs)
        except Exception:
            return getattr(self._fallback, method_name)(**kwargs)

    def topic(
        self,
        *,
        interests: list[str],
        previous_topic: str = "",
        covered_topics: list[str] | None = None,
        requested_topic: str = "",
    ) -> dict[str, Any]:
        return self._call(
            "topic",
            interests=interests,
            previous_topic=previous_topic,
            covered_topics=covered_topics,
            requested_topic=requested_topic,
        )

    def task(self, *, topic: str) -> dict[str, Any]:
        return self._call("task", topic=topic)

    def hint(self, *, task: str, hint_baseline: str) -> dict[str, Any]:
        return self._call("hint", task=task, hint_baseline=hint_baseline)

    def evaluate(self, *, task: str, answer: str, hint_baseline: str) -> dict[str, Any]:
        return self._call("evaluate", task=task, answer=answer, hint_baseline=hint_baseline)

    def chat_reply(self, *, text: str, current_topic: str, current_task: str) -> dict[str, Any]:
        return self._call("chat_reply", text=text, current_topic=current_topic, current_task=current_task)

    def progress(self, *, attempted: int, avg_score: float, best_score: int, current_topic: str) -> dict[str, Any]:
        return self._call(
            "progress",
            attempted=attempted,
            avg_score=avg_score,
            best_score=best_score,
            current_topic=current_topic,
        )


tutor = _TutorFacade()


class ChatsService:
    @staticmethod
    @transaction.atomic
    def get_or_create_ai_chat(*, user) -> Chat:
        chat = Chat.objects.filter(kind=Chat.KIND_AI, user_a=user).first()
        if chat:
            return chat
        return Chat.objects.create(kind=Chat.KIND_AI, user_a=user)

    @staticmethod
    @transaction.atomic
    def get_or_create_direct_chat(*, user, peer) -> Chat:
        pair_key = Chat.build_pair_key(kind=Chat.KIND_DIRECT, user_a_id=user.id, user_b_id=peer.id)
        chat = Chat.objects.filter(pair_key=pair_key).first()
        if chat:
            return chat

        low, high = sorted([user, peer], key=lambda x: x.id)
        return Chat.objects.create(kind=Chat.KIND_DIRECT, user_a=low, user_b=high)

    @staticmethod
    def list_user_chats(*, user):
        return Chat.objects.filter(Q(user_a=user) | Q(user_b=user))

    @staticmethod
    def get_chat_for_user(*, chat_id: int, user) -> Chat:
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist as exc:
            raise ChatsServiceError("Chat not found") from exc

        if not chat.is_participant(user.id):
            raise ChatsServiceError("Access denied")
        return chat

    @staticmethod
    def _parse_command(text: str) -> tuple[str, str]:
        stripped = (text or "").strip()
        if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
            stripped = stripped[1:-1].strip()
        if not stripped.startswith("#"):
            return "", stripped

        parts = stripped.split(" ", 1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""
        return cmd, arg

    @staticmethod
    def _interests_for_user(user) -> list[str]:
        try:
            return list(
                Interest.objects.filter(user=user)
                .select_related("name")
                .values_list("name__name", flat=True)
            )
        except (ProgrammingError, OperationalError):
            # Keep chats functional even if Interest tables are not migrated yet.
            return []

    @staticmethod
    def _assistant_text(response_type: str, payload: dict[str, Any]) -> str:
        if response_type == "topic":
            return f"Topic: {payload.get('topic', '')}\n{payload.get('explanation', '')}".strip()
        if response_type == "task":
            return f"Task: {payload.get('task', '')}\nHint baseline: {payload.get('hint_baseline', '')}".strip()
        if response_type == "hint":
            return f"Hint: {payload.get('hint', '')}".strip()
        if response_type == "evaluation":
            return f"Score: {payload.get('score', 0)}/100\nFeedback: {payload.get('feedback', '')}".strip()
        if response_type == "progress":
            return (
                f"Attempts: {payload.get('attempted', 0)}\n"
                f"Average score: {payload.get('avg_score', 0)}\n"
                f"Best score: {payload.get('best_score', 0)}\n"
                f"Summary: {payload.get('summary', '')}"
            ).strip()
        return payload.get("reply", "")

    @staticmethod
    def _normalize_topic_name(topic: str) -> str:
        return " ".join((topic or "").strip().lower().split())

    @classmethod
    def _handle_topic(cls, *, chat: Chat, user, requested_topic: str = "") -> SendResult:
        covered_topics = list(chat.topics.values_list("normalized_name", flat=True))
        result = tutor.topic(
            interests=cls._interests_for_user(user),
            previous_topic=chat.current_topic,
            covered_topics=covered_topics,
            requested_topic=requested_topic.strip(),
        )
        if requested_topic.strip():
            result["topic"] = requested_topic.strip()

        normalized_topic = cls._normalize_topic_name(result["topic"])
        if not requested_topic.strip() and normalized_topic in covered_topics:
            # As a final guard, ensure new auto-generated topic differs from covered history.
            fallback = f"{result['topic']} ({len(covered_topics) + 1})"
            result["topic"] = fallback
            normalized_topic = cls._normalize_topic_name(fallback)

        chat.current_topic = result["topic"]
        chat.current_task = ""
        chat.current_task_hint = ""
        chat.last_command = "#topic"
        chat.save(update_fields=["current_topic", "current_task", "current_task_hint", "last_command", "updated_at"])
        ChatTopic.objects.get_or_create(
            chat=chat,
            normalized_name=normalized_topic,
            defaults={"topic_name": result["topic"]},
        )
        return SendResult(response_type="topic", payload=result)

    @staticmethod
    def _handle_task(*, chat: Chat) -> SendResult:
        if not chat.current_topic:
            raise ChatsServiceError("Use #topic first")

        result = tutor.task(topic=chat.current_topic)
        chat.current_task = result["task"]
        chat.current_task_hint = result["hint_baseline"]
        chat.last_command = "#task"
        chat.save(update_fields=["current_task", "current_task_hint", "last_command", "updated_at"])
        return SendResult(response_type="task", payload=result)

    @staticmethod
    def _handle_hint(*, chat: Chat) -> SendResult:
        if not chat.current_task:
            raise ChatsServiceError("Use #task first")

        result = tutor.hint(task=chat.current_task, hint_baseline=chat.current_task_hint)
        chat.last_command = "#hint"
        chat.save(update_fields=["last_command", "updated_at"])
        return SendResult(response_type="hint", payload=result)

    @staticmethod
    def _handle_answer(*, chat: Chat, answer_text: str) -> SendResult:
        if not chat.current_task:
            raise ChatsServiceError("Use #task first")
        if not answer_text:
            raise ChatsServiceError("Use format: #answer <your answer>")

        result = tutor.evaluate(task=chat.current_task, answer=answer_text, hint_baseline=chat.current_task_hint)
        AIAttempt.objects.create(
            chat=chat,
            task_text=chat.current_task,
            answer_text=answer_text,
            score=result["score"],
            feedback=result["feedback"],
        )
        chat.last_command = "#answer"
        chat.save(update_fields=["last_command", "updated_at"])
        return SendResult(response_type="evaluation", payload=result)

    @staticmethod
    def _handle_evaluate(*, chat: Chat) -> SendResult:
        qs = chat.attempts.all()
        attempted = qs.count()
        avg_score = qs.aggregate(avg=Avg("score"))["avg"] or 0
        best_score = qs.order_by("-score").values_list("score", flat=True).first() or 0

        result = tutor.progress(
            attempted=attempted,
            avg_score=float(avg_score),
            best_score=int(best_score),
            current_topic=chat.current_topic,
        )
        return SendResult(response_type="progress", payload=result)

    @staticmethod
    def _chat_reply(*, text: str, chat: Chat) -> SendResult:
        result = tutor.chat_reply(text=text, current_topic=chat.current_topic, current_task=chat.current_task)
        return SendResult(response_type="chat", payload=result)

    @classmethod
    def send_message(cls, *, chat: Chat, user, text: str) -> dict:
        stripped = (text or "").strip()
        if not stripped:
            raise ChatsServiceError("Message cannot be empty")
        if not chat.is_participant(user.id):
            raise ChatsServiceError("Access denied")

        user_message = ChatMessage.objects.create(
            chat=chat,
            sender_type=ChatMessage.SENDER_USER,
            sender_user=user,
            content=stripped,
        )

        chat.save(update_fields=["updated_at"])

        command, arg = cls._parse_command(stripped)
        user_message.command = command
        user_message.save(update_fields=["command"])

        # In direct chats, AI should participate only for explicit command messages.
        if chat.kind == Chat.KIND_DIRECT and not command:
            return {
                "type": "message",
                "chat_id": chat.id,
                "message": {
                    "id": user_message.id,
                    "content": user_message.content,
                },
            }

        if command == "#topic":
            result = cls._handle_topic(chat=chat, user=user, requested_topic=arg)
        elif command == "#task":
            result = cls._handle_task(chat=chat)
        elif command == "#hint":
            result = cls._handle_hint(chat=chat)
        elif command == "#answer":
            result = cls._handle_answer(chat=chat, answer_text=arg)
        elif command == "#evaluate":
            result = cls._handle_evaluate(chat=chat)
        elif command.startswith("#"):
            raise ChatsServiceError("Unsupported command")
        else:
            result = cls._chat_reply(text=stripped, chat=chat)

        ai_message = ChatMessage.objects.create(
            chat=chat,
            sender_type=ChatMessage.SENDER_AI,
            content=cls._assistant_text(result.response_type, result.payload),
            command=command,
        )

        chat.save(update_fields=["updated_at"])

        return {
            "type": result.response_type,
            "chat_id": chat.id,
            "data": result.payload,
            "user_message_id": user_message.id,
            "ai_message_id": ai_message.id,
        }
