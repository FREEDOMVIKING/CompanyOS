from __future__ import annotations
import re

class SignalNormalizer:
    """304: normalize raw evidence into comparable text signals."""

    def normalize_text(self, text):
        text = re.sub(r"\s+", " ", str(text or "")).strip()
        return text

    def record(self, record):
        out = dict(record)
        out["title"] = self.normalize_text(out.get("title"))
        out["text"] = self.normalize_text(out.get("text"))
        return out
