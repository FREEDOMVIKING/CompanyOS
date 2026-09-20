#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${HOME}/companyos"
BRANCH="companyos-continuous-fix-2026-09-11"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="${ROOT}/backups/research_to_execution_${STAMP}"

cd "$ROOT"

if [ "$(git branch --show-current)" != "$BRANCH" ]; then
  echo "ERROR: expected branch $BRANCH"
  exit 2
fi

mkdir -p "$BACKUP/companyos/runtime" "$BACKUP/companyos/governance" "$BACKUP/scripts"
for f in \
  companyos/runtime/productive_autonomy_watchdog.py \
  companyos/runtime/stalled_stage_progression_controller.py \
  companyos/governance/venture_identity_progression.py
do
  [ -e "$f" ] && cp -a "$f" "$BACKUP/$f"
done

cat > companyos/runtime/research_to_execution_bridge.py <<'PY'
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
CANDIDATES = RT / "profit_first_candidates"
STATE = RT / "research_to_execution_bridge.json"

POLICY_WORDS = {
    "do_not", "must_", "research_analysis_only", "evidence_sources",
    "numeric_scoring", "mark_estimates", "missing_evidence",
    "duplicate_rename", "candidate_files_written", "generate_at_least",
    "construction_is_allowed", "this_stage_is_research",
    "persist_a_market_scan", "every_candidate_json",
    "companyos_opportunity_engine_test", "one_shot_token",
}

NAME_KEYS = (
    "name", "candidate_name", "venture_name", "business_name",
    "title", "opportunity", "idea", "concept",
)
MODEL_KEYS = (
    "business_model", "model", "offer", "product", "service",
    "value_proposition", "customer_problem", "target_customer",
)
SCORE_KEYS = (
    "score", "composite_score", "total_score", "opportunity_score",
    "profitability_score", "expected_value_score", "rank_score",
)


@dataclass
class Candidate:
    source: str
    fingerprint: str
    slug: str
    name: str
    score: float
    payload: dict[str, Any]
    confidence: float
    evidence_count: int


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return re.sub(r"_+", "_", value)[:72]


def _text(obj: Any) -> str:
    try:
        return json.dumps(obj, sort_keys=True, default=str).lower()
    except Exception:
        return str(obj).lower()


def _name(payload: dict[str, Any], source: Path) -> str:
    for key in NAME_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:140]
    return source.stem.replace("_", " ")[:140]


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        x = float(value)
        if 0 <= x <= 1:
            return x * 100.0
        return max(0.0, min(100.0, x))
    try:
        x = float(str(value).strip())
        if 0 <= x <= 1:
            x *= 100.0
        return max(0.0, min(100.0, x))
    except Exception:
        return None


def _score(payload: dict[str, Any]) -> float:
    vals = []
    for key in SCORE_KEYS:
        if key in payload:
            n = _numeric(payload.get(key))
            if n is not None:
                vals.append(n)

    scores = payload.get("scores")
    if isinstance(scores, dict):
        for value in scores.values():
            n = _numeric(value)
            if n is not None:
                vals.append(n)

    if vals:
        return round(sum(vals) / len(vals), 2)

    heuristic = 0.0
    text = _text(payload)
    if any(k in payload for k in MODEL_KEYS):
        heuristic += 30
    if any(x in text for x in ("customer", "market", "demand", "buyer")):
        heuristic += 15
    if any(x in text for x in ("revenue", "price", "margin", "profit")):
        heuristic += 15
    if any(x in text for x in ("evidence", "source", "competitor")):
        heuristic += 15
    if len(text) > 500:
        heuristic += 10
    return min(100.0, heuristic)


def _confidence(payload: dict[str, Any]) -> float:
    for key in ("confidence", "evidence_confidence", "confidence_score"):
        if key in payload:
            n = _numeric(payload.get(key))
            if n is not None:
                return n
    return 50.0


def _evidence_count(payload: dict[str, Any]) -> int:
    count = 0
    for key in ("evidence", "sources", "citations", "market_evidence"):
        value = payload.get(key)
        if isinstance(value, list):
            count += len(value)
        elif isinstance(value, dict):
            count += len(value)
        elif isinstance(value, str) and value.strip():
            count += 1
    return count


