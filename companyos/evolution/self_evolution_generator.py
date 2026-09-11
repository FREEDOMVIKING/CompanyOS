from __future__ import annotations
import json, os, re, time
from pathlib import Path
ROOT=Path.home()/"companyos"
RUNTIME=ROOT/".companyos_runtime"
GENERATED=RUNTIME/"generated_improvements"
STATE=RUNTIME/"self_evolution_generator_state.json"
SIGNALS=["provider_activation_state_missing","research_output_exists_but_not_materialized","candidate_pool_too_small","sector_diversity_low","business_model_diversity_low","partial_cycle_errors","reasoning_http_error"]
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8",errors="ignore"))
    except:return d
def save(p,o):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,default=str)+"\n",encoding="utf-8")
def collect():
    out=[]
    for p in [RUNTIME/"runtime_health_autorecovery_report.json",RUNTIME/"profit_first_evidence_report.json",RUNTIME/"self_improvement_state.json",RUNTIME/"companyos_full_autonomy.log"]:
        if p.exists():
            try:out.append(p.read_text(encoding="utf-8",errors="ignore")[-40000:])
            except:pass
    return "\n".join(out).lower()
def detect_gaps():
    t=collect();g=[]
    for s in SIGNALS:
        c=t.count(s)
        if c:g.append({"signal":s,"count":c,"priority":min(1.0,.3+c*.05)})
    req=["COMPANYOS_DOMAIN_CHECK_CMD","COMPANYOS_DOMAIN_REGISTER_CMD","COMPANYOS_WEB_DEPLOY_CMD","COMPANYOS_DNS_CONFIG_CMD"]
    missing=[x for x in req if not os.getenv(x,"").strip()]
    if missing:g.append({"signal":"real_launch_provider_configuration","count":len(missing),"priority":.95,"missing":missing})
    return sorted(g,key=lambda x:x["priority"],reverse=True)
def slug(s):return re.sub(r"[^a-z0-9]+","_",s.lower()).strip("_")[:60]
def module_for(gap):
    s=gap["signal"];name="capability_gap_"+slug(s)
    body="from __future__ import annotations\n\ndef capability_gap_report():\n    return "+repr({"status":"capability_gap_report","signal":s,"recommendations":["Inspect evidence for this signal","Add targeted remediation behind tests and rollback protection"]})+"\n"
    return name,body
def generate_one(gap):
    name,body=module_for(gap);stamp=int(time.time());d=GENERATED/f"{name}_{stamp}";d.mkdir(parents=True,exist_ok=True)
    m=d/f"{name}.py";m.write_text(body,encoding="utf-8")
    test_source = f"""from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("{name}.py")
SPEC = importlib.util.spec_from_file_location(
    "generated_candidate_module",
    MODULE_PATH,
)

assert SPEC is not None
assert SPEC.loader is not None

MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

def test_imports():
    report = MODULE.capability_gap_report()
    assert report["signal"]
"""
    t.write_text(test_source, encoding="utf-8")
    meta={"generated_at_unix":time.time(),"gap":gap,"module":str(m),"test":str(t),"status":"generated_for_promotion_pipeline"};save(d/"manifest.json",meta);return meta
def run_once(max_new=3):
    st=load(STATE,{"generated_signals":[]});seen=set(st.get("generated_signals",[]));created=[];gaps=detect_gaps()
    for g in gaps:
        if g["signal"] in seen:continue
        created.append(generate_one(g));seen.add(g["signal"])
        if len(created)>=max_new:break
    result={"ts":time.time(),"gaps_detected":gaps,"new_generated":created,"generated_count":len(created)};st["generated_signals"]=sorted(seen);st["last_run"]=result;save(STATE,st);return result
