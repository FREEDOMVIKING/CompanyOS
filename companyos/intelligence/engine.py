from pathlib import Path
from datetime import datetime, timezone
import os

from .storage import read_json, write_json
from .portfolio import portfolio_health, rank_opportunities, allocate_shared_resources
from .council import executive_council
from .strategy import strategic_plan
from .learning import derive_playbooks, learning_summary

class ExecutiveIntelligenceEngine:
    def __init__(self,home=None):
        self.home=Path(home or os.environ.get("COMPANYOS_HOME",str(Path.home()/"companyos")))
        self.ops=self.home/"companyos_runtime"/"opscenter"
        self.orch=self.home/"companyos_runtime"/"orchestrator"
        self.runtime=self.home/"companyos_runtime"/"intelligence"
        self.runtime.mkdir(parents=True,exist_ok=True)

    def run_cycle(self):
        ops=read_json(self.ops/"latest_ops_snapshot.json",{})
        orch=read_json(self.orch/"latest_orchestration.json",{})
        ventures=ops.get("ventures",[])
        bottlenecks=ops.get("bottlenecks",[])
        events=ops.get("events",[])
        decisions=ops.get("executive",{}).get("decisions",[]) or ops.get("tasks",[])
        finance={
            "deployable":ops.get("capital",{}).get("deployable",0),
            "reserve":ops.get("capital",{}).get("reserve",0),
        }

        portfolio=portfolio_health(ventures)
        opportunities=rank_opportunities(ventures)
        council=executive_council(ventures,bottlenecks,finance)
        strategy=strategic_plan(opportunities,council,portfolio)
        allocations=allocate_shared_resources(ventures)
        playbooks=derive_playbooks(events,decisions)

        result={
            "phase":"19001-19500",
            "generated_at":datetime.now(timezone.utc).isoformat(),
            "portfolio":portfolio,
            "opportunities":opportunities,
            "executive_council":council,
            "strategy":strategy,
            "resource_arbitration":allocations,
            "playbooks":playbooks,
            "learning":learning_summary(playbooks,events),
            "orchestration_summary":orch.get("summary",{}),
        }
        write_json(self.runtime/"latest_intelligence.json",result)
        history=read_json(self.runtime/"intelligence_history.json",[])
        history.append({
            "generated_at":result["generated_at"],
            "portfolio_score":portfolio["score"],
            "opportunity_count":len(opportunities),
            "playbook_count":len(playbooks),
        })
        write_json(self.runtime/"intelligence_history.json",history[-1000:])
        return result
