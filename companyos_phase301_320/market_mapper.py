from __future__ import annotations
from collections import Counter

class MarketMapper:
    """307: lightweight market/theme mapping from research evidence."""

    def map(self, records):
        tokens = []
        stop = {
            "the","and","for","with","that","this","from","have","will","your",
            "are","was","were","into","their","they","you","but","not","can"
        }
        for r in records:
            for token in (str(r.get("title","")) + " " + str(r.get("text",""))).lower().split():
                token = "".join(ch for ch in token if ch.isalnum() or ch in "-_")
                if len(token) >= 5 and token not in stop:
                    tokens.append(token)
        return [{"theme": k, "mentions": v} for k, v in Counter(tokens).most_common(30)]
