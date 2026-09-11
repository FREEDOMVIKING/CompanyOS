from __future__ import annotations
from collections import Counter

class TrendDetector:
    """309: repeated-signal detector across multiple evidence records."""

    def detect(self, problems):
        words = []
        for p in problems:
            for word in str(p.get("statement","")).lower().split():
                word = "".join(ch for ch in word if ch.isalnum())
                if len(word) >= 6:
                    words.append(word)
        return [{"signal": k, "count": v} for k, v in Counter(words).most_common(20) if v >= 2]
