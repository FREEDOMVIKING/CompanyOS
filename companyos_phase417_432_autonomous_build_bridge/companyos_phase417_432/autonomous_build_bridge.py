from .venture_build_intake import VentureBuildIntake
from .specialist_dispatcher import SpecialistDispatcher
from .build_cycle import BuildCycle
from .metric_instrumentation import MetricInstrumentation

class AutonomousBuildBridge:
    """427-431: bridge venture factory output into the existing autonomous builder contract."""

    def prepare_build(self, packet):
        gate = VentureBuildIntake().accept(packet)
        if not gate["accepted"]:
            return {"success":False,"status":"build_intake_rejected","gate":gate}

        return {
            "success":True,
            "status":"autonomous_build_packet_ready",
            "venture_id":packet["venture_id"],
            "specialist_jobs":SpecialistDispatcher().dispatch(packet["task_graph"]),
            "build_state":BuildCycle().start(packet),
            "quality_contract":{"required":packet["quality_gates"]},
            "metric_plan":MetricInstrumentation().plan(packet["kpis"]),
            "builder_contract":{
                "mode":"bounded_autonomous_build",
                "workspace_isolation":True,
                "tests_required":True,
                "repair_loop_required":True,
                "commit_only_after_verification":True,
                "external_launch":False,
                "financial_actions":False,
            },
        }
