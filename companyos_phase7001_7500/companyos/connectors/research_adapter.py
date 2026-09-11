class ResearchAdapter:
    def prepare(self, query, source_preferences=None):
        return {
            "capability":"research",
            "query":query,
            "source_preferences":list(source_preferences or ["official","reputable_news","public_web"]),
            "status":"prepared"
        }

    def normalize(self, provider_result):
        items=list((provider_result or {}).get("items",[]))
        return {
            "success":bool(items),
            "items":items,
            "evidence_count":len(items),
            "provider":(provider_result or {}).get("provider")
        }
