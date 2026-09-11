from pathlib import Path
import py_compile

ROOT = Path.home() / "companyos"
watchdog = ROOT / "companyos/runtime/productive_autonomy_watchdog.py"
module = ROOT / "companyos/strategy/profit_first_enrichment_expansion.py"

for p in [watchdog, module]:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")

py_compile.compile(str(watchdog), doraise=True)
py_compile.compile(str(module), doraise=True)

txt = watchdog.read_text(encoding="utf-8")
tick = txt.find("def tick")
hook = txt.find("maybe_run_profit_first_enrichment_expansion(", tick)
if tick < 0 or hook < 0:
    raise SystemExit("VERIFY_FAIL: hook missing from tick()")

from companyos.strategy.profit_first_enrichment_expansion import expansion_goal, enrichment_goal, validation_goal
checks = [
    "AT LEAST" in expansion_goal(),
    "20 materially different candidates" in expansion_goal(),
    "8 unrelated sectors" in expansion_goal(),
    "7 business-model families" in expansion_goal(),
    "never inflate confidence" in enrichment_goal(),
    "Do not auto-build" in validation_goal([]),
]
for i, ok in enumerate(checks, 1):
    print(f"CHECK_{i}:", "PASS" if ok else "FAIL")
if not all(checks):
    raise SystemExit("VERIFY_FAIL: policy contract")

print("PROFIT_FIRST_ENRICHMENT_EXPANSION_VERIFY: PASS")