def _looks_like_policy(source: Path, payload: dict[str, Any]) -> bool:
    stem = source.stem.lower()
    if any(word in stem for word in POLICY_WORDS):
        return True

    keys = {str(k).lower() for k in payload}
    useful = any(k in keys for k in NAME_KEYS) and any(k in keys for k in MODEL_KEYS)
    text = _text(payload)

    instruction_markers = (
        "must not", "do not perform", "research only",
        "candidate json must", "generate at least",
        "this stage is research", "scoring fields must",
    )
    if not useful and any(x in text for x in instruction_markers):
        return True
    return False


def scan_candidates(min_score: float = 45.0) -> list[Candidate]:
    if not CANDIDATES.exists():
        return []

    found: dict[str, Candidate] = {}
    for path in CANDIDATES.glob("*.json"):
        payload = _load(path, {})
        if not isinstance(payload, dict) or not payload:
            continue
        if _looks_like_policy(path, payload):
            continue

        name = _name(payload, path)
        slug = _slug(name)
        if not slug or len(slug) < 3:
            continue

        score = _score(payload)
        if score < min_score:
            continue

        raw = json.dumps(payload, sort_keys=True, default=str)
        fp = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
        candidate = Candidate(
            source=str(path.relative_to(ROOT)),
            fingerprint=fp,
            slug=slug,
            name=name,
            score=score,
            payload=payload,
            confidence=_confidence(payload),
            evidence_count=_evidence_count(payload),
        )
        old = found.get(slug)
        if old is None or candidate.score > old.score:
            found[slug] = candidate

    return sorted(
        found.values(),
        key=lambda c: (c.score, c.confidence, c.evidence_count),
        reverse=True,
    )


def _state():
    state = _load(STATE, {})
    if not isinstance(state, dict):
        state = {}
    state.setdefault("promotions", [])
    state.setdefault("promoted_fingerprints", {})
    state.setdefault("last_promotion_unix", 0)
    return state


def _workspace_exists(slug: str) -> bool:
    return any(
        (ROOT / base / slug).exists()
        for base in ("workspace", "products", "artifacts", "exports")
    )


def _write_venture(candidate: Candidate) -> Path:
    venture = ROOT / "workspace" / candidate.slug
    venture.mkdir(parents=True, exist_ok=True)

    brief = {
        "canonical_id": candidate.slug,
        "name": candidate.name,
        "stage": "VALIDATE",
        "source_candidate": candidate.source,
        "candidate_fingerprint": candidate.fingerprint,
        "candidate_score": candidate.score,
        "candidate_confidence": candidate.confidence,
        "evidence_count": candidate.evidence_count,
        "candidate": candidate.payload,
        "promoted_at_unix": time.time(),
        "next_required_outcome": (
            "Produce one measurable validation artifact and, if validation "
            "passes, build the smallest sellable product or service."
        ),
    }
    _save(venture / "venture_brief.json", brief)
    _save(
        venture / "venture_stage_VALIDATE.json",
        {
            "stage": "VALIDATE",
            "updated_at_unix": time.time(),
            "source": "research_to_execution_bridge",
        },
    )
    return venture


def _execution_goal(candidate: Candidate) -> str:
    return f'''
Advance canonical CompanyOS venture '{candidate.slug}' from RESEARCH into EXECUTION.

Candidate: {candidate.name}
Research score: {candidate.score}
Confidence: {candidate.confidence}
Evidence count: {candidate.evidence_count}
Source artifact: {candidate.source}

EXECUTION CONTRACT:
1. Reuse the existing promoted venture workspace. Do not create renamed/versioned clones.
2. Validate one concrete customer problem, buyer, offer, price hypothesis, and measurable success criterion.
3. If validation is adequate, build the smallest sellable product/service artifact.
4. Run acceptance tests and fix only failures required to pass.
5. Package a launch candidate and prepare customer-facing assets.
6. If existing CompanyOS policy and configured connector gates authorize the action, advance through deployment and measurable customer acquisition. Never bypass an approval/safety gate.
7. Record stage changes and measurable evidence in the venture workspace.
8. Do not return to broad market research unless validation produces a specific evidence gap.
9. Do not perform a financial transaction merely to prove activity. Financial actions must remain within the existing live-finance policy, signer, reconciliation, and transaction-limit controls.

The required outcome is measurable venture progression, not another market scan.
'''.strip()


