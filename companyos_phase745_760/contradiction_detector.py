class ContradictionDetector:
    """753: detect simple opposing claims on same topic."""
    def detect(self, claims):
        contradictions=[]
        by_topic={}
        for c in claims or []:
            topic=c.get("topic")
            stance=c.get("stance")
            if not topic or stance is None:
                continue
            by_topic.setdefault(topic,set()).add(str(stance).lower())
        for topic, stances in by_topic.items():
            if "positive" in stances and "negative" in stances:
                contradictions.append(topic)
            if "true" in stances and "false" in stances:
                contradictions.append(topic)
        return {"has_contradictions":bool(contradictions),"topics":sorted(set(contradictions))}
