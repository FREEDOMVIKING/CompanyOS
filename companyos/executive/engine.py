from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .audit import run_self_audit
from .capital import allocate_capital
from .cascade import detect_failure_cascades
from .dependencies import analyze_dependencies
from .memory import compress_memory
from .models import AllocationDecision, Venture, Worker
from .prioritizer import rank_ventures, score_venture
from .scaling import recommend_scale_action
from .storage import JsonStore
from .workforce import assign_workers


class ExecutiveEngine:
    def __init__(self, runtime_dir: Path):
        self.store = JsonStore(runtime_dir)

    def run_cycle(
        self,
        ventures: List[Venture],
        workers: List[Worker],
        available_capital: float,
    ) -> Dict:
        timestamp = datetime.now(timezone.utc).isoformat()
        ranking = rank_ventures(ventures)
        dependency_report = analyze_dependencies(ventures)
        cascades = detect_failure_cascades(ventures, dependency_report)
        capital = allocate_capital(ventures, available_capital)
        workforce = assign_workers(ventures, workers)

        decisions = []
        for venture in ventures:
            allocation = capital["allocations"].get(venture.venture_id, {})
            reasons = [
                f"priority_score={score_venture(venture)}",
                f"stage={venture.stage}",
                f"risk={venture.risk}",
            ]
            if venture.venture_id in dependency_report["blocked_by_dependency"]:
                reasons.append("dependency_attention_required")
            decisions.append(
                AllocationDecision(
                    venture_id=venture.venture_id,
                    priority_score=score_venture(venture),
                    capital_proposed=float(allocation.get("proposed", 0.0)),
                    workers_proposed=workforce.get(venture.venture_id, []),
                    scale_action=recommend_scale_action(venture),
                    approval_required=bool(allocation.get("approval_required", False)),
                    reasons=reasons,
                ).to_dict()
            )

        audit = run_self_audit(ventures, workers, capital, dependency_report)
        prior_events = self.store.read("executive_events.json", [])
        memory = compress_memory(prior_events)

        result = {
            "phase": "18201-18300",
            "timestamp": timestamp,
            "ranking": ranking,
            "capital": capital,
            "workforce": workforce,
            "dependencies": dependency_report,
            "failure_cascades": cascades,
            "decisions": decisions,
            "audit": audit,
            "memory_summary": memory,
            "safety": {
                "financial_execution": "proposal_only",
                "irreversible_external_actions": "approval_gate_required",
            },
        }

        self.store.write("latest_priority_ranking.json", ranking)
        self.store.write("latest_capital_proposals.json", capital)
        self.store.write("latest_workforce_plan.json", workforce)
        self.store.write("latest_dependency_report.json", dependency_report)
        self.store.write("latest_failure_cascades.json", cascades)
        self.store.write("latest_executive_decisions.json", decisions)
        self.store.write("latest_self_audit.json", audit)
        self.store.write("ceo_memory_compressed.json", memory)
        self.store.write("executive_dashboard.json", result)
        self.store.append_event({
            "type": "executive_cycle",
            "timestamp": timestamp,
            "outcome": "passed" if audit["passed"] else "attention_required",
            "lesson": "Preserve capital reserve and isolate risky dependencies before scaling.",
        })
        return result
