from __future__ import annotations

from .ai_client import call_ai


def _clamp_score(value, low=1.0, high=5.0) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 3.0
    return max(low, min(high, score))


def _mastery(avg: float) -> str:
    if avg >= 4.5:
        return "Advanced"
    if avg >= 3.5:
        return "Intermediate"
    if avg >= 2.5:
        return "Developing"
    return "Beginner"


def _default_state(state: dict | None) -> dict:
    merged = dict(state or {})
    merged.setdefault("topic", None)
    merged.setdefault("task", None)
    merged.setdefault("score_history", [])
    merged.setdefault("answers_count", 0)
    merged.setdefault("tasks_count", 0)
    return merged


def process_ai_command(
    message: str,
    context: str = "",
    interests: list[str] | None = None,
    state: dict | None = None,
):
    raw = (message or "").strip()
    if not raw:
        return {"type": "info", "message": "Message is empty."}

    safe_state = _default_state(state)
    safe_interests = [x for x in (interests or []) if isinstance(x, str) and x.strip()]
    interests_text = ", ".join(safe_interests) if safe_interests else "general learning"

    if not raw.startswith("#"):
        return {
            "type": "info",
            "message": "AI only works with commands: #help, #topic, #task, #answer <text>, #progress",
            "state": safe_state,
        }

    parts = raw.split(maxsplit=1)
    command = parts[0].lower()
    payload = parts[1].strip() if len(parts) > 1 else ""

    if command == "#help":
        return {
            "type": "help",
            "message": (
                "Flow: 1) #topic -> 2) #task -> 3) #answer <your answer> -> 4) #progress. "
                "Repeat this loop for strong mastery."
            ),
            "state": safe_state,
        }

    if command == "#progress":
        history = safe_state.get("score_history", [])
        avg = sum(history) / len(history) if history else 0.0
        return {
            "type": "progress",
            "answers_count": safe_state.get("answers_count", 0),
            "tasks_count": safe_state.get("tasks_count", 0),
            "average_score": round(avg, 2),
            "mastery": _mastery(avg),
            "message": f"Progress: tasks={safe_state.get('tasks_count', 0)}, answers={safe_state.get('answers_count', 0)}, avg={round(avg, 2)}/5",
            "state": safe_state,
        }

    if command == "#topic":
        prompt = f"""
Generate one study topic based on learner interests.
Interests: {interests_text}
Extra user request: {payload or 'none'}

Return ONLY JSON:
{{
  "type": "topic",
  "title": "short title",
  "explanation": "2-3 sentence simple explanation"
}}
"""
        result = call_ai(prompt)

        title = result.get("title") or result.get("topic") or f"{(safe_interests[0] if safe_interests else 'Study')} Basics"
        explanation = result.get("explanation") or result.get("description") or "Start with key concepts and discuss one practical example."

        safe_state["topic"] = {
            "title": title,
            "explanation": explanation,
            "from_interests": safe_interests,
        }
        safe_state["task"] = None

        return {
            "type": "topic",
            "title": title,
            "explanation": explanation,
            "next_step": "Now run #task to get a focused challenge.",
            "state": safe_state,
        }

    if command == "#task":
        active_topic = (safe_state.get("topic") or {}).get("title") or payload
        if not active_topic:
            return {
                "type": "info",
                "message": "First run #topic to generate a topic, then use #task.",
                "state": safe_state,
            }

        prompt = f"""
Generate one practical study task based on topic: {active_topic}
Learner interests: {interests_text}
Optional context:
{context or 'none'}

Return ONLY JSON:
{{
  "type": "task",
  "question": "clear single task question"
}}
"""
        result = call_ai(prompt)

        question = result.get("question") or result.get("task") or f"Explain '{active_topic}' with one real-world example."

        safe_state["task"] = {"question": question, "topic": active_topic}
        safe_state["tasks_count"] = int(safe_state.get("tasks_count", 0)) + 1

        return {
            "type": "task",
            "topic": active_topic,
            "question": question,
            "rubric": "Good answer should: define concept, explain why, give one concrete example.",
            "next_step": "Reply with #answer <your answer>",
            "state": safe_state,
        }

    if command == "#answer":
        active_task = (safe_state.get("task") or {}).get("question")
        if not active_task:
            return {
                "type": "info",
                "message": "No active task. Use #task first.",
                "state": safe_state,
            }

        if not payload:
            return {
                "type": "info",
                "message": "Use format: #answer <your answer>",
                "state": safe_state,
            }

        prompt = f"""
Evaluate student's answer for this task.
Task: {active_task}
Answer: {payload}

Score from 1 to 5 and provide short feedback.
Return ONLY JSON:
{{
  "type": "evaluation",
  "score": 1-5,
  "feedback": "short feedback"
}}
"""
        result = call_ai(prompt)

        score = _clamp_score(result.get("score", 3))
        feedback = result.get("feedback") or result.get("explanation") or "Good attempt. Add more detail and one concrete example."

        history = safe_state.get("score_history", [])
        history.append(score)
        safe_state["score_history"] = history[-20:]
        safe_state["answers_count"] = int(safe_state.get("answers_count", 0)) + 1

        avg = sum(safe_state["score_history"]) / len(safe_state["score_history"])

        return {
            "type": "evaluation",
            "task": active_task,
            "score": score,
            "feedback": feedback,
            "average_score": round(avg, 2),
            "mastery": _mastery(avg),
            "next_step": "Use #task for a new challenge or #progress to see learning status.",
            "state": safe_state,
        }

    return {
        "type": "info",
        "message": "Unknown command. Use #help, #topic, #task, #answer <text>, #progress",
        "state": safe_state,
    }
