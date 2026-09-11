#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG_PATH = MEMORY / "proposal_approval_config.json"
PROPOSALS_PATH = MEMORY / "project_proposals.json"
OPPORTUNITIES_PATH = MEMORY / "discovered_opportunities.json"
HANDOFF_QUEUE_PATH = MEMORY / "product_factory_handoff_queue.json"
HANDOFF_RESULTS_PATH = MEMORY / "product_factory_handoff_results.json"
AUDIT_PATH = MEMORY / "proposal_approval_audit.json"
HEALTH_PATH = MEMORY / "proposal_approval_health.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(value, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    temp.replace(path)


def audit(action: str, result: dict[str, Any]) -> None:
    records = load_json(AUDIT_PATH, [])

    if not isinstance(records, list):
        records = []

    records.append({
        "timestamp": now(),
        "action": action,
        "success": result.get("success", False),
        "result": result,
    })

    save_json(AUDIT_PATH, records[-1000:])


def update_proposal_statistics(store: dict[str, Any]) -> None:
    proposals = store.get("proposals", [])

    store["statistics"] = {
        "total": len(proposals),
        "pending_owner_approval": sum(
            1 for item in proposals
            if item.get("status") == "pending_owner_approval"
        ),
        "approved": sum(
            1 for item in proposals
            if item.get("status") == "approved"
        ),
        "rejected": sum(
            1 for item in proposals
            if item.get("status") == "rejected"
        ),
        "held": sum(
            1 for item in proposals
            if item.get("status") == "hold"
        ),
        "handed_to_factory": sum(
            1 for item in proposals
            if item.get("status") == "handed_to_factory"
        ),
    }

    store["last_updated_at"] = now()


def update_handoff_statistics(store: dict[str, Any]) -> None:
    handoffs = store.get("handoffs", [])

    store["statistics"] = {
        "total": len(handoffs),
        "queued": sum(
            1 for item in handoffs
            if item.get("status") == "queued"
        ),
        "completed": sum(
            1 for item in handoffs
            if item.get("status") == "completed"
        ),
        "blocked": sum(
            1 for item in handoffs
            if item.get("status") == "blocked"
        ),
        "failed": sum(
            1 for item in handoffs
            if item.get("status") == "failed"
        ),
    }

    store["last_updated_at"] = now()


