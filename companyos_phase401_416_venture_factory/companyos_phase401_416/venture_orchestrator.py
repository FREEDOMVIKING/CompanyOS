import hashlib
from .venture_intake import VentureIntake
from .product_brief import ProductBrief
from .mvp_scope import MVPScope
from .architecture_plan import ArchitecturePlan
from .specialist_team import SpecialistTeam
from .task_graph import TaskGraph
from .milestone_planner import MilestonePlanner
from .build_budget import BuildBudget
from .quality_gates import QualityGates
from .release_plan import ReleasePlan
from .kpi_contract import KPIContract

class VentureOrchestrator:
    """414: produce a complete bounded MVP venture packet."""

    def __init__(self):
        self.intake = VentureIntake()

    def prepare(self, thesis, validation):
        gate = self.intake.accept(validation)
        if not gate["accepted"]:
            return {"success":False,"status":"venture_rejected_by_validation_gate","gate":gate}

        brief = ProductBrief().build(thesis)
        venture_id = "venture_" + hashlib.sha256(
            str(brief.get("product_name","venture")).encode()
        ).hexdigest()[:12]

        return {
            "success":True,
            "status":"venture_packet_ready",
            "venture_id":venture_id,
            "gate":gate,
            "brief":brief,
            "mvp_scope":MVPScope().define(brief),
            "architecture":ArchitecturePlan().build(brief),
            "specialist_team":SpecialistTeam().assign(brief),
            "task_graph":TaskGraph().create(),
            "milestones":MilestonePlanner().build(),
            "build_budget":BuildBudget().limits(),
            "quality_gates":QualityGates().gates(),
            "release_plan":ReleasePlan().build(),
            "kpis":KPIContract().build(),
        }
