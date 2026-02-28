import json

from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser


class PlainTextJSONParser(BaseParser):
    media_type = "text/plain"

    def parse(self, stream, media_type=None, parser_context=None):
        raw = stream.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        text = (raw or "").strip()
        if not text:
            return {}
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ParseError("Invalid JSON in text/plain body") from exc
        if not isinstance(payload, dict):
            raise ParseError("JSON body must be an object")
        return payload
