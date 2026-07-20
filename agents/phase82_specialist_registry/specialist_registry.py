import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase82"
STATE_FILE = MEMORY / "specialist_registry.json"
MEMORY.mkdir(parents=True, exist_ok=True)

DEFAULT_SPECIALISTS = {
    "research_agent": ["market_research", "evidence_analysis", "risk_discovery"],
    "strategy_agent": ["business_model", "positioning", "prioritization"],
    "builder_agent": ["implementation_planning", "technical_design", "testing"],
    "growth_agent": ["customer_acquisition", "pricing", "validation"],
    "finance_agent": ["unit_economics", "budget_modeling", "forecasting"],
    "operations_agent": ["process_design", "monitoring", "quality_control"],
    "ceo_agent": ["synthesis", "decision_support", "portfolio_review"],
}

def load():
    if not STATE_FILE.exists():
        data = {"phase": 82, "specialists": DEFAULT_SPECIALISTS}
        STATE_FILE.write_text(json.dumps(data, indent=2))
        return data
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        data = {"phase": 82, "specialists": DEFAULT_SPECIALISTS}
        STATE_FILE.write_text(json.dumps(data, indent=2))
        return data

def get(role):
    data = load()
    return {
        "success": role in data.get("specialists", {}),
        "status": "phase82_specialist_found" if role in data.get("specialists", {}) else "phase82_specialist_not_found",
        "role": role,
        "capabilities": data.get("specialists", {}).get(role, []),
    }

def status():
    data = load()
    return {
        "success": True,
        "status": "phase82_specialist_registry_status",
        "specialist_count": len(data.get("specialists", {})),
        "specialists": data.get("specialists", {}),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
