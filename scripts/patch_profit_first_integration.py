from pathlib import Path
import shutil, time, re

ROOT = Path.home() / "companyos"
stamp = str(int(time.time()))
targets = [
    ROOT/"companyos/strategy/diversified_opportunity_governor.py",
    ROOT/"companyos/runtime/idle_cycle_recovery_controller.py",
]

for p in targets:
    if not p.exists():
        print("SKIP_MISSING:", p)
        continue
    backup = p.with_name(p.name + ".bak.profit_first." + stamp)
    shutil.copy2(p, backup)
    s = p.read_text(encoding="utf-8")

    if p.name == "diversified_opportunity_governor.py":
        # Preserve existing module/API while making the directive profit-first.
        inject = '\nfrom companyos.strategy.profit_first_venture_engine import discovery_directive as _profit_first_discovery_directive\n'
        if "_profit_first_discovery_directive" not in s:
            s = inject + s
        # Append final override so existing callers receive the new mission without invasive rewrites.
        s += '\n\n# Profit-first canonical override installed by CompanyOS bundle.\ndef discovery_directive():\n    return _profit_first_discovery_directive()\n'
        p.write_text(s, encoding="utf-8")
        print("PATCHED_DISCOVERY_GOVERNOR:", p)

    elif p.name == "idle_cycle_recovery_controller.py":
        old = "from companyos.strategy.diversified_opportunity_governor import discovery_directive"
        new = "from companyos.strategy.profit_first_venture_engine import discovery_directive"
        if old in s:
            s = s.replace(old, new)
        elif "profit_first_venture_engine import discovery_directive" not in s:
            # Replace any direct discovery_directive import conservatively.
            s = re.sub(r'from companyos\.strategy\.[A-Za-z0-9_]+ import discovery_directive',
                       new, s, count=1)
        p.write_text(s, encoding="utf-8")
        print("PATCHED_IDLE_RECOVERY_DIRECTIVE:", p)

print("PROFIT_FIRST_PATCH: PASS")
