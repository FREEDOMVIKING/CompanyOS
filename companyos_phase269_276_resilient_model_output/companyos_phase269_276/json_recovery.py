from __future__ import annotations
import ast
import json
import re
from typing import Any, Dict, List

class JsonRecovery:
    """270: recover structured JSON from fences, prose, or near-JSON output."""

    def candidates(self, text: str) -> List[str]:
        text = (text or "").strip()
        items = []

        if text:
            items.append(text)

        fenced = re.findall(r"```(?:json)?\\s*(.*?)```", text, flags=re.I | re.S)
        items.extend(x.strip() for x in fenced if x.strip())

        # Balanced-ish outer object candidates.
        starts = [m.start() for m in re.finditer(r"\\{", text)]
        for start in starts:
            depth = 0
            in_string = False
            escape = False
            for i in range(start, len(text)):
                ch = text[i]
                if in_string:
                    if escape:
                        escape = False
                    elif ch == "\\\\":
                        escape = True
                    elif ch == '"':
                        in_string = False
                    continue

                if ch == '"':
                    in_string = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        items.append(text[start:i+1])
                        break

        deduped = []
        seen = set()
        for item in items:
            item = item.strip()
            if item and item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped

    def parse(self, text: str) -> Dict[str, Any]:
        errors = []

        for candidate in self.candidates(text):
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return {
                        "success": True,
                        "data": data,
                        "method": "json",
                        "candidate": candidate,
                    }
            except Exception as exc:
                errors.append(f"json:{type(exc).__name__}")

            # Conservative Python-literal fallback for single quotes/trailing commas.
            try:
                data = ast.literal_eval(candidate)
                if isinstance(data, dict):
                    return {
                        "success": True,
                        "data": data,
                        "method": "literal_eval",
                        "candidate": candidate,
                    }
            except Exception as exc:
                errors.append(f"literal:{type(exc).__name__}")

            # Small repair pass: remove trailing commas before ] or }.
            repaired = re.sub(r",\\s*([}\\]])", r"\\1", candidate)
            if repaired != candidate:
                try:
                    data = json.loads(repaired)
                    if isinstance(data, dict):
                        return {
                            "success": True,
                            "data": data,
                            "method": "trailing_comma_repair",
                            "candidate": repaired,
                        }
                except Exception as exc:
                    errors.append(f"repair:{type(exc).__name__}")

        return {
            "success": False,
            "reason": "json_recovery_failed",
            "errors": errors[-12:],
        }
