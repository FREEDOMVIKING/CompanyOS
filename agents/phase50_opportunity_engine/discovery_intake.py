#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime, timezone

from agents.phase50_opportunity_engine.opportunity_engine import process

ROOT = Path(__file__).resolve().parents[2]
INBOX = ROOT / "ceo_memory/phase50/discovery_inbox.json"
HISTORY = ROOT / "ceo_memory/phase50/discovery_history.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def submit(candidate):
    inbox = load_json(INBOX, {"candidates": []})

    candidate = dict(candidate)
    candidate["discovered_at"] = candidate.get("discovered_at") or now()
    candidate["intake_status"] = "pending_evaluation"

    inbox.setdefault("candidates", []).append(candidate)
    save_json(INBOX, inbox)

    return {
        "success": True,
        "status": "phase50_candidate_submitted",
        "candidate": candidate
    }


def run_intake():
    inbox = load_json(INBOX, {"candidates": []})
    candidates = inbox.get("candidates", [])

    if not candidates:
        return {
            "success": True,
            "status": "phase50_no_candidates",
            "processed": 0
        }

    result = process(candidates)

    history = load_json(HISTORY, {"runs": []})
    history.setdefault("runs", []).append({
        "run_at": now(),
        "candidate_count": len(candidates),
        "result": result
    })

    save_json(HISTORY, history)
    save_json(INBOX, {"candidates": []})

    return {
        "success": True,
        "status": "phase50_discovery_intake_complete",
        "processed": len(candidates),
        "engine_result": result
    }


def status():
    inbox = load_json(INBOX, {"candidates": []})
    history = load_json(HISTORY, {"runs": []})

    return {
        "success": True,
        "status": "phase50_discovery_intake_status",
        "pending_candidates": len(inbox.get("candidates", [])),
        "historical_runs": len(history.get("runs", []))
    }
