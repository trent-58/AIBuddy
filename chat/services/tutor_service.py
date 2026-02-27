from __future__ import annotations

import random
from typing import Any

from .openai_client import OpenAIClient


def _as_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _normalize_interests(interests: Any) -> list[str]:
    if interests is None:
        return []
    if isinstance(interests, str):
        return [x.strip() for x in interests.split(",") if x.strip()]
    if isinstance(interests, dict):
        # dict kelib qolsa value laridan foydalanamiz
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


def _topic_parts(topic_title: str) -> tuple[str, str]:
    # "Python - Common Mistakes" -> ("Python", "Common Mistakes")
    if " - " in topic_title:
        left, right = topic_title.split(" - ", 1)
        return left.strip(), right.strip()
    return topic_title.strip(), "Practical Perspective"


class TutorService:
    def __init__(self, client: OpenAIClient):
        self.client = client

    @staticmethod
    def _validate_topic(payload: dict[str, Any]) -> dict[str, Any]:
        topic_title = _as_text(payload.get("topic_title"))
        explanation = _as_text(payload.get("explanation"))
        if not topic_title:
            raise ValueError("topic_title is required")
        explanation = TutorService._ensure_detailed_explanation(topic_title, explanation)
        return {"topic_title": topic_title, "explanation": explanation[:1800]}

    @staticmethod
    def _ensure_detailed_explanation(topic_title: str, explanation: str) -> str:
        text = (explanation or "").strip()
        if len(text) >= 260:
            return text

        base_topic, angle = _topic_parts(topic_title)
        outcomes = [
            "design clearer solutions",
            "avoid common implementation errors",
            "improve decision-making in projects",
            "build confidence with structured reasoning",
        ]
        exercises = [
            "a mini script with input/output and validation",
            "a small debugging walkthrough with 2-3 edge cases",
            "a simple refactor task to improve readability",
            "a short practical task with measurable result",
        ]
        focus_points = [
            "core terminology, expected behavior, and boundaries",
            "patterns, anti-patterns, and trade-offs",
            "step-by-step logic and error prevention",
            "implementation flow and quality checks",
        ]

        if text:
            intro = text
        else:
            intro = f"{base_topic} is explored through a {angle.lower()} approach."

        return (
            f"What it is: {intro}\n"
            f"Why it matters: mastering {base_topic} helps you {random.choice(outcomes)} in real tasks.\n"
            f"Key points to focus on: {random.choice(focus_points)}.\n"
            f"Real-world example: practice with {random.choice(exercises)} related to {base_topic.lower()}.\n"
            f"How to start: study one small concept from {angle.lower()}, implement it, then explain your result in your own words."
        )

    @staticmethod
    def _validate_task(payload: dict[str, Any]) -> dict[str, Any]:
        task = _as_text(payload.get("task"))
        task_type = _as_text(payload.get("task_type")).lower()
        expected_answer_hint = _as_text(payload.get("expected_answer_hint"))

        if task_type not in {"conceptual", "practical", "coding"}:
            task_type = "conceptual"
        if not task:
            raise ValueError("task is required")
        if not expected_answer_hint:
            expected_answer_hint = "Focus on correctness, structure, and a practical example."

        return {
            "task": task,
            "task_type": task_type,
            "expected_answer_hint": expected_answer_hint,
        }

    @staticmethod
    def _validate_answer(payload: dict[str, Any]) -> dict[str, Any]:
        score = payload.get("score", 0)
        try:
            score = int(float(score))
        except (TypeError, ValueError):
            score = 0
        score = max(0, min(100, score))

        feedback = _as_text(payload.get("feedback"))
        improvement = _as_text(payload.get("improvement"))
        mistakes = payload.get("common_mistakes", [])
        if not isinstance(mistakes, list):
            mistakes = []
        mistakes = [str(x).strip() for x in mistakes if str(x).strip()]

        if not feedback:
            feedback = "Answer reviewed. Add clearer reasoning and examples."
        if not improvement:
            improvement = "Revise your explanation with concrete steps and validate assumptions."

        return {
            "score": score,
            "feedback": feedback,
            "improvement": improvement,
            "common_mistakes": mistakes,
        }

    @staticmethod
    def _validate_hint(payload: dict[str, Any]) -> dict[str, Any]:
        hint = _as_text(payload.get("hint"))
        next_step_question = _as_text(payload.get("next_step_question"))
        if not hint:
            hint = "Break the problem into smaller steps and define key terms first."
        if not next_step_question:
            next_step_question = "Which single concept is most important to solve this task?"
        return {"hint": hint, "next_step_question": next_step_question}

    @staticmethod
    def _validate_progress(payload: dict[str, Any]) -> dict[str, Any]:
        attempted = payload.get("attempted", 0)
        avg_score = payload.get("avg_score", 0.0)
        last_topic = _as_text(payload.get("last_topic"))
        strengths = payload.get("strengths", [])
        weaknesses = payload.get("weaknesses", [])
        next_recommendation = _as_text(payload.get("next_recommendation"))

        try:
            attempted = int(attempted)
        except (TypeError, ValueError):
            attempted = 0
        try:
            avg_score = float(avg_score)
        except (TypeError, ValueError):
            avg_score = 0.0

        if not isinstance(strengths, list):
            strengths = []
        if not isinstance(weaknesses, list):
            weaknesses = []

        strengths = [str(x).strip() for x in strengths if str(x).strip()]
        weaknesses = [str(x).strip() for x in weaknesses if str(x).strip()]

        if not next_recommendation:
            next_recommendation = "Practice one more task and compare with your previous feedback."

        return {
            "attempted": attempted,
            "avg_score": round(avg_score, 2),
            "last_topic": last_topic,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "next_recommendation": next_recommendation,
        }

    @staticmethod
    def _validate_chat(payload: dict[str, Any]) -> dict[str, Any]:
        reply = _as_text(payload.get("reply"))
        if not reply:
            reply = "Let’s break your question into smaller parts and solve it step-by-step."
        return {"reply": reply}

    def generate_topic(self, interests: list[str]) -> dict[str, Any]:
        # norm_interests = _normalize_interests(interests)
        # interests_text = ", ".join(norm_interests) if norm_interests else "fast api learning"
        # chosen_interest = random.choice(norm_interests) if norm_interests else "fast api learning"
        # random_angles = [
        #     "fast api, authentication", "fast api schemas"
        # ]
        # chosen_angle = random.choice(random_angles)
        # return self.client.generate_json(
        #     system_prompt="You are a professional tutor. Always return strict JSON.",
        #     user_prompt=(
        #         "You are a professional tutor. Generate a structured topic explanation based on "
        #         f"user's interests: {interests_text}.\n"
        #         f"Focus interest: {chosen_interest}.\n"
        #         f"Use random angle: {chosen_angle}.\n"
        #         "Language must be English only.\n"
        #         "Explanation must be detailed (at least 5 clear sentences) and include:\n"
        #         "1) what it is, 2) why it matters, 3) key points, 4) one real-world example, 5) how to start.\n"
        #         "Return JSON ONLY: {\"topic_title\":\"...\",\"explanation\":\"...\"}"
        #     ),
        #     validator=self._validate_topic,
        #     temperature=0.2,
        # )

        return self.client.generate_json(system_prompt="fast api", user_prompt="authentication", validator=self._validate_topic)


    def generate_task(self, current_topic: str) -> dict[str, Any]:
        return self.client.generate_json(
            system_prompt="You are a tutor. Return strict JSON only.",
            user_prompt=(
                f"Create a practical learning task based on topic: {current_topic}.\n"
                "Return JSON ONLY: {\"task\":\"...\",\"task_type\":\"conceptual|practical|coding\",\"expected_answer_hint\":\"...\"}"
            ),
            validator=self._validate_task,
            temperature=0.25,
        )

    def evaluate_answer(self, *, current_task: str, user_answer: str, expected_answer_hint: str) -> dict[str, Any]:
        return self.client.generate_json(
            system_prompt="You are a strict but fair tutor. Return strict JSON only.",
            user_prompt=(
                "You are a strict but fair tutor. Evaluate the student answer. Give score 0-100. Be objective.\n"
                f"Task: {current_task}\n"
                f"Expected answer hint: {expected_answer_hint}\n"
                f"Student answer: {user_answer}\n"
                "Return JSON ONLY: {\"score\":0,\"feedback\":\"...\",\"improvement\":\"...\",\"common_mistakes\":[\"...\"]}"
            ),
            validator=self._validate_answer,
            temperature=0.1,
        )

    def give_hint(self, current_task: str) -> dict[str, Any]:
        return self.client.generate_json(
            system_prompt="You are a tutor. Give hint only, never full solution. Return strict JSON.",
            user_prompt=(
                "Give only a hint. Do not reveal the full solution.\n"
                f"Task: {current_task}\n"
                "Return JSON ONLY: {\"hint\":\"...\",\"next_step_question\":\"...\"}"
            ),
            validator=self._validate_hint,
            temperature=0.2,
        )

    # def summarize_progress(self, *, attempted: int, avg_score: float, last_topic: str, feedback_summaries: list[str]) -> dict[str, Any]:
    #     feedback_text = " | ".join(feedback_summaries) if feedback_summaries else "No attempts yet"
    #     return self.client.generate_json(
    #         system_prompt="You are a professional tutor. Return strict JSON only.",
    #         user_prompt=(
    #             "Summarize learning progress professionally.\n"
    #             f"attempted={attempted}, avg_score={avg_score}, last_topic={last_topic or 'N/A'}\n"
    #             f"last_feedback_summaries={feedback_text}\n"
    #             "Return JSON ONLY: {\"attempted\":0,\"avg_score\":0.0,\"last_topic\":\"...\",\"strengths\":[\"...\"],\"weaknesses\":[\"...\"],\"next_recommendation\":\"...\"}"
    #         ),
    #         validator=self._validate_progress,
    #         temperature=0.2,
    #     )

    # def generate_task(self, current_topic: str) -> dict[str, Any]:
    #     return self.client.generate_json(
    #         system_prompt="You are a tutor. Return strict JSON only.",
    #         user_prompt=(
    #             f"Create a practical learning task based on topic: {current_topic}.\n"
    #             "Return JSON ONLY: {\"task\":\"...\",\"task_type\":\"conceptual|practical|coding\",\"expected_answer_hint\":\"...\"}"
    #         ),
    #         validator=self._validate_task,
    #         temperature=0.25,
    #     )

    # def evaluate_answer(self, *, current_task: str, user_answer: str, expected_answer_hint: str) -> dict[str, Any]:
    #     return self.client.generate_json(
    #         system_prompt="You are a strict but fair tutor. Return strict JSON only.",
    #         user_prompt=(
    #             "You are a strict but fair tutor. Evaluate the student answer. Give score 0-100. Be objective.\n"
    #             f"Task: {current_task}\n"
    #             f"Expected answer hint: {expected_answer_hint}\n"
    #             f"Student answer: {user_answer}\n"
    #             "Return JSON ONLY: {\"score\":0,\"feedback\":\"...\",\"improvement\":\"...\",\"common_mistakes\":[\"...\"]}"
    #         ),
    #         validator=self._validate_answer,
    #         temperature=0.1,
    #     )

    # def give_hint(self, current_task: str) -> dict[str, Any]:
    #     return self.client.generate_json(
    #         system_prompt="You are a tutor. Give hint only, never full solution. Return strict JSON.",
    #         user_prompt=(
    #             "Give only a hint. Do not reveal the full solution.\n"
    #             f"Task: {current_task}\n"return self.client.generate_json
    #             "Return JSON ONLY: {\"hint\":\"...\",\"next_step_question\":\"...\"}"
    #         ),
    #         validator=self._validate_hint,
    #         temperature=0.2,
    #     )

    # def summarize_progress(self, *, attempted: int, avg_score: float, last_topic: str, feedback_summaries: list[str]) -> dict[str, Any]:
    #     feedback_text = " | ".join(feedback_summaries) if feedback_summaries else "No attempts yet"
    #     return self.client.generate_json(
    #         system_prompt="You are a professional tutor. Return strict JSON only.",
    #         user_prompt=(
    #             "Summarize learning progress professionally.\n"
    #             f"attempted={attempted}, avg_score={avg_score}, last_topic={last_topic or 'N/A'}\n"
    #             f"last_feedback_summaries={feedback_text}\n"
    #             "Return JSON ONLY: {\"attempted\":0,\"avg_score\":0.0,\"last_topic\":\"...\",\"strengths\":[\"...\"],\"weaknesses\":[\"...\"],\"next_recommendation\":\"...\"}"
    #         ),
    #         validator=self._validate_progress,
    #         temperature=0.2,
    #     )

    # def chat_reply(self, *, history: str, user_message: str, current_topic: str, current_task: str) -> dict[str, Any]:
    #     return self.client.generate_json(
    #         system_prompt="You are an AI tutor. Return strict JSON only.",
    #         user_prompt=(
    #             f"Current topic: {current_topic or 'N/A'}\n"
    #             f"Current task: {current_task or 'N/A'}\n"
    #             f"Recent history: {history or 'N/A'}\n"
    #             f"User message: {user_message}\n"
    #             "Return JSON ONLY: {\"reply\":\"...\"}"
    #         ),
    #         validator=self._validate_chat,
    #         temperature=0.35,
    #     )
        

    # def chat_reply(self, *, history: str, user_message: str, current_topic: str, current_task: str) -> dict[str, Any]:
    #     return self.client.generate_json(
    #         system_prompt="You are an AI tutor. Return strict JSON only.",
    #         user_prompt=(
    #             f"Current topic: {current_topic or 'N/A'}\n"
    #             f"Current task: {current_task or 'N/A'}\n"
    #             f"Recent history: {history or 'N/A'}\n"
    #             f"User message: {user_message}\n"
    #             "Return JSON ONLY: {\"reply\":\"...\"}"
    #         ),
    #         validator=self._validate_chat,
    #         temperature=0.35,
    #     )
