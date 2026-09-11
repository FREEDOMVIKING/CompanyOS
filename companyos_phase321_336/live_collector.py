from __future__ import annotations
from .http_client import ResearchHttpClient
from .source_router import SourceRouter
from .fetch_budget import FetchBudget
from .provenance import Provenance

class LiveCollector:
    """329: collect records from explicitly configured live sources."""

    def __init__(self):
        limits = FetchBudget().limits()
        self.client = ResearchHttpClient(timeout=limits["timeout_seconds"])
        self.router = SourceRouter()
        self.provenance = Provenance()
        self.limits = limits

    def collect(self, sources):
        records, errors = [], []

        enabled = [s for s in sources if s.get("enabled", True)]
        for source in enabled[:self.limits["max_sources"]]:
            try:
                response = self.client.get(source["url"], headers=source.get("headers"))
                parsed = self.router.parse(response["body"], source)
                for record in parsed:
                    records.append(self.provenance.attach(record, source))
                    if len(records) >= self.limits["max_records"]:
                        break
            except Exception as exc:
                errors.append({
                    "source": source.get("name"),
                    "url": source.get("url"),
                    "error": f"{type(exc).__name__}:{exc}",
                })

            if len(records) >= self.limits["max_records"]:
                break

        return {"records": records, "errors": errors}
