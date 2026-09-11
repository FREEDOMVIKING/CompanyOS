from pathlib import Path
import shutil, time, re

p = Path.home() / "companyos" / "companyos" / "runtime" / "productive_autonomy_watchdog.py"
if not p.exists():
    raise SystemExit("FAIL: productive_autonomy_watchdog.py not found")

backup = p.with_name(p.name + ".bak.idle_recovery." + str(int(time.time())))
shutil.copy2(p, backup)
s = p.read_text(encoding="utf-8")

imp = "from companyos.runtime.idle_cycle_recovery_controller import maybe_recover as maybe_recover_idle_cycles"
if imp not in s:
    if "from typing import Any" in s:
        s = s.replace("from typing import Any", "from typing import Any\\n" + imp, 1)
    else:
        s = imp + "\\n" + s

m = re.search(r"(^def tick\\([^)]*\\):\\s*\\n)", s, flags=re.M)
if not m:
    raise SystemExit("FAIL: watchdog tick() function not found")

injection = (
    '    idle_recovery = maybe_recover_idle_cycles(\\n'
    '        min_idle_cycles=int(os.getenv("COMPANYOS_IDLE_RECOVERY_MIN_CYCLES", "25")),\\n'
    '        cooldown_seconds=int(os.getenv("COMPANYOS_IDLE_RECOVERY_COOLDOWN_SECONDS", "300")),\\n'
    '    )\\n'
    '    if idle_recovery.get("started"):\\n'
    '        log("IDLE_CYCLE_RECOVERY " + json.dumps(idle_recovery, default=str, sort_keys=True))\\n\\n'
)

window = s[m.end():m.end()+1200]
if "maybe_recover_idle_cycles(" not in window:
    s = s[:m.end()] + injection + s[m.end():]

p.write_text(s, encoding="utf-8")
print("BACKUP:", backup)
print("IDLE_CYCLE_RECOVERY_WATCHDOG_PATCH: PASS")
print("DEFAULT_MIN_IDLE_CYCLES: 25")
print("DEFAULT_COOLDOWN_SECONDS: 300")