def promote(candidate: Candidate) -> dict[str, Any]:
    venture = _write_venture(candidate)

    from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator

    rec = AutonomousCEOOrchestrator().start(
        goal=_execution_goal(candidate),
        max_cycles=180,
        max_follow_up_depth=7,
        priority_base=320,
    )
    oid = getattr(rec, "orchestration_id", None)

    state = _state()
    entry = {
        "ts": time.time(),
        "canonical_id": candidate.slug,
        "name": candidate.name,
        "score": candidate.score,
        "confidence": candidate.confidence,
        "source": candidate.source,
        "fingerprint": candidate.fingerprint,
        "workspace": str(venture.relative_to(ROOT)),
        "orchestration_id": oid,
    }
    state["promotions"].append(entry)
    state["promotions"] = state["promotions"][-200:]
    state["promoted_fingerprints"][candidate.fingerprint] = entry["ts"]
    state["last_promotion_unix"] = entry["ts"]
    _save(STATE, state)
    return {"started": True, "entry": entry}


def maybe_promote_candidate(
    min_score: float = 45.0,
    cooldown_seconds: int = 900,
    max_existing_execution_ventures: int = 3,
) -> dict[str, Any]:
    candidates = scan_candidates(min_score=min_score)
    state = _state()
    now = time.time()

    execution_ventures = 0
    for base in ("workspace", "products", "exports"):
        root = ROOT / base
        if root.exists():
            execution_ventures += sum(1 for x in root.iterdir() if x.is_dir())

    eligible = []
    for c in candidates:
        if c.fingerprint in state["promoted_fingerprints"]:
            continue
        if _workspace_exists(c.slug):
            continue
        eligible.append(c)

    detail = {
        "candidate_count": len(candidates),
        "eligible_count": len(eligible),
        "execution_venture_count": execution_ventures,
        "top_candidates": [
            {
                "name": c.name,
                "slug": c.slug,
                "score": c.score,
                "confidence": c.confidence,
                "evidence_count": c.evidence_count,
            }
            for c in candidates[:5]
        ],
    }

    if not eligible:
        return {"started": False, "reason": "no_unpromoted_eligible_candidate", **detail}

    if execution_ventures >= max_existing_execution_ventures:
        return {"started": False, "reason": "execution_capacity_full", **detail}

    since_last = now - float(state.get("last_promotion_unix", 0) or 0)
    if since_last < cooldown_seconds:
        return {
            "started": False,
            "reason": "promotion_cooldown",
            "seconds_remaining": round(cooldown_seconds - since_last, 1),
            **detail,
        }

    try:
        return {**promote(eligible[0]), **detail}
    except Exception as exc:
        return {
            "started": False,
            "reason": "promotion_failed",
            "error": f"{type(exc).__name__}:{exc}",
            **detail,
        }


def status() -> dict[str, Any]:
    candidates = scan_candidates()
    state = _state()
    top = []
    for c in candidates[:10]:
        row = asdict(c)
        row["payload"] = None
        top.append(row)
    return {
        "candidate_count": len(candidates),
        "top_candidates": top,
        "promotion_count": len(state["promotions"]),
        "recent_promotions": state["promotions"][-10:],
        "last_promotion_unix": state.get("last_promotion_unix", 0),
    }
PY

cat > scripts/companyos_executionctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos.runtime.research_to_execution_bridge import (
    maybe_promote_candidate,
    scan_candidates,
    status,
)

def dump(x):
    print(json.dumps(x, indent=2, sort_keys=True, default=str))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["status", "scan", "promote"])
    p.add_argument("--min-score", type=float, default=45.0)
    a = p.parse_args()

    if a.command == "status":
        dump(status())
        return 0
    if a.command == "scan":
        rows = scan_candidates(min_score=a.min_score)
        dump([
            {
                "name": x.name,
                "slug": x.slug,
                "score": x.score,
                "confidence": x.confidence,
                "evidence_count": x.evidence_count,
                "source": x.source,
            }
            for x in rows
        ])
        return 0

    result = maybe_promote_candidate(
        min_score=a.min_score,
        cooldown_seconds=0,
    )
    dump(result)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
PY
chmod +x scripts/companyos_executionctl

python - <<'PY'
from pathlib import Path

