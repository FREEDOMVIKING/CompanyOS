from pathlib import Path
from .storage import now, read_json, atomic_write_json, append_jsonl
from .planner import plan_for
from .builders import (
    build_workspace, build_product_package, build_website_bundle,
    build_checkout_manifest, build_delivery_manifest, build_review_packet
)
from .rollback import create_snapshot

class AutonomousExecutionEngineV38:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/autonomous_execution_engine_v38_1600001_1650000"
        self.records = self.home / "execution_engine_records_v38"
        self.workspaces = self.home / "execution_workspaces_v38"
        self.history_file = self.records / "execution_history.jsonl"
        for p in (self.live, self.runtime, self.records, self.workspaces):
            p.mkdir(parents=True, exist_ok=True)

    def approved_ventures(self):
        data = read_json(self.live / "approved_for_launch_prep_v37.json", {"ventures":[]})
        return data.get("ventures", []) or []

    def existing_state(self):
        return read_json(self.live / "autonomous_execution_engine_v38_live.json", {})

    def existing_index(self):
        state = self.existing_state()
        return {x.get("execution_id"): x for x in state.get("executions", []) or []}

    def prepare_one(self, approved):
        plan = plan_for(approved)
        ws = build_workspace(self.workspaces, plan)
        rollback = create_snapshot(ws, plan)

        product = build_product_package(ws, plan)
        website = build_website_bundle(ws, plan)
        checkout = build_checkout_manifest(ws, plan)
        delivery = build_delivery_manifest(ws, plan)

        artifacts = {
            "workspace": str(ws),
            "product_package": str(ws / "product/product_package.json"),
            "website_index": str(ws / "website/index.html"),
            "website_manifest": str(ws / "website/website_manifest.json"),
            "checkout_manifest": str(ws / "checkout/checkout_manifest.json"),
            "customer_delivery_manifest": str(ws / "delivery/customer_delivery_manifest.json"),
            "rollback_snapshot": str(ws / "rollback/rollback_snapshot.json"),
        }

        packet = build_review_packet(ws, plan, artifacts)
        completed = [
            "workspace",
            "rollback_snapshot",
            "product_package",
            "website_bundle",
            "checkout_manifest",
            "customer_delivery_manifest",
            "external_execution_review_packet",
        ]

        row = {
            **plan,
            "status": "READY_FOR_EXTERNAL_EXECUTION_REVIEW",
            "completed_steps": completed,
            "failed_steps": [],
            "artifacts": artifacts,
            "review_packet": packet,
            "automatic_external_execution_enabled": True,
            "automatic_publication_enabled": True,
            "automatic_spending_enabled": True,
            "wallet_signing_enabled": True,
            "updated_at": now(),
        }
        append_jsonl(self.history_file, {
            "event":"execution_prepared",
            "execution_id":row["execution_id"],
            "venture_id":row["venture_id"],
            "status":row["status"],
            "ts":now()
        })
        return row

    def run_cycle(self):
        approved = self.approved_ventures()
        old = self.existing_index()
        executions = []

        for venture in approved:
            plan = plan_for(venture)
            prior = old.get(plan["execution_id"])
            if prior and prior.get("status") == "READY_FOR_EXTERNAL_EXECUTION_REVIEW":
                executions.append(prior)
            else:
                executions.append(self.prepare_one(venture))

        ready = sum(x.get("status") == "READY_FOR_EXTERNAL_EXECUTION_REVIEW" for x in executions)
        failed = sum(bool(x.get("failed_steps")) for x in executions)

        state = {
            "status":"autonomous_execution_engine_ready",
            "approved_ventures_received":len(approved),
            "executions_total":len(executions),
            "ready_for_external_execution_review":ready,
            "failed_executions":failed,
            "active_executions":sum(x.get("status") not in ("READY_FOR_EXTERNAL_EXECUTION_REVIEW","FAILED") for x in executions),
            "executions":executions,
            "automatic_external_execution_enabled":True,
            "automatic_publication_enabled":True,
            "automatic_domain_purchase_enabled":True,
            "automatic_spending_enabled":True,
            "wallet_signing_enabled":True,
            "dashboard_url":"http://127.0.0.1:8800",
            "updated_at":now(),
        }

        atomic_write_json(self.runtime / "execution_engine_state.json", state)
        atomic_write_json(self.live / "autonomous_execution_engine_v38_live.json", state)
        atomic_write_json(self.live / "external_execution_review_queue_v38.json", {
            "executions":[
                {
                    "execution_id":x["execution_id"],
                    "venture_id":x["venture_id"],
                    "venture_name":x["venture_name"],
                    "status":x["status"],
                    "review_packet":x["artifacts"].get("workspace") + "/external_execution_review_packet.json",
                    "external_execution_enabled":True
                }
                for x in executions
                if x.get("status") == "READY_FOR_EXTERNAL_EXECUTION_REVIEW"
            ],
            "updated_at":now()
        })
        return state
