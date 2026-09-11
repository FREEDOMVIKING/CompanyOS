from __future__ import annotations
import json, os, py_compile, shutil, subprocess, time, hashlib
from pathlib import Path

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
EV = RUNTIME / "self_evolution"
STAGING = EV / "staging"
PROMOTED = EV / "promoted"
REJECTED = EV / "rejected"
BACKUPS = EV / "backups"
LEDGER = EV / "evolution_ledger.jsonl"
STATE = EV / "state.json"
GEN_ROOTS = [
    RUNTIME / "generated_improvements",
    ROOT / "companyos_runtime" / "generated_improvements",
    ROOT / "generated_improvements",
]
MIN_SCORE = float(os.getenv("COMPANYOS_EVOLUTION_MIN_PROMOTION_SCORE", "0.85"))
TIMEOUT = int(os.getenv("COMPANYOS_EVOLUTION_TEST_TIMEOUT", "120"))


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return default


def save(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def append_ledger(obj):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True, default=str) + "\n")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def discover() -> list[dict]:
    out, seen = [], set()
    for root in GEN_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            rp = str(p.resolve())
            if rp in seen:
                continue
            seen.add(rp)
            out.append({
                "path": rp,
                "mtime": p.stat().st_mtime,
                "size": p.stat().st_size,
                "sha256": digest(p),
            })
    return sorted(out, key=lambda x: x["mtime"], reverse=True)


def compile_test(path: Path) -> dict:
    try:
        py_compile.compile(str(path), doraise=True)
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def import_test(path: Path) -> dict:
    code = (
        "import importlib.util;"
        f"p={str(path)!r};"
        "s=importlib.util.spec_from_file_location('companyos_candidate',p);"
        "m=importlib.util.module_from_spec(s);"
        "s.loader.exec_module(m);"
        "print('IMPORT_OK')"
    )
    try:
        cp = subprocess.run(["python", "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT)
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout": cp.stdout[-4000:],
            "stderr": cp.stderr[-4000:],
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def pytest_test(path: Path) -> dict:
    tests = []
    for base in (path.parent, path.parent / "tests"):
        if base.exists():
            tests.extend(base.glob("test_*.py"))
            tests.extend(base.glob("*_test.py"))
    tests = sorted(set(tests))
    if not tests:
        return {"ok": True, "skipped": True, "reason": "no_local_tests_found"}
    try:
        cp = subprocess.run(
            ["python", "-m", "pytest", "-q"] + [str(t) for t in tests],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
        return {
            "ok": cp.returncode == 0,
            "skipped": False,
            "tests": [str(t) for t in tests],
            "returncode": cp.returncode,
            "stdout": cp.stdout[-12000:],
            "stderr": cp.stderr[-12000:],
        }
    except Exception as exc:
        return {"ok": False, "skipped": False, "error": f"{type(exc).__name__}: {exc}"}


def evaluate(path: Path) -> dict:
    static = compile_test(path)
    imp = import_test(path) if static["ok"] else {"ok": False, "skipped": True}
    tests = pytest_test(path) if static["ok"] and imp["ok"] else {"ok": False, "skipped": True}
    score = 0.0
    score += 0.35 if static.get("ok") else 0.0
    score += 0.35 if imp.get("ok") else 0.0
    score += 0.15 if tests.get("skipped") else (0.30 if tests.get("ok") else 0.0)
    eligible = score >= MIN_SCORE and static.get("ok") and imp.get("ok") and (tests.get("ok") or tests.get("skipped"))
    return {"static": static, "import": imp, "tests": tests, "score": round(score, 3), "eligible": bool(eligible)}


def health_check() -> dict:
    checks = {}
    status_script = ROOT / "scripts" / "companyos_productive_autonomy.sh"
    if status_script.exists():
        try:
            cp = subprocess.run(["bash", str(status_script), "status"], cwd=ROOT, capture_output=True, text=True, timeout=30)
            checks["productive_autonomy"] = {
                "ok": cp.returncode == 0,
                "stdout": cp.stdout[-4000:],
                "stderr": cp.stderr[-4000:],
            }
        except Exception as exc:
            checks["productive_autonomy"] = {"ok": False, "error": str(exc)}
    return {"ok": all(v.get("ok", False) for v in checks.values()) if checks else True, "checks": checks}


def promote(candidate: str, target_rel: str | None = None, require_approval: bool = False) -> dict:
    src = Path(candidate).expanduser().resolve()
    if not src.exists():
        return {"ok": False, "reason": "candidate_not_found"}

    eid = f"evolution-{int(time.time())}"
    staged = STAGING / eid / src.name
    staged.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, staged)
    evaluation = evaluate(staged)

    record = {
        "evolution_id": eid,
        "candidate": str(src),
        "candidate_sha256": digest(src),
        "staged": str(staged),
        "evaluation": evaluation,
        "target_rel": target_rel,
        "started_at_unix": time.time(),
    }

    if not evaluation["eligible"]:
        reject_dir = REJECTED / eid
        reject_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(staged, reject_dir / staged.name)
        record.update({"status": "REJECTED_TESTS", "finished_at_unix": time.time()})
        append_ledger(record)
        return record

    if require_approval:
        record.update({"status": "AWAITING_APPROVAL", "finished_at_unix": time.time()})
        append_ledger(record)
        return record

    if target_rel:
        target = (ROOT / target_rel).resolve()
        if ROOT.resolve() not in target.parents and target != ROOT.resolve():
            return {"ok": False, "reason": "target_outside_companyos_root"}
    else:
        target = ROOT / "companyos" / "evolution_promoted" / src.name

    target.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if target.exists():
        backup = BACKUPS / eid / target.relative_to(ROOT)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)

    shutil.copy2(staged, target)
    post_static = compile_test(target)
    post_health = health_check()

    if not post_static.get("ok") or not post_health.get("ok"):
        if backup and backup.exists():
            shutil.copy2(backup, target)
            rollback = "restored_backup"
        else:
            target.unlink(missing_ok=True)
            rollback = "removed_new_file"
        record.update({
            "status": "ROLLED_BACK",
            "target": str(target),
            "backup": str(backup) if backup else None,
            "rollback": rollback,
            "post_static": post_static,
            "post_health": post_health,
            "finished_at_unix": time.time(),
        })
        append_ledger(record)
        return record

    promoted_copy = PROMOTED / eid / target.name
    promoted_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, promoted_copy)
    record.update({
        "status": "PROMOTED",
        "target": str(target),
        "backup": str(backup) if backup else None,
        "post_static": post_static,
        "post_health": post_health,
        "promoted_sha256": digest(target),
        "finished_at_unix": time.time(),
    })
    append_ledger(record)

    state = load(STATE, {"promotions": 0, "rollbacks": 0, "rejections": 0})
    state["promotions"] = int(state.get("promotions", 0)) + 1
    state["last_promotion"] = record
    save(STATE, state)
    return record


def ledger(limit: int = 50) -> list[dict]:
    if not LEDGER.exists():
        return []
    out = []
    for line in LEDGER.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out
