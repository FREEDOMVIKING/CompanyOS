class QueryTransformer:
    """779: adapt query shape per provider."""
    def transform(self, query, provider):
        q = str(query or "").strip()
        if provider == "github":
            return {"q": q, "type": "issues_code_repos"}
        if provider == "hacker_news":
            return {"q": q, "type": "discussion_signal"}
        if provider == "public_web":
            return {"q": q, "type": "web_search"}
        if provider == "official_sources":
            return {"q": q, "type": "official_only"}
        return {"q": q, "type": "generic"}
