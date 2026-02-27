from __future__ import annotations

import json
import os
import time
from typing import Any, Callable

from openai import OpenAI, OpenAIError


class OpenAIClientError(Exception):
    pass


class OpenAIClient:
    def __init__(self, *, model: str | None = None, timeout: float = 30.0, max_retries: int = 2):
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise OpenAIClientError("OPENAI_API_KEY is not configured")

        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_retries = max_retries

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        validator: Callable[[dict[str, Any]], dict[str, Any]],
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
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
                    raise OpenAIClientError("OpenAI returned empty response")

                try:
                    payload = json.loads(content)
                except json.JSONDecodeError as exc:
                    raise OpenAIClientError(f"OpenAI returned invalid JSON: {exc}") from exc

                if not isinstance(payload, dict):
                    raise OpenAIClientError("OpenAI JSON is not an object")

                return validator(payload)

            except (OpenAIError, OpenAIClientError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(0.4 * (attempt + 1))
                    continue
                break

        raise OpenAIClientError(f"OpenAI call failed after retries: {last_error}")
