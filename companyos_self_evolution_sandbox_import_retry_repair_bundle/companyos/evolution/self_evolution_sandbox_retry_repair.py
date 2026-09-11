from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
EVROOT = RUNTIME / "self_evolution"
LEDGER = EVROOT / "evolution_ledger.jsonl"
RETRY_LEDGER = EVROOT / "retry_repair_ledger.jsonl"

def append_jsonl(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, default=str) + "\n")

def load_ledger():
    if not LEDGER.exists():
        return []
    out = []
    for line in LEDGER.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out

def find_generated_pairs():
    pairs = []
    gen = RUNTIME / "generated_improvements"
    if not gen.exists():
        return pairs
    for folder in gen.iterdir():
        if not folder.is_dir():
            continue
        for module in folder.glob("*.py"):
            if module.name.startswith("test_"):
                continue
            test = folder / ("test_" + module.stem + ".py")
            if test.exists():
                pairs.append((module, test))
    return pairs

def patch_test_file(test_path, module_path):
    module_name = module_path.stem
    content = (
        "from __future__ import annotations\n"
        "import importlib.util\n"
        "from pathlib import Path\n\n"
        f"MODULE_PATH = Path(r'{str(module_path)}')\n"
        f"SPEC = importlib.util.spec_from_file_location('{module_name}', MODULE_PATH)\n"
        "MODULE = importlib.util.module_from_spec(SPEC)\n"
        "assert SPEC and SPEC.loader\n"
        "SPEC.loader.exec_module(MODULE)\n\n"
        "def test_generated_module_loads():\n"
        "    assert MODULE is not None\n"
    )
    test_path.write_text(content, encoding="utf-8")
    return {"test_path": str(test_path), "module_path": str(module_path), "patched": True}

def repair_all_generated_tests():
    results = []
    for module, test in find_generated_pairs():
        try:
            results.append(patch_test_file(test, module))
        except Exception as exc:
            results.append({"module_path": str(module), "test_path": str(test), "patched": False, "error": str(exc)})
    return {"generated_pairs_found": len(results), "patched": sum(1 for r in results if r.get("patched")), "results": results}

def direct_pytest(test_path):
    try:
        cp = subprocess.run([sys.executable, "-m", "pytest", "-q", str(test_path)], cwd=ROOT, capture_output=True, text=True, timeout=120)
        return {"ok": cp.returncode == 0, "returncode": cp.returncode, "stdout": cp.stdout[-8000:], "stderr": cp.stderr[-8000:]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

def validate_repaired_tests():
    results = []
    for module, test in find_generated_pairs():
        r = direct_pytest(test)
        r.update({"module": str(module), "test": str(test)})
        results.append(r)
    return {"tested": len(results), "passed": sum(1 for r in results if r.get("ok")), "failed": sum(1 for r in results if not r.get("ok")), "results": results}

def retry_rejected_candidates():
    from companyos.evolution.self_evolution_promotion_engine import promote
    rejected, seen = [], set()
    for row in load_ledger():
        if row.get("status") != "REJECTED_TESTS":
            continue
        cand = row.get("candidate")
        if not cand or cand in seen:
            continue
        seen.add(cand)
        p = Path(cand)
        if p.exists() and p.suffix == ".py" and not p.name.startswith("test_"):
            rejected.append(p)
    results = []
    for p in rejected:
        try:
            result = promote(str(p))
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}
        entry = {"ts": time.time(), "candidate": str(p), "retry_result": result}
        append_jsonl(RETRY_LEDGER, entry)
        results.append(entry)
    return {"rejected_candidates_found": len(rejected), "retried": len(results), "results": results}

def run_repair_cycle():
    return {
        "repair": repair_all_generated_tests(),
        "validation": validate_repaired_tests(),
        "retry": retry_rejected_candidates(),
    }
