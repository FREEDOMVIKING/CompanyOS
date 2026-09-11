#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

ROOT = Path.home() / "companyos"
STATE_DIR = ROOT / "companyos_runtime" / "phase17701_17800"
STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class ResourcePool:
    resource_id: str
    kind: str
    capacity: float
    cost_per_unit: float
    capabilities: set[str] = field(default_factory=set)


@dataclass(slots=True)
class VentureDemand:
    venture_id: str
    priority: float
    expected_value: float
    risk: float
    required_capabilities: set[str]
    requested_capacity: float


@dataclass(slots=True)
class KnowledgeAsset:
    asset_id: str
    source_venture_id: str
    topic: str
    quality: float
    reusable: bool
    tags: set[str] = field(default_factory=set)


@dataclass(slots=True)
class PortfolioLearning:
    learning_id: str
    source_venture_id: str
    lesson: str
    confidence: float
    recommended_action: str
    created_at: float


class AutonomousPortfolioOrchestrator:
    """Coordinates shared resources, knowledge, and learning across ventures."""

    def __init__(self, state_dir: Path = STATE_DIR) -> None:
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _stable_id(prefix: str, payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True, default=list).encode("utf-8")
        return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:12]}"

    def allocate_shared_resources(
        self,
        resources: Iterable[ResourcePool],
        demands: Iterable[VentureDemand],
    ) -> list[dict[str, Any]]:
        resources = list(resources)
        demands = sorted(
            list(demands),
            key=lambda d: (
                (d.expected_value * d.priority * max(1.0 - d.risk, 0.0)),
                d.priority,
            ),
            reverse=True,
        )

        remaining = {r.resource_id: max(r.capacity, 0.0) for r in resources}
        allocations: list[dict[str, Any]] = []

        for demand in demands:
            needed = max(demand.requested_capacity, 0.0)
            for resource in resources:
                if needed <= 0:
                    break
                if demand.required_capabilities and not (
                    resource.capabilities & demand.required_capabilities
                ):
                    continue

                available = remaining[resource.resource_id]
                granted = min(available, needed)
                if granted <= 0:
                    continue

                allocations.append(
                    {
                        "venture_id": demand.venture_id,
                        "resource_id": resource.resource_id,
                        "kind": resource.kind,
                        "granted_capacity": round(granted, 4),
                        "estimated_cost": round(granted * resource.cost_per_unit, 2),
                        "priority": demand.priority,
                        "risk": demand.risk,
                        "external_commitment_created": False,
                    }
                )
                remaining[resource.resource_id] = round(available - granted, 4)
                needed = round(needed - granted, 4)

            if needed > 0:
                allocations.append(
                    {
                        "venture_id": demand.venture_id,
                        "resource_id": None,
                        "kind": "unfilled",
                        "granted_capacity": 0.0,
                        "estimated_cost": 0.0,
                        "priority": demand.priority,
                        "risk": demand.risk,
                        "unfilled_capacity": needed,
                        "external_commitment_created": False,
                    }
                )

        payload = {
            "generated_at": time.time(),
            "allocations": allocations,
            "remaining_capacity": remaining,
            "external_commitments_created": False,
            "requires_existing_approval_gates": True,
        }
        self._write_json(self.state_dir / "latest_resource_plan.json", payload)
        return allocations

    def route_knowledge(
        self,
        assets: Iterable[KnowledgeAsset],
        venture_topics: dict[str, set[str]],
    ) -> list[dict[str, Any]]:
        routes: list[dict[str, Any]] = []
        for asset in assets:
            if not asset.reusable or asset.quality < 0.6:
                continue
            asset_topics = {asset.topic, *asset.tags}
            for venture_id, topics in venture_topics.items():
                if venture_id == asset.source_venture_id:
                    continue
                overlap = asset_topics & topics
                if not overlap:
                    continue
                routes.append(
                    {
                        "asset_id": asset.asset_id,
                        "from_venture": asset.source_venture_id,
                        "to_venture": venture_id,
                        "matched_topics": sorted(overlap),
                        "quality": asset.quality,
                        "copy_only": True,
                    }
                )

        self._write_json(self.state_dir / "latest_knowledge_routes.json", routes)
        return routes

    def record_learning(
        self,
        source_venture_id: str,
        lesson: str,
        confidence: float,
        recommended_action: str,
    ) -> PortfolioLearning:
        confidence = max(0.0, min(float(confidence), 1.0))
        payload = {
            "source_venture_id": source_venture_id,
            "lesson": lesson,
            "confidence": confidence,
            "recommended_action": recommended_action,
        }
        learning = PortfolioLearning(
            learning_id=self._stable_id("learning", payload),
            source_venture_id=source_venture_id,
            lesson=lesson,
            confidence=confidence,
            recommended_action=recommended_action,
            created_at=time.time(),
        )
        self._append_jsonl(self.state_dir / "portfolio_learning.jsonl", asdict(learning))
        return learning

    def refine_strategy(
        self,
        current_weights: dict[str, float],
        learnings: Iterable[PortfolioLearning],
    ) -> dict[str, Any]:
        updated = {key: float(value) for key, value in current_weights.items()}
        applied: list[str] = []

        for learning in learnings:
            if learning.confidence < 0.65:
                continue

            action = learning.recommended_action.lower().strip()
            if action.startswith("increase:"):
                key = action.split(":", 1)[1].strip()
                updated[key] = round(updated.get(key, 0.0) + 0.05 * learning.confidence, 4)
                applied.append(learning.learning_id)
            elif action.startswith("decrease:"):
                key = action.split(":", 1)[1].strip()
                updated[key] = round(max(updated.get(key, 0.0) - 0.05 * learning.confidence, 0.0), 4)
                applied.append(learning.learning_id)

        total = sum(updated.values())
        if total > 0:
            updated = {key: round(value / total, 4) for key, value in updated.items()}

        payload = {
            "generated_at": time.time(),
            "previous_weights": current_weights,
            "updated_weights": updated,
            "applied_learning_ids": applied,
            "automatic_external_changes": False,
        }
        self._write_json(self.state_dir / "latest_strategy_refinement.json", payload)
        return payload

    def command_center(
        self,
        allocations: list[dict[str, Any]],
        knowledge_routes: list[dict[str, Any]],
        learnings: Iterable[PortfolioLearning],
    ) -> dict[str, Any]:
        learnings = list(learnings)
        ventures = sorted(
            {
                row["venture_id"]
                for row in allocations
                if row.get("venture_id")
            }
            | {
                route["to_venture"]
                for route in knowledge_routes
            }
        )

        command = {
            "generated_at": time.time(),
            "active_ventures": ventures,
            "resource_allocation_count": len(allocations),
            "knowledge_route_count": len(knowledge_routes),
            "learning_count": len(learnings),
            "high_confidence_learning_count": sum(
                1 for item in learnings if item.confidence >= 0.75
            ),
            "external_actions_allowed": False,
            "financial_transfers_allowed": False,
        }
        self._write_json(self.state_dir / "latest_command_center.json", command)
        return command

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=list) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    @staticmethod
    def _append_jsonl(path: Path, payload: Any) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, default=list) + "\n")


