from __future__ import annotations

class PublicSourcePack:
    """355: no-secret public starter sources for first real discovery cycles."""

    def describe(self):
        return {
            "sources": [
                {
                    "name": "Hacker News official API",
                    "type": "hackernews",
                    "enabled": True,
                    "priority": 0.8,
                    "category": "technology_and_business_signals",
                    "requires_api_key": False,
                },
                {
                    "name": "GitHub public issue search",
                    "type": "github_issues",
                    "enabled": True,
                    "priority": 0.9,
                    "category": "software_customer_pain",
                    "requires_api_key": False,
                },
            ]
        }
