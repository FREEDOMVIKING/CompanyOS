
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

class OpportunityIntelligenceV21:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/opportunity_intelligence_v21_750001_800000"
        self.ventures = self.home / "generated_ventures_v19"
        self.records = self.home / "opportunity_records_v21"
        self.products = self.home / "companyos_runtime/product_portfolio_v7_live.json"
        self.marketing = self.live / "autonomous_sales_marketing_v12_live.json"
        self.enterprise = self.live / "enterprise_automation_v15_live.json"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

    def venture_dirs(self):
        if not self.ventures.exists():
            return []
        return [p for p in sorted(self.ventures.iterdir()) if p.is_dir()]

    def score(self, venture_dir):
        manifest = read_json(venture_dir / "venture_manifest.json", {})
        branding = read_json(venture_dir / "branding.json", {})
        offer = read_json(venture_dir / "offer.json", {})
        economics = read_json(venture_dir / "economics.json", {})
        checklist = read_json(venture_dir / "launch_checklist.json", {"items": []})
        marketing = read_json(self.marketing, {})
        enterprise = read_json(self.enterprise, {})

        evidence = {}

        demand = 0
        if manifest.get("name"):
            demand += 10
            evidence["venture_named"] = True
        summary = manifest.get("source_opportunity", {}).get("summary")
        if summary:
            demand += 10
            evidence["opportunity_summary_present"] = True
        if marketing.get("campaigns_ready", 0) or marketing.get("campaigns", 0):
            demand += 10
            evidence["campaign_assets_present"] = True
        if manifest.get("state") in ("READY_FOR_LAUNCH_REVIEW", "NEEDS_MORE_VALIDATION"):
            demand += 5
        demand = min(35, demand)

        offer_quality = 0
        if offer.get("primary_offer"):
            offer_quality += 10
        if offer.get("price_test_usd"):
            offer_quality += 10
        if branding.get("tagline"):
            offer_quality += 5
        offer_quality = min(25, offer_quality)

        profitability = 0
        margin = float(economics.get("estimated_gross_margin_percent", 0) or 0)
        startup = float(economics.get("startup_cost_assumption_usd", 0) or 0)
        if margin >= 70:
            profitability += 15
        elif margin >= 40:
            profitability += 10
        elif margin > 0:
            profitability += 5
        if startup <= 100:
            profitability += 5
        profitability = min(20, profitability)

        execution = 0
        if (venture_dir / "landing_page.html").exists():
            execution += 10
        if checklist.get("items"):
            execution += 5
        if branding and offer and economics:
            execution += 5
        execution = min(20, execution)

        competition_risk = 15
        # No live external research provider is connected.
        # Keep this conservative rather than inventing market facts.
        external_research_available = False

        raw_total = demand + offer_quality + profitability + execution
        adjusted = max(0, min(100, raw_total - max(0, competition_risk - 10)))

        if adjusted >= 75:
            confidence = "STRONG_INTERNAL_EVIDENCE"
        elif adjusted >= 60:
            confidence = "MODERATE_INTERNAL_EVIDENCE"
        else:
            confidence = "WEAK_INTERNAL_EVIDENCE"

        result = {
            "venture_id": manifest.get("venture_id", venture_dir.name),
            "name": manifest.get("name", venture_dir.name),
            "workspace": str(venture_dir),
            "scores": {
                "demand_evidence": demand,
                "offer_quality": offer_quality,
                "profitability": profitability,
                "execution_readiness": execution,
                "competition_risk": competition_risk,
                "overall": round(adjusted, 2),
            },
            "confidence": confidence,
            "external_research_available": external_research_available,
            "external_research_status": "NOT_CONNECTED",
            "evidence": evidence,
            "recommendation": (
                "Use this score to re-run Validation Director V20."
                if adjusted >= 60
                else "Collect stronger customer-demand evidence before launch review."
            ),
            "updated_at": now(),
        }

        source = manifest.setdefault("source_opportunity", {})
        source["score"] = round(adjusted, 2)
        source["evidence_source"] = "companyos_internal_evidence_v21"
        source["external_research_available"] = False
        manifest["opportunity_intelligence_v21"] = {
            "score": round(adjusted, 2),
            "confidence": confidence,
            "updated_at": result["updated_at"],
        }
        write_json(venture_dir / "venture_manifest.json", manifest)
        write_json(self.records / f"{result['venture_id']}.json", result)
        return result

    def run_cycle(self):
        results = [self.score(p) for p in self.venture_dirs()]
        results.sort(key=lambda x: x["scores"]["overall"], reverse=True)
        state = {
            "status": "opportunity_intelligence_ready",
            "opportunities_scored": len(results),
            "strong_internal_evidence": sum(r["scores"]["overall"] >= 75 for r in results),
            "moderate_internal_evidence": sum(60 <= r["scores"]["overall"] < 75 for r in results),
            "weak_internal_evidence": sum(r["scores"]["overall"] < 60 for r in results),
            "top_opportunity": results[0]["name"] if results else None,
            "external_research_provider_connected": False,
            "results": results,
            "dashboard_url": "http://127.0.0.1:8783",
            "updated_at": now(),
        }
        write_json(self.runtime / "opportunity_intelligence_state.json", state)
        write_json(self.live / "opportunity_intelligence_v21_live.json", state)
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "opportunity_intelligence_v21_cycle",
            "event_type": "opportunity_intelligence_v21_cycle",
            "state": state,
        })
        return state
