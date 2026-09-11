from __future__ import annotations
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
GEN_ROOT = RUNTIME / "generated_improvements"
LEDGER = RUNTIME / "self_evolution" / "permanent_integration_ledger.jsonl"
STATE = RUNTIME / "self_evolution" / "permanent_integration_state.json"

INTERVAL = int(os.getenv("COMPANYOS_PERMANENT_EVOLUTION_INTERVAL_SECONDS", "300"))

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

def self_contained_test(module_path: Path) -> Path:
    test_path = module_path.parent / f"test_{module_path.stem}.py"
    content = (
        "from __future__ import annotations\n"
        "import importlib.util\n"
        "from pathlib import Path\n\n"
        "MODULE_PATH = Path(__file__).with_name(" + repr(module_path.name) + ")\n"
        "SPEC = importlib.util.spec_from_file_location('candidate_module', MODULE_PATH)\n"
        "assert SPEC and SPEC.loader\n"
        "MODULE = importlib.util.module_from_spec(SPEC)\n"
        "SPEC.loader.exec_module(MODULE)\n\n"
        "def test_generated_module_loads():\n"
        "    assert MODULE is not None\n"
    )
    test_path.write_text(content, encoding="utf-8")
    return test_path

def discover_generated_modules() -> list[Path]:
    if not GEN_ROOT.exists():
        return []
    out = []
    for folder in GEN_ROOT.iterdir():
        if not folder.is_dir():
            continue
        for p in folder.glob("*.py"):
            if p.name.startswith("test_"):
                continue
            out.append(p)
    return sorted(out, key=lambda p: p.stat().st_mtime)

def run_pytest(test_path: Path) -> dict:
    try:
        cp = subprocess.run(
            ["python", "-m", "pytest", "-q", str(test_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout": cp.stdout[-6000:],
            "stderr": cp.stderr[-6000:],
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

def run_once() -> dict:
    from companyos.evolution.self_evolution_promotion_engine import promote

    state = load(STATE, {"processed": {}, "totals": {"promoted": 0, "rejected": 0, "rolled_back": 0}})
    processed = state.setdefault("processed", {})
    results = []

    for module in discover_generated_modules():
        key = str(module.resolve())
        mtime = module.stat().st_mtime
        marker = processed.get(key)
        if marker and float(marker.get("mtime", 0)) >= mtime:
            continue

        test_path = self_contained_test(module)
        test_result = run_pytest(test_path)

        entry = {
            "ts": time.time(),
            "module": str(module),
            "test_path": str(test_path),
            "test_result": test_result,
        }

        if not test_result.get("ok"):
            entry["status"] = "REJECTED_PRE_PROMOTION_TESTS"
            state["totals"]["rejected"] = int(state["totals"].get("rejected", 0)) + 1
            processed[key] = {"mtime": mtime, "status": entry["status"]}
            append(entry)
            results.append(entry)
            continue

        promo = promote(str(module))
        entry["promotion_result"] = promo
        entry["status"] = promo.get("status", "UNKNOWN")

        if entry["status"] == "PROMOTED":
            state["totals"]["promoted"] = int(state["totals"].get("promoted", 0)) + 1
        elif entry["status"] == "ROLLED_BACK":
            state["totals"]["rolled_back"] = int(state["totals"].get("rolled_back", 0)) + 1
        elif str(entry["status"]).startswith("REJECTED"):
            state["totals"]["rejected"] = int(state["totals"].get("rejected", 0)) + 1

        processed[key] = {"mtime": mtime, "status": entry["status"]}
        append(entry)
        results.append(entry)

    state["last_run_unix"] = time.time()
    state["last_results"] = results[-50:]
    save(STATE, state)

    return {
        "ok": True,
        "processed_now": len(results),
        "results": results,
        "state": state,
    }
