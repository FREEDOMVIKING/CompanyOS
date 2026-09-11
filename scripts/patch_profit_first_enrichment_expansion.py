from pathlib import Path
import shutil, time, re

ROOT = Path.home() / "companyos"
p = ROOT / "companyos" / "runtime" / "productive_autonomy_watchdog.py"
if not p.exists():
    raise SystemExit("FAIL: productive_autonomy_watchdog.py not found")

backup = p.with_name(p.name + ".bak.enrichment_expansion." + str(int(time.time())))
shutil.copy2(p, backup)
s = p.read_text(encoding="utf-8")

imp = "from companyos.strategy.profit_first_enrichment_expansion import maybe_run as maybe_run_profit_first_enrichment_expansion"
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

hook = """    profit_first_enrichment_expansion = maybe_run_profit_first_enrichment_expansion(
        cooldown_seconds=int(os.getenv("COMPANYOS_PROFIT_FIRST_ENRICHMENT_COOLDOWN_SECONDS", "300")),
    )
    if profit_first_enrichment_expansion.get("started"):
        log("PROFIT_FIRST_ENRICHMENT_EXPANSION " + json.dumps(profit_first_enrichment_expansion, default=str, sort_keys=True))

"""

window = s[m.end():m.end()+12000]
if "maybe_run_profit_first_enrichment_expansion(" not in window:
    s = s[:m.end()] + hook + s[m.end():]

p.write_text(s, encoding="utf-8")

patched = p.read_text(encoding="utf-8")
tick = patched.find("def tick")
hook_pos = patched.find("maybe_run_profit_first_enrichment_expansion(", tick)
if tick < 0 or hook_pos < 0 or hook_pos - tick > 13000:
    raise SystemExit("FAIL: enrichment/expansion hook not inside tick()")

print("BACKUP:", backup)
print("PROFIT_FIRST_ENRICHMENT_EXPANSION_WATCHDOG_PATCH: PASS")
print("HOOK_INSIDE_TICK: YES")
