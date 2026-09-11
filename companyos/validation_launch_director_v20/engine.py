
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

class ValidationLaunchDirectorV20:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/validation_launch_director_v20_700001_750000"
        self.ventures = self.home / "generated_ventures_v19"
        self.records = self.home / "validation_records_v20"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

    def venture_dirs(self):
        if not self.ventures.exists():
            return []
        return [p for p in sorted(self.ventures.iterdir()) if p.is_dir()]

    def validate_venture(self, venture_dir):
        manifest = read_json(venture_dir / "venture_manifest.json", {})
        branding = read_json(venture_dir / "branding.json", {})
        offer = read_json(venture_dir / "offer.json", {})
        economics = read_json(venture_dir / "economics.json", {})
        checklist = read_json(venture_dir / "launch_checklist.json", {"items": []})
        landing_exists = (venture_dir / "landing_page.html").exists()

        branding_score = 20 if branding.get("venture_name") and branding.get("tagline") else 8
        offer_score = 20 if offer.get("primary_offer") and offer.get("price_test_usd") else 8
        landing_score = 15 if landing_exists else 0
        economics_score = 15 if economics.get("estimated_gross_margin_percent") is not None else 5
        source_score = min(20, float(manifest.get("source_opportunity", {}).get("score", 0) or 0) / 5)
        execution_score = 10 if checklist.get("items") else 3

        total = round(
            branding_score + offer_score + landing_score +
            economics_score + source_score + execution_score,
            2
        )

        prices = [float(x) for x in offer.get("price_test_usd", []) if isinstance(x, (int, float))]
        if prices:
            recommended_price = sorted(prices)[len(prices) // 2]
        else:
            recommended_price = 49.0

        blockers = []
        if not landing_exists:
            blockers.append("landing_page_missing")
        if not branding.get("venture_name"):
            blockers.append("branding_incomplete")
        if not offer.get("primary_offer"):
            blockers.append("offer_incomplete")
        if float(manifest.get("source_opportunity", {}).get("score", 0) or 0) < 60:
            blockers.append("weak_source_opportunity_score")

        state = "READY_FOR_LAUNCH_REVIEW" if total >= 75 and not blockers else "NEEDS_MORE_VALIDATION"

        evidence = {
            "branding_complete": bool(branding.get("venture_name") and branding.get("tagline")),
            "offer_complete": bool(offer.get("primary_offer") and offer.get("price_test_usd")),
            "landing_page_exists": landing_exists,
            "economics_present": bool(economics),
            "launch_checklist_present": bool(checklist.get("items")),
            "source_opportunity_score": manifest.get("source_opportunity", {}).get("score", 0),
        }

        result = {
            "venture_id": manifest.get("venture_id", venture_dir.name),
            "name": manifest.get("name", venture_dir.name),
            "workspace": str(venture_dir),
            "previous_readiness_score": manifest.get("readiness_score", 0),
            "validation_score": total,
            "state": state,
            "recommended_price_usd": recommended_price,
            "blockers": blockers,
            "evidence": evidence,
            "profitability_assessment": {
                "gross_margin_percent": economics.get("estimated_gross_margin_percent", 0),
                "startup_cost_assumption_usd": economics.get("startup_cost_assumption_usd", 0),
                "status": "PROMISING_BUT_UNVERIFIED" if total >= 75 else "INSUFFICIENT_VALIDATION",
            },
            "competition_assessment": {
                "status": "RESEARCH_REQUIRED",
                "note": "No external market data was used by this local validator.",
            },
            "launch_recommendation": (
                "Queue for human launch review."
                if state == "READY_FOR_LAUNCH_REVIEW"
                else "Resolve blockers and collect stronger market evidence."
            ),
            "external_launch_approved": False,
            "validated_at": now(),
        }

        manifest["readiness_score"] = total
        manifest["state"] = state
        manifest["validation_v20"] = {
            "score": total,
            "blockers": blockers,
            "validated_at": result["validated_at"],
        }
        write_json(venture_dir / "venture_manifest.json", manifest)
        write_json(self.records / f"{result['venture_id']}.json", result)
        return result

    def run_cycle(self):
        results = [self.validate_venture(p) for p in self.venture_dirs()]
        results.sort(key=lambda x: x["validation_score"], reverse=True)

        state = {
            "status": "validation_launch_director_ready",
            "ventures_validated": len(results),
            "ready_for_launch_review": sum(r["state"] == "READY_FOR_LAUNCH_REVIEW" for r in results),
            "needs_more_validation": sum(r["state"] != "READY_FOR_LAUNCH_REVIEW" for r in results),
            "top_venture": results[0]["name"] if results else None,
            "results": results,
            "external_launch_enabled": False,
            "dashboard_url": "http://127.0.0.1:8782",
            "updated_at": now(),
        }

        write_json(self.runtime / "validation_state.json", state)
        write_json(self.live / "validation_launch_director_v20_live.json", state)
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "validation_launch_director_v20_cycle",
            "event_type": "validation_launch_director_v20_cycle",
            "state": state,
        })
        return state
