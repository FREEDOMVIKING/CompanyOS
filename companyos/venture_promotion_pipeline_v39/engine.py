from pathlib import Path
from .storage import now, read_json, atomic_write_json, append_jsonl

class VenturePromotionPipelineV39:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/venture_promotion_pipeline_v39_1650001_1700000"
        self.records = self.home / "venture_promotion_records_v39"
        self.history = self.records / "promotion_history.jsonl"
        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

    def source_v37(self):
        # Primary source written by V37.
        data = read_json(self.live / "approved_for_launch_prep_v37.json", {})
        ventures = data.get("ventures", []) or []
        if ventures:
            return ventures

        # Fallback: derive from V37 live state.
        state = read_json(self.live / "autonomous_launch_control_v37_live.json", {})
        return state.get("approved_for_launch_prep", []) or []

    def normalize(self, v):
        return {
            "venture_id": v.get("venture_id"),
            "venture_name": v.get("venture_name") or v.get("name"),
            "review_id": v.get("review_id"),
            "launch_score": float(v.get("launch_score", 0) or 0),
            "status": "APPROVED_FOR_LAUNCH_PREP",
            "external_execution_enabled": False,
            "financial_commitment_enabled": False,
        }

    def validate(self, v):
        problems = []
        if not v.get("venture_id"): problems.append("missing_venture_id")
        if not (v.get("venture_name") or v.get("name")): problems.append("missing_venture_name")
        if not v.get("review_id"): problems.append("missing_review_id")
        if str(v.get("status", "")).upper() != "APPROVED_FOR_LAUNCH_PREP":
            problems.append("not_approved_for_launch_prep")
        if v.get("external_execution_enabled") is True:
            problems.append("external_execution_must_remain_disabled")
        return problems

    def run_cycle(self):
        source = self.source_v37()
        valid, failed = [], []

        for v in source:
            problems = self.validate(v)
            if problems:
                failed.append({
                    "venture_id": v.get("venture_id"),
                    "venture_name": v.get("venture_name") or v.get("name"),
                    "review_id": v.get("review_id"),
                    "status": "PROMOTION_FAILED",
                    "problems": problems,
                    "retryable": True,
                    "updated_at": now(),
                })
                continue
            valid.append(self.normalize(v))

        # Deduplicate by venture_id+review_id.
        seen = set()
        promoted = []
        for v in valid:
            key = (v["venture_id"], v["review_id"])
            if key in seen:
                continue
            seen.add(key)
            promoted.append(v)

        # Canonical handoff consumed by V38.
        atomic_write_json(self.live / "approved_for_launch_prep_v37.json", {
            "ventures": promoted,
            "updated_at": now(),
            "written_by": "venture_promotion_pipeline_v39"
        })

        # Additional observability files.
        atomic_write_json(self.live / "v39_promoted_for_execution.json", {
            "ventures": promoted,
            "updated_at": now()
        })
        atomic_write_json(self.records / "failed_promotions.json", {
            "failed": failed,
            "updated_at": now()
        })

        for v in promoted:
            append_jsonl(self.history, {
                "event": "venture_promoted_to_v38_intake",
                "venture_id": v["venture_id"],
                "review_id": v["review_id"],
                "ts": now()
            })

        state = {
            "status": "venture_promotion_pipeline_ready",
            "source_approvals": len(source),
            "promoted": len(promoted),
            "failed": len(failed),
            "pending": 0,
            "promotions": promoted,
            "failures": failed,
            "v38_intake_file": str(self.live / "approved_for_launch_prep_v37.json"),
            "automatic_external_execution_enabled": False,
            "automatic_publication_enabled": False,
            "automatic_spending_enabled": False,
            "dashboard_url": "http://127.0.0.1:8801",
            "updated_at": now()
        }

        atomic_write_json(self.runtime / "venture_promotion_pipeline_state.json", state)
        atomic_write_json(self.live / "venture_promotion_pipeline_v39_live.json", state)
        return state
