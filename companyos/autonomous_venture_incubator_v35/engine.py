
import json, os, tempfile, hashlib
from pathlib import Path
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def read_json(path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, default=str)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

class AutonomousVentureIncubatorV35:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/autonomous_venture_incubator_v35_1450001_1500000"
        self.records = self.home / "venture_incubator_records_v35"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

    def current_portfolio(self):
        state = read_json(self.live / "portfolio_orchestrator_v34_live.json", {})
        return state.get("ventures", []) or []

    def current_categories(self):
        cats = set()
        for v in self.current_portfolio():
            name = (v.get("name") or "").lower()
            if "template" in name:
                cats.add("digital_templates")
            if "construction" in name:
                cats.add("construction")
            if "service" in name:
                cats.add("services")
            if "software" in name or "app" in name:
                cats.add("software")
        return cats

    def internal_signals(self):
        signals = []
        for fn in [
            "internet_opportunity_hunter_v27_live.json",
            "autonomous_marketing_acquisition_v31_live.json",
            "autonomous_finance_treasury_v30_live.json",
            "autonomous_business_operations_v32_live.json",
        ]:
            d = read_json(self.live / fn, {})
            if d:
                signals.append({"source": fn, "data": d})
        return signals

    def generate_candidates(self):
        existing_names = {v.get("name") for v in self.current_portfolio()}
        categories = self.current_categories()
        ideas = [
            {
                "name": "AI Proposal Generator for Small Contractors",
                "category": "construction_software",
                "model": "subscription",
                "problem": "Small contractors lose time writing estimates and proposals manually.",
                "offer": "Generate polished proposals, scopes, and follow-up drafts from job details.",
                "base_demand": 82, "base_margin": 90, "base_readiness": 78
            },
            {
                "name": "Local Service Lead Intake Automation",
                "category": "local_services",
                "model": "subscription",
                "problem": "Small service companies miss calls and fail to follow up consistently.",
                "offer": "Lead capture, qualification, quote intake, and follow-up workflow.",
                "base_demand": 84, "base_margin": 86, "base_readiness": 80
            },
            {
                "name": "Micro Business SOP Library",
                "category": "digital_products",
                "model": "digital_bundle",
                "problem": "Small businesses often lack repeatable operating procedures.",
                "offer": "Role-based SOP templates, onboarding checklists, and process packs.",
                "base_demand": 74, "base_margin": 96, "base_readiness": 92
            },
            {
                "name": "Mobile Jobsite Daily Report Assistant",
                "category": "construction_software",
                "model": "subscription",
                "problem": "Field crews need faster daily reports and documentation.",
                "offer": "Convert short field notes into structured daily reports and action items.",
                "base_demand": 80, "base_margin": 88, "base_readiness": 76
            },
            {
                "name": "Customer Follow-up Message Pack Generator",
                "category": "sales_automation",
                "model": "subscription",
                "problem": "Small businesses fail to consistently follow up with warm leads.",
                "offer": "Generate personalized follow-up sequences and CRM-ready drafts.",
                "base_demand": 78, "base_margin": 91, "base_readiness": 84
            },
        ]

        candidates = []
        for idea in ideas:
            if idea["name"] in existing_names:
                continue

            diversification = 10
            if idea["category"] in categories:
                diversification = 2

            validation = idea["base_demand"]
            profitability = idea["base_margin"]
            readiness = idea["base_readiness"]

            overall = round(
                validation * 0.40 +
                profitability * 0.30 +
                readiness * 0.20 +
                diversification * 0.10, 2
            )

            if overall >= 82:
                stage = "INCUBATE_PRIORITY"
            elif overall >= 72:
                stage = "VALIDATE"
            else:
                stage = "WATCHLIST"

            candidate_id = hashlib.sha256(idea["name"].encode()).hexdigest()[:16]

            candidates.append({
                "venture_id": candidate_id,
                **idea,
                "validation_score": validation,
                "profitability_score": profitability,
                "execution_readiness_score": readiness,
                "diversification_score": diversification,
                "overall_score": overall,
                "incubator_stage": stage,
                "external_launch_approved": False,
                "capital_committed_usd": 0,
            })

        return sorted(candidates, key=lambda x: x["overall_score"], reverse=True)

    def handoff_queue(self, candidates):
        queue = []
        for c in candidates:
            if c["incubator_stage"] in ("INCUBATE_PRIORITY", "VALIDATE"):
                queue.append({
                    "handoff_id": f"portfolio-{c['venture_id']}",
                    "venture_id": c["venture_id"],
                    "name": c["name"],
                    "score": c["overall_score"],
                    "status": "READY_FOR_PORTFOLIO_REVIEW",
                    "target": "portfolio_orchestrator_v34",
                    "automatic_launch": False,
                })
        return queue

    def concentration_recommendation(self):
        p = read_json(self.live / "portfolio_orchestrator_v34_live.json", {})
        risk = p.get("concentration", {}).get("concentration_risk")
        if risk == "HIGH":
            return "Prioritize incubation of at least 2 ventures from different categories."
        if risk == "MODERATE":
            return "Add one additional differentiated venture before increasing concentration."
        return "Maintain diversification while validating the strongest candidates."

    def run_cycle(self):
        candidates = self.generate_candidates()
        queue = self.handoff_queue(candidates)
        state = {
            "status": "autonomous_venture_incubator_ready",
            "candidates_total": len(candidates),
            "priority_incubations": sum(c["incubator_stage"] == "INCUBATE_PRIORITY" for c in candidates),
            "validation_queue": sum(c["incubator_stage"] == "VALIDATE" for c in candidates),
            "portfolio_handoffs": len(queue),
            "top_candidate": candidates[0]["name"] if candidates else None,
            "top_candidate_score": candidates[0]["overall_score"] if candidates else 0,
            "diversification_recommendation": self.concentration_recommendation(),
            "candidates": candidates,
            "portfolio_handoff_queue": queue,
            "automatic_company_formation_enabled": False,
            "automatic_external_launch_enabled": False,
            "automatic_capital_commitment_enabled": False,
            "dashboard_url": "http://127.0.0.1:8797",
            "updated_at": now(),
        }

        write_json(self.runtime / "venture_incubator_state.json", state)
        write_json(self.live / "autonomous_venture_incubator_v35_live.json", state)
        write_json(self.records / "venture_candidates.json", {
            "candidates": candidates, "updated_at": now()
        })
        write_json(self.records / "portfolio_handoff_queue.json", {
            "handoffs": queue, "updated_at": now()
        })
        return state
