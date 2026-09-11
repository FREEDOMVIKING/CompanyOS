from pathlib import Path
from .util import stable_id

BUILTINS = [
    ("research","Research Plugin","3.0",["opportunity_research","evidence_synthesis"]),
    ("product","Product Plugin","3.0",["product_planning","artifact_readiness"]),
    ("marketing","Marketing Plugin","3.0",["campaign_planning","acquisition_analysis"]),
    ("finance","Finance Plugin","3.0",["budget_analysis","revenue_analysis"]),
    ("operations","Operations Plugin","3.0",["workflow_health","bottleneck_analysis"]),
    ("customer","Customer Success Plugin","3.0",["support_analysis","retention_planning"]),
    ("launch","Launch Plugin","3.0",["launch_readiness","handoff_generation"]),
    ("recovery","Recovery Plugin","3.0",["health_checks","local_recovery"]),
]

def register_builtin_plugins(db):
    for pid,name,version,caps in BUILTINS:
        db.upsert_plugin(pid,name,version,"builtin",caps,True,"OK")

def discover_legacy_plugins(home, db):
    p=Path(home)/"plugins"
    if not p.exists(): return 0
    count=0
    for item in p.iterdir():
        if item.name.startswith("."): continue
        db.upsert_plugin(stable_id("legacy-plugin",item.name),item.name,"legacy",str(item),["legacy_adapter"],True,"UNKNOWN")
        count+=1
    return count
