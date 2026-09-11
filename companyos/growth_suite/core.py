import json, os, tempfile
from pathlib import Path

def read_json(path, default):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return default

def write_json(path, data):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(path.parent),prefix=path.name+".")
    try:
        with os.fdopen(fd,"w") as f:
            json.dump(data,f,indent=2,sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

from datetime import datetime, timezone

def research_snapshot(home):
    opportunities=read_json(home/"companyos_runtime"/"opportunity_engine"/"ranking.json",[])
    return {
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "opportunity_count":len(opportunities),
        "top_topics":[x.get("title") for x in opportunities[:5]],
        "status":"active",
    }

def revenue_snapshot(home):
    ventures=read_json(home/"companyos_runtime"/"venture_builder"/"build_history.json",[])
    return {
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "venture_count":len(ventures),
        "projected_revenue":sum(float(x.get("projected_revenue",0) or 0) for x in ventures),
        "status":"active",
    }

def marketing_snapshot(home):
    latest=read_json(home/"companyos_runtime"/"venture_builder"/"latest_build.json",{})
    return {
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "active_campaigns":1 if latest else 0,
        "latest_venture":latest.get("title"),
        "status":"active",
    }

def acquisition_snapshot(home):
    return {
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "lead_pipeline":["prospect","qualified","pilot","customer"],
        "status":"active",
    }

def portfolio_snapshot(home):
    builds=read_json(home/"companyos_runtime"/"venture_builder"/"build_history.json",[])
    return {
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "portfolio_size":len(builds),
        "ventures":builds[-20:],
        "status":"active",
    }

def improvement_snapshot(home):
    return {
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "recommendations":[
            "keep active service tests isolated from historical tests",
            "prioritize configured connectors",
            "advance only ventures with validated evidence",
        ],
        "status":"active",
    }