def find_proposal(
    proposal_id: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    store = load_json(
        PROPOSALS_PATH,
        {
            "schema_version": 1,
            "proposals": [],
            "statistics": {},
        },
    )

    for proposal in store.get("proposals", []):
        if proposal.get("id") == proposal_id:
            return store, proposal

    return store, None


def find_opportunity(opportunity_id: str) -> dict[str, Any] | None:
    store = load_json(OPPORTUNITIES_PATH, {})

    for opportunity in store.get("opportunities", []):
        if opportunity.get("id") == opportunity_id:
            return opportunity

    return None


def normalize_name(value: str) -> str:
    return "".join(
        character.lower()
        for character in value
        if character.isalnum()
    )


def existing_project_names() -> set[str]:
    names: set[str] = set()

    paths = [
        MEMORY / "portfolio.json",
        MEMORY / "portfolio_state.json",
        MEMORY / "project_registry.json",
        MEMORY / "products.json",
        MEMORY / "product_factory.json",
        MEMORY / "factory_projects.json",
        MEMORY / "businesses.json",
    ]

    for path in paths:
        data = load_json(path, {})

        records: list[Any] = []

        if isinstance(data, list):
            records = data

        elif isinstance(data, dict):
            for key in (
                "projects",
                "products",
                "portfolio",
                "items",
                "businesses",
                "factory_projects",
            ):
                value = data.get(key)

                if isinstance(value, list):
                    records.extend(value)

        for item in records:
            if isinstance(item, str):
                names.add(normalize_name(item))

            elif isinstance(item, dict):
                name = (
                    item.get("name")
                    or item.get("title")
                    or item.get("project_name")
                    or item.get("product_name")
                )

                if name:
                    names.add(normalize_name(str(name)))

    return names


def decision(
    proposal_id: str,
    new_status: str,
    reason: str | None = None,
) -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "proposal_approval_disabled",
        }
        audit(new_status, result)
        return result

    if new_status not in {"approved", "rejected", "hold"}:
        result = {
            "success": False,
            "status": "invalid_proposal_decision",
            "decision": new_status,
        }
        audit(new_status, result)
        return result

    store, proposal = find_proposal(proposal_id)

    if not proposal:
        result = {
            "success": False,
            "status": "proposal_not_found",
            "proposal_id": proposal_id,
        }
        audit(new_status, result)
        return result

    old_status = proposal.get("status")

    if old_status == "handed_to_factory":
        result = {
            "success": False,
            "status": "proposal_already_handed_to_factory",
            "proposal_id": proposal_id,
        }
        audit(new_status, result)
        return result

    proposal["status"] = new_status
    proposal["updated_at"] = now()
    proposal["owner_decision_at"] = now()
    proposal["owner_decision"] = new_status
    proposal["owner_decision_reason"] = reason

    if new_status == "approved":
        proposal["approved_by_owner"] = True
        proposal["approved_at"] = now()
        proposal["factory_handoff_status"] = "ready"

    elif new_status == "rejected":
        proposal["approved_by_owner"] = False
        proposal["rejected_at"] = now()
        proposal["factory_handoff_status"] = "blocked"

    elif new_status == "hold":
        proposal["approved_by_owner"] = False
        proposal["held_at"] = now()
        proposal["factory_handoff_status"] = "on_hold"

    update_proposal_statistics(store)
    save_json(PROPOSALS_PATH, store)

    result = {
        "success": True,
        "status": f"proposal_{new_status}",
        "proposal_id": proposal_id,
        "title": proposal.get("title"),
        "previous_status": old_status,
        "proposal_status": new_status,
        "reason": reason,
        "owner_approval_recorded": True,
        "automatic_factory_handoff": False,
        "automatic_spending": False,
        "automatic_publication": False,
    }

    audit(new_status, result)
    return result


def handoff_id(proposal_id: str) -> str:
    digest = hashlib.sha256(
        f"{proposal_id}:factory".encode("utf-8")
    ).hexdigest()[:14]

    return f"handoff-{digest}"


