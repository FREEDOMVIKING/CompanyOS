from pathlib import Path
import shutil, time, re

ROOT = Path.home() / "companyos"
p = ROOT / "companyos" / "runtime" / "productive_autonomy_watchdog.py"
if not p.exists():
    raise SystemExit("FAIL: productive_autonomy_watchdog.py not found")

backup = p.with_name(p.name + ".bak.profit_first_dispatcher." + str(int(time.time())))
shutil.copy2(p, backup)
s = p.read_text(encoding="utf-8")

imp = "from companyos.runtime.profit_first_dispatcher import maybe_dispatch as maybe_dispatch_profit_first"
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

hook = """    profit_first_dispatch = maybe_dispatch_profit_first(
        min_idle_cycles=int(os.getenv("COMPANYOS_PROFIT_FIRST_DISPATCH_MIN_IDLE_CYCLES", "20")),
        cooldown_seconds=int(os.getenv("COMPANYOS_PROFIT_FIRST_DISPATCH_COOLDOWN_SECONDS", "300")),
    )
    if profit_first_dispatch.get("started"):
        log("PROFIT_FIRST_DISPATCH " + json.dumps(profit_first_dispatch, default=str, sort_keys=True))

"""

window = s[m.end():m.end()+3000]
if "maybe_dispatch_profit_first(" not in window:
    s = s[:m.end()] + hook + s[m.end():]

p.write_text(s, encoding="utf-8")

patched = p.read_text(encoding="utf-8")
tick_pos = patched.find("def tick")
hook_pos = patched.find("maybe_dispatch_profit_first(", tick_pos)
if tick_pos < 0 or hook_pos < 0 or hook_pos - tick_pos > 4000:
    raise SystemExit("FAIL: dispatcher hook not inserted into tick()")

print("BACKUP:", backup)
print("PROFIT_FIRST_DISPATCHER_WATCHDOG_PATCH: PASS")
print("DISPATCH_HOOK_INSIDE_TICK: YES")
