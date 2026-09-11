from __future__ import annotations
import hashlib

class EvidenceDeduper:
    """305: stable duplicate detection for repeated research cycles."""

    def fingerprint(self, record):
        basis = "|".join([
            str(record.get("source", "")).strip().lower(),
            str(record.get("url", "")).strip().lower(),
            str(record.get("title", "")).strip().lower(),
            str(record.get("text", ""))[:500].strip().lower(),
        ])
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()

    def unique(self, records):
        seen, out = set(), []
        for record in records:
            fp = self.fingerprint(record)
            if fp in seen:
                continue
            seen.add(fp)
            item = dict(record)
            item["fingerprint"] = fp
            out.append(item)
        return out
