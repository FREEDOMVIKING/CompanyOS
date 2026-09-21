from __future__ import annotations

import json
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
RAW_DIR = RUNTIME / "canonical_research_outputs"
STATE = RUNTIME / "research_output_capture_state.json"
INDEX = RUNTIME / "canonical_research_output_index.jsonl"

INTERESTING_NAME_PARTS = (
    "research",
    "discover",
    "opportun",
    "market",
    "venture",
    "candidate",
    "analy",
    "evaluate",
    "rank",
    "plan",
    "agent",
    "execute",
    "dispatch",
    "orchestrat",
)

_tls = threading.local()


def _portable_path(path: Path) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)

def _safe(v: Any, depth: int = 0) -> Any:
    if depth > 6:
        return repr(v)[:2000]
    if v is None or isinstance(v, (bool, int, float, str)):
        if isinstance(v, str):
            return v[:20000]
        return v
    if isinstance(v, Path):
        return str(v)
    if isinstance(v, dict):
        out = {}
        for i, (k, val) in enumerate(v.items()):
            if i >= 300:
                out["__truncated__"] = True
                break
            out[str(k)[:300]] = _safe(val, depth + 1)
        return out
    if isinstance(v, (list, tuple, set)):
        return [_safe(x, depth + 1) for x in list(v)[:300]]
    if hasattr(v, "__dict__"):
        try:
            return {
                "__class__": f"{v.__class__.__module__}.{v.__class__.__name__}",
                **_safe(vars(v), depth + 1),
            }
        except Exception:
            pass
    try:
        return repr(v)[:10000]
    except Exception:
        return f"<unserializable {type(v).__name__}>"

def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def _save(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

def _append_jsonl(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True, default=str) + "\n")

def _interesting(frame) -> bool:
    code = frame.f_code
    filename = str(code.co_filename)
    name = str(code.co_name).lower()
    if "/companyos/" not in filename.replace("\\", "/"):
        return False
    return any(part in name for part in INTERESTING_NAME_PARTS)

def _profiler(frame, event, arg):
    if event != "return":
        return
    ctx = getattr(_tls, "ctx", None)
    if not ctx or not _interesting(frame):
        return
    try:
        val = _safe(arg)
        # Skip trivial None/booleans to reduce noise.
        if val is None or isinstance(val, bool):
            return
        ctx["returns"].append({
            "function": frame.f_code.co_name,
            "module": frame.f_globals.get("__name__"),
            "filename": str(frame.f_code.co_filename),
            "lineno": frame.f_lineno,
            "return_value": val,
        })
        if len(ctx["returns"]) > 1000:
            ctx["returns"] = ctx["returns"][-1000:]
    except Exception:
        pass

def begin_capture(goal: Any = None) -> dict:
    ctx = {
        "started_at_unix": time.time(),
        "goal": _safe(goal),
        "returns": [],
    }
    _tls.ctx = ctx
    sys.setprofile(_profiler)
    threading.setprofile(_profiler)
    return ctx

def end_capture(result: Any = None, error: str | None = None) -> dict:
    try:
        sys.setprofile(None)
        threading.setprofile(None)
    except Exception:
        pass
    ctx = getattr(_tls, "ctx", None) or {
        "started_at_unix": time.time(),
        "goal": None,
        "returns": [],
    }
    _tls.ctx = None
    ctx["finished_at_unix"] = time.time()
    ctx["result"] = _safe(result)
    ctx["error"] = error
    return ctx

