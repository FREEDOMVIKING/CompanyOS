from pathlib import Path
import shutil, time, re

ROOT = Path.home() / "companyos"
p = ROOT / "companyos" / "runtime" / "productive_autonomy_watchdog.py"
if not p.exists():
    raise SystemExit("FAIL: productive_autonomy_watchdog.py not found")

backup = p.with_name(p.name + ".bak.profit_first_research." + str(int(time.time())))
shutil.copy2(p, backup)
s = p.read_text(encoding="utf-8")

imp = "from companyos.strategy.profit_first_research_pipeline import maybe_run as maybe_run_profit_first_research"
if imp not in s:
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

hook = """    profit_first_research = maybe_run_profit_first_research(
        cooldown_seconds=int(os.getenv("COMPANYOS_PROFIT_FIRST_RESEARCH_COOLDOWN_SECONDS", "300")),
    )
    if profit_first_research.get("started"):
        log("PROFIT_FIRST_RESEARCH " + json.dumps(profit_first_research, default=str, sort_keys=True))

"""

window = s[m.end():m.end()+5000]
if "maybe_run_profit_first_research(" not in window:
    s = s[:m.end()] + hook + s[m.end():]

p.write_text(s, encoding="utf-8")

patched = p.read_text(encoding="utf-8")
tick = patched.find("def tick")
pos = patched.find("maybe_run_profit_first_research(", tick)
if tick < 0 or pos < 0 or pos - tick > 6000:
    raise SystemExit("FAIL: research hook not inside tick()")

print("BACKUP:", backup)
print("PROFIT_FIRST_RESEARCH_WATCHDOG_PATCH: PASS")
print("RESEARCH_HOOK_INSIDE_TICK: YES")
