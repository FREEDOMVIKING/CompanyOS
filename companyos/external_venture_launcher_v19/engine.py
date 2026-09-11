
import json
import os
import re
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

def slugify(value):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(value).lower())).strip("-")

class ExternalVentureLauncherV19:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/external_venture_launcher_v19_650001_700000"
        self.generated = self.home / "generated_ventures_v19"
        self.launch_queue = self.runtime / "launch_queue.json"
        self.executive = self.live / "enterprise_automation_v15_live.json"
        self.roadmap = self.live / "venture_progress_live.json"
        self.opportunities = self.live / "approved_opportunities.json"
        for p in (self.live, self.runtime, self.generated):
            p.mkdir(parents=True, exist_ok=True)

    def source_opportunities(self):
        items = []
        data = read_json(self.opportunities, {})
        for item in data.get("opportunities", []):
            if str(item.get("status", "")).upper() in ("APPROVED", "READY", "SELECTED"):
                items.append(item)

        if not items:
            enterprise = read_json(self.executive, {})
            for v in enterprise.get("venture_priorities", []) or []:
                items.append({
                    "opportunity_id": v.get("venture_id"),
                    "name": v.get("name"),
                    "status": "APPROVED_INTERNAL",
                    "score": v.get("priority_score", 0),
                    "summary": "Imported from Enterprise Automation venture priorities.",
                })

        if not items:
            items = [{
                "opportunity_id": "digital-template-business",
                "name": "Digital Template Business",
                "status": "APPROVED_INTERNAL",
                "score": 90,
                "summary": "Existing active CompanyOS venture.",
            }]
        return items

    def readiness_score(self, opportunity):
        score = float(opportunity.get("score", 0) or 0)
        has_name = bool(opportunity.get("name"))
        has_summary = bool(opportunity.get("summary"))
        score += 5 if has_name else 0
        score += 5 if has_summary else 0
        return max(0, min(100, round(score, 2)))

    def make_branding(self, opportunity):
        name = opportunity.get("name") or "New Venture"
        return {
            "venture_name": name,
            "tagline": f"Practical tools and solutions from {name}",
            "positioning": "Useful, focused, and easy to buy.",
            "tone": ["clear", "credible", "practical"],
            "status": "DRAFT_REVIEW_REQUIRED",
        }

    def make_offer(self, opportunity):
        name = opportunity.get("name") or "New Venture"
        return {
            "primary_offer": f"{name} Starter Offer",
            "offer_type": "digital_product_or_service",
            "target_customer": "Small business operators and practical buyers",
            "price_test_usd": [29, 49, 79],
            "guarantee": "No guarantee generated automatically",
            "status": "DRAFT_REVIEW_REQUIRED",
        }

    def landing_page(self, venture_dir, branding, offer):
        html = f"""<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{branding['venture_name']}</title>
<style>
body{{font-family:system-ui;margin:0;background:#0b1020;color:#eef2ff}}
main{{max-width:900px;margin:auto;padding:40px 20px}}
section{{background:#151d33;border-radius:20px;padding:28px;margin:20px 0}}
a{{display:inline-block;background:#eef2ff;color:#0b1020;padding:14px 18px;border-radius:12px;text-decoration:none;font-weight:700}}
</style>
</head>
<body><main>
<section>
<h1>{branding['venture_name']}</h1>
<h2>{branding['tagline']}</h2>
<p>{branding['positioning']}</p>
<a href="#">Launch approval required</a>
</section>
<section>
<h2>{offer['primary_offer']}</h2>
<p>Target customer: {offer['target_customer']}</p>
<p>Suggested test prices: ${offer['price_test_usd'][0]}, ${offer['price_test_usd'][1]}, ${offer['price_test_usd'][2]}</p>
</section>
</main></body></html>"""
        (venture_dir / "landing_page.html").write_text(html, encoding="utf-8")

    def build_venture(self, opportunity):
        venture_id = slugify(opportunity.get("opportunity_id") or opportunity.get("name"))
        venture_dir = self.generated / venture_id
        venture_dir.mkdir(parents=True, exist_ok=True)

        branding = self.make_branding(opportunity)
        offer = self.make_offer(opportunity)
        readiness = self.readiness_score(opportunity)
        checklist = [
            {"step": "Branding reviewed", "done": False},
            {"step": "Offer reviewed", "done": False},
            {"step": "Landing page reviewed", "done": False},
            {"step": "Payment flow verified", "done": False},
            {"step": "Domain selected", "done": False},
            {"step": "External publication approved", "done": False},
        ]
        economics = {
            "estimated_price_points_usd": offer["price_test_usd"],
            "estimated_gross_margin_percent": 90,
            "startup_cost_assumption_usd": 0,
            "profitability_status": "UNVERIFIED_UNTIL_REAL_SALES",
        }

        self.landing_page(venture_dir, branding, offer)
        write_json(venture_dir / "branding.json", branding)
        write_json(venture_dir / "offer.json", offer)
        write_json(venture_dir / "launch_checklist.json", {"items": checklist})
        write_json(venture_dir / "economics.json", economics)

        manifest = {
            "venture_id": venture_id,
            "name": opportunity.get("name"),
            "source_opportunity": opportunity,
            "workspace": str(venture_dir),
            "readiness_score": readiness,
            "state": "READY_FOR_LAUNCH_REVIEW" if readiness >= 75 else "NEEDS_MORE_VALIDATION",
            "external_publish_approved": False,
            "domain_purchase_approved": False,
            "funds_committed": False,
            "created_at": now(),
        }
        write_json(venture_dir / "venture_manifest.json", manifest)
        return manifest

    def run_cycle(self):
        queue = []
        for opportunity in self.source_opportunities():
            queue.append(self.build_venture(opportunity))
        queue.sort(key=lambda x: x["readiness_score"], reverse=True)

        state = {
            "status": "external_venture_launcher_ready",
            "ventures_prepared": len(queue),
            "ready_for_launch_review": sum(v["state"] == "READY_FOR_LAUNCH_REVIEW" for v in queue),
            "launch_queue": queue,
            "top_venture": queue[0]["name"] if queue else None,
            "external_launch_enabled": False,
            "domain_purchase_enabled": False,
            "fund_spend_enabled": False,
            "dashboard_url": "http://127.0.0.1:8781",
            "updated_at": now(),
        }
        write_json(self.launch_queue, state)
        write_json(self.live / "external_venture_launcher_v19_live.json", state)
        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "external_venture_launcher_v19_cycle",
            "event_type": "external_venture_launcher_v19_cycle",
            "state": state,
        })
        return state
