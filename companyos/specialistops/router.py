from .research_specialist import ResearchSpecialist
from .finance_specialist import FinanceSpecialist
from .product_specialist import ProductSpecialist
from .growth_specialist import GrowthSpecialist
from .operations_specialist import OperationsSpecialist
from .customer_success_specialist import CustomerSuccessSpecialist

class SpecialistCapabilityRouter:
    MAP = {
        "research": ResearchSpecialist,
        "finance": FinanceSpecialist,
        "product": ProductSpecialist,
        "growth": GrowthSpecialist,
        "operations": OperationsSpecialist,
        "customer_success": CustomerSuccessSpecialist,
    }

    def __init__(self, root):
        self.root = root

    def supports(self, department):
        return department in self.MAP

    def execute(self, job, department):
        cls = self.MAP.get(department)
        if not cls:
            return {"success":False, "error":"unsupported_specialist_department", "department":department}
        return cls(self.root).execute(job)
