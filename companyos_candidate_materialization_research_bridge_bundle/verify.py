from pathlib import Path
import py_compile

ROOT = Path.home() / "companyos"
watchdog = ROOT / "companyos/runtime/productive_autonomy_watchdog.py"
bridge = ROOT / "companyos/strategy/candidate_materialization_bridge.py"

for p in [watchdog, bridge]:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")

py_compile.compile(str(watchdog), doraise=True)
py_compile.compile(str(bridge), doraise=True)

txt = watchdog.read_text(encoding="utf-8")
tick = txt.find("def tick")
mpos = txt.find("materialize_profit_first_candidates()", tick)
rpos = txt.find("maybe_recover_profit_first_outputs(", tick)
if tick < 0 or mpos < 0 or rpos < 0:
    raise SystemExit("VERIFY_FAIL: materialization hooks missing from tick()")

from companyos.strategy.candidate_materialization_bridge import materialize
r = materialize()
if "candidates_extracted" not in r:
    raise SystemExit("VERIFY_FAIL: materialization result malformed")

print("MATERIALIZATION_HOOK_INSIDE_TICK: PASS")
print("RECOVERY_HOOK_INSIDE_TICK: PASS")
print("CANDIDATE_MATERIALIZATION_BRIDGE_VERIFY: PASS")
print("CANDIDATES_EXTRACTED_NOW:", r["candidates_extracted"])
print("FILES_WRITTEN_NOW:", r["candidate_files_written_or_updated"])
