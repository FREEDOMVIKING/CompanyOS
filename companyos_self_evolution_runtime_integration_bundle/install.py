from pathlib import Path
import shutil, os, time
ROOT=Path.home()/'companyos'; SRC=Path(__file__).resolve().parent; stamp=str(int(time.time()))
for rel in ['companyos/evolution/self_evolution_runtime_integration.py','scripts/companyos_self_evolution_runtime_once.py','scripts/companyos_self_evolution_runtime_status.py','scripts/companyos_self_evolution_runtime.sh']:
    s=SRC/rel; d=ROOT/rel; d.parent.mkdir(parents=True,exist_ok=True)
    if d.exists(): shutil.copy2(d,d.with_name(d.name+'.bak.'+stamp))
    shutil.copy2(s,d); print('INSTALLED:',d)
os.chmod(ROOT/'scripts/companyos_self_evolution_runtime.sh',0o755)
print('SELF_EVOLUTION_RUNTIME_INTEGRATION_INSTALL: PASS')
print('AUTO_DISCOVERY_OF_GENERATED_IMPROVEMENTS: ENABLED')
print('AUTO_SANDBOX_EVALUATION: ENABLED')
print('AUTO_SAFE_PROMOTION_TO_EXTENSION_NAMESPACE: ENABLED')
print('AUTO_ROLLBACK_INHERITED: ENABLED')
print('RUNTIME_LEDGER: ENABLED')
print('CORE_OVERWRITE_BY_DEFAULT: NO')
