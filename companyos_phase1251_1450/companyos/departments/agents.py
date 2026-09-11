from .models import DepartmentResult

class DepartmentAgent:
    name="general"
    def run(self, order, shared):
        return DepartmentResult(self.name, "complete",
            [f"{self.name} assessed: {order.objective}"],
            [{"kind":"internal_analysis","department":self.name}],
            {"confidence":0.75})

class ResearchAgent(DepartmentAgent):
    name="research"
    def run(self, order, shared):
        return DepartmentResult(self.name,"complete",
            ["market evidence mapped","competitors and alternatives queued","customer pain hypotheses ranked"],
            [{"kind":"targeted_research"},{"kind":"customer_interview_plan"}],
            {"confidence":0.82})

class ProductAgent(DepartmentAgent):
    name="product"
    def run(self, order, shared):
        return DepartmentResult(self.name,"complete",
            ["smallest valuable scope defined","acceptance criteria generated"],
            [{"kind":"build_plan"},{"kind":"internal_prototype"}],
            {"confidence":0.84})

class GrowthAgent(DepartmentAgent):
    name="growth"
    def run(self, order, shared):
        return DepartmentResult(self.name,"complete",
            ["channel experiments ranked","pricing experiment prepared"],
            [{"kind":"internal_campaign_plan"},{"kind":"large_marketing_spend","amount":500}],
            {"confidence":0.79})

class SalesAgent(DepartmentAgent):
    name="sales"
    def run(self, order, shared):
        return DepartmentResult(self.name,"complete",
            ["ICP refined","qualification pipeline prepared"],
            [{"kind":"internal_lead_scoring"},{"kind":"contract_signature"}],
            {"confidence":0.81})

class FinanceAgent(DepartmentAgent):
    name="finance"
    def run(self, order, shared):
        return DepartmentResult(self.name,"complete",
            ["unit economics reviewed","runway guard active"],
            [{"kind":"internal_budget_model"},{"kind":"bank_transfer","amount":1000}],
            {"confidence":0.88})

class OperationsAgent(DepartmentAgent):
    name="operations"
    def run(self, order, shared):
        return DepartmentResult(self.name,"complete",
            ["SOP generated","health checks scheduled","rollback path retained"],
            [{"kind":"internal_sop_update"},{"kind":"production_delete"}],
            {"confidence":0.9})

class CustomerSuccessAgent(DepartmentAgent):
    name="customer_success"
    def run(self, order, shared):
        return DepartmentResult(self.name,"complete",
            ["onboarding friction reviewed","retention risks ranked"],
            [{"kind":"internal_onboarding_improvement"}],
            {"confidence":0.83})
