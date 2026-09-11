from __future__ import annotations
import os

class FetchBudget:
    """327: bounded live-fetch limits."""

    def limits(self):
        return {
            "max_sources": max(1, int(os.getenv("COMPANYOS_RESEARCH_MAX_SOURCES", "12"))),
            "max_records": max(5, int(os.getenv("COMPANYOS_RESEARCH_MAX_RECORDS", "80"))),
            "timeout_seconds": max(5, int(os.getenv("COMPANYOS_RESEARCH_TIMEOUT_SECONDS", "20"))),
        }
