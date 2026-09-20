#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.83 IDLE PROFIT AUTO-SEED ====="

python - <<'PY'
from pathlib import Path
import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
REPORT_DIR = RUNTIME / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

SRC = ROOT / "companyos/runtime/continuous_goal_runtime.py"
STAMP = int(time.time())
SNAP_DIR = RUNTIME / "checkpoints" / f"v65_83_idle_profit_autoseed_before_{STAMP}"
SNAP_DIR.mkdir(parents=True, exist_ok=True)
BACKUP = SNAP_DIR / "continuous_goal_runtime.py.before"

print("REPO=", ROOT)
print("SOURCE=", SRC)
print("SNAPSHOT_DIR=", SNAP_DIR)

if not SRC.exists():
    raise SystemExit("V65_83_ABORT=continuous_goal_runtime_missing")

source = SRC.read_text(encoding="utf-8")

required = [
    "if dispatched == 0:",
    "result = self.scheduler.process_next()",
    "state.last_reason = result.reason",
]
missing = [x for x in required if x not in source]
print("PATCH_ANCHOR_MISSING=", missing)
if missing:
    raise SystemExit("V65_83_ABORT=runtime_patch_anchor_missing")

shutil.copy2(SRC, BACKUP)
print("SOURCE_BACKUP=", BACKUP)

if "import json, time, os" not in source:
    source = source.replace("import json, time\n", "import json, time, os\n", 1)

if "    # V65.83 profit auto-seed state" not in source:
    anchor = "    ceo_failures: int = 0\n"
    replacement = (
        "    ceo_failures: int = 0\n"
        "    # V65.83 profit auto-seed state\n"
        "    auto_seeded_profit_goals: int = 0\n"
        "    last_auto_seed_unix: float = 0.0\n"
    )
    if anchor not in source:
        raise SystemExit("V65_83_ABORT=state_field_anchor_missing")
    source = source.replace(anchor, replacement, 1)

if "        # V65.83 idle profit auto-seed configuration" not in source:
    anchor = '        self.stop_path = self.runtime_root / "continuous_goal_runtime.stop"\n'
    replacement = (
        '        self.stop_path = self.runtime_root / "continuous_goal_runtime.stop"\n'
        "        # V65.83 idle profit auto-seed configuration\n"
        '        self.profit_autoseed_enabled = os.getenv("COMPANYOS_PROFIT_AUTOSEED_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}\n'
        '        self.profit_autoseed_cooldown_seconds = max(0, int(os.getenv("COMPANYOS_PROFIT_AUTOSEED_COOLDOWN_SECONDS", "300")))\n'
    )
    if anchor not in source:
        raise SystemExit("V65_83_ABORT=constructor_anchor_missing")
    source = source.replace(anchor, replacement, 1)

if "    # V65.83 idle profit auto-seed helper" not in source:
    anchor = "    def cycle(self, state):\n"
    helper = r'''    # V65.83 idle profit auto-seed helper
    def _auto_seed_profit_goal_if_idle(self, state):
        # Seed exactly one new profit-first CEO goal only when CompanyOS is
        # globally idle. This creates internal intake only.
        if not self.profit_autoseed_enabled:
            return None

        now = time.time()
        if (
            self.profit_autoseed_cooldown_seconds > 0
            and float(getattr(state, "last_auto_seed_unix", 0.0) or 0.0) > 0
            and now - float(state.last_auto_seed_unix) < self.profit_autoseed_cooldown_seconds
        ):
            return None

        intake_records = self.scheduler.intake.all_records()
        if any(r.state in ("PENDING", "CLAIMED") for r in intake_records):
            return None

        orchestration_records = []
        for p in sorted(self.scheduler.ceo.root.glob("*.json")):
            try:
                orchestration_records.append(self.scheduler.ceo.load(p.stem))
            except Exception:
                continue
        if any(r.state == "RUNNING" for r in orchestration_records):
            return None

        queue = self.execution_loop.queue
        if any(t.state in ("QUEUED", "CLAIMED", "RUNNING") for t in queue.all_tasks()):
            return None

        from companyos.strategy.profit_first_venture_engine import discovery_directive

        goal = discovery_directive()
        intake_id = f"auto-profit-{int(now)}"
        rec = self.scheduler.intake.submit(
            goal=goal,
            priority=1,
            metadata={
                "source": "continuous_goal_runtime_v65_83",
                "profit_first": True,
                "auto_seeded": True,
                "internal_only": True,
                "created_at_unix": now,
            },
            intake_id=intake_id,
            max_attempts=3,
        )

        state.auto_seeded_profit_goals = int(
            getattr(state, "auto_seeded_profit_goals", 0) or 0
        ) + 1
        state.last_auto_seed_unix = now
        return rec.intake_id

'''
    if anchor not in source:
        raise SystemExit("V65_83_ABORT=cycle_anchor_missing")
    source = source.replace(anchor, helper + anchor, 1)

