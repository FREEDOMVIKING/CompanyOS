class EvidenceRescoreEngine:
    """937-944: convert evidence quality into updated validation scores."""
    SOURCE_WEIGHTS = {
        "official": 1.00,
        "reputable_news": 0.85,
        "competitor_site": 0.75,
        "public_web": 0.65,
        "github": 0.70,
        "hacker_news": 0.45,
    }

    def score(self, packet):
        evidence = list((packet or {}).get("evidence") or [])
        if not evidence:
            return {
                "problem_evidence": 0.0,
                "pricing_validation": 0.0,
                "demand_evidence": 0.0,
                "alternative_evidence": 0.0,
                "weighted_evidence_quality": 0.0,
            }

        seen = set()
        totals = {"problem":0.0,"pricing":0.0,"demand":0.0,"alternatives":0.0}
        quality_total = 0.0
        usable = 0

        for e in evidence:
            if not isinstance(e, dict):
                continue
            key = e.get("url") or e.get("id") or str(e)
            if key in seen:
                continue
            seen.add(key)

            src = e.get("source_class","public_web")
            weight = float(self.SOURCE_WEIGHTS.get(src,0.5))
            freshness = float(e.get("freshness_score",1.0) or 1.0)
            freshness = max(0.25,min(1.0,freshness))
            contradiction = 0.7 if e.get("contradicted") else 1.0
            q = weight * freshness * contradiction
            quality_total += q
            usable += 1

            tags = set(e.get("tags",[]))
            for dim in totals:
                if dim in tags:
                    totals[dim] += q

            if e.get("willingness_to_pay_score"):
                totals["pricing"] += min(1.0,float(e.get("willingness_to_pay_score",0))) * 0.6

        denom = max(1.0, usable * 0.75)
        result = {
            "problem_evidence": round(min(1.0, totals["problem"]/denom),3),
            "pricing_validation": round(min(1.0, totals["pricing"]/denom),3),
            "demand_evidence": round(min(1.0, totals["demand"]/denom),3),
            "alternative_evidence": round(min(1.0, totals["alternatives"]/denom),3),
            "weighted_evidence_quality": round(min(1.0, quality_total/max(1,usable)),3),
        }
        return result

    def apply_to_validation(self, validation, packet):
        v = dict(validation or {})
        scores = dict(v.get("scores") or {})
        rescored = self.score(packet)
        scores.update(rescored)
        research_conf = float(scores.get("research_confidence", packet.get("confidence",0)) or 0)
        confidence = (
            research_conf*0.25
            + rescored["problem_evidence"]*0.25
            + rescored["pricing_validation"]*0.20
            + rescored["demand_evidence"]*0.20
            + rescored["weighted_evidence_quality"]*0.10
        )
        scores["validation_confidence"] = round(min(1.0,max(0.0,confidence)),3)
        v["scores"] = scores
        return v
