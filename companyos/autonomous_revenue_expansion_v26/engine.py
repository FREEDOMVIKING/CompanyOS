
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

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

def append_jsonl(path, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True, default=str) + "\n")

class AutonomousRevenueExpansionV26:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/autonomous_revenue_expansion_v26_1000001_1050000"
        self.records = self.home / "revenue_expansion_records_v26"
        self.ventures = self.home / "generated_ventures_v19"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

    def venture_dirs(self):
        if not self.ventures.exists():
            return []
        return [p for p in sorted(self.ventures.iterdir()) if p.is_dir()]

    def build_portfolio(self):
        research = read_json(self.live / "autonomous_research_network_v22_live.json", {})
        validation = read_json(self.live / "validation_launch_director_v20_live.json", {})
        learning = read_json(self.live / "self_improvement_learning_v23_live.json", {})
        enterprise = read_json(self.live / "enterprise_automation_v15_live.json", {})
        revenue = read_json(self.live / "autonomous_revenue_v11_live.json", {})

        validation_by_id = {
            x.get("venture_id"): x for x in validation.get("results", []) or []
        }
        research_by_id = research.get("venture_evidence", {}) or {}
        pricing_by_id = {
            x.get("venture_id"): x for x in learning.get("pricing_recommendations", []) or []
        }

        portfolio = []
        for vdir in self.venture_dirs():
            manifest = read_json(vdir / "venture_manifest.json", {})
            economics = read_json(vdir / "economics.json", {})
            vid = manifest.get("venture_id", vdir.name)
            validation_row = validation_by_id.get(vid, {})
            research_row = research_by_id.get(vid, {})
            pricing_row = pricing_by_id.get(vid, {})

            readiness = float(
                validation_row.get("validation_score",
                manifest.get("readiness_score", 0)) or 0
            )
            signal = float(research_row.get("external_signal_score", 0) or 0)
            margin = float(economics.get("estimated_gross_margin_percent", 0) or 0)
            source_score = float(manifest.get("source_opportunity", {}).get("score", 0) or 0)

            portfolio_score = round(
                readiness * 0.40 +
                source_score * 0.25 +
                min(signal, 100) * 0.15 +
                min(margin, 100) * 0.20,
                2
            )

            if portfolio_score >= 80:
                recommendation = "PROMOTE"
            elif portfolio_score >= 60:
                recommendation = "HOLD_AND_VALIDATE"
            else:
                recommendation = "DEPRIORITIZE"

            recommended_price = pricing_row.get("recommended_price_usd")
            if recommended_price is None:
                prices = read_json(vdir / "offer.json", {}).get("price_test_usd", [])
                recommended_price = prices[len(prices)//2] if prices else 49

            portfolio.append({
                "venture_id": vid,
                "name": manifest.get("name", vdir.name),
                "workspace": str(vdir),
                "readiness_score": readiness,
                "source_score": source_score,
                "external_signal_score": signal,
                "gross_margin_percent": margin,
                "portfolio_score": portfolio_score,
                "recommended_action": recommendation,
                "recommended_price_usd": recommended_price,
                "external_launch_approved": False,
                "funding_approved": False,
                "updated_at": now(),
            })

        portfolio.sort(key=lambda x: x["portfolio_score"], reverse=True)
        return portfolio, enterprise, revenue

    def forecast(self, portfolio):
        scenarios = []
        for item in portfolio:
            price = float(item.get("recommended_price_usd", 0) or 0)
            scenarios.append({
                "venture_id": item["venture_id"],
                "name": item["name"],
                "monthly_revenue_scenarios_usd": {
                    "conservative_5_sales": round(price * 5, 2),
                    "base_20_sales": round(price * 20, 2),
                    "growth_50_sales": round(price * 50, 2),
                },
                "assumption": "Scenario math only; not a prediction.",
            })
        return scenarios

    def allocation(self, portfolio):
        promoted = [x for x in portfolio if x["recommended_action"] == "PROMOTE"]
        if not promoted:
            return []
        total_score = sum(x["portfolio_score"] for x in promoted) or 1
        return [{
            "venture_id": x["venture_id"],
            "name": x["name"],
            "recommended_attention_percent": round(x["portfolio_score"] / total_score * 100, 1),
            "cash_allocation_usd": 0,
            "requires_approval": True,
        } for x in promoted]

    def expansion_queue(self, portfolio):
        queue = []
        names = {x["name"].lower() for x in portfolio}
        templates = [
            ("small-business-automation-kit", "Small Business Automation Kit"),
            ("customer-response-bundle", "Customer Response Bundle"),
            ("field-service-estimate-pack", "Field Service Estimate Pack"),
        ]
        for vid, name in templates:
            if name.lower() not in names:
                queue.append({
                    "opportunity_id": vid,
                    "name": name,
                    "status": "INTERNAL_RESEARCH_QUEUE",
                    "external_research_required": True,
                    "build_approved": False,
                })
        return queue

    def approval_queue(self, portfolio):
        approvals = []
        for item in portfolio:
            if item["recommended_action"] == "PROMOTE":
                approvals.append({
                    "approval_id": f"launch-{item['venture_id']}",
                    "type": "VENTURE_PROMOTION",
                    "venture_id": item["venture_id"],
                    "name": item["name"],
                    "reason": f"Portfolio score {item['portfolio_score']}",
                    "status": "REVIEW_REQUIRED",
                })
        return approvals

    def run_cycle(self):
        portfolio, enterprise, revenue = self.build_portfolio()
        forecasts = self.forecast(portfolio)
        allocation = self.allocation(portfolio)
        expansion = self.expansion_queue(portfolio)
        approvals = self.approval_queue(portfolio)

        state = {
            "status": "autonomous_revenue_expansion_ready",
            "ventures_total": len(portfolio),
            "ventures_promoted": sum(x["recommended_action"] == "PROMOTE" for x in portfolio),
            "ventures_on_hold": sum(x["recommended_action"] == "HOLD_AND_VALIDATE" for x in portfolio),
            "ventures_deprioritized": sum(x["recommended_action"] == "DEPRIORITIZE" for x in portfolio),
            "top_venture": portfolio[0]["name"] if portfolio else None,
            "portfolio": portfolio,
            "revenue_forecasts": forecasts,
            "capital_allocation_recommendations": allocation,
            "expansion_queue": expansion,
            "approval_queue": approvals,
            "verified_revenue_usd": (
                enterprise.get("kpis", {}).get("revenue_usd", 0)
                if isinstance(enterprise, dict) else 0
            ),
            "external_actions_enabled": False,
            "automatic_fund_allocation_enabled": False,
            "automatic_venture_retirement_enabled": False,
            "dashboard_url": "http://127.0.0.1:8788",
            "updated_at": now(),
        }

        write_json(self.runtime / "revenue_expansion_state.json", state)
        write_json(self.live / "autonomous_revenue_expansion_v26_live.json", state)
        write_json(self.records / "portfolio_registry.json", {
            "portfolio": portfolio,
            "updated_at": now(),
        })
        write_json(self.records / "approval_queue.json", {
            "approvals": approvals,
            "updated_at": now(),
        })
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "autonomous_revenue_expansion_v26_cycle",
            "event_type": "autonomous_revenue_expansion_v26_cycle",
            "state": {
                "ventures_total": state["ventures_total"],
                "ventures_promoted": state["ventures_promoted"],
                "top_venture": state["top_venture"],
            },
        })
        return state
