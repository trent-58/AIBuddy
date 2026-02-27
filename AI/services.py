from .ai_client import call_ai
from .commands_processor import process_ai_command


class AIService:
    @staticmethod
    def process_command(message: str, context: str = "", interests=None, state=None):
        return process_ai_command(
            message=message,
            context=context,
            interests=interests,
            state=state,
        )

    @staticmethod
    def generate_duo_task(interests=None):
        interests_text = ", ".join(interests) if interests else "general topics"

        prompt = f"""
        Generate a collaborative discussion task for two students.
        Interests: {interests_text}

        Return JSON:
        {{
          "title": "short engaging title",
          "description": "clear discussion instructions"
        }}
        """
        return call_ai(prompt)

    @staticmethod
    def evaluate_discussion(submissions):
        discussion_text = "\n".join([s.content for s in submissions])

        prompt = f"""
        You are an AI judge evaluating a discussion between two students.

        Discussion:
        {discussion_text}

        Evaluate:
        - Collaboration
        - Depth
        - Clarity

        Return JSON:
        {{
          "score": number (0-10),
          "explanation": "short professional feedback"
        }}
        """
        return call_ai(prompt)
