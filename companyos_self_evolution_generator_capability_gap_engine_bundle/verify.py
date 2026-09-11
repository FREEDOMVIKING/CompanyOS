from pathlib import Path
import py_compile
ROOT=Path.home()/"companyos"
for rel in ["companyos/evolution/self_evolution_generator.py","scripts/companyos_self_evolution_generate_once.py","scripts/companyos_self_evolution_full_cycle.py"]:
 p=ROOT/rel;print(p,"=>","PASS" if p.exists() else "FAIL")
 if not p.exists():raise SystemExit("VERIFY_FAIL")
 py_compile.compile(str(p),doraise=True)
from companyos.evolution.self_evolution_generator import detect_gaps
from companyos.evolution.self_evolution_runtime_integration import run_once
from companyos.evolution.self_evolution_promotion_engine import promote
print("GAP_DETECTION_FUNCTION: PASS")
print("CURRENT_GAPS_DETECTED:",len(detect_gaps()))
print("PROMOTION_PIPELINE_IMPORTS: PASS")
print("SELF_EVOLUTION_GENERATOR_CAPABILITY_GAP_ENGINE_VERIFY: PASS")
