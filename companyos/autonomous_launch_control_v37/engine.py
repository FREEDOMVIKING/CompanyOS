from pathlib import Path
from .storage import now, read_json, atomic_write_json, append_jsonl, decision_hash
from .models import LaunchDecision

ALLOWED_DECISIONS = {"APPROVE", "HOLD", "REJECT"}

class AutonomousLaunchControlV37:
    def __init__(self, home):
        self.home = Path(home)
        self.live = self.home / ".companyos_runtime"
        self.runtime = self.home / "companyos_runtime/autonomous_launch_control_v37_1550001_1600000"
        self.records = self.home / "launch_control_records_v37"
        self.decisions_file = self.records / "decisions.json"
        self.history_file = self.records / "launch_history.jsonl"
        self.approved_file = self.records / "approved_for_launch_prep.json"
        self.settings_file = self.records / "settings.json"

        for p in (self.live, self.runtime, self.records):
            p.mkdir(parents=True, exist_ok=True)

        if not self.decisions_file.exists():
            atomic_write_json(self.decisions_file, {"decisions": []})
        if not self.approved_file.exists():
            atomic_write_json(self.approved_file, {"ventures": []})
        if not self.settings_file.exists():
            atomic_write_json(self.settings_file, {
                "require_explicit_approval": True,
                "automatic_external_launch_enabled": False,
                "automatic_publication_enabled": False,
                "automatic_spending_enabled": False
            })

    def launch_director_state(self):
        return read_json(self.live / "autonomous_launch_director_v36_live.json", {})

    def source_reviews(self):
        state = self.launch_director_state()
        reviews = state.get("launch_review_queue", []) or []
        ventures = {v.get("venture_id"): v for v in state.get("ventures", []) or []}

        normalized = []
        for review in reviews:
            v = ventures.get(review.get("venture_id"), {})
            normalized.append({
                "review_id": review.get("review_id"),
                "venture_id": review.get("venture_id"),
                "venture_name": review.get("venture_name") or v.get("name"),
                "launch_score": float(review.get("launch_score", v.get("launch_score", 0)) or 0),
                "launch_state": review.get("launch_state") or v.get("launch_state"),
                "status": review.get("status", "EXECUTIVE_REVIEW_REQUIRED"),
                "blockers": v.get("blockers", []),
                "recommendation": v.get("recommendation"),
            })
        return normalized

    def decisions(self):
        return read_json(self.decisions_file, {"decisions":[]}).get("decisions", [])

    def decision_index(self):
        return {d.get("review_id"): d for d in self.decisions()}

    def effective_reviews(self):
        decisions = self.decision_index()
        rows = []
        for r in self.source_reviews():
            d = decisions.get(r["review_id"])
            row = dict(r)
            if d:
                row["executive_decision"] = d.get("decision")
                row["executive_reason"] = d.get("reason")
                row["decision_at"] = d.get("created_at")
                row["decision_hash"] = d.get("decision_hash")
                row["effective_status"] = d.get("new_status")
            else:
                row["executive_decision"] = None
                row["effective_status"] = "PENDING_EXECUTIVE_REVIEW"
            rows.append(row)
        return rows

    def make_decision(self, review_id, decision, reason="", actor="local_executive"):
        decision = str(decision).upper().strip()
        if decision not in ALLOWED_DECISIONS:
            raise ValueError("decision must be APPROVE, HOLD, or REJECT")

        review = next((r for r in self.source_reviews() if r.get("review_id") == review_id), None)
        if not review:
            raise KeyError("review_id not found in V36 launch review queue")

        if decision == "APPROVE":
            new_status = "APPROVED_FOR_LAUNCH_PREP"
        elif decision == "HOLD":
            new_status = "HELD_FOR_REVIEW"
        else:
            new_status = "REJECTED_BY_EXECUTIVE"

        record = LaunchDecision(
            review_id=review_id,
            venture_id=review.get("venture_id"),
            venture_name=review.get("venture_name"),
            decision=decision,
            reason=reason or "",
            actor=actor,
            created_at=now(),
            source_launch_score=float(review.get("launch_score", 0) or 0),
            previous_status=review.get("status", "EXECUTIVE_REVIEW_REQUIRED"),
            new_status=new_status
        ).to_dict()
        record["decision_hash"] = decision_hash(record)

        data = read_json(self.decisions_file, {"decisions":[]})
        existing = [d for d in data.get("decisions", []) if d.get("review_id") != review_id]
        existing.append(record)
        atomic_write_json(self.decisions_file, {"decisions": existing, "updated_at": now()})
        append_jsonl(self.history_file, record)

        self._sync_approved_queue()
        self.run_cycle()
        return record

    def _sync_approved_queue(self):
        approved = []
        for d in self.decisions():
            if d.get("decision") == "APPROVE":
                approved.append({
                    "venture_id": d.get("venture_id"),
                    "venture_name": d.get("venture_name"),
                    "review_id": d.get("review_id"),
                    "launch_score": d.get("source_launch_score"),
                    "status": "APPROVED_FOR_LAUNCH_PREP",
                    "approved_at": d.get("created_at"),
                    "external_execution_enabled": False,
                    "financial_commitment_enabled": False
                })
        atomic_write_json(self.approved_file, {"ventures": approved, "updated_at": now()})
        atomic_write_json(self.live / "approved_for_launch_prep_v37.json", {"ventures": approved, "updated_at": now()})
        return approved

    def analytics(self, reviews):
        pending = sum(r.get("effective_status") == "PENDING_EXECUTIVE_REVIEW" for r in reviews)
        approved = sum(r.get("executive_decision") == "APPROVE" for r in reviews)
        held = sum(r.get("executive_decision") == "HOLD" for r in reviews)
        rejected = sum(r.get("executive_decision") == "REJECT" for r in reviews)
        avg_score = round(sum(float(r.get("launch_score",0) or 0) for r in reviews) / len(reviews), 2) if reviews else 0
        return {
            "reviews_total": len(reviews),
            "pending": pending,
            "approved": approved,
            "held": held,
            "rejected": rejected,
            "average_launch_score": avg_score
        }

    def run_cycle(self):
        reviews = self.effective_reviews()
        approved_queue = self._sync_approved_queue()
        analytics = self.analytics(reviews)
        launch_state = self.launch_director_state()

        state = {
            "status": "autonomous_launch_control_ready",
            "source_v36_status": launch_state.get("status"),
            "reviews": reviews,
            "analytics": analytics,
            "approved_for_launch_prep": approved_queue,
            "top_candidate": reviews[0].get("venture_name") if reviews else None,
            "top_candidate_score": reviews[0].get("launch_score") if reviews else 0,
            "require_explicit_approval": True,
            "automatic_external_launch_enabled": False,
            "automatic_publication_enabled": False,
            "automatic_spending_enabled": False,
            "wallet_signing_enabled": False,
            "dashboard_url": "http://127.0.0.1:8799",
            "updated_at": now()
        }

        atomic_write_json(self.runtime / "launch_control_state.json", state)
        atomic_write_json(self.live / "autonomous_launch_control_v37_live.json", state)
        atomic_write_json(self.live / "executive_approval_handoff_v37.json", {
            "approved_for_launch_prep": approved_queue,
            "external_execution_enabled": False,
            "updated_at": now()
        })
        return state
