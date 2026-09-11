from .system_inventory import SystemInventory
from .integration_validator import IntegrationValidator
from .end_to_end_runner import EndToEndRunner
from .regression_matrix import RegressionMatrix
from .dependency_auditor import DependencyAuditor
from .continuity_checker import ContinuityChecker
from .recovery_validator import RecoveryValidator
from .approval_boundary_validator import ApprovalBoundaryValidator
from .production_readiness import ProductionReadiness
from .single_command_runtime import SingleCommandRuntime
from .final_state import FinalState
from .final_audit import FinalAudit

class FinalIntegrationController:
    def __init__(self,root):
        self.root=root
        self.state=FinalState(root)
        self.audit=FinalAudit(root)

    def run(self, package_root, interfaces=None, available_stages=None, regression_checks=None,
            dependencies=None, checkpoints=None, queues=None, memories=None,
            recovery_scenarios=None, actions=None):
        inventory=SystemInventory().inspect(package_root)
        integrations=IntegrationValidator().validate(interfaces or [])
        e2e=EndToEndRunner().run(available_stages or [])
        regression=RegressionMatrix().evaluate(regression_checks or [])
        deps=DependencyAuditor().inspect(dependencies or [])
        continuity=ContinuityChecker().evaluate(checkpoints,queues,memories)
        recovery=RecoveryValidator().validate(recovery_scenarios or [])
        approvals=ApprovalBoundaryValidator().validate(actions or [])
        readiness=ProductionReadiness().score(inventory,integrations,e2e,regression,continuity,recovery,approvals)
        result={
            "success":True,
            "status":"final_integration_validation_cycle_complete",
            "inventory":inventory,
            "integrations":integrations,
            "end_to_end":e2e,
            "regression":regression,
            "dependency_audit":deps,
            "continuity":continuity,
            "recovery":recovery,
            "approval_boundaries":approvals,
            "production_readiness":readiness,
            "single_command_runtime":SingleCommandRuntime().commands()
        }
        self.state.save(result)
        self.audit.append("final_validation_cycle",result)
        return result
