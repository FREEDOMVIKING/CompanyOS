from pathlib import Path
import py_compile
ROOT=Path.home()/'companyos'
for rel in ['companyos/evolution/self_evolution_runtime_integration.py','scripts/companyos_self_evolution_runtime_once.py','scripts/companyos_self_evolution_runtime_status.py']:
    p=ROOT/rel; print(p,'=>','PASS' if p.exists() else 'FAIL')
    if not p.exists(): raise SystemExit('VERIFY_FAIL')
    py_compile.compile(str(p),doraise=True)
try:
    from companyos.evolution.self_evolution_promotion_engine import promote
except Exception as exc:
    raise SystemExit(f'VERIFY_FAIL: promotion engine missing: {exc}')
from companyos.evolution.self_evolution_runtime_integration import discover
print('DISCOVERY_FUNCTION: PASS')
print('CURRENT_DISCOVERED_IMPROVEMENTS:',len(discover()))
print('SELF_EVOLUTION_RUNTIME_INTEGRATION_VERIFY: PASS')
