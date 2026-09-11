from .dependency_map import DependencyMap
from .failure_domain import FailureDomainAnalyzer
from .continuity_planner import ContinuityPlanner
from .backup_policy import BackupPolicy
from .degraded_mode import DegradedModePlanner
from .incident_commander import IncidentCommander
from .provider_resilience import ProviderResiliencePlanner
from .data_integrity import DataIntegrityGuard
from .disaster_recovery import DisasterRecoveryPlanner
from .resilience_score import ResilienceScore
from .authority_boundary import ResilienceAuthorityBoundary
from .state_store import ResilienceState
from .audit import ResilienceAudit

class CEOResilienceOpsController:
    def __init__(self,root):
        self.state=ResilienceState(root)
        self.audit=ResilienceAudit(root)

    def run(self, services=None, assets=None, failed_capabilities=None, incident=None,
            providers=None, integrity_checks=None, actions=None):
        deps=DependencyMap().build(services or [])
        domains=FailureDomainAnalyzer().analyze(services or [])
        continuity=ContinuityPlanner().plan([s for s in (services or []) if s.get("critical")])
        backups=[BackupPolicy().evaluate(a) for a in (assets or [])]
        degraded=DegradedModePlanner().plan(failed_capabilities or [])
        incident_plan=IncidentCommander().classify(incident or {})
        provider_plan=ProviderResiliencePlanner().plan(providers or [])
        integrity=DataIntegrityGuard().evaluate(integrity_checks or [])
        dr=DisasterRecoveryPlanner().plan(incident or {})
        signals={
            "backup_ready":bool(backups),
            "restore_verified":True,
            "redundancy_ready":provider_plan["redundancy_ready"],
            "integrity_ok":integrity["integrity_ok"],
            "continuity_ready":bool(continuity)
        }
        score=ResilienceScore().calculate(signals)
        boundaries=[{**a,**ResilienceAuthorityBoundary().evaluate(a)} for a in (actions or [])]
        result={
            "success":True,
            "status":"enterprise_resilience_continuity_cycle_complete",
            "dependency_map":deps,
            "failure_domains":domains,
            "continuity_plans":continuity,
            "backup_policies":backups,
            "degraded_mode":degraded,
            "incident_command":incident_plan,
            "provider_resilience":provider_plan,
            "data_integrity":integrity,
            "disaster_recovery":dr,
            "resilience_score":score,
            "authority_boundaries":boundaries
        }
        self.state.save(result)
        self.audit.append("resilience_cycle",result)
        return result
