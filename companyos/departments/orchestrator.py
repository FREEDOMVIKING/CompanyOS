import uuid
from dataclasses import asdict
from .models import WorkOrder
from .memory import ExecutiveMemory
from .authority import AuthorityGate
from .agents import ResearchAgent, ProductAgent, GrowthAgent, SalesAgent, FinanceAgent, OperationsAgent, CustomerSuccessAgent

class ExecutiveOrchestrator:
    def __init__(self, memory_root=None):
        agents=[ResearchAgent(),ProductAgent(),GrowthAgent(),SalesAgent(),FinanceAgent(),OperationsAgent(),CustomerSuccessAgent()]
        self.agents={a.name:a for a in agents}
        self.memory=ExecutiveMemory(memory_root)
        self.authority=AuthorityGate()

    def delegate(self, objective, departments=None, context=None):
        departments=departments or list(self.agents)
        run_id="exec_"+uuid.uuid4().hex[:12]
        results=[]; approvals=[]
        shared={"run_id":run_id,"context":context or {},"memory":self.memory.recent(20)}
        for i,name in enumerate(departments):
            if name not in self.agents: continue
            order=WorkOrder(f"{run_id}_{i}",objective,name,context=context or {})
            result=self.agents[name].run(order,shared)
            row=asdict(result)
            checked=[]
            for action in row["actions"]:
                decision=self.authority.evaluate(action)
                checked.append({**action,"authority":decision})
                if decision["requires_approval"]:
                    approvals.append({"department":name,"action":action,"decision":decision})
            row["actions"]=checked
            results.append(row)
            self.memory.remember("department_result",row)
        confidence=round(sum(r["metrics"].get("confidence",0) for r in results)/max(len(results),1),3)
        summary={"success":True,"run_id":run_id,"objective":objective,"departments":results,
                 "executive_confidence":confidence,"approval_queue":approvals,
                 "portfolio_coordination":{"shared_memory":True,"cross_department_context":True,
                    "resource_conflicts_detected":False,"next_action":"continue_autonomous_internal_work"}}
        self.memory.remember("executive_run",summary)
        return summary
