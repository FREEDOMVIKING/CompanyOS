import tempfile,unittest
from pathlib import Path
from companyos.roadmap_execution_bridge.engine import RoadmapExecutionBridge
from companyos.milestone_generator_v3.engine import MilestoneGeneratorV3
from companyos.specialist_assignment_v3.engine import SpecialistAssignmentV3
from companyos.venture_artifact_pipeline.engine import VentureArtifactPipeline
from companyos.execution_evidence_linker.engine import ExecutionEvidenceLinker
from companyos.progress_sync_v3.engine import ProgressSyncV3
from companyos.venture_validation_engine.engine import VentureValidationEngine
from companyos.launch_readiness_engine.engine import LaunchReadinessEngine
from companyos.dashboard_cluster_manager.engine import DashboardClusterManager
from companyos.execution_recovery_manager.engine import ExecutionRecoveryManager
class T(unittest.TestCase):
    def test_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            h=Path(td)
            self.assertEqual(RoadmapExecutionBridge(h).run()["status"],"linked")
            self.assertEqual(len(MilestoneGeneratorV3(h).run()["milestones"]),5)
            self.assertEqual(len(SpecialistAssignmentV3(h).run()["assignments"]),5)
            self.assertTrue(Path(VentureArtifactPipeline(h).run()["artifact_dir"]).exists())
            self.assertEqual(ExecutionEvidenceLinker(h).run()["evidence_state"],"LINKED")
            self.assertEqual(ProgressSyncV3(h).run()["active"],1)
            self.assertTrue(VentureValidationEngine(h).run()["passed"])
            self.assertIn("ready",LaunchReadinessEngine(h).run())
            self.assertEqual(DashboardClusterManager(h).run()["ports"]["venture_progress"],8767)
            self.assertFalse(ExecutionRecoveryManager(h).run()["recovery_needed"])
if __name__=="__main__":unittest.main()
