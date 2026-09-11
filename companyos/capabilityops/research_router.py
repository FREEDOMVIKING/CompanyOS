class ResearchRouter:
    def build_request(self, job):
        payload=job.get("payload",{})
        event=payload.get("event",{})
        query=payload.get("query") or event.get("payload",{}).get("signal") or payload.get("scope") or "general research"
        return {
            "query":query,
            "requirements":{
                "source_diversity":True,
                "citations":True,
                "freshness":"prefer_recent"
            }
        }
