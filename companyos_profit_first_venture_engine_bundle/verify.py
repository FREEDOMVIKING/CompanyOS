from pathlib import Path
import py_compile, os, subprocess

ROOT=Path.home()/"companyos"
files=[
 ROOT/"companyos/strategy/profit_first_venture_engine.py",
 ROOT/"companyos/strategy/profit_first_opportunity_governor.py",
]
for p in files:
    if not p.exists(): raise SystemExit("FAIL missing "+str(p))
    py_compile.compile(str(p),doraise=True)

from companyos.strategy.profit_first_venture_engine import ensure_policy, discovery_directive
p=ensure_policy()
d=discovery_directive()
checks={
 "business_model_neutral":p.get("business_model_neutral") is True,
 "research_before_build":p.get("research_before_build") is True,
 "no_build_below_threshold":p.get("no_build_below_threshold") is True,
 "portfolio_reallocation":p.get("portfolio_reallocation_enabled") is True,
 "broad_candidate_pool":p.get("minimum_candidates",0)>=20,
 "multi_model":p.get("minimum_business_model_families",0)>=7,
 "profit_language":"expected profit" in d.lower(),
 "no_forced_build":"continue research" in d.lower(),
}
for k,v in checks.items(): print(k, "=>", "PASS" if v else "FAIL")
if not all(checks.values()): raise SystemExit("PROFIT_FIRST_VERIFY_FAIL")

dg=ROOT/"companyos/strategy/diversified_opportunity_governor.py"
if dg.exists():
    txt=dg.read_text(encoding="utf-8")
    if "_profit_first_discovery_directive" not in txt:
        raise SystemExit("FAIL discovery governor not integrated")
    print("DISCOVERY_GOVERNOR_INTEGRATION: PASS")

idle=ROOT/"companyos/runtime/idle_cycle_recovery_controller.py"
if idle.exists():
    txt=idle.read_text(encoding="utf-8")
    if "profit_first_venture_engine import discovery_directive" not in txt:
        raise SystemExit("FAIL idle recovery not using profit-first directive")
    print("IDLE_RECOVERY_INTEGRATION: PASS")

print("PROFIT_FIRST_VENTURE_ENGINE_VERIFY: PASS")