if "                    # V65.83 auto-seed exactly one profit-first goal when globally idle" not in source:
    old = (
        "                else:\n"
        "                    state.idle_cycles += 1\n"
        "                    state.last_reason = result.reason\n"
    )
    new = (
        "                else:\n"
        "                    # V65.83 auto-seed exactly one profit-first goal when globally idle\n"
        "                    seeded_id = self._auto_seed_profit_goal_if_idle(state)\n"
        "                    if seeded_id:\n"
        "                        seeded = self.scheduler.process_next()\n"
        "                        if seeded.processed and seeded.orchestration_id:\n"
        "                            state.goals_processed += 1\n"
        "                            state.last_orchestration_id = seeded.orchestration_id\n"
        '                            state.last_reason = "profit_goal_auto_seeded_and_orchestrated"\n'
        "                        else:\n"
        '                            state.last_reason = "profit_goal_auto_seeded"\n'
        "                    else:\n"
        "                        state.idle_cycles += 1\n"
        "                        state.last_reason = result.reason\n"
    )
    if old not in source:
        raise SystemExit("V65_83_ABORT=idle_branch_anchor_missing")
    source = source.replace(old, new, 1)

SRC.write_text(source, encoding="utf-8")
print("PATCH_STATUS=applied")

py_compile.compile(str(SRC), doraise=True)
print("PY_COMPILE=PASS")

patched = SRC.read_text(encoding="utf-8")
static_checks = {
    "state_fields": "auto_seeded_profit_goals" in patched and "last_auto_seed_unix" in patched,
    "enabled_env": "COMPANYOS_PROFIT_AUTOSEED_ENABLED" in patched,
    "cooldown_env": "COMPANYOS_PROFIT_AUTOSEED_COOLDOWN_SECONDS" in patched,
    "global_idle_helper": "_auto_seed_profit_goal_if_idle" in patched,
    "profit_directive_import": "from companyos.strategy.profit_first_venture_engine import discovery_directive" in patched,
    "internal_only_metadata": '"internal_only": True' in patched,
    "immediate_scheduler_process": 'state.last_reason = "profit_goal_auto_seeded_and_orchestrated"' in patched,
}
print("STATIC_CHECKS=", static_checks)
if not all(static_checks.values()):
    raise SystemExit("V65_83_FAIL=static_contract_incomplete")

