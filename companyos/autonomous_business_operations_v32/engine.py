
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

class AutonomousBusinessOperationsV32:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/autonomous_business_operations_v32_1300001_1350000"
        self.records = self.home / "business_operations_records_v32"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

    def module_states(self):
        names = {
            "opportunity_hunter": "internet_opportunity_hunter_v27_live.json",
            "product_builder": "autonomous_product_builder_v28_live.json",
            "storefront_sales": "autonomous_storefront_sales_v29_live.json",
            "finance_treasury": "autonomous_finance_treasury_v30_live.json",
            "marketing_acquisition": "autonomous_marketing_acquisition_v31_live.json",
            "revenue_expansion": "autonomous_revenue_expansion_v26_live.json",
            "specialist_workforce": "autonomous_specialist_workforce_v24_live.json",
            "validation": "validation_launch_director_v20_live.json",
            "research": "autonomous_research_network_v22_live.json",
            "learning": "self_improvement_learning_v23_live.json",
        }
        return {k: read_json(self.live / v, {}) for k, v in names.items()}

    def health(self, states):
        expected = {
            "opportunity_hunter": "internet_opportunity_hunter_ready",
            "product_builder": "autonomous_product_builder_ready",
            "storefront_sales": "autonomous_storefront_sales_ready",
            "finance_treasury": "autonomous_finance_treasury_ready",
            "marketing_acquisition": "autonomous_marketing_acquisition_ready",
            "revenue_expansion": "autonomous_revenue_expansion_ready",
            "specialist_workforce": "autonomous_specialist_workforce_ready",
        }
        rows = []
        for name, expected_status in expected.items():
            actual = states.get(name, {}).get("status")
            rows.append({
                "module": name,
                "healthy": actual == expected_status,
                "status": actual or "MISSING",
                "expected": expected_status,
            })
        good = sum(x["healthy"] for x in rows)
        return {
            "modules": rows,
            "healthy": good,
            "total": len(rows),
            "health_percent": round(good / len(rows) * 100) if rows else 0
        }

    def workflows(self, s):
        opportunity = s["opportunity_hunter"]
        builder = s["product_builder"]
        storefront = s["storefront_sales"]
        marketing = s["marketing_acquisition"]
        finance = s["finance_treasury"]
        revenue = s["revenue_expansion"]
        validation = s["validation"]

        workflows = []

        discovered = int(opportunity.get("opportunities_discovered", 0) or 0)
        built = int(builder.get("products_built", 0) or 0)
        products = storefront.get("analytics", {}).get("products_total", 0) or 0
        orders = storefront.get("analytics", {}).get("orders_total", 0) or 0
        campaigns = int(marketing.get("campaigns_total", 0) or 0)
        leads = int(marketing.get("leads_total", 0) or 0)
        verified_revenue = float(finance.get("pnl", {}).get("revenue_usd", 0) or 0)
        top_venture = revenue.get("top_venture")
        ready_for_launch = int(validation.get("ready_for_launch_review", 0) or 0)

        workflows.append({
            "workflow_id": "opportunity_to_product",
            "name": "Opportunity → Product",
            "priority": 100 if built == 0 else 75,
            "dependencies": ["opportunity_hunter", "product_builder"],
            "status": "ACTIVE" if discovered > 0 or built > 0 else "WAITING_FOR_EVIDENCE",
            "next_action": "Build highest-confidence approved opportunity" if discovered > 0 else "Collect more opportunity evidence",
            "assigned_agent": "product_builder",
        })

        workflows.append({
            "workflow_id": "product_to_storefront",
            "name": "Product → Storefront",
            "priority": 95,
            "dependencies": ["product_builder", "storefront_sales"],
            "status": "ACTIVE" if built > 0 and products > 0 else "BLOCKED",
            "next_action": "Prepare storefront review package" if built > 0 else "Wait for product build",
            "assigned_agent": "sales",
        })

        workflows.append({
            "workflow_id": "storefront_to_marketing",
            "name": "Storefront → Marketing",
            "priority": 90,
            "dependencies": ["storefront_sales", "marketing_acquisition"],
            "status": "ACTIVE" if products > 0 and campaigns > 0 else "BLOCKED",
            "next_action": "Collect traffic and conversion evidence" if campaigns > 0 else "Generate campaign plan",
            "assigned_agent": "cmo",
        })

        workflows.append({
            "workflow_id": "marketing_to_sales",
            "name": "Marketing → Sales",
            "priority": 88 if orders == 0 else 70,
            "dependencies": ["marketing_acquisition", "storefront_sales"],
            "status": "ACTIVE" if campaigns > 0 else "BLOCKED",
            "next_action": "Improve first-sale conversion loop" if orders == 0 else "Optimize conversion rate",
            "assigned_agent": "sales",
        })

        workflows.append({
            "workflow_id": "sales_to_finance",
            "name": "Sales → Finance",
            "priority": 82,
            "dependencies": ["storefront_sales", "finance_treasury"],
            "status": "ACTIVE",
            "next_action": "Reconcile verified sales into executive ledger",
            "assigned_agent": "cfo",
        })

        workflows.append({
            "workflow_id": "venture_validation",
            "name": "Venture Validation",
            "priority": 96 if ready_for_launch == 0 else 80,
            "dependencies": ["research", "validation", "revenue_expansion"],
            "status": "ACTIVE",
            "next_action": "Strengthen validation evidence" if ready_for_launch == 0 else "Prepare launch review",
            "assigned_agent": "research",
            "top_venture": top_venture,
        })

        workflows.append({
            "workflow_id": "revenue_feedback_loop",
            "name": "Revenue Feedback Loop",
            "priority": 99 if verified_revenue == 0 else 85,
            "dependencies": ["storefront_sales", "finance_treasury", "learning"],
            "status": "WAITING_FOR_FIRST_VERIFIED_SALE" if verified_revenue == 0 else "ACTIVE",
            "next_action": "Capture first verified sale" if verified_revenue == 0 else "Feed verified performance into pricing and learning",
            "assigned_agent": "ceo",
        })

        for w in workflows:
            w["updated_at"] = now()
        return sorted(workflows, key=lambda x: x["priority"], reverse=True)

    def execution_queue(self, workflows):
        queue = []
        for i, w in enumerate(workflows, 1):
            queue.append({
                "queue_position": i,
                "workflow_id": w["workflow_id"],
                "task": w["next_action"],
                "assigned_agent": w["assigned_agent"],
                "priority": w["priority"],
                "status": "QUEUED_INTERNAL" if w["status"] != "BLOCKED" else "WAITING_DEPENDENCY",
                "external_action_required": False,
            })
        return queue

    def stalled(self, workflows):
        problems = []
        for w in workflows:
            if w["status"] in ("BLOCKED", "WAITING_FOR_EVIDENCE", "WAITING_FOR_FIRST_VERIFIED_SALE"):
                problems.append({
                    "workflow_id": w["workflow_id"],
                    "state": w["status"],
                    "recovery": w["next_action"],
                    "destructive_recovery_allowed": False,
                })
        return problems

    def recurring_jobs(self):
        return [
            {"job": "cross_module_health_check", "cadence": "every_15_minutes", "enabled": True},
            {"job": "workflow_priority_refresh", "cadence": "every_15_minutes", "enabled": True},
            {"job": "finance_reconciliation", "cadence": "hourly", "enabled": True},
            {"job": "marketing_metrics_refresh", "cadence": "hourly", "enabled": True},
            {"job": "portfolio_reprioritization", "cadence": "daily", "enabled": True},
            {"job": "learning_feedback_refresh", "cadence": "daily", "enabled": True},
        ]

    def run_cycle(self):
        states = self.module_states()
        health = self.health(states)
        workflows = self.workflows(states)
        queue = self.execution_queue(workflows)
        stalled = self.stalled(workflows)
        jobs = self.recurring_jobs()

        state = {
            "status": "autonomous_business_operations_ready",
            "operations_health_percent": health["health_percent"],
            "modules_healthy": health["healthy"],
            "modules_total": health["total"],
            "workflow_count": len(workflows),
            "queued_internal_tasks": len(queue),
            "stalled_workflows": len(stalled),
            "top_priority_workflow": workflows[0]["name"] if workflows else None,
            "module_health": health["modules"],
            "workflows": workflows,
            "execution_queue": queue,
            "recovery_candidates": stalled,
            "recurring_internal_jobs": jobs,
            "automatic_external_actions_enabled": False,
            "automatic_spending_enabled": False,
            "automatic_publication_enabled": False,
            "automatic_customer_outreach_enabled": False,
            "destructive_recovery_enabled": False,
            "dashboard_url": "http://127.0.0.1:8794",
            "updated_at": now(),
        }

        write_json(self.runtime / "business_operations_state.json", state)
        write_json(self.live / "autonomous_business_operations_v32_live.json", state)
        write_json(self.records / "workflow_registry.json", {
            "workflows": workflows,
            "updated_at": now(),
        })
        write_json(self.records / "execution_queue.json", {
            "queue": queue,
            "updated_at": now(),
        })
        write_json(self.records / "recovery_candidates.json", {
            "recovery_candidates": stalled,
            "updated_at": now(),
        })

        append_jsonl(self.live / "full_autonomy_journal.jsonl", {
            "ts": now(),
            "event": "autonomous_business_operations_v32_cycle",
            "event_type": "autonomous_business_operations_v32_cycle",
            "state": {
                "operations_health_percent": state["operations_health_percent"],
                "workflow_count": state["workflow_count"],
                "queued_internal_tasks": state["queued_internal_tasks"],
                "top_priority_workflow": state["top_priority_workflow"],
            }
        })
        return state
