import json

def prioritize(projects):
    scored = []
    for p in projects or []:
        revenue = float(p.get("revenue", 0))
        cost = float(p.get("cost", 0))
        health = p.get("health", "unknown")
        health_bonus = {"good": 20, "healthy": 20, "warning": 5, "poor": -20}.get(health, 0)
        score = (revenue - cost) + health_bonus
        item = dict(p)
        item["priority_score"] = round(score, 2)
        scored.append(item)
    scored.sort(key=lambda x: x["priority_score"], reverse=True)
    return {
        "success": True,
        "status": "phase88_portfolio_prioritized",
        "projects": scored,
    }

def status():
    return {"success": True, "status": "phase88_portfolio_prioritizer_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
