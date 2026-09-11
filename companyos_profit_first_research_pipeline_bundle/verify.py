from pathlib import Path
import py_compile

ROOT = Path.home() / "companyos"
watchdog = ROOT / "companyos/runtime/productive_autonomy_watchdog.py"
pipeline = ROOT / "companyos/strategy/profit_first_research_pipeline.py"

for p in [watchdog, pipeline]:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")

py_compile.compile(str(watchdog), doraise=True)
py_compile.compile(str(pipeline), doraise=True)

txt = watchdog.read_text(encoding="utf-8")
tick = txt.find("def tick")
hook = txt.find("maybe_run_profit_first_research(", tick)
if tick < 0 or hook < 0 or hook - tick > 6000:
    raise SystemExit("VERIFY_FAIL: research hook not inside tick()")

from companyos.strategy.profit_first_research_pipeline import research_goal
g = research_goal()
required = [
    "at least 20 materially different opportunities",
    "at least 8 unrelated sectors",
    "at least 7 business-model families",
    ".companyos_runtime/profit_first_candidates/",
    "evidence_sources",
]
for item in required:
    if item not in g:
        raise SystemExit("VERIFY_FAIL missing contract: " + item)

print("RESEARCH_HOOK_INSIDE_TICK: PASS")
print("STRUCTURED_OUTPUT_CONTRACT: PASS")
print("PROFIT_FIRST_RESEARCH_PIPELINE_VERIFY: PASS")