def create_handoff(proposal_id: str) -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})
    proposal_store, proposal = find_proposal(proposal_id)

    if not proposal:
        result = {
            "success": False,
            "status": "proposal_not_found",
            "proposal_id": proposal_id,
        }
        audit("handoff", result)
        return result

    if (
        config.get("require_approved_status_for_handoff", True)
        and proposal.get("status") != "approved"
    ):
        result = {
            "success": False,
            "status": "factory_handoff_blocked",
            "proposal_id": proposal_id,
            "reason": "Proposal must be approved before factory handoff",
            "current_status": proposal.get("status"),
            "next_command": (
                f"python companyos/approvalctl approve {proposal_id}"
            ),
        }
        audit("handoff", result)
        return result

    title = str(proposal.get("title", ""))

    if (
        config.get("duplicate_project_protection", True)
        and normalize_name(title) in existing_project_names()
    ):
        proposal["factory_handoff_status"] = "blocked_duplicate"
        proposal["updated_at"] = now()
        update_proposal_statistics(proposal_store)
        save_json(PROPOSALS_PATH, proposal_store)

        result = {
            "success": False,
            "status": "factory_handoff_duplicate_blocked",
            "proposal_id": proposal_id,
            "title": title,
            "reason": "A project with the same normalized name already exists",
        }
        audit("handoff", result)
        return result

    queue = load_json(
        HANDOFF_QUEUE_PATH,
        {
            "schema_version": 1,
            "handoffs": [],
            "statistics": {},
            "last_updated_at": None,
        },
    )

    handoffs = queue.setdefault("handoffs", [])
    item_id = handoff_id(proposal_id)

    for existing in handoffs:
        if existing.get("id") == item_id:
            result = {
                "success": True,
                "status": "factory_handoff_already_exists",
                "handoff": existing,
            }
            audit("handoff", result)
            return result

    opportunity = find_opportunity(
        str(proposal.get("opportunity_id", ""))
    ) or {}

    handoff = {
        "id": item_id,
        "proposal_id": proposal_id,
        "opportunity_id": proposal.get("opportunity_id"),
        "project_name": title,
        "project_type": opportunity.get(
            "category",
            "business_product",
        ),
        "status": "queued",
        "priority_score": proposal.get("priority_score"),
        "confidence_score": proposal.get("confidence_score"),
        "target_customer": proposal.get("target_customer"),
        "customer_problem": proposal.get("customer_problem"),
        "proposed_solution": proposal.get("proposed_solution"),
        "revenue_model": proposal.get("revenue_model"),
        "objectives": proposal.get("objectives", []),
        "mvp_features": proposal.get("mvp_features", []),
        "milestones": proposal.get("milestones", []),
        "risks": proposal.get("risks", []),
        "assumptions": proposal.get("assumptions", []),
        "revenue_hypothesis": proposal.get(
            "revenue_hypothesis",
            {},
        ),
        "estimated_launch_window": proposal.get(
            "estimated_launch_window"
        ),
        "factory_permissions": {
            "internal_planning": True,
            "internal_design": True,
            "internal_build": True,
            "internal_testing": True,
            "external_publication": False,
            "external_spending": False,
            "external_execution": False,
        },
        "owner_approved": True,
        "automatic_publication": False,
        "automatic_spending": False,
        "created_at": now(),
        "updated_at": now(),
    }

    handoffs.append(handoff)
    update_handoff_statistics(queue)
    save_json(HANDOFF_QUEUE_PATH, queue)

    proposal["factory_handoff_status"] = "queued"
    proposal["factory_handoff_id"] = item_id
    proposal["updated_at"] = now()
    update_proposal_statistics(proposal_store)
    save_json(PROPOSALS_PATH, proposal_store)

    result = {
        "success": True,
        "status": "factory_handoff_queued",
        "handoff_id": item_id,
        "proposal_id": proposal_id,
        "project_name": title,
        "internal_factory_execution_allowed": True,
        "external_publication": False,
        "external_spending": False,
    }

    audit("handoff", result)
    return result


def detect_factory_registry_path() -> Path:
    candidates = [
        MEMORY / "factory_projects.json",
        MEMORY / "product_factory.json",
        MEMORY / "products.json",
        MEMORY / "project_registry.json",
    ]

    for path in candidates:
        if path.exists():
            return path

    return MEMORY / "factory_projects.json"


def append_project_to_registry(
    path: Path,
    project: dict[str, Any],
) -> None:
    data = load_json(path, {})

    if isinstance(data, list):
        data.append(project)

    elif isinstance(data, dict):
        target_key = None

        for key in (
            "projects",
            "products",
            "factory_projects",
            "items",
        ):
            if isinstance(data.get(key), list):
                target_key = key
                break

        if target_key is None:
            target_key = "projects"
            data[target_key] = []

        data[target_key].append(project)

    else:
        data = {
            "schema_version": 1,
            "projects": [project],
        }

    save_json(path, data)