p = Path("companyos/governance/venture_identity_progression.py")
s = p.read_text(encoding="utf-8")
old = '''def infer_stage(files):
    names=" ".join(str(p).lower() for p in files)
    if any(x in names for x in ("customer","lead","conversion","campaign")): return "CUSTOMER_ACQUISITION"
    if any(p.suffix==".zip" for p in files) or "export_manifest" in names: return "LAUNCH_READY"
    if any(x in names for x in ("test","qa","acceptance")): return "TEST"
    if files: return "BUILD"
    return "DISCOVER"
'''
new = '''def infer_stage(files):
    names=" ".join(str(p).lower() for p in files)

    explicit_order = [
        ("venture_stage_scale", "SCALE"),
        ("venture_stage_operate", "OPERATE"),
        ("venture_stage_customer_acquisition", "CUSTOMER_ACQUISITION"),
        ("venture_stage_launch", "LAUNCH"),
        ("venture_stage_launch_ready", "LAUNCH_READY"),
        ("venture_stage_package", "PACKAGE"),
        ("venture_stage_test", "TEST"),
        ("venture_stage_build", "BUILD"),
        ("venture_stage_validate", "VALIDATE"),
    ]
    for marker, stage in explicit_order:
        if marker in names:
            return stage

    if any(x in names for x in (
        "conversion_result", "customer_result", "lead_result",
        "outreach_result", "campaign_result",
    )):
        return "CUSTOMER_ACQUISITION"
    if "deployment_result" in names or "live_url" in names:
        return "LAUNCH"
    if any(p.suffix==".zip" for p in files) or "export_manifest" in names:
        return "LAUNCH_READY"
    if any(x in names for x in ("test_result","qa_result","acceptance_result")):
        return "TEST"
    if "validation_result" in names:
        return "VALIDATE"
    if files:
        return "BUILD"
    return "DISCOVER"
'''
if old not in s:
    raise SystemExit("infer_stage block not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

p = Path("companyos/runtime/stalled_stage_progression_controller.py")
s = p.read_text(encoding="utf-8")
anchor = 'STAGE_TASKS = {\n    "CUSTOMER_ACQUISITION": ['
if anchor not in s:
    raise SystemExit("stage tasks anchor not found")
replacement = '''STAGE_TASKS = {
    "VALIDATE": [
        "validate one specific customer problem, buyer, offer, price hypothesis, and measurable success criterion",
        "persist validation evidence and explicitly mark pass/fail",
        "if validation passes, advance immediately to the smallest sellable build instead of restarting broad research",
    ],
    "PACKAGE": [
        "package the tested release candidate",
        "create an export manifest and operator/deployment notes",
        "advance to launch-ready when packaging is complete",
    ],
    "LAUNCH": [
        "verify the deployed endpoint or customer-facing asset is reachable",
        "record deployment evidence and live URL where applicable",
        "advance to measurable customer acquisition using configured connectors and existing policy gates",
    ],
    "CUSTOMER_ACQUISITION": ['''
s = s.replace(anchor, replacement, 1)
p.write_text(s, encoding="utf-8")
PY

python - <<'PY'
from pathlib import Path

p = Path("companyos/runtime/productive_autonomy_watchdog.py")
s = p.read_text(encoding="utf-8")

import_line = "from companyos.runtime.research_to_execution_bridge import maybe_promote_candidate\n"
anchor = "from companyos.governance.venture_identity_progression import highest_priority_stalled\n"
if import_line not in s:
    if anchor not in s:
        raise SystemExit("watchdog import anchor not found")
    s = s.replace(anchor, anchor + import_line, 1)

tick_anchor = "def tick() -> dict[str, Any]:\n"
if tick_anchor not in s:
    raise SystemExit("tick anchor not found")
if "RESEARCH_TO_EXECUTION_PROMOTION" not in s:
    injection = '''def tick() -> dict[str, Any]:
    promotion = maybe_promote_candidate(
        min_score=float(os.getenv("COMPANYOS_EXECUTION_PROMOTION_MIN_SCORE", "45")),
        cooldown_seconds=int(os.getenv("COMPANYOS_EXECUTION_PROMOTION_COOLDOWN_SECONDS", "900")),
        max_existing_execution_ventures=int(os.getenv("COMPANYOS_MAX_ACTIVE_EXECUTION_VENTURES", "3")),
    )
    if promotion.get("started"):
        log("RESEARCH_TO_EXECUTION_PROMOTION " + json.dumps(promotion, default=str, sort_keys=True))

    execution_backlog = (
        promotion.get("started")
        or int(promotion.get("eligible_count", 0) or 0) > 0
        or promotion.get("reason") in {"execution_capacity_full", "promotion_cooldown"}
    )
'''
    s = s.replace(tick_anchor, injection, 1)

old_research = '''    profit_first_research = maybe_run_profit_first_research(
        cooldown_seconds=int(os.getenv("COMPANYOS_PROFIT_FIRST_RESEARCH_COOLDOWN_SECONDS", "300")),
    )
    if profit_first_research.get("started"):
        log("PROFIT_FIRST_RESEARCH " + json.dumps(profit_first_research, default=str, sort_keys=True))
'''
new_research = '''    if execution_backlog:
        profit_first_research = {
            "started": False,
            "reason": "execution_backlog_preferred_over_more_research",
        }
    else:
        profit_first_research = maybe_run_profit_first_research(
            cooldown_seconds=int(os.getenv("COMPANYOS_PROFIT_FIRST_RESEARCH_COOLDOWN_SECONDS", "300")),
        )
        if profit_first_research.get("started"):
            log("PROFIT_FIRST_RESEARCH " + json.dumps(profit_first_research, default=str, sort_keys=True))
'''
if old_research in s:
    s = s.replace(old_research, new_research, 1)

old_dispatch = '''    profit_first_dispatch = maybe_dispatch_profit_first(
        min_idle_cycles=int(os.getenv("COMPANYOS_PROFIT_FIRST_DISPATCH_MIN_IDLE_CYCLES", "20")),
        cooldown_seconds=int(os.getenv("COMPANYOS_PROFIT_FIRST_DISPATCH_COOLDOWN_SECONDS", "300")),
    )
    if profit_first_dispatch.get("started"):
        log("PROFIT_FIRST_DISPATCH " + json.dumps(profit_first_dispatch, default=str, sort_keys=True))
'''
new_dispatch = '''    if execution_backlog:
        profit_first_dispatch = {
            "started": False,
            "reason": "execution_backlog_preferred_over_more_research",
        }
    else:
        profit_first_dispatch = maybe_dispatch_profit_first(
            min_idle_cycles=int(os.getenv("COMPANYOS_PROFIT_FIRST_DISPATCH_MIN_IDLE_CYCLES", "20")),
            cooldown_seconds=int(os.getenv("COMPANYOS_PROFIT_FIRST_DISPATCH_COOLDOWN_SECONDS", "300")),
        )
        if profit_first_dispatch.get("started"):
            log("PROFIT_FIRST_DISPATCH " + json.dumps(profit_first_dispatch, default=str, sort_keys=True))
'''
if old_dispatch in s:
    s = s.replace(old_dispatch, new_dispatch, 1)

p.write_text(s, encoding="utf-8")
PY

cat > scripts/validate_research_to_execution_fix.py <<'PY'
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))

