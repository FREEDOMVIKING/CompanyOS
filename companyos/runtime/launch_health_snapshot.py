from __future__ import annotations
import json
from pathlib import Path

def build_snapshot():
    home=Path.home()
    rt=home/".companyos_runtime"
    paths={
      "financial_state": rt/"treasury_live_state.json",
      "ceo_runtime_state": rt/"autonomous_ceo_runtime_service.json",
      "continuous_goal_state": rt/"continuous_goal_runtime_state.json",
      "approval_queue": rt/"approval_queue",
      "opportunities": rt/"opportunities",
      "research_signals": rt/"research_signals",
      "research_evidence": rt/"research_evidence",
    }
    snap={}
    for k,p in paths.items():
        if p.is_dir():
            snap[k]={"present":p.exists(),"count":len(list(p.glob("*.json"))) if p.exists() else 0}
        else:
            snap[k]={"present":p.exists()}
            if p.exists():
                try: snap[k]["data"]=json.loads(p.read_text())
                except Exception: snap[k]["data"]="unreadable"
    return snap
