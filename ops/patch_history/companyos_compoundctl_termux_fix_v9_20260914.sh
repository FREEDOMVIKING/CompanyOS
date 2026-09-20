#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${HOME}/companyos"
cd "$ROOT"

echo "==== CompanyOS V9: compoundctl Termux import fix ===="

mkdir -p scripts .companyos_backups
STAMP="$(date +%Y%m%d_%H%M%S)"
[ -f scripts/companyos_compoundctl ] && cp -p scripts/companyos_compoundctl ".companyos_backups/companyos_compoundctl.${STAMP}.bak"

cat > scripts/companyos_compoundctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
"""Termux-safe control utility for CompanyOS compounding capability expansion."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
root_s = str(ROOT)
if root_s not in sys.path:
    sys.path.insert(0, root_s)

def _load_module():
    try:
        from companyos.runtime.compounding_capability_expansion import (
            CompoundingCapabilityExpansion,
        )
        return CompoundingCapabilityExpansion
    except ImportError:
        # Support implementations exposing a runtime-style class name instead.
        from companyos.runtime import compounding_capability_expansion as mod
        for name in (
            "CompoundingCapabilityExpansion",
            "CompoundingCapabilityExpansionRuntime",
            "CapabilityCompoundingRuntime",
        ):
            cls = getattr(mod, name, None)
            if cls is not None:
                return cls
        raise

def _state_paths():
    rt = ROOT / ".companyos_runtime"
    names = (
        "compounding_capability_expansion_state.json",
        "capability_expansion_compounding_state.json",
        "compounding_expansion_state.json",
    )
    return [rt / n for n in names]

def status():
    for p in _state_paths():
        if p.exists():
            try:
                print(json.dumps(json.loads(p.read_text()), indent=2, sort_keys=True))
                return 0
            except Exception as e:
                print(json.dumps({"ok": False, "state_path": str(p), "error": str(e)}, indent=2))
                return 1
    # If the module has its own status API, try it without assuming one.
    try:
        cls = _load_module()
        obj = cls()
        for name in ("status", "snapshot", "state"):
            fn = getattr(obj, name, None)
            if callable(fn):
                value = fn()
                print(json.dumps(value, indent=2, sort_keys=True, default=str))
                return 0
    except Exception as e:
        print(json.dumps({"ok": False, "reason": "state_not_found", "module_error": str(e)}, indent=2))
        return 1
    print(json.dumps({"ok": False, "reason": "state_not_found"}, indent=2))
    return 1

def once():
    cls = _load_module()
    obj = cls()
    for name in ("run_once", "cycle_once", "tick", "step", "evaluate_once"):
        fn = getattr(obj, name, None)
        if callable(fn):
            value = fn()
            if value is not None:
                print(json.dumps(value, indent=2, sort_keys=True, default=str))
            else:
                print(json.dumps({"ok": True, "action": name}))
            return 0
    raise RuntimeError("No supported one-cycle method found; supervised runtime left unchanged.")

def events():
    rt = ROOT / ".companyos_runtime"
    candidates = sorted(
        list(rt.glob("*compound*event*.json*")) +
        list(rt.glob("*capability*expansion*event*.json*")) +
        list(rt.glob("*compound*ledger*.json*")),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    )
    if not candidates:
        print(json.dumps({"events": [], "reason": "no_event_artifact_found"}, indent=2))
        return 0
    p = candidates[0]
    print(f"EVENT_SOURCE={p}")
    try:
        data = json.loads(p.read_text())
        print(json.dumps(data, indent=2, sort_keys=True, default=str))
    except Exception:
        lines = p.read_text(errors="replace").splitlines()
        print("\n".join(lines[-100:]))
    return 0

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        return status()
    if cmd == "once":
        return once()
    if cmd == "events":
        return events()
    if cmd in ("help", "-h", "--help"):
        print("usage: scripts/companyos_compoundctl {status|once|events}")
        return 0
    print(f"Unknown command: {cmd}", file=sys.stderr)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x scripts/companyos_compoundctl

echo "[1/5] Python import contract"
python - <<'PY'
import sys
from pathlib import Path
root=Path.cwd()
sys.path.insert(0, str(root))
import companyos
import companyos.runtime.compounding_capability_expansion
print("IMPORT_CONTRACT=PASS")
PY

echo "[2/5] Control script compile"
python -m py_compile scripts/companyos_compoundctl
echo "COMPOUNDCTL_COMPILE=PASS"

echo "[3/5] Control status"
scripts/companyos_compoundctl status || true

echo "[4/5] Supervisor status"
if [ -x scripts/companyosctl ]; then
  scripts/companyosctl status
else
  echo "WARN: scripts/companyosctl not found/executable"
fi

echo "[5/5] Git checkpoint"
git add scripts/companyos_compoundctl
if ! git diff --cached --quiet; then
  git commit -m "Fix Termux compound capability control imports"
  git push origin HEAD || echo "WARN: git push failed; local commit preserved"
else
  echo "No new git diff to commit."
fi

echo
echo "COMPANYOS_COMPOUNDCTL_TERMUX_FIX_V9=PASS"
echo "Next inspection commands:"
echo "  scripts/companyos_compoundctl status"
echo "  scripts/companyos_compoundctl events"
