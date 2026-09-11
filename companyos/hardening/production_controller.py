from .health_matrix import HealthMatrix
from .slo_engine import SLOEngine
from .incident_manager import IncidentManager
from .backup_manager import BackupManager
from .integrity_checker import IntegrityChecker
from .config_validator import ConfigValidator
from .secret_reference_audit import SecretReferenceAudit
from .rollback_manager import RollbackManager
from .chaos_probe import ChaosProbe
from .capacity_planner import CapacityPlanner
from .observability import ObservabilitySnapshot
from .release_gate import ReleaseGate
from .hardening_state import HardeningState
from .hardening_audit import HardeningAudit

class ProductionHardeningController:
    def __init__(self,root):
        self.root=root
        self.state=HardeningState(root)
        self.audit=HardeningAudit(root)

    def run(self, components=None, metrics=None, slo_targets=None, incident_signals=None,
            config=None, required_config=None, secret_config=None, release=None,
            integrity_paths=None, chaos_scenarios=None, workload=0, workers=1):
        health=HealthMatrix().evaluate(components or [])
        slos=SLOEngine().evaluate(metrics or {},slo_targets or {})
        incidents=IncidentManager().classify(incident_signals or [])
        backup=BackupManager(self.root).manifest(integrity_paths or [])
        integrity=IntegrityChecker().verify_required(integrity_paths or [])
        config_result=ConfigValidator().validate(config or {},required_config or [])
        secret_result=SecretReferenceAudit().inspect(secret_config or {})
        rollback=RollbackManager().plan(release or {})
        chaos=[ChaosProbe().run(x) for x in (chaos_scenarios or [])]
        capacity=CapacityPlanner().recommend(workload,workers)
        observability=ObservabilitySnapshot().build(health,slos,incidents,capacity)
        gate=ReleaseGate().evaluate(health,slos,config_result,secret_result,rollback)
        result={
            "success":True,
            "status":"production_hardening_observability_cycle_complete",
            "health":health,
            "slos":slos,
            "incidents":incidents,
            "backup_manifest":backup,
            "integrity":integrity,
            "config_validation":config_result,
            "secret_reference_audit":secret_result,
            "rollback_plan":rollback,
            "chaos_probes":chaos,
            "capacity_plan":capacity,
            "observability":observability,
            "release_gate":gate
        }
        self.state.save(result)
        self.audit.append("hardening_cycle",result)
        return result