def process_handoffs() -> dict[str, Any]:
    queue = load_json(
        HANDOFF_QUEUE_PATH,
        {
            "schema_version": 1,
            "handoffs": [],
            "statistics": {},
        },
    )

    results_store = load_json(
        HANDOFF_RESULTS_PATH,
        {
            "schema_version": 1,
            "results": [],
            "last_updated_at": None,
        },
    )

    results = results_store.setdefault("results", [])
    registry_path = detect_factory_registry_path()

    processed = 0
    completed = 0
    failed = 0
    result_items: list[dict[str, Any]] = []

    for handoff in queue.get("handoffs", []):
        if handoff.get("status") != "queued":
            continue

        processed += 1

        try:
            project = {
                "id": f"project-{handoff.get('id')}",
                "name": handoff.get("project_name"),
                "title": handoff.get("project_name"),
                "source": "approved_proposal_handoff",
                "proposal_id": handoff.get("proposal_id"),
                "opportunity_id": handoff.get("opportunity_id"),
                "status": "planned",
                "stage": "planning",
                "priority_score": handoff.get("priority_score"),
                "target_customer": handoff.get("target_customer"),
                "customer_problem": handoff.get(
                    "customer_problem"
                ),
                "proposed_solution": handoff.get(
                    "proposed_solution"
                ),
                "revenue_model": handoff.get("revenue_model"),
                "objectives": handoff.get("objectives", []),
                "mvp_features": handoff.get("mvp_features", []),
                "milestones": handoff.get("milestones", []),
                "risks": handoff.get("risks", []),
                "assumptions": handoff.get("assumptions", []),
                "factory_permissions": handoff.get(
                    "factory_permissions",
                    {},
                ),
                "automatic_spending": False,
                "automatic_publication": False,
                "created_at": now(),
                "updated_at": now(),
            }

            if normalize_name(
                str(project.get("name", ""))
            ) in existing_project_names():
                handoff["status"] = "blocked"
                handoff["last_error"] = (
                    "Duplicate project detected during processing"
                )
                handoff["updated_at"] = now()

                item_result = {
                    "success": False,
                    "status": "handoff_blocked_duplicate",
                    "handoff_id": handoff.get("id"),
                    "project_name": project.get("name"),
                }

                failed += 1

            else:
                append_project_to_registry(
                    registry_path,
                    project,
                )

                handoff["status"] = "completed"
                handoff["factory_project_id"] = project["id"]
                handoff["factory_registry"] = str(registry_path)
                handoff["completed_at"] = now()
                handoff["updated_at"] = now()
                handoff["last_error"] = None

                proposal_store, proposal = find_proposal(
                    str(handoff.get("proposal_id"))
                )

                if proposal:
                    proposal["status"] = "handed_to_factory"
                    proposal["factory_handoff_status"] = "completed"
                    proposal["factory_project_id"] = project["id"]
                    proposal["updated_at"] = now()
                    update_proposal_statistics(proposal_store)
                    save_json(PROPOSALS_PATH, proposal_store)

                item_result = {
                    "success": True,
                    "status": "handoff_completed",
                    "handoff_id": handoff.get("id"),
                    "factory_project_id": project["id"],
                    "factory_registry": str(registry_path),
                    "project_name": project.get("name"),
                }

                completed += 1

        except Exception as exc:
            handoff["status"] = "failed"
            handoff["last_error"] = str(exc)
            handoff["updated_at"] = now()

            item_result = {
                "success": False,
                "status": "handoff_failed",
                "handoff_id": handoff.get("id"),
                "error": str(exc),
            }

            failed += 1

        results.append({
            "timestamp": now(),
            **item_result,
        })
        result_items.append(item_result)

    update_handoff_statistics(queue)
    save_json(HANDOFF_QUEUE_PATH, queue)

    results_store["results"] = results[-1000:]
    results_store["last_updated_at"] = now()
    save_json(HANDOFF_RESULTS_PATH, results_store)

    health = {
        "healthy": failed == 0,
        "last_processed_at": now(),
        "processed": processed,
        "completed": completed,
        "failed": failed,
        "factory_registry": str(registry_path),
        "last_error": (
            None
            if failed == 0
            else "One or more handoffs failed"
        ),
    }
    save_json(HEALTH_PATH, health)

    result = {
        "success": failed == 0,
        "status": "factory_handoff_queue_processed",
        "processed": processed,
        "completed": completed,
        "failed": failed,
        "factory_registry": str(registry_path),
        "results": result_items,
        "automatic_spending": False,
        "automatic_publication": False,
    }

    audit("process", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})
    proposals = load_json(PROPOSALS_PATH, {})
    queue = load_json(HANDOFF_QUEUE_PATH, {})
    health = load_json(HEALTH_PATH, {})

    result = {
        "success": True,
        "status": "proposal_approval_status",
        "enabled": config.get("enabled", False),
        "owner_approval_required": config.get(
            "owner_approval_required",
            True,
        ),
        "automatic_approval": config.get(
            "automatic_approval",
            False,
        ),
        "automatic_factory_handoff": config.get(
            "automatic_factory_handoff",
            False,
        ),
        "automatic_project_creation": config.get(
            "automatic_project_creation",
            False,
        ),
        "automatic_spending": config.get(
            "automatic_spending",
            False,
        ),
        "automatic_publication": config.get(
            "automatic_publication",
            False,
        ),
        "proposal_statistics": proposals.get("statistics", {}),
        "handoff_statistics": queue.get("statistics", {}),
        "health": health,
    }

    audit("status", result)
    return result


