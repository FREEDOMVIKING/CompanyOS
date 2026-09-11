from pathlib import Path
import py_compile

ROOT = Path.home() / "companyos"
watchdog = ROOT / "companyos/runtime/productive_autonomy_watchdog.py"
dispatcher = ROOT / "companyos/runtime/profit_first_dispatcher.py"

for p in [watchdog, dispatcher]:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")

py_compile.compile(str(watchdog), doraise=True)
py_compile.compile(str(dispatcher), doraise=True)

txt = watchdog.read_text(encoding="utf-8")
tick = txt.find("def tick")
hook = txt.find("maybe_dispatch_profit_first(", tick)
if tick < 0 or hook < 0 or hook - tick > 4000:
    raise SystemExit("VERIFY_FAIL: dispatcher hook not inside tick()")

from companyos.strategy.profit_first_venture_engine import discovery_directive
d = discovery_directive()
if "PRIMARY ECONOMIC DIRECTIVE" not in d:
    raise SystemExit("VERIFY_FAIL: profit-first directive missing")

print("DISPATCH_HOOK_INSIDE_TICK: PASS")
print("PROFIT_FIRST_DIRECTIVE_LOAD: PASS")
print("PROFIT_FIRST_DISPATCHER_VERIFY: PASS")
