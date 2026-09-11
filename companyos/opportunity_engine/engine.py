
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_WEIGHTS = {
    "demand": 0.28,
    "trend": 0.16,
    "profit": 0.24,
    "risk": 0.16,
    "evidence": 0.16,
}

def read_json(path, default):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return default

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".")
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def append_json(path, item, limit=5000):
    rows = read_json(path, [])
    if not isinstance(rows, list):
        rows = []
    rows.append(item)
    write_json(path, rows[-limit:])

def clamp(value):
    return max(0.0, min(1.0, float(value)))

def research_plan(title):
    return {
        "topic": title,
        "questions": [
            "Who experiences this problem?",
            "How often does it happen?",
            "What is currently paid to solve it?",
            "Which competitors exist?",
            "What blocks adoption?",
        ],
        "source_requirements": [
            "customer interviews",
            "competitor websites",
            "pricing pages",
            "industry reports",
        ],
        "status": "waiting_for_provider",
    }

def evidence_summary(evidence):
    clean = [str(x).strip() for x in evidence if str(x).strip()]
    return {
        "evidence_count": len(clean),
        "strength": round(min(1.0, len(clean) / 8.0), 4),
        "summary": clean[:10],
        "fact_status": "user_or_provider_supplied",
    }

def competitor_analysis(competitors):
    if not competitors:
        return {
            "count": 0,
            "average_price": 0.0,
            "gaps": ["competitor_research_required"],
            "intensity": 0.2,
        }
    prices = [float(x.get("price", 0) or 0) for x in competitors if x.get("price") is not None]
    gaps = []
    for field in ["automation", "mobile", "support", "integration", "price_transparency"]:
        if not any(bool(c.get(field)) for c in competitors):
            gaps.append(field)
    return {
        "count": len(competitors),
        "average_price": round(sum(prices) / len(prices), 2) if prices else 0.0,
        "gaps": gaps,
        "intensity": round(min(1.0, 0.2 + 0.12 * len(competitors)), 4),
    }

def demand_estimate(signals, evidence_strength):
    search = float(signals.get("search_interest", 0.5) or 0.5)
    pain = float(signals.get("pain_severity", 0.5) or 0.5)
    frequency = float(signals.get("problem_frequency", 0.5) or 0.5)
    willingness = float(signals.get("willingness_to_pay", 0.5) or 0.5)
    return round(clamp(0.25*search + 0.30*pain + 0.20*frequency + 0.15*willingness + 0.10*evidence_strength), 4)

def trend_estimate(signals):
    score = clamp(
        0.40 * float(signals.get("growth", 0.5) or 0.5)
        + 0.35 * float(signals.get("adoption", 0.5) or 0.5)
        + 0.25 * float(signals.get("momentum", 0.5) or 0.5)
    )
    label = "rising" if score >= 0.65 else "stable" if score >= 0.4 else "declining"
    return {"score": round(score, 4), "label": label}

def profitability(assumptions, demand):
    price = float(assumptions.get("price", 100) or 100)
    customers = float(assumptions.get("monthly_customers", 10) or 10)
    variable = float(assumptions.get("variable_cost_per_customer", 20) or 20)
    fixed = float(assumptions.get("monthly_fixed_cost", 500) or 500)
    adjusted = customers * (0.5 + demand)
    revenue = price * adjusted
    cost = fixed + variable * adjusted
    profit = revenue - cost
    margin = profit / revenue if revenue else 0.0
    return {
        "monthly_revenue": round(revenue, 2),
        "monthly_cost": round(cost, 2),
        "monthly_profit": round(profit, 2),
        "margin": round(margin, 4),
        "annual_revenue": round(revenue * 12, 2),
        "annual_profit": round(profit * 12, 2),
    }

def risk_analysis(demand, trend, competition, forecast):
    risks = []
    if demand < 0.45:
        risks.append("weak_demand")
    if trend["label"] == "declining":
        risks.append("declining_market")
    if competition["intensity"] > 0.75:
        risks.append("intense_competition")
    if forecast["margin"] < 0.20:
        risks.append("thin_margin")
    return {
        "score": round(min(1.0, 0.15 + 0.20 * len(risks)), 4),
        "risks": risks or ["normal_execution_risk"],
    }

def product_ideas(title, problem, customer):
    base = title.strip() or problem.strip() or "New Venture"
    return [
        {"name": base + " Assistant", "type": "software_service", "customer": customer, "mvp": ["intake", "automation", "reporting"]},
        {"name": base + " Managed Service", "type": "service", "customer": customer, "mvp": ["assessment", "delivery", "monthly review"]},
        {"name": base + " Toolkit", "type": "digital_product", "customer": customer, "mvp": ["templates", "calculator", "guide"]},
    ]

def pricing(demand, competitor_average):
    anchor = competitor_average if competitor_average > 0 else 99.0
    multiplier = 1.15 if demand >= 0.7 else 1.0 if demand >= 0.45 else 0.8
    return {
        "entry": round(anchor * 0.5 * multiplier, 2),
        "core": round(anchor * multiplier, 2),
        "premium": round(anchor * 2.0 * multiplier, 2),
        "model": "monthly_or_project_based",
    }

def adaptive_weights(history):
    weights = dict(DEFAULT_WEIGHTS)
    if any(x.get("outcome") == "success" for x in history):
        weights["evidence"] += 0.02
        weights["demand"] += 0.02
    if any(x.get("outcome") == "failure" for x in history):
        weights["risk"] += 0.04
        weights["profit"] -= 0.02
    total = sum(weights.values())
    return {k: round(v / total, 4) for k, v in weights.items()}

