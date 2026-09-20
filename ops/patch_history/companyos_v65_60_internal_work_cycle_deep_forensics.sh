#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.60 INTERNAL WORK CYCLE DEEP FORENSICS ====="
echo "SOURCE_WRITES=0"

python - <<'PY'
from pathlib import Path
import ast, inspect, importlib, json, tempfile, traceback, time

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
    raise SystemExit("V65_60_ABORT=test_not_found")

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
    raise SystemExit("V65_60_ABORT=kernel_import_not_found")

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
print(inspect.getsource(Kernel.run_cycle))

# Print helper methods called by run_cycle.
run_src = inspect.getsource(Kernel.run_cycle)
run_ast = ast.parse(run_src)
called = set()
for n in ast.walk(run_ast):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
        if isinstance(n.func.value, ast.Name) and n.func.value.id == "self":
            called.add(n.func.attr)

print("\n===== RUN_CYCLE SELF-HELPERS =====")
for name in sorted(called):
    if name in {"run_cycle"}:
        continue
    fn = getattr(Kernel, name, None)
    if fn is not None and callable(fn):
        try:
            print(f"\n--- {name}{inspect.signature(fn)} ---")
            print(inspect.getsource(fn))
        except Exception as exc:
            print(name, "SOURCE_ERROR=", repr(exc))

# Reproduce safely in isolated temp dir. Never touches live kernel state.
print("\n===== ISOLATED REPRODUCTION =====")
with tempfile.TemporaryDirectory() as td:
    state_dir = Path(td)
    k = Kernel(state_dir=state_dir)
    item = WorkItem("a", "alpha", "Research", 90, 0.8, 0.2, [], ["research"])

    print("STATE_DIR=", state_dir)
    print("ITEM=", repr(item))

    before = {}
    for key, value in vars(k).items():
        try:
            json.dumps(value, default=str)
            before[key] = value
        except Exception:
            before[key] = repr(value)
    print("KERNEL_BEFORE=", json.dumps(before, default=str, indent=2))

    enq = k.enqueue(item)
    print("ENQUEUE_RESULT=", repr(enq))

    mid = {}
    for key, value in vars(k).items():
        try:
            json.dumps(value, default=str)
            mid[key] = value
        except Exception:
            mid[key] = repr(value)
    print("KERNEL_AFTER_ENQUEUE=", json.dumps(mid, default=str, indent=2))

    # Show any durable files created in isolated state.
    files = []
    for p in sorted(state_dir.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(state_dir))
            try:
                content = p.read_text(errors="ignore")
            except Exception:
                content = "<binary/unreadable>"
            files.append((rel, content[:8000]))
            print(f"\n===== STATE FILE {rel} =====")
            print(content[:8000])

    try:
        result = k.run_cycle(capabilities={"research"})
        print("RUN_CYCLE_RESULT=", json.dumps(result, default=str, indent=2))
    except Exception as exc:
        print("RUN_CYCLE_EXCEPTION=", type(exc).__name__, str(exc))
        traceback.print_exc()
        result = {"exception": type(exc).__name__, "message": str(exc)}

    after = {}
    for key, value in vars(k).items():
        try:
            json.dumps(value, default=str)
            after[key] = value
        except Exception:
            after[key] = repr(value)
    print("KERNEL_AFTER_CYCLE=", json.dumps(after, default=str, indent=2))

    # Compact diagnosis from result shape.
    print("\n===== COMPACT DIAGNOSIS =====")
    for key in (
        "executed_count", "attempted_count", "queued_count", "blocked_count",
        "skipped_count", "failed_count", "results", "failures", "blocked",
        "reason", "status"
    ):
        if isinstance(result, dict) and key in result:
            print(f"{key}=", repr(result[key]))

report = {
    "version": "V65.60",
    "timestamp": int(time.time()),
    "source_writes": 0,
    "test_file": str(test_file.relative_to(ROOT)),
    "kernel_module": module_name,
    "kernel_source": str(src_path),
    "kernel_signature": str(inspect.signature(Kernel)),
    "workitem_signature": str(inspect.signature(WorkItem)),
}
rp = REPORT_DIR / f"v65_60_internal_work_cycle_forensics_{report['timestamp']}.json"
rp.write_text(json.dumps(report, indent=2))

print("\nREPORT=", rp)
print("V65_60_FORENSICS=COMPLETE")
PY