test_code = r'''
from companyos.runtime.continuous_goal_runtime import ContinuousGoalRuntime, ContinuousGoalRuntimeState

runtime = ContinuousGoalRuntime(interval_seconds=1, max_failures=3)
state = ContinuousGoalRuntimeState(running=True, ready=True, last_reason="isolated_start")

state = runtime.cycle(state)

records = runtime.scheduler.intake.all_records()
auto = [r for r in records if r.metadata.get("auto_seeded") is True]

print("ISOLATED_CYCLE1_REASON=", state.last_reason)
print("ISOLATED_AUTO_SEEDED_COUNT=", state.auto_seeded_profit_goals)
print("ISOLATED_INTAKE_COUNT=", len(records))
print("ISOLATED_AUTO_INTAKES=", len(auto))
print("ISOLATED_LAST_ORCHESTRATION_ID=", state.last_orchestration_id)

if state.auto_seeded_profit_goals != 1:
    raise SystemExit("isolated_autoseed_count_wrong")
if len(auto) != 1:
    raise SystemExit("isolated_auto_intake_count_wrong")
if not state.last_orchestration_id:
    raise SystemExit("isolated_orchestration_not_created")
if auto[0].state != "SUBMITTED":
    raise SystemExit(f"isolated_intake_state_wrong:{auto[0].state}")

goal = auto[0].goal.lower()
if "primary economic directive" not in goal:
    raise SystemExit("isolated_goal_missing_primary_economic_directive")
if "profit" not in goal:
    raise SystemExit("isolated_goal_missing_profit_language")
if not auto[0].metadata.get("internal_only"):
    raise SystemExit("isolated_goal_not_internal_only")

state2 = runtime.cycle(state)
records2 = runtime.scheduler.intake.all_records()
auto2 = [r for r in records2 if r.metadata.get("auto_seeded") is True]

print("ISOLATED_CYCLE2_REASON=", state2.last_reason)
print("ISOLATED_AUTO_SEEDED_COUNT_AFTER_2=", state2.auto_seeded_profit_goals)
print("ISOLATED_AUTO_INTAKES_AFTER_2=", len(auto2))

if len(auto2) != 1:
    raise SystemExit("isolated_duplicate_autoseed_detected")

print("ISOLATED_IDLE_AUTOSEED=PASS")
print("ISOLATED_ANTI_FLOOD=PASS")
'''

with tempfile.TemporaryDirectory(prefix="companyos_v65_83_home_") as td:
    env = os.environ.copy()
    env["HOME"] = td
    env["PYTHONPATH"] = str(ROOT)
    env["COMPANYOS_PROFIT_AUTOSEED_ENABLED"] = "1"
    env["COMPANYOS_PROFIT_AUTOSEED_COOLDOWN_SECONDS"] = "300"

    cp = subprocess.run(
        [sys.executable, "-c", test_code],
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
    )

    print("ISOLATED_RETURN_CODE=", cp.returncode)
    print("ISOLATED_STDOUT_BEGIN")
    print(cp.stdout[-12000:])
    print("ISOLATED_STDOUT_END")
    if cp.stderr:
        print("ISOLATED_STDERR_BEGIN")
        print(cp.stderr[-8000:])
        print("ISOLATED_STDERR_END")

    if cp.returncode != 0:
        raise SystemExit("V65_83_FAIL=isolated_autoseed_regression")

print("REAL_RUNTIME_MUTATION=NONE")
print("REAL_PROFIT_GOAL_SEEDED=FALSE")
print("REAL_RUNTIME_STARTED=FALSE")

report = {
    "version": "V65.83",
    "timestamp": STAMP,
    "source": str(SRC),
    "source_backup": str(BACKUP),
    "static_checks": static_checks,
    "isolated_regression_passed": True,
    "real_runtime_mutated": False,
}
rp = REPORT_DIR / f"v65_83_idle_profit_autoseed_{STAMP}.json"
rp.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

print("REPORT=", rp)
print("ROLLBACK_SOURCE=", BACKUP)
print("V65_83_PROFIT_AUTOSEED_PATCH=PASS")
print("V65_83_GLOBAL_IDLE_GATE=PASS")
print("V65_83_ANTI_FLOOD_COOLDOWN=PASS")
print("V65_83_ISOLATED_RUNTIME_TEST=PASS")
print("V65_83_COMPLETE")
PY