def opportunity_score(demand, trend, forecast, risk, evidence_strength, weights):
    normalized_profit = (max(-1.0, min(1.0, forecast["margin"])) + 1.0) / 2.0
    value = (
        weights["demand"] * demand
        + weights["trend"] * trend["score"]
        + weights["profit"] * normalized_profit
        + weights["risk"] * (1.0 - risk["score"])
        + weights["evidence"] * evidence_strength
    )
    return round(clamp(value), 4)

def executive_decision(score, evidence, forecast, risk):
    blockers = []
    if evidence["strength"] < 0.4:
        blockers.append("collect_more_evidence")
    if forecast["monthly_profit"] <= 0:
        blockers.append("revise_economics")
    if risk["score"] >= 0.6:
        blockers.append("reduce_risk")
    if score >= 0.72 and not blockers:
        action = "advance_to_build"
    elif score >= 0.50:
        action = "advance_to_validation"
    elif score >= 0.35:
        action = "research_more"
    else:
        action = "archive"
    return {"action": action, "score": score, "blockers": blockers}

class OpportunityEngine:
    def __init__(self, home=None):
        self.home = Path(home or os.environ.get("COMPANYOS_HOME", str(Path.home() / "companyos")))
        self.runtime = self.home / "companyos_runtime" / "opportunity_engine"
        self.runtime.mkdir(parents=True, exist_ok=True)

    def add(self, title, problem="", customer=""):
        item = {
            "opportunity_id": str(uuid.uuid4()),
            "title": title,
            "problem": problem,
            "customer": customer,
            "evidence": [],
            "competitors": [],
            "market_signals": {},
            "assumptions": {},
            "status": "discovered",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        append_json(self.runtime / "opportunities.json", item)
        return item

    def evaluate(self, opportunity):
        evidence = evidence_summary(opportunity.get("evidence", []))
        competition = competitor_analysis(opportunity.get("competitors", []))
        demand = demand_estimate(opportunity.get("market_signals", {}), evidence["strength"])
        trend = trend_estimate(opportunity.get("market_signals", {}))
        forecast = profitability(opportunity.get("assumptions", {}), demand)
        risk = risk_analysis(demand, trend, competition, forecast)
        weights = adaptive_weights(read_json(self.runtime / "outcomes.json", []))
        score = opportunity_score(demand, trend, forecast, risk, evidence["strength"], weights)
        ideas = product_ideas(opportunity["title"], opportunity.get("problem", ""), opportunity.get("customer", ""))
        prices = pricing(demand, competition["average_price"])
        swot = {
            "strengths": ["structured automation", "repeatable delivery"],
            "weaknesses": ["assumptions_need_validation"],
            "opportunities": competition["gaps"] + [trend["label"] + "_market"],
            "threats": ["competitor_response", "customer_acquisition_cost", "execution_delay"],
        }
        marketing = {
            "positioning": f"Help {opportunity.get('customer') or 'target customers'} solve {opportunity.get('problem') or 'a costly recurring problem'} faster.",
            "channels": ["direct outreach", "content", "partnerships", "search"],
            "launch_sequence": ["interview 10 prospects", "run landing-page test", "close pilot customers", "measure retention"],
        }
        decision = executive_decision(score, evidence, forecast, risk)
        business_plan = {
            "executive_summary": f"Validate and launch {opportunity['title']}.",
            "problem": opportunity.get("problem"),
            "customer": opportunity.get("customer"),
            "recommended_product": ideas[0],
            "pricing": prices,
            "go_to_market": marketing,
            "financial_projection": forecast,
            "risk": risk,
            "swot": swot,
            "milestones": [
                "complete customer discovery",
                "validate willingness to pay",
                "build minimum viable offer",
                "launch pilot",
                "review unit economics",
                "scale or stop",
            ],
        }
        return {
            "opportunity_id": opportunity["opportunity_id"],
            "title": opportunity["title"],
            "research_plan": research_plan(opportunity["title"]),
            "evidence": evidence,
            "competitors": competition,
            "demand": demand,
            "trend": trend,
            "forecast": forecast,
            "product_ideas": ideas,
            "pricing": prices,
            "marketing": marketing,
            "risk": risk,
            "swot": swot,
            "weights": weights,
            "score": score,
            "decision": decision,
            "business_plan": business_plan,
        }

    def run_cycle(self):
        opportunities = read_json(self.runtime / "opportunities.json", [])
        if not opportunities:
            self.add(
                "AI estimating for small contractors",
                "Slow manual estimating",
                "small construction contractors",
            )
            opportunities = read_json(self.runtime / "opportunities.json", [])
        ranking = sorted((self.evaluate(x) for x in opportunities), key=lambda x: x["score"], reverse=True)
        pipeline = [
            {
                "opportunity_id": item["opportunity_id"],
                "title": item["title"],
                "score": item["score"],
                "stage": item["decision"]["action"],
            }
            for item in ranking
        ]
        snapshot = {
            "phase": "23001-25000",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "opportunity_count": len(ranking),
            "ranking": ranking,
            "pipeline": pipeline,
        }
        write_json(self.runtime / "latest_snapshot.json", snapshot)
        write_json(self.runtime / "ranking.json", ranking)
        write_json(self.runtime / "pipeline.json", pipeline)
        return snapshot
