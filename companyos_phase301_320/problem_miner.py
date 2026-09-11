from __future__ import annotations
import re

class ProblemMiner:
    """306: extract likely pain/problem statements from evidence."""

    MARKERS = (
        "problem","pain","frustrat","difficult","expensive","slow","manual",
        "waste","struggle","complain","inefficient","time-consuming","broken"
    )

    def mine(self, records):
        problems = []
        for record in records:
            text = f"{record.get('title','')}. {record.get('text','')}"
            sentences = re.split(r"(?<=[.!?])\s+", text)
            for sentence in sentences:
                low = sentence.lower()
                if any(marker in low for marker in self.MARKERS):
                    problems.append({
                        "statement": sentence.strip()[:600],
                        "source": record.get("source"),
                        "url": record.get("url"),
                        "fingerprint": record.get("fingerprint"),
                    })
        return problems
