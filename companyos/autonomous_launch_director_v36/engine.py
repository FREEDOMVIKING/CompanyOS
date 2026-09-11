
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

class AutonomousLaunchDirectorV36:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/autonomous_launch_director_v36_1500001_1550000"
        self.records = self.home / "launch_director_records_v36"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

    def state(self, filename):
        return read_json(self.live / filename, {})

    def collect_ventures(self):
        ventures = []
        portfolio = self.state("portfolio_orchestrator_v34_live.json")
        incubator = self.state("autonomous_venture_incubator_v35_live.json")

        for v in portfolio.get("ventures", []) or []:
            ventures.append({
                "venture_id": v.get("venture_id") or hashlib.sha256(str(v.get("name")).encode()).hexdigest()[:16],
                "name": v.get("name") or "Unnamed Venture",
                "source": "portfolio_v34",
                "base_score": float(v.get("portfolio_score", 0) or 0),
                "recommended_action": v.get("recommended_action"),
            })

        for c in incubator.get("candidates", []) or []:
            if not any(x["name"] == c.get("name") for x in ventures):
                ventures.append({
                    "venture_id": c.get("venture_id") or hashlib.sha256(str(c.get("name")).encode()).hexdigest()[:16],
                    "name": c.get("name") or "Unnamed Venture",
                    "source": "incubator_v35",
                    "base_score": float(c.get("overall_score", 0) or 0),
                    "recommended_action": c.get("incubator_stage"),
                })
        return ventures

    def module_readiness(self, venture):
        product = self.state("autonomous_product_builder_v28_live.json")
        storefront = self.state("autonomous_storefront_sales_v29_live.json")
        finance = self.state("autonomous_finance_treasury_v30_live.json")
        marketing = self.state("autonomous_marketing_acquisition_v31_live.json")
        operations = self.state("autonomous_business_operations_v32_live.json")
        customer = self.state("autonomous_customer_success_v33_live.json")
        validation = self.state("validation_launch_director_v20_live.json")

        name = venture["name"].lower()

        products = storefront.get("catalog", []) or product.get("products", []) or []
        matching_products = [
            p for p in products
            if name in str(p.get("name","")).lower()
            or str(p.get("name","")).lower() in name
        ]

        product_ready = bool(matching_products)
        storefront_ready = storefront.get("status") == "autonomous_storefront_sales_ready"
        finance_ready = finance.get("status") == "autonomous_finance_treasury_ready"
        marketing_ready = marketing.get("status") == "autonomous_marketing_acquisition_ready"
        operations_ready = operations.get("status") == "autonomous_business_operations_ready"
        customer_ready = customer.get("status") == "autonomous_customer_success_ready"

        ready_for_launch_review = int(validation.get("ready_for_launch_review", 0) or 0) > 0
        verified_revenue = float(finance.get("pnl", {}).get("revenue_usd", 0) or 0)
        campaigns = int(marketing.get("campaigns_total", 0) or 0)
        ops_health = int(operations.get("operations_health_percent", 0) or 0)

        checks = [
            {"key":"product_ready","label":"Product artifact ready","passed":product_ready,"weight":20},
            {"key":"storefront_ready","label":"Storefront system ready","passed":storefront_ready,"weight":15},
            {"key":"marketing_ready","label":"Marketing system ready","passed":marketing_ready,"weight":15},
            {"key":"finance_ready","label":"Finance system ready","passed":finance_ready,"weight":15},
            {"key":"operations_ready","label":"Business operations ready","passed":operations_ready,"weight":15},
            {"key":"customer_ready","label":"Customer success ready","passed":customer_ready,"weight":10},
            {"key":"validation_ready","label":"Validation launch review ready","passed":ready_for_launch_review,"weight":10},
        ]

        weighted = sum(c["weight"] for c in checks if c["passed"])
        evidence_bonus = 0
        if campaigns > 0:
            evidence_bonus += 2
        if verified_revenue > 0:
            evidence_bonus += 5
        if ops_health >= 90:
            evidence_bonus += 3

        score = min(100, weighted + evidence_bonus)

        blockers = [c["key"] for c in checks if not c["passed"]]
        if score >= 90 and not blockers:
            state = "READY_FOR_LAUNCH_REVIEW"
            recommendation = "Prepare executive launch review packet."
        elif score >= 75:
            state = "NEAR_READY"
            recommendation = "Resolve remaining blockers before launch review."
        elif score >= 55:
            state = "VALIDATE_MORE"
            recommendation = "Continue validation and operational preparation."
        else:
            state = "NOT_READY"
            recommendation = "Do not launch; complete core readiness work first."

        return {
            "launch_score": score,
            "launch_state": state,
            "recommendation": recommendation,
            "checks": checks,
            "blockers": blockers,
            "verified_revenue_usd": verified_revenue,
            "campaigns_detected": campaigns,
            "operations_health_percent": ops_health,
        }

    def launch_packet(self, venture, readiness):
        return {
            "packet_id": f"launch-{venture['venture_id']}",
            "venture_id": venture["venture_id"],
            "venture_name": venture["name"],
            "launch_score": readiness["launch_score"],
            "launch_state": readiness["launch_state"],
            "blockers": readiness["blockers"],
            "checklist": readiness["checks"],
            "recommendation": readiness["recommendation"],
            "external_launch_approved": False,
            "public_publish_approved": False,
            "financial_commitment_approved": False,
            "created_at": now(),
        }

    def run_cycle(self):
        ventures = []
        review_queue = []
        packets = []

        for v in self.collect_ventures():
            readiness = self.module_readiness(v)
            row = {**v, **readiness}
            ventures.append(row)

            packet = self.launch_packet(v, readiness)
            packets.append(packet)

            if readiness["launch_state"] in ("READY_FOR_LAUNCH_REVIEW", "NEAR_READY"):
                review_queue.append({
                    "review_id": packet["packet_id"],
                    "venture_id": v["venture_id"],
                    "venture_name": v["name"],
                    "launch_score": readiness["launch_score"],
                    "launch_state": readiness["launch_state"],
                    "status": "EXECUTIVE_REVIEW_REQUIRED",
                    "automatic_external_launch": False,
                })

        ventures.sort(key=lambda x: x["launch_score"], reverse=True)
        review_queue.sort(key=lambda x: x["launch_score"], reverse=True)

        state = {
            "status": "autonomous_launch_director_ready",
            "ventures_evaluated": len(ventures),
            "ready_for_launch_review": sum(v["launch_state"] == "READY_FOR_LAUNCH_REVIEW" for v in ventures),
            "near_ready": sum(v["launch_state"] == "NEAR_READY" for v in ventures),
            "review_queue_size": len(review_queue),
            "top_launch_candidate": ventures[0]["name"] if ventures else None,
            "top_launch_score": ventures[0]["launch_score"] if ventures else 0,
            "ventures": ventures,
            "launch_review_queue": review_queue,
            "automatic_external_launch_enabled": False,
            "automatic_publication_enabled": False,
            "automatic_financial_commitments_enabled": False,
            "dashboard_url": "http://127.0.0.1:8798",
            "updated_at": now(),
        }

        write_json(self.runtime / "launch_director_state.json", state)
        write_json(self.live / "autonomous_launch_director_v36_live.json", state)
        write_json(self.records / "launch_review_queue.json", {
            "reviews": review_queue,
            "updated_at": now()
        })
        write_json(self.records / "launch_packets.json", {
            "packets": packets,
            "updated_at": now()
        })
        write_json(self.live / "executive_launch_handoff_v36.json", {
            "top_launch_candidate": state["top_launch_candidate"],
            "top_launch_score": state["top_launch_score"],
            "review_queue_size": state["review_queue_size"],
            "updated_at": now()
        })
        return state