def demo() -> dict[str, Any]:
    orchestrator = AutonomousPortfolioOrchestrator()

    resources = [
        ResourcePool("research_pool", "research", 12.0, 80.0, {"research", "validation"}),
        ResourcePool("builder_pool", "engineering", 20.0, 140.0, {"python", "api", "testing"}),
        ResourcePool("ops_pool", "operations", 10.0, 95.0, {"operations", "launch"}),
    ]

    demands = [
        VentureDemand("alpha", 0.95, 120000.0, 0.20, {"python", "api"}, 10.0),
        VentureDemand("beta", 0.80, 65000.0, 0.30, {"research"}, 7.0),
        VentureDemand("gamma", 0.60, 30000.0, 0.55, {"operations"}, 8.0),
    ]

    assets = [
        KnowledgeAsset(
            "asset_pricing",
            "alpha",
            "pricing",
            0.90,
            True,
            {"subscription", "willingness_to_pay"},
        ),
        KnowledgeAsset(
            "asset_launch",
            "beta",
            "launch",
            0.82,
            True,
            {"operations", "checklist"},
        ),
    ]

    venture_topics = {
        "alpha": {"api", "subscription"},
        "beta": {"pricing", "validation"},
        "gamma": {"launch", "operations"},
    }

    allocations = orchestrator.allocate_shared_resources(resources, demands)
    routes = orchestrator.route_knowledge(assets, venture_topics)

    learning_a = orchestrator.record_learning(
        "alpha",
        "Subscription offers converted better than one-time pricing.",
        0.88,
        "increase:recurring_revenue",
    )
    learning_b = orchestrator.record_learning(
        "gamma",
        "Launch complexity was underestimated.",
        0.81,
        "decrease:execution_speed",
    )

    strategy = orchestrator.refine_strategy(
        {
            "recurring_revenue": 0.40,
            "execution_speed": 0.30,
            "risk_control": 0.30,
        },
        [learning_a, learning_b],
    )
    center = orchestrator.command_center(
        allocations,
        routes,
        [learning_a, learning_b],
    )

    return {
        "ok": True,
        "allocation_count": len(allocations),
        "knowledge_route_count": len(routes),
        "updated_strategy": strategy["updated_weights"],
        "command_center": center,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("demo", "status"))
    args = parser.parse_args()

    if args.action == "demo":
        print(json.dumps(demo(), indent=2, sort_keys=True))
        return 0

    print(
        json.dumps(
            {
                "ok": True,
                "state_files": sorted(path.name for path in STATE_DIR.glob("*")),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