def list_pending() -> dict[str, Any]:
    store = load_json(PROPOSALS_PATH, {})
    pending = [
        item
        for item in store.get("proposals", [])
        if item.get("status") == "pending_owner_approval"
    ]

    result = {
        "success": True,
        "status": "pending_proposal_list",
        "count": len(pending),
        "proposals": [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "priority_score": item.get("priority_score"),
                "recommendation": item.get("recommendation"),
                "risk_level": item.get("risk_level"),
                "go_hold_recommendation": item.get(
                    "go_hold_recommendation"
                ),
            }
            for item in pending
        ],
    }

    audit("pending", result)
    return result


def list_handoffs() -> dict[str, Any]:
    queue = load_json(HANDOFF_QUEUE_PATH, {})
    handoffs = queue.get("handoffs", [])

    result = {
        "success": True,
        "status": "factory_handoff_list",
        "count": len(handoffs),
        "statistics": queue.get("statistics", {}),
        "handoffs": [
            {
                "id": item.get("id"),
                "proposal_id": item.get("proposal_id"),
                "project_name": item.get("project_name"),
                "status": item.get("status"),
                "factory_project_id": item.get(
                    "factory_project_id"
                ),
                "last_error": item.get("last_error"),
            }
            for item in handoffs
        ],
    }

    audit("handoffs", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: proposal_approval_manager.py "
            "approve <proposal_id> [reason]|"
            "reject <proposal_id> [reason]|"
            "hold <proposal_id> [reason]|"
            "handoff <proposal_id>|process|"
            "pending|handoffs|status"
        )
        return 2

    action = sys.argv[1].lower()

    try:
        if action in {"approve", "reject", "hold"}:
            if len(sys.argv) < 3:
                raise ValueError("Proposal ID is required")

            proposal_id = sys.argv[2]
            reason = " ".join(sys.argv[3:]).strip() or None

            status_map = {
                "approve": "approved",
                "reject": "rejected",
                "hold": "hold",
            }

            return print_result(
                decision(
                    proposal_id,
                    status_map[action],
                    reason,
                )
            )

        if action == "handoff":
            if len(sys.argv) < 3:
                raise ValueError("Proposal ID is required")

            return print_result(create_handoff(sys.argv[2]))

        if action == "process":
            return print_result(process_handoffs())

        if action == "pending":
            return print_result(list_pending())

        if action == "handoffs":
            return print_result(list_handoffs())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_approval_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "proposal_approval_error",
            "action": action,
            "error": str(exc),
        }

        save_json(
            HEALTH_PATH,
            {
                "healthy": False,
                "last_checked_at": now(),
                "last_error": str(exc),
            },
        )

        audit("error", result)
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
