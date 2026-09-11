from pathlib import Path
import shutil
import time
import re

p = Path.home() / "companyos" / "companyos" / "runtime" / "productive_autonomy_watchdog.py"
if not p.exists():
    raise SystemExit("FAIL: productive_autonomy_watchdog.py not found")

backup = p.with_name(p.name + ".bak.idle_recovery_v2." + str(int(time.time())))
shutil.copy2(p, backup)
s = p.read_text(encoding="utf-8")

imp = "from companyos.runtime.idle_cycle_recovery_controller import maybe_recover as maybe_recover_idle_cycles"
if imp not in s:
    marker = "from typing import Any"
    if marker in s:
        s = s.replace(marker, marker + "\n" + imp, 1)
    else:
        s = imp + "\n" + s

m = re.search(r'(^def\s+tick\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:\s*\n)', s, flags=re.M)
if not m:
    raise SystemExit("FAIL: annotated watchdog tick() function not found")

injection = (
    '    idle_recovery = maybe_recover_idle_cycles(\n'
    '        min_idle_cycles=int(os.getenv("COMPANYOS_IDLE_RECOVERY_MIN_CYCLES", "25")),\n'
    '        cooldown_seconds=int(os.getenv("COMPANYOS_IDLE_RECOVERY_COOLDOWN_SECONDS", "300")),\n'
    '    )\n'
    '    if idle_recovery.get("started"):\n'
    '        log("IDLE_CYCLE_RECOVERY " + json.dumps(idle_recovery, default=str, sort_keys=True))\n\n'
)

window = s[m.end():m.end()+1600]
if "maybe_recover_idle_cycles(" not in window:
    s = s[:m.end()] + injection + s[m.end():]

p.write_text(s, encoding="utf-8")

patched = p.read_text(encoding="utf-8")
tick_pos = patched.find("def tick")
recovery_pos = patched.find("maybe_recover_idle_cycles(", tick_pos)
if tick_pos < 0 or recovery_pos < 0 or recovery_pos - tick_pos > 2200:
    raise SystemExit("FAIL: recovery hook was not inserted into tick()")

print("BACKUP:", backup)
print("IDLE_CYCLE_RECOVERY_V2_WATCHDOG_PATCH: PASS")
print("ANNOTATED_TICK_SIGNATURE_SUPPORTED: YES")
print("RECOVERY_HOOK_CONFIRMED_INSIDE_TICK: YES")
