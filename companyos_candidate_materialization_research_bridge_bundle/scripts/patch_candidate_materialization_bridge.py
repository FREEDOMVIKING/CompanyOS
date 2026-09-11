from pathlib import Path
import shutil, time, re

ROOT = Path.home() / "companyos"
p = ROOT / "companyos" / "runtime" / "productive_autonomy_watchdog.py"
if not p.exists():
    raise SystemExit("FAIL: productive_autonomy_watchdog.py not found")

backup = p.with_name(p.name + ".bak.candidate_bridge." + str(int(time.time())))
shutil.copy2(p, backup)
s = p.read_text(encoding="utf-8")

imports = [
    "from companyos.strategy.candidate_materialization_bridge import materialize as materialize_profit_first_candidates",
    "from companyos.strategy.candidate_materialization_bridge import maybe_recover_missing_outputs as maybe_recover_profit_first_outputs",
]

for imp in imports:
    if imp in s:
        continue
    marker = "from typing import Any"
    if marker in s:
        s = s.replace(marker, marker + "\n" + imp, 1)
    else:
        lines = s.splitlines()
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("from __future__ import"):
                insert_at = i + 1
        lines.insert(insert_at, imp)
        s = "\n".join(lines) + "\n"

m = re.search(r'(^def\s+tick\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:\s*\n)', s, flags=re.M)
if not m:
    raise SystemExit("FAIL: watchdog tick() not found")

hook = """    candidate_materialization = materialize_profit_first_candidates()
    if candidate_materialization.get("candidate_files_written_or_updated", 0) > 0:
        log("PROFIT_FIRST_CANDIDATES_MATERIALIZED " + json.dumps(candidate_materialization, default=str, sort_keys=True))

    candidate_recovery = maybe_recover_profit_first_outputs(
        min_expected_candidates=1,
        cooldown_seconds=int(os.getenv("COMPANYOS_CANDIDATE_RECOVERY_COOLDOWN_SECONDS", "300")),
    )
    if candidate_recovery.get("started"):
        log("PROFIT_FIRST_CANDIDATE_RECOVERY " + json.dumps(candidate_recovery, default=str, sort_keys=True))

"""

window = s[m.end():m.end()+8000]
if "materialize_profit_first_candidates()" not in window:
    s = s[:m.end()] + hook + s[m.end():]

p.write_text(s, encoding="utf-8")

patched = p.read_text(encoding="utf-8")
tick = patched.find("def tick")
mpos = patched.find("materialize_profit_first_candidates()", tick)
rpos = patched.find("maybe_recover_profit_first_outputs(", tick)
if tick < 0 or mpos < 0 or rpos < 0 or max(mpos, rpos) - tick > 9000:
    raise SystemExit("FAIL: bridge hooks not inserted inside tick()")

print("BACKUP:", backup)
print("CANDIDATE_MATERIALIZATION_WATCHDOG_PATCH: PASS")
print("MATERIALIZATION_HOOK_INSIDE_TICK: YES")
print("RECOVERY_HOOK_INSIDE_TICK: YES")
