class QueryRouter:
    """748: route research queries by intent/source fit."""
    def route(self, query_type):
        mapping = {
            "technical": ["github", "official_docs", "public_web"],
            "market": ["public_web", "news", "hacker_news"],
            "competitor": ["public_web", "news", "github"],
            "pricing": ["public_web", "competitor_sites", "news"],
            "regulatory": ["official_sources", "public_web"],
        }
        return mapping.get(query_type, ["public_web", "hacker_news", "local_cache"])
