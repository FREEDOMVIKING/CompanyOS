from typing import Dict, List

def portfolio_health(ventures: List[Dict]) -> Dict:
    if not ventures:
        return {"score":0.0,"healthy":0,"attention":0,"critical":0}
    scores=[]
    healthy=attention=critical=0
    for v in ventures:
        score=float(v.get("health_score",0) or 0)
        scores.append(score)
        if score >= 0.7: healthy += 1
        elif score >= 0.4: attention += 1
        else: critical += 1
    return {
        "score":round(sum(scores)/len(scores),4),
        "healthy":healthy,
        "attention":attention,
        "critical":critical,
    }

def rank_opportunities(ventures: List[Dict]) -> List[Dict]:
    ranked=[]
    for v in ventures:
        priority=float(v.get("priority_score",0) or 0)
        health=float(v.get("health_score",0) or 0)
        confidence=float(v.get("confidence",0.5) or 0.5)
        risk=float(v.get("risk",0.5) or 0.5)
        score=0.35*priority+0.25*health+0.25*confidence+0.15*(1-risk)
        ranked.append({
            "venture_id":v.get("venture_id"),
            "name":v.get("name"),
            "opportunity_score":round(score,4),
            "recommended_posture":_posture(score,risk),
        })
    return sorted(ranked,key=lambda x:x["opportunity_score"],reverse=True)

def allocate_shared_resources(ventures: List[Dict], total_capacity: float=1.0) -> List[Dict]:
    weights=[]
    for v in ventures:
        weight=max(0.01,float(v.get("priority_score",0) or 0)+float(v.get("health_score",0) or 0))
        weights.append((v,weight))
    total=sum(w for _,w in weights) or 1.0
    return [{
        "venture_id":v.get("venture_id"),
        "capacity_share":round(total_capacity*w/total,4)
    } for v,w in weights]

def _posture(score,risk):
    if score >= 0.75 and risk <= 0.45: return "accelerate"
    if score >= 0.5: return "invest_selectively"
    if risk >= 0.7: return "contain_risk"
    return "validate"
