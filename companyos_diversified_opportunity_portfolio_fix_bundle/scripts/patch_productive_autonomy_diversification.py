from pathlib import Path
import shutil,time

p=Path.home()/"companyos"/"companyos"/"runtime"/"productive_autonomy_watchdog.py"
if not p.exists():
    raise SystemExit("FAIL: productive_autonomy_watchdog.py not found")

backup=p.with_name(p.name+".bak.diversification."+str(int(time.time())))
shutil.copy2(p,backup)
s=p.read_text(encoding="utf-8")

imp="from companyos.strategy.diversified_opportunity_governor import discovery_directive, should_force_diversified_discovery"
if imp not in s:
    marker="from typing import Any"
    if marker in s:
        s=s.replace(marker,marker+"\n"+imp,1)
    else:
        s=imp+"\n"+s

needle='def start_internal_goal(goal: str) -> str:'
idx=s.find(needle)
if idx<0:
    raise SystemExit("FAIL: start_internal_goal not found")

body_start=idx+len(needle)
insert='''\n    if should_force_diversified_discovery():\n        goal = discovery_directive()\n'''
if "should_force_diversified_discovery()" not in s[body_start:body_start+500]:
    s=s[:body_start]+insert+s[body_start:]

p.write_text(s,encoding="utf-8")
print("BACKUP:",backup)
print("DIVERSIFIED_OPPORTUNITY_WATCHDOG_PATCH: PASS")
