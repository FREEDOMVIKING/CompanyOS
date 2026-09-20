#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.60A INTERNAL WORK CYCLE DEEP FORENSICS (FIXED) ====="
echo "SOURCE_WRITES=0"

python - <<'PY'
from pathlib import Path
import ast, inspect, importlib, json, tempfile, traceback, time, textwrap

ROOT = Path.home() / "companyos"
REPORT_DIR = Path.home() / ".companyos_runtime/reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Resolve exact test + imported kernel module locally.
test_file = None
test_text = None
for p in sorted((ROOT / "tests").rglob("*.py")):
    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        continue
    if "def test_internal_work_executes" in txt and "WorkItem" in txt:
        test_file = p
        test_text = txt
        break

if test_file is None:
    raise SystemExit("V65_60A_ABORT=test_not_found")

print("TEST_FILE=", test_file.relative_to(ROOT))

tree = ast.parse(test_text)
imports = []
for n in tree.body:
    if isinstance(n, ast.ImportFrom) and n.module:
        names = [a.name for a in n.names]
        if any(x in names for x in ("AutonomousOperationsKernel", "WorkItem")):
            imports.append((n.module, names))
            print("IMPORT=", n.module, names)

if not imports:
    raise SystemExit("V65_60A_ABORT=kernel_import_not_found")

module_name = imports[0][0]
mod = importlib.import_module(module_name)
Kernel = getattr(mod, "AutonomousOperationsKernel")
WorkItem = getattr(mod, "WorkItem")

src_path = Path(inspect.getsourcefile(Kernel))
print("KERNEL_MODULE=", module_name)
print("KERNEL_SOURCE=", src_path)
print("KERNEL_SIGNATURE=", inspect.signature(Kernel))
print("WORKITEM_SIGNATURE=", inspect.signature(WorkItem))

print("\n===== WORKITEM CLASS =====")
print(inspect.getsource(WorkItem))

print("\n===== KERNEL __INIT__ =====")
print(inspect.getsource(Kernel.__init__))

print("\n===== KERNEL ENQUEUE =====")
print(inspect.getsource(Kernel.enqueue))

print("\n===== KERNEL RUN_CYCLE =====")
run_src_raw = inspect.getsource(Kernel.run_cycle)
print(run_src_raw)

# FIX: inspect.getsource(method) is class-indented. Dedent before AST parsing.
run_src = textwrap.dedent(run_src_raw)
run_ast = ast.parse(run_src)

called = set()
for n in ast.walk(run_ast):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
        if isinstance(n.func.value, ast.Name) and n.func.value.id == "self":
            called.add(n.func.attr)

print("\n===== RUN_CYCLE SELF-HELPERS =====")
helper_sources = {}
for name in sorted(called):
    if name == "run_cycle":
        continue
    fn = getattr(Kernel, name, None)
    if fn is not None and callable(fn):
        try:
            sig = str(inspect.signature(fn))
            src = inspect.getsource(fn)
            helper_sources[name] = {"signature": sig, "source": src}
            print(f"\n--- {name}{sig} ---")
            print(src)
        except Exception as exc:
            helper_sources[name] = {"error": repr(exc)}
            print(name, "SOURCE_ERROR=", repr(exc))

print("\n===== ISOLATED REPRODUCTION =====")
with tempfile.TemporaryDirectory() as td:
    state_dir = Path(td)
    k = Kernel(state_dir=state_dir)
    item = WorkItem("a", "alpha", "Research", 90, 0.8, 0.2, [], ["research"])

    print("STATE_DIR=", state_dir)
    print("ITEM=", repr(item))

    enq = k.enqueue(item)
    print("ENQUEUE_RESULT=", repr(enq))

    # Show queue as loaded by the kernel.
    try:
        q = k.load_queue()
        print("QUEUE_AFTER_ENQUEUE=", [repr(x) for x in q])
    except Exception as exc:
        print("QUEUE_LOAD_ERROR=", type(exc).__name__, str(exc))
        q = []

    # Directly probe select_ready before run_cycle.
    try:
        completed_ids = {
            item.work_id for item in q if getattr(item, "status", None) == "completed"
        }
        ready = k.select_ready(q, completed_ids, {"research"})
        print("COMPLETED_IDS=", completed_ids)
        print("SELECT_READY_COUNT=", len(ready))
        print("SELECT_READY_ITEMS=", [repr(x) for x in ready])
    except Exception as exc:
        print("SELECT_READY_ERROR=", type(exc).__name__, str(exc))
        ready = []

    # If select_ready returns an item, directly probe execute_internal on a fresh
    # isolated kernel copy only. This never touches live state.
    if ready:
        try:
            direct = k.execute_internal(ready[0])
            print("DIRECT_EXECUTE_INTERNAL_RESULT=", repr(direct))
        except Exception as exc:
            print("DIRECT_EXECUTE_INTERNAL_ERROR=", type(exc).__name__, str(exc))
            traceback.print_exc()

    # Reset isolated state and reproduce exactly as the test does.
    k = Kernel(state_dir=state_dir)
    # Clear and enqueue once to avoid direct-probe mutations affecting cycle proof.
    try:
        # overwrite queue through public save_queue if available
        if hasattr(k, "save_queue"):
            k.save_queue([])
    except Exception:
        pass
    k.enqueue(WorkItem("a", "alpha", "Research", 90, 0.8, 0.2, [], ["research"]))

    try:
        result = k.run_cycle(capabilities={"research"})
        print("RUN_CYCLE_RESULT=", json.dumps(result, default=str, indent=2))
    except Exception as exc:
        print("RUN_CYCLE_EXCEPTION=", type(exc).__name__, str(exc))
        traceback.print_exc()
        result = {"exception": type(exc).__name__, "message": str(exc)}

    try:
        q_after = k.load_queue()
        print("QUEUE_AFTER_CYCLE=", [repr(x) for x in q_after])
    except Exception as exc:
        print("QUEUE_AFTER_CYCLE_ERROR=", type(exc).__name__, str(exc))

    print("\n===== COMPACT DIAGNOSIS =====")
    if isinstance(result, dict):
        for key in (
            "executed_count", "held_for_gate_count", "last_result_status",
            "blocked_dependency_ids", "missing_capability_ids",
            "awaiting_existing_gate_ids", "results", "failures",
            "queue_size", "status", "reason"
        ):
            if key in result:
                print(f"{key}=", repr(result[key]))

report = {
    "version": "V65.60A",
    "timestamp": int(time.time()),
    "source_writes": 0,
    "test_file": str(test_file.relative_to(ROOT)),
    "kernel_module": module_name,
    "kernel_source": str(src_path),
    "kernel_signature": str(inspect.signature(Kernel)),
    "workitem_signature": str(inspect.signature(WorkItem)),
    "run_cycle_helpers": helper_sources,
}
rp = REPORT_DIR / f"v65_60a_internal_work_cycle_forensics_{report['timestamp']}.json"
rp.write_text(json.dumps(report, indent=2))

print("\nREPORT=", rp)
print("V65_60A_FORENSICS=COMPLETE")
PY
