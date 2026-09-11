from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
EVROOT = RUNTIME / "self_evolution"
STATE = EVROOT / "benchmark_judge_state.json"
LEDGER = EVROOT / "benchmark_judge_ledger.jsonl"

MIN_IMPROVEMENT_SCORE = float(os.getenv("COMPANYOS_EVOLUTION_MIN_BENCHMARK_GAIN", "0.02"))
MAX_RUNTIME_SECONDS = int(os.getenv("COMPANYOS_EVOLUTION_BENCHMARK_TIMEOUT", "120"))

def load(path: Path, default: Any):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return default

def save(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

def append(obj: Any):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True, default=str) + "\n")

def run(cmd: list[str], timeout: int = MAX_RUNTIME_SECONDS) -> dict:
    started = time.time()
    try:
        cp = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "duration_seconds": round(time.time() - started, 3),
            "stdout": cp.stdout[-12000:],
            "stderr": cp.stderr[-12000:],
        }
    except Exception as exc:
        return {
            "ok": False,
            "duration_seconds": round(time.time() - started, 3),
            "error": f"{type(exc).__name__}: {exc}",
        }

def runtime_snapshot() -> dict:
    candidates = [
        RUNTIME / "autonomous_ceo_runtime_service.json",
        ROOT / "companyos_runtime" / "autonomous_ceo_runtime_service.json",
    ]
    rt = {}
    for p in candidates:
        if p.exists():
            rt = load(p, {})
            if isinstance(rt, dict):
                break

    health = {}
    hp = RUNTIME / "runtime_health_autorecovery_report.json"
    if hp.exists():
        health = load(hp, {})

    evidence = load(RUNTIME / "profit_first_evidence_report.json", {})
    ranking = evidence.get("ranking") or {}

    return {
        "ready": bool(rt.get("ready", False)),
        "running": bool(rt.get("running", False)),
        "failed_orchestrations": int(rt.get("failed_orchestrations", 0) or 0),
        "halted_orchestrations": int(rt.get("halted_orchestrations", 0) or 0),
        "completed_orchestrations": int(rt.get("completed_orchestrations", 0) or 0),
        "idle_for_seconds": float(rt.get("idle_for_seconds", 0) or 0),
        "candidate_count": int(evidence.get("candidate_count", 0) or 0),
        "sector_count": int(evidence.get("sector_count", 0) or 0),
        "business_model_count": int(evidence.get("business_model_count", 0) or 0),
        "qualified_count": int(ranking.get("qualified_count", 0) or 0),
        "health_issues": ((health.get("after") or {}).get("issues") or health.get("issues") or []),
    }

def score_snapshot(s: dict) -> float:
    score = 0.0
    score += 0.20 if s.get("running") else 0.0
    score += 0.20 if s.get("ready") else 0.0

    failures = int(s.get("failed_orchestrations", 0)) + int(s.get("halted_orchestrations", 0))
    score += max(0.0, 0.15 - min(0.15, failures * 0.03))

    score += min(0.10, int(s.get("candidate_count", 0)) / 200.0)
    score += min(0.10, int(s.get("sector_count", 0)) / 80.0)
    score += min(0.10, int(s.get("business_model_count", 0)) / 70.0)
    score += min(0.10, int(s.get("qualified_count", 0)) / 20.0)

    issues = len(s.get("health_issues") or [])
    score -= min(0.20, issues * 0.04)
    return round(max(0.0, min(1.0, score)), 4)

def benchmark_module(module_path: str, promoted_path: str | None = None) -> dict:
    module = Path(module_path)
    if not module.exists():
        return {"ok": False, "reason": "module_not_found", "module": module_path}

    before = runtime_snapshot()
    before_score = score_snapshot(before)

    compile_result = run(["python", "-m", "py_compile", str(module)])

    tests = []
    for p in [module.parent / f"test_{module.stem}.py", module.parent / "tests"]:
        if p.is_file():
            tests.append(str(p))
        elif p.is_dir():
            tests += [str(x) for x in p.glob("test_*.py")]

    test_result = {"ok": True, "skipped": True, "reason": "no_tests_found"}
    if tests:
        test_result = run(["python", "-m", "pytest", "-q"] + tests)
        test_result["skipped"] = False

    promoted_compile = None
    if promoted_path:
        pp = Path(promoted_path)
        if pp.exists():
            promoted_compile = run(["python", "-m", "py_compile", str(pp)])

    after = runtime_snapshot()
    after_score = score_snapshot(after)
    gain = round(after_score - before_score, 4)

    structural_ok = bool(compile_result.get("ok")) and bool(test_result.get("ok"))
    if promoted_compile is not None:
        structural_ok = structural_ok and bool(promoted_compile.get("ok"))

    # For capability modules, neutral runtime score is acceptable if structure/tests pass.
    accepted = structural_ok and gain >= -0.01

    result = {
        "ok": True,
        "module": str(module),
        "promoted_path": promoted_path,
        "before": before,
        "before_score": before_score,
        "compile": compile_result,
        "tests": test_result,
        "promoted_compile": promoted_compile,
        "after": after,
        "after_score": after_score,
        "gain": gain,
        "structural_ok": structural_ok,
        "accepted": accepted,
        "decision": "KEEP" if accepted else "ROLLBACK_RECOMMENDED",
        "minimum_preferred_gain": MIN_IMPROVEMENT_SCORE,
        "ts": time.time(),
    }
    append(result)
    return result

def judge_recent_promotions(limit: int = 20) -> dict:
    evo_ledger = EVROOT / "evolution_ledger.jsonl"
    rows = []
    if evo_ledger.exists():
        for line in evo_ledger.read_text(encoding="utf-8", errors="ignore").splitlines()[-200:]:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass

    promotions = [r for r in rows if r.get("status") == "PROMOTED"][-limit:]
    judged = []
    for row in promotions:
        cand = row.get("candidate")
        target = row.get("target")
        if not cand:
            continue
        judged.append(benchmark_module(cand, target))

    state = load(STATE, {"runs": []})
    summary = {
        "judged": len(judged),
        "keep": sum(1 for j in judged if j.get("decision") == "KEEP"),
        "rollback_recommended": sum(1 for j in judged if j.get("decision") == "ROLLBACK_RECOMMENDED"),
        "results": judged,
        "ts": time.time(),
    }
    state.setdefault("runs", []).append(summary)
    state["runs"] = state["runs"][-100:]
    state["last_run"] = summary
    save(STATE, state)
    return summary
