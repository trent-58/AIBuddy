from __future__ import annotations

from collections import Counter

from .ai_client import call_ai


class OpenAITutorService:
    @staticmethod
    def _extract_text(payload: dict, keys: list[str], default: str) -> str:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return default

    @staticmethod
    def generate_topic(interests: list[str]) -> dict:
        # interests_text = ", ".join(interests) if interests else "general learning"
        # prompt = (
        #     "You are a professional tutor. Generate a structured topic explanation "
        #     f"based on user's interests: {interests_text}.\n"
        #     "Return JSON with keys: title, explanation."
        # )
        # result = call_ai(prompt)

        # title = OpenAITutorService._extract_text(
        #     result,
        #     ["title", "topic"],
        #     f"{(interests[0] if interests else 'General Learning').title()} Foundations",
        # )
        # explanation = OpenAITutorService._extract_text(
        #     result,
        #     ["explanation", "description", "message"],
        #     "Study key principles and connect them with one practical real-world example.",
        # )
        return {"title": "fast api", "explanation": "authentication"}

    @staticmethod
    def generate_task(current_topic: str) -> dict:
        prompt = (
            "Create a practical learning task based on topic: "
            f"{current_topic}.\n"
            "Task may be conceptual, practical, or coding exercise.\n"
            "Return JSON with keys: task, task_type."
        )
        result = call_ai(prompt)

        task = OpenAITutorService._extract_text(
            result,
            ["task", "question", "message"],
            f"Explain '{current_topic}' and provide one practical example from real-world projects.",
        )
        task_type = OpenAITutorService._extract_text(result, ["task_type", "type"], "conceptual")
        return {"task": task, "task_type": task_type}

    @staticmethod
    def evaluate_answer(current_task: str, user_answer: str) -> dict:
        prompt = (
            "You are a strict but fair tutor. Evaluate the student answer. "
            "Give score 0-100. Be objective.\n"
            f"Task: {current_task}\n"
            f"Answer: {user_answer}\n"
            "Return JSON: {score, feedback, improvement}."
        )
        result = call_ai(prompt)

        raw_score = result.get("score", 0)
        try:
            score = int(float(raw_score))
        except (TypeError, ValueError):
            score = min(95, max(40, len(user_answer.strip()) * 2))

        score = max(0, min(100, score))
        feedback = OpenAITutorService._extract_text(
            result,
            ["feedback", "explanation", "message"],
            "Reasonable attempt. Improve structure and add stronger technical detail.",
        )
        improvement = OpenAITutorService._extract_text(
            result,
            ["improvement", "next_step"],
            "Add one concrete example and explain the reasoning step-by-step.",
        )

        return {
            "score": score,
            "feedback": feedback,
            "improvement": improvement,
        }

    @staticmethod
    def help_hint(current_task: str) -> dict:
        prompt = (
            "Give only a hint. Do not reveal the full solution.\n"
            f"Task: {current_task}\n"
            "Return JSON with key: hint."
        )
        result = call_ai(prompt)
        hint = OpenAITutorService._extract_text(
            result,
            ["hint", "message", "feedback"],
            "Break the task into: definition, why it works, and one practical example.",
        )
        return {"hint": hint}

    @staticmethod
    def summarize_progress(total_tasks: int, average_score: float, weak_areas: list[str], last_topic: str) -> dict:
        weak_text = ", ".join(weak_areas) if weak_areas else "none detected"
        prompt = (
            "Summarize learning progress professionally.\n"
            f"Total tasks attempted: {total_tasks}\n"
            f"Average score: {average_score}\n"
            f"Weak areas: {weak_text}\n"
            f"Last topic studied: {last_topic or 'N/A'}\n"
            "Return JSON with key: summary"
        )
        result = call_ai(prompt)
        summary = OpenAITutorService._extract_text(
            result,
            ["summary", "message", "feedback"],
            f"You attempted {total_tasks} tasks with average score {average_score}. Focus on: {weak_text}.",
        )
        return {"summary": summary}

    @staticmethod
    def general_chat(context: str, user_message: str, current_topic: str, current_task: str) -> dict:
        prompt = (
            "You are an AI tutor in a study session.\n"
            f"Current topic: {current_topic or 'none'}\n"
            f"Current task: {current_task or 'none'}\n"
            f"Recent context:\n{context or 'N/A'}\n"
            f"User message: {user_message}\n"
            "Return JSON with key: reply"
        )
        result = call_ai(prompt)
        reply = OpenAITutorService._extract_text(
            result,
            ["reply", "message", "feedback", "raw"],
            "Good question. Clarify your goal, then we can break it into steps.",
        )
        return {"reply": reply}


def detect_weak_areas(feedback_texts: list[str]) -> list[str]:
    keywords = {
        "clarity": ["clarity", "clear", "unclear", "structure"],
        "accuracy": ["accuracy", "incorrect", "correct", "mistake", "error"],
        "depth": ["depth", "detail", "shallow", "deeper"],
        "examples": ["example", "real-world", "practical"],
    }

    scores = Counter()
    joined = " ".join(feedback_texts).lower()
    for area, words in keywords.items():
        for word in words:
            if word in joined:
                scores[area] += 1

    if not scores:
        return []

    return [name for name, _ in scores.most_common(3)]