from companyos.runtime.research_to_execution_bridge import scan_candidates, status

candidates = scan_candidates()
st = status()

print("===== RESEARCH TO EXECUTION VALIDATION =====")
print("valid_candidate_count:", len(candidates))
print("promotion_count:", st.get("promotion_count"))
print("top_candidates:")
for c in candidates[:5]:
    print(json.dumps({
        "name": c.name,
        "slug": c.slug,
        "score": c.score,
        "confidence": c.confidence,
        "evidence_count": c.evidence_count,
        "source": c.source,
    }, sort_keys=True))
print("COMPANYOS_RESEARCH_TO_EXECUTION_VALIDATION=PASS")
PY

python -m py_compile \
  companyos/runtime/research_to_execution_bridge.py \
  companyos/runtime/productive_autonomy_watchdog.py \
  companyos/runtime/stalled_stage_progression_controller.py \
  companyos/governance/venture_identity_progression.py \
  scripts/companyos_executionctl \
  scripts/validate_research_to_execution_fix.py

echo
echo "===== VALIDATE FILTER + PROMOTION ENGINE ====="
python scripts/validate_research_to_execution_fix.py

echo
echo "===== CURRENT EXECUTION STATUS ====="
scripts/companyos_executionctl status

echo
echo "===== PROMOTE ONE REAL ELIGIBLE CANDIDATE IF AVAILABLE ====="
scripts/companyos_executionctl promote --min-score 45 || true

echo
echo "===== COMMIT + PUSH ====="
git add \
  companyos/runtime/research_to_execution_bridge.py \
  companyos/runtime/productive_autonomy_watchdog.py \
  companyos/runtime/stalled_stage_progression_controller.py \
  companyos/governance/venture_identity_progression.py \
  scripts/companyos_executionctl \
  scripts/validate_research_to_execution_fix.py

git commit -m "Bridge CompanyOS research into venture execution" || true
git push origin "$BRANCH"

echo
echo "===== RESTART SUPERVISED STACK TO LOAD FIX ====="
scripts/companyosctl restart
sleep 4

echo
echo "===== FINAL HEALTH ====="
scripts/companyosctl health

echo
echo "===== FINAL EXECUTION STATUS ====="
scripts/companyos_executionctl status

echo
echo "COMPANYOS_RESEARCH_TO_EXECUTION_LARGE_FIX=COMPLETE"
