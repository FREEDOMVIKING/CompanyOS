#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
STATE_DIR = ROOT / "companyos_runtime" / "phase18201_18300"
STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class VentureSnapshot:
    venture_id: str
    revenue_signal: float
    margin_signal: float
    throughput: float
    health_score: float
    backlog: int
    idle_workers: int
    required_workers: int
    risk_score: float
    external_blocker: bool = False


@dataclass(slots=True)
class OpportunityRecord:
    opportunity_id: str
    title: str
    expected_value: float
    urgency: float
    confidence: float
    required_capabilities: list[str]
    related_ventures: list[str]


class ExecutiveMissionControl:
    """Portfolio-wide executive coordination, memory, KPIs, and event routing."""

    def __init__(self, state_dir: Path = STATE_DIR) -> None:
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write(path: Path, payload: Any) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    @staticmethod
    def _append(path: Path, payload: Any) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    @staticmethod
    def _id(prefix: str, payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:12]}"

    def aggregate_kpis(self, ventures: list[VentureSnapshot]) -> dict[str, Any]:
        if not ventures:
            payload = {
                "generated_at": time.time(),
                "venture_count": 0,
                "portfolio_health": 0.0,
                "average_margin_signal": 0.0,
                "average_throughput": 0.0,
                "total_backlog": 0,
                "total_idle_workers": 0,
                "blocked_venture_count": 0,
            }
        else:
            payload = {
                "generated_at": time.time(),
                "venture_count": len(ventures),
                "portfolio_health": round(
                    statistics.fmean(v.health_score for v in ventures), 4
                ),
                "average_margin_signal": round(
                    statistics.fmean(v.margin_signal for v in ventures), 6
                ),
                "average_throughput": round(
                    statistics.fmean(v.throughput for v in ventures), 6
                ),
                "total_backlog": sum(v.backlog for v in ventures),
                "total_idle_workers": sum(v.idle_workers for v in ventures),
                "blocked_venture_count": sum(
                    1 for v in ventures if v.external_blocker
                ),
            }

        self._write(self.state_dir / "portfolio_kpis.json", payload)
        return payload

    def predict_health_trends(
        self,
        ventures: list[VentureSnapshot],
    ) -> list[dict[str, Any]]:
        trends = []

        for venture in ventures:
            pressure = min(
                1.0,
                max(
                    0.0,
                    (venture.backlog / 20.0) * 0.35
                    + (1.0 - venture.throughput) * 0.25
                    + venture.risk_score * 0.20
                    + (1.0 - venture.health_score / 100.0) * 0.20,
                ),
            )

            if venture.external_blocker:
                direction = "critical"
                projected_health = max(0.0, venture.health_score - 20.0)
            elif pressure >= 0.65:
                direction = "declining"
                projected_health = max(0.0, venture.health_score - 10.0)
            elif pressure <= 0.30:
                direction = "improving"
                projected_health = min(100.0, venture.health_score + 5.0)
            else:
                direction = "stable"
                projected_health = venture.health_score

            trends.append(
                {
                    "venture_id": venture.venture_id,
                    "direction": direction,
                    "pressure_score": round(pressure, 6),
                    "projected_health": round(projected_health, 4),
                }
            )

        trends.sort(
            key=lambda item: (
                item["direction"] == "critical",
                item["direction"] == "declining",
                item["pressure_score"],
            ),
            reverse=True,
        )
        self._write(self.state_dir / "venture_health_trends.json", trends)
        return trends

    def resource_exchange(
        self,
        ventures: list[VentureSnapshot],
    ) -> dict[str, Any]:
        donors = [
            venture
            for venture in ventures
            if venture.idle_workers > 0 and not venture.external_blocker
        ]
        receivers = [
            venture
            for venture in ventures
            if venture.required_workers > 0 and not venture.external_blocker
        ]

        transfers = []
        donor_state = {
            venture.venture_id: venture.idle_workers
            for venture in donors
        }

        receivers.sort(
            key=lambda venture: (
                venture.backlog,
                venture.health_score < 60,
                venture.revenue_signal,
            ),
            reverse=True,
        )

        for receiver in receivers:
            needed = receiver.required_workers
            for donor in donors:
                available = donor_state[donor.venture_id]
                if available <= 0 or needed <= 0:
                    continue
                moved = min(available, needed)
                donor_state[donor.venture_id] -= moved
                needed -= moved
                transfers.append(
                    {
                        "from_venture": donor.venture_id,
                        "to_venture": receiver.venture_id,
                        "workers": moved,
                        "external_action_executed": False,
                        "financial_action_executed": False,
                    }
                )

        payload = {
            "generated_at": time.time(),
            "transfers": transfers,
            "external_actions_require_existing_gate": True,
            "financial_actions_require_existing_gate": True,
        }
        self._write(self.state_dir / "resource_exchange_plan.json", payload)
        return payload

    def opportunity_queue(
        self,
        opportunities: list[OpportunityRecord],
        available_capabilities: set[str],
    ) -> list[dict[str, Any]]:
        queue = []

        for opportunity in opportunities:
            capability_match = all(
                capability in available_capabilities
                for capability in opportunity.required_capabilities
            )
            score = round(
                opportunity.expected_value * 0.40
                + opportunity.urgency * 0.25
                + opportunity.confidence * 0.25
                + (0.10 if capability_match else 0.0),
                6,
            )
            queue.append(
                {
                    "opportunity_id": opportunity.opportunity_id,
                    "title": opportunity.title,
                    "score": score,
                    "capability_match": capability_match,
                    "related_ventures": opportunity.related_ventures,
                    "action": (
                        "advance_to_internal_planning"
                        if capability_match
                        else "request_internal_capability"
                    ),
                }
            )

        queue.sort(key=lambda item: item["score"], reverse=True)
        payload = {
            "generated_at": time.time(),
            "queue": queue,
        }
        self._write(self.state_dir / "strategic_opportunity_queue.json", payload)
        return queue

    def publish_event(
        self,
        event_type: str,
        source: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        event = {
            "event_id": self._id(
                "event",
                {
                    "event_type": event_type,
                    "source": source,
                    "payload": payload,
                    "at": time.time(),
                },
            ),
            "event_type": event_type,
            "source": source,
            "payload": payload,
            "created_at": time.time(),
            "external_action_executed": False,
            "financial_action_executed": False,
        }
        self._append(self.state_dir / "enterprise_event_bus.jsonl", event)
        return event

    def executive_memory(
        self,
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        timeline = sorted(
            events,
            key=lambda event: event.get("created_at", 0.0),
        )
        payload = {
            "generated_at": time.time(),
            "event_count": len(timeline),
            "timeline": timeline,
        }
        self._write(self.state_dir / "executive_memory_timeline.json", payload)
        return payload

    def performance_analysis(
        self,
        ventures: list[VentureSnapshot],
        kpis: dict[str, Any],
        trends: list[dict[str, Any]],
    ) -> dict[str, Any]:
        declining = {
            item["venture_id"]
            for item in trends
            if item["direction"] in {"declining", "critical"}
        }

        ranked = sorted(
            (
                {
                    "venture_id": venture.venture_id,
                    "performance_score": round(
                        venture.revenue_signal * 0.30
                        + venture.margin_signal * 0.25
                        + venture.throughput * 0.20
                        + (venture.health_score / 100.0) * 0.15
                        + (1.0 - venture.risk_score) * 0.10,
                        6,
                    ),
                    "needs_recovery": venture.venture_id in declining,
                }
                for venture in ventures
            ),
            key=lambda item: item["performance_score"],
            reverse=True,
        )

        payload = {
            "generated_at": time.time(),
            "portfolio_kpis": kpis,
            "venture_rankings": ranked,
            "recovery_candidates": [
                item["venture_id"]
                for item in ranked
                if item["needs_recovery"]
            ],
        }
        self._write(
            self.state_dir / "organization_performance_analysis.json",
            payload,
        )
        return payload

    def mission_control_dashboard(
        self,
        kpis: dict[str, Any],
        opportunities: list[dict[str, Any]],
        trends: list[dict[str, Any]],
        resource_plan: dict[str, Any],
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        top_opportunity = opportunities[0] if opportunities else None
        payload = {
            "generated_at": time.time(),
            "status": "mission_control_online",
            "portfolio_kpis": kpis,
            "top_opportunity": top_opportunity,
            "declining_or_critical_ventures": [
                item["venture_id"]
                for item in trends
                if item["direction"] in {"declining", "critical"}
            ],
            "planned_worker_transfers": len(resource_plan["transfers"]),
            "top_performing_venture": (
                performance["venture_rankings"][0]["venture_id"]
                if performance["venture_rankings"]
                else None
            ),
            "external_actions_enabled": False,
            "financial_actions_enabled": False,
        }
        self._write(
            self.state_dir / "executive_mission_control_dashboard.json",
            payload,
        )
        return payload

    def demo(self) -> dict[str, Any]:
        ventures = [
            VentureSnapshot(
                "venture_alpha",
                revenue_signal=0.90,
                margin_signal=0.78,
                throughput=0.82,
                health_score=91,
                backlog=4,
                idle_workers=2,
                required_workers=0,
                risk_score=0.16,
            ),
            VentureSnapshot(
                "venture_beta",
                revenue_signal=0.74,
                margin_signal=0.62,
                throughput=0.49,
                health_score=68,
                backlog=13,
                idle_workers=0,
                required_workers=2,
                risk_score=0.28,
            ),
            VentureSnapshot(
                "venture_gamma",
                revenue_signal=0.66,
                margin_signal=0.58,
                throughput=0.35,
                health_score=47,
                backlog=16,
                idle_workers=0,
                required_workers=1,
                risk_score=0.42,
            ),
            VentureSnapshot(
                "venture_delta",
                revenue_signal=0.81,
                margin_signal=0.70,
                throughput=0.20,
                health_score=31,
                backlog=11,
                idle_workers=1,
                required_workers=0,
                risk_score=0.55,
                external_blocker=True,
            ),
        ]

        opportunities = [
            OpportunityRecord(
                "opp_alpha",
                "Shared customer analytics service",
                0.91,
                0.76,
                0.86,
                ["python", "analytics"],
                ["venture_alpha", "venture_beta"],
            ),
            OpportunityRecord(
                "opp_beta",
                "Automated operations dashboard",
                0.78,
                0.88,
                0.80,
                ["python", "frontend"],
                ["venture_beta", "venture_gamma"],
            ),
            OpportunityRecord(
                "opp_gamma",
                "External partner integration",
                0.89,
                0.65,
                0.62,
                ["integration"],
                ["venture_delta"],
            ),
        ]

        capabilities = {"python", "analytics", "frontend"}
        kpis = self.aggregate_kpis(ventures)
        trends = self.predict_health_trends(ventures)
        resource_plan = self.resource_exchange(ventures)
        opportunity_queue = self.opportunity_queue(
            opportunities,
            capabilities,
        )

        events = [
            self.publish_event(
                "portfolio_kpis_updated",
                "kpi_aggregator",
                kpis,
            ),
            self.publish_event(
                "resource_exchange_planned",
                "resource_exchange",
                {"transfer_count": len(resource_plan["transfers"])},
            ),
            self.publish_event(
                "opportunity_queue_updated",
                "opportunity_queue",
                {"top_opportunity": opportunity_queue[0]["opportunity_id"]},
            ),
        ]

        memory = self.executive_memory(events)
        performance = self.performance_analysis(
            ventures,
            kpis,
            trends,
        )
        dashboard = self.mission_control_dashboard(
            kpis,
            opportunity_queue,
            trends,
            resource_plan,
            performance,
        )

        return {
            "ok": True,
            "kpis": kpis,
            "trends": trends,
            "resource_exchange": resource_plan,
            "opportunity_queue": opportunity_queue,
            "memory": memory,
            "performance": performance,
            "dashboard": dashboard,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["demo", "status"])
    args = parser.parse_args()

    control = ExecutiveMissionControl()
    result = (
        control.demo()
        if args.action == "demo"
        else {
            "ok": True,
            "state_files": sorted(
                path.name for path in control.state_dir.glob("*")
            ),
        }
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
