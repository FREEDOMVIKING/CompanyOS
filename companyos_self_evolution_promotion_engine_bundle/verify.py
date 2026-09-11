from pathlib import Path
import py_compile

ROOT = Path.home()/"companyos"
for rel in [
    "companyos/evolution/self_evolution_promotion_engine.py",
    "scripts/companyos_self_evolution_promote.py",
    "scripts/companyos_self_evolution_status.py",
]:
    p = ROOT/rel
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
    py_compile.compile(str(p), doraise=True)

from companyos.evolution.self_evolution_promotion_engine import STAGING, evaluate
STAGING.mkdir(parents=True, exist_ok=True)
probe = STAGING/"verify_probe.py"
probe.write_text("def probe():\n    return True\n", encoding="utf-8")
r = evaluate(probe)
if not r.get("eligible"):
    raise SystemExit("VERIFY_FAIL: sandbox evaluation")
print("SANDBOX_EVALUATION: PASS")
print("SELF_EVOLUTION_PROMOTION_ENGINE_VERIFY: PASS")