def persist_capture(ctx: dict) -> dict:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    result = ctx.get("result")
    orchestration_id = None
    if isinstance(result, dict):
        orchestration_id = result.get("orchestration_id") or result.get("id")
    if not orchestration_id and isinstance(result, dict) and isinstance(result.get("__class__"), str):
        orchestration_id = result.get("orchestration_id")
    if not orchestration_id:
        # Search serialized result text conservatively.
        try:
            text = json.dumps(result, default=str)
            import re
            m = re.search(r'"orchestration_id"\s*:\s*"([^"]+)"', text)
            if m:
                orchestration_id = m.group(1)
        except Exception:
            pass

    stamp = int(ctx.get("started_at_unix", time.time()) * 1000)
    oid_part = str(orchestration_id or "unknown").replace("/", "_")[:120]
    path = RAW_DIR / f"{stamp}_{oid_part}.json"

    payload = {
        "capture_version": 1,
        "orchestration_id": orchestration_id,
        **ctx,
    }
    _save(path, payload)

    index_row = {
        "ts": time.time(),
        "orchestration_id": orchestration_id,
        "path": _portable_path(path),
        "captured_return_events": len(ctx.get("returns", [])),
        "had_error": bool(ctx.get("error")),
    }
    _append_jsonl(INDEX, index_row)

    st = _load(STATE, {"captures": []})
    st["last_capture_unix"] = index_row["ts"]
    st["last_capture"] = index_row
    st.setdefault("captures", []).append(index_row)
    st["captures"] = st["captures"][-200:]
    _save(STATE, st)

    return index_row

def install_orchestrator_capture() -> bool:
    try:
        from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
    except Exception:
        return False

    current = getattr(AutonomousCEOOrchestrator, "start", None)
    if current is None:
        return False
    if getattr(current, "_companyos_raw_capture_wrapped", False):
        return True

    original = current

    def wrapped(self, *args, **kwargs):
        goal = kwargs.get("goal")
        if goal is None and args:
            goal = args[0]
        begin_capture(goal)
        result = None
        err = None
        try:
            result = original(self, *args, **kwargs)
            return result
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
            raise
        finally:
            ctx = end_capture(result=result, error=err)
            persist_capture(ctx)

    wrapped._companyos_raw_capture_wrapped = True
    wrapped._companyos_raw_capture_original = original
    AutonomousCEOOrchestrator.start = wrapped
    return True

# COMPANYOS_SPECIALIST_RESULT_CAPTURE_V69_13
def persist_specialist_result(task: Any, result: Any, agent_name: str | None = None) -> dict:
    # Persist the result of an actually executed specialist task. This complements
    # the legacy orchestrator-start profiler, whose scope ends before handlers run.
    task_type = str(getattr(task, "task_type", "") or "")
    task_id = str(getattr(task, "task_id", "") or "")
    payload = getattr(task, "payload", {}) or {}
    goal_id = str(payload.get("goal_id") or "") if isinstance(payload, dict) else ""

    artifact_payload = None
    artifact_path = None
    if isinstance(result, dict) and result.get("artifact"):
        artifact_path = str(result.get("artifact"))
        try:
            p = Path(artifact_path)
            if p.exists() and p.is_file() and p.stat().st_size <= 2_000_000:
                artifact_payload = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            artifact_payload = None

    record = {
        "capture_version": 2,
        "capture_kind": "specialist_task_result",
        "captured_at_unix": time.time(),
        "task_id": task_id,
        "task_type": task_type,
        "goal_id": goal_id,
        "agent_name": agent_name,
        "task_payload": _safe(payload),
        "result": _safe(result),
        "artifact_path": artifact_path,
        "artifact_payload": _safe(artifact_payload),
    }

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = int(record["captured_at_unix"] * 1000)
    safe_task = "".join(c for c in task_id if c.isalnum() or c in "-_")[:100] or "unknown"
    path = RAW_DIR / f"{stamp}_{safe_task}_{task_type or 'task'}.json"
    _save(path, record)

    index_row = {
        "ts": record["captured_at_unix"],
        "orchestration_id": goal_id.split(":goal:", 1)[0] if ":goal:" in goal_id else None,
        "goal_id": goal_id,
        "task_id": task_id,
        "task_type": task_type,
        "agent_name": agent_name,
        "path": str(path),
        "capture_kind": "specialist_task_result",
    }
    _append_jsonl(INDEX, index_row)
    return index_row
