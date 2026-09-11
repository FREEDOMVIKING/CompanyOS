class ResearchMoreMission:
    """531: create targeted follow-up research instructions for weak candidates."""

    def build(self, candidate):
        return {
            "mission_type":"research",
            "priority":0.7,
            "blocked_on":[],
            "context":{
                "focus_theme":candidate.get("theme"),
                "candidate_name":candidate.get("name"),
                "evidence_links":candidate.get("evidence_links",[])[:10],
                "research_goal":"increase source diversity, pain certainty, and commercial-intent evidence",
            }
        }
