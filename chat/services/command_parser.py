from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_COMMANDS = {"topic", "task", "answer", "help", "progress"}


@dataclass(frozen=True)
class ParsedCommand:
    name: str
    argument: str



def parse_command(content: str) -> ParsedCommand | None:
    text = (content or "").strip()
    if not text.startswith("#"):
        return None

    body = text[1:].strip()
    if not body:
        return ParsedCommand(name="", argument="")

    parts = body.split(maxsplit=1)
    name = parts[0].lower().strip()
    argument = parts[1].strip() if len(parts) > 1 else ""

    if name not in SUPPORTED_COMMANDS:
        return ParsedCommand(name="unknown", argument=argument)

    return ParsedCommand(name=name, argument=argument)
