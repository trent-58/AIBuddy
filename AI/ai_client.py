import json
import os
import re

try:
    from openai import OpenAI, OpenAIError
except Exception:  # pragma: no cover
    OpenAI = None

    class OpenAIError(Exception):
        pass


def _fallback(prompt: str):
    p = prompt.lower()
    interests_match = re.search(r"Interests:\s*(.+)", prompt, re.IGNORECASE)
    raw_interests = interests_match.group(1).strip() if interests_match else ""
    first_interest = raw_interests.split(",")[0].strip() if raw_interests else "Study"

    if '"type": "topic"' in p and '"title"' in p and '"explanation"' in p:
        interest_title = first_interest.title() if first_interest else "Study"
        return {
            "type": "topic",
            "title": f"{interest_title} Foundations",
            "explanation": f"Learn the core ideas of {first_interest or 'this topic'} and connect them to one practical real-world case.",
        }
    if '"score"' in p and '"explanation"' in p:
        return {"score": 7, "explanation": "Good discussion. Add more concrete examples."}
    if '"title"' in p and '"description"' in p:
        return {
            "title": "Collaborative Learning Task",
            "description": "Explain one key concept each, give real examples, and summarize together.",
        }
    if '"question"' in p:
        return {"type": "task", "question": "Give one real-world example and explain why it works."}
    if '"feedback"' in p:
        return {"type": "evaluation", "score": 4, "feedback": "Nice effort. Clarify your reasoning."}
    return {"message": "Great point. Can you add one practical example?"}


def call_ai(prompt: str, temperature: float = 0.4):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or OpenAI is None:
        return _fallback(prompt)

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI tutor. Always return valid JSON only.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=temperature,
        )

        content = response.choices[0].message.content
        if not content:
            return _fallback(prompt)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw": content}

    except OpenAIError as e:
        return {
            "error": "AI unavailable",
            "message": str(e),
        }
