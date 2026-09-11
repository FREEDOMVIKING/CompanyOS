
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

class PortfolioOrchestratorV34:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/portfolio_orchestrator_v34_1400001_1450000"
        self.records = self.home / "portfolio_records_v34"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

    def collect_ventures(self):
        candidates = []

        rev = read_json(self.live / "autonomous_revenue_expansion_v26_live.json", {})
        for v in rev.get("portfolio", []) or []:
            candidates.append({
                "venture_id": v.get("venture_id") or hashlib.sha256(str(v.get("name")).encode()).hexdigest()[:12],
                "name": v.get("name") or "Unnamed Venture",
                "portfolio_score": float(v.get("portfolio_score", 0) or 0),
                "state": v.get("action") or v.get("state") or "UNKNOWN",
                "source": "revenue_expansion_v26"
            })

        launcher = read_json(self.live / "external_venture_launcher_v19_live.json", {})
        top = launcher.get("top_venture")
        if top and not any(x["name"] == top for x in candidates):
            candidates.append({
                "venture_id": hashlib.sha256(top.encode()).hexdigest()[:12],
                "name": top,
                "portfolio_score": float(launcher.get("top_venture_score", 60) or 60),
                "state": launcher.get("top_venture_state") or "PREPARED",
                "source": "venture_launcher_v19"
            })

        builder = read_json(self.live / "autonomous_product_builder_v28_live.json", {})
        for p in builder.get("products", []) or []:
            name = p.get("name")
            if name and not any(x["name"] == name for x in candidates):
                candidates.append({
                    "venture_id": hashlib.sha256(name.encode()).hexdigest()[:12],
                    "name": name,
                    "portfolio_score": float(p.get("quality_score", 0) or 0),
                    "state": p.get("state") or "PRODUCT_STAGE",
                    "source": "product_builder_v28"
                })

        if not candidates:
            legacy = read_json(self.home / "ceo_memory/venture_registry.json", {})
            for v in legacy.get("ventures", []) or []:
                candidates.append({
                    "venture_id": v.get("venture_id") or hashlib.sha256(str(v.get("name")).encode()).hexdigest()[:12],
                    "name": v.get("name") or "Unnamed Venture",
                    "portfolio_score": float(v.get("score", 50) or 50),
                    "state": v.get("state") or "UNKNOWN",
                    "source": "legacy_registry"
                })
        return candidates

    def enrich(self, venture):
        storefront = read_json(self.live / "autonomous_storefront_sales_v29_live.json", {})
        finance = read_json(self.live / "autonomous_finance_treasury_v30_live.json", {})
        marketing = read_json(self.live / "autonomous_marketing_acquisition_v31_live.json", {})
        validation = read_json(self.live / "validation_launch_director_v20_live.json", {})
        ops = read_json(self.live / "autonomous_business_operations_v32_live.json", {})

        name = venture["name"].lower()
        products = storefront.get("catalog", []) or []
        matching_products = [p for p in products if name in str(p.get("name","")).lower() or str(p.get("name","")).lower() in name]

        verified_revenue = float(finance.get("pnl", {}).get("revenue_usd", 0) or 0)
        campaign_count = int(marketing.get("campaigns_total", 0) or 0)
        ready_for_launch = int(validation.get("ready_for_launch_review", 0) or 0)
        stalled = int(ops.get("stalled_workflows", 0) or 0)

        score = float(venture.get("portfolio_score", 0) or 0)
        if matching_products:
            score += 5
        if campaign_count > 0:
            score += 3
        if verified_revenue > 0:
            score += 10
        if ready_for_launch > 0:
            score += 5
        if stalled > 0:
            score -= min(10, stalled * 2)
        score = max(0, min(100, round(score, 2)))

        if verified_revenue > 0 and score >= 80:
            action = "PROMOTE"
        elif score >= 75:
            action = "VALIDATE_AND_GROW"
        elif score >= 55:
            action = "HOLD_AND_VALIDATE"
        else:
            action = "REASSESS"

        return {
            **venture,
            "portfolio_score": score,
            "recommended_action": action,
            "product_count": len(matching_products),
            "verified_revenue_usd": verified_revenue if matching_products else 0,
            "campaign_support": campaign_count > 0,
            "launch_review_ready": ready_for_launch > 0,
            "stalled_workflow_pressure": stalled,
        }

    def allocation_recommendations(self, ventures):
        if not ventures:
            return []
        total_score = sum(v["portfolio_score"] for v in ventures) or 1
        out = []
        for v in ventures:
            share = round(v["portfolio_score"] / total_score * 100, 2)
            out.append({
                "venture_id": v["venture_id"],
                "name": v["name"],
                "recommended_attention_percent": share,
                "recommended_action": v["recommended_action"],
                "capital_movement_allowed": False,
            })
        return sorted(out, key=lambda x: x["recommended_attention_percent"], reverse=True)

    def concentration(self, allocations):
        top = allocations[0]["recommended_attention_percent"] if allocations else 0
        if top >= 70:
            risk = "HIGH"
        elif top >= 50:
            risk = "MODERATE"
        else:
            risk = "BALANCED"
        return {
            "top_venture_attention_percent": top,
            "concentration_risk": risk,
            "automatic_rebalancing_enabled": False,
        }

    def run_cycle(self):
        ventures = [self.enrich(v) for v in self.collect_ventures()]
        ventures.sort(key=lambda x: x["portfolio_score"], reverse=True)
        allocations = self.allocation_recommendations(ventures)
        concentration = self.concentration(allocations)

        state = {
            "status": "portfolio_orchestrator_ready",
            "ventures_total": len(ventures),
            "top_venture": ventures[0]["name"] if ventures else None,
            "top_venture_score": ventures[0]["portfolio_score"] if ventures else 0,
            "ventures": ventures,
            "allocation_recommendations": allocations,
            "concentration": concentration,
            "automatic_capital_reallocation_enabled": False,
            "automatic_venture_retirement_enabled": False,
            "automatic_external_launch_enabled": False,
            "dashboard_url": "http://127.0.0.1:8796",
            "updated_at": now(),
        }

        write_json(self.runtime / "portfolio_orchestrator_state.json", state)
        write_json(self.live / "portfolio_orchestrator_v34_live.json", state)
        write_json(self.records / "venture_rankings.json", {
            "ventures": ventures, "updated_at": now()
        })
        write_json(self.records / "allocation_recommendations.json", {
            "allocations": allocations, "updated_at": now()
        })
        return state
