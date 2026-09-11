from .pipeline_graph import PipelineGraph
from .quality_gate import CIQualityGate
from .security_gate import SecurityGate
from .artifact_builder import ArtifactBuilder
from .release_manifest import ReleaseManifest
from .staging_validator import StagingValidator
from .deployment_gate import DeploymentGate
from .postdeploy_verifier import PostDeployVerifier
from .rollback_policy import RollbackPolicy
from .release_ledger import ReleaseLedger
from .pipeline_state import PipelineState
from .pipeline_audit import PipelineAudit

class CEOCICDController:
    def __init__(self, root):
        self.root = root
        self.state = PipelineState(root)
        self.audit = PipelineAudit(root)
        self.ledger = ReleaseLedger(root)

    def run(self, version, source_digest, checks, scans, smoke_tests=True, staging_health=True,
            production_approval=False, deploy_success=True, postdeploy_health=True):
        graph = PipelineGraph().build()
        quality = CIQualityGate().evaluate(checks or {})
        security = SecurityGate().evaluate(scans or {})
        artifact = ArtifactBuilder().build(version, source_digest, {"pipeline": "companyos"})
        manifest = ReleaseManifest().create(artifact, quality, security)
        staging = StagingValidator().validate(smoke_tests, staging_health)
        gate = DeploymentGate().evaluate(manifest, staging, approval=production_approval)

        deploy = {
            "attempted": gate["production_deploy_allowed"],
            "success": bool(deploy_success) if gate["production_deploy_allowed"] else False,
            "blocked_reason": None if gate["production_deploy_allowed"] else "approval_or_precondition_gate"
        }

        postdeploy = PostDeployVerifier().verify(
            smoke_ok=deploy["success"],
            health_ok=postdeploy_health if deploy["success"] else False
        )
        rollback = RollbackPolicy().evaluate(deploy, postdeploy)

        result = {
            "success": True,
            "status": "autonomous_cicd_release_engineering_cycle_complete",
            "pipeline_graph": graph,
            "quality_gate": quality,
            "security_gate": security,
            "artifact": artifact,
            "release_manifest": manifest,
            "staging_validation": staging,
            "deployment_gate": gate,
            "production_deploy": deploy,
            "postdeploy_verification": postdeploy,
            "rollback_policy": rollback
        }

        # Persist the completed pipeline result before attaching the
        # ledger receipt. This prevents the receipt from recursively
        # containing the result that contains the receipt.
        self.state.save(result)
        self.audit.append("cicd_cycle", result)

        release_record = self.ledger.append(result)
        result["release_record"] = {
            "timestamp": release_record["timestamp"],
            "digest": release_record["digest"]
        }
        return result
