from __future__ import annotations
from typing import Any, List

class ResponseExtractor:
    """269: collect likely text payloads from varied model/provider responses."""

    def extract(self, payload: Any) -> List[str]:
        out = []

        if isinstance(payload, str):
            out.append(payload)

        elif isinstance(payload, dict):
            for key in ("content", "text", "output", "response", "message"):
                value = payload.get(key)
                if isinstance(value, str):
                    out.append(value)
                elif isinstance(value, dict):
                    for subkey in ("content", "text"):
                        sub = value.get(subkey)
                        if isinstance(sub, str):
                            out.append(sub)

            choices = payload.get("choices")
            if isinstance(choices, list):
                for choice in choices:
                    if isinstance(choice, dict):
                        msg = choice.get("message")
                        if isinstance(msg, dict):
                            content = msg.get("content")
                            if isinstance(content, str):
                                out.append(content)
                        text = choice.get("text")
                        if isinstance(text, str):
                            out.append(text)

        deduped = []
        seen = set()
        for item in out:
            item = item.strip()
            if item and item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped
