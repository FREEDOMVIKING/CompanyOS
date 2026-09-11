import html
import json
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from .storage import read_json, write_json, append_json

def slugify(value):
    out="".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    while "--" in out:out=out.replace("--","-")
    return out.strip("-") or "venture"

def product_spec(opportunity):
    plan=opportunity.get("business_plan",{})
    product=plan.get("recommended_product") or {}
    title=opportunity.get("title","New Venture")
    customer=plan.get("customer") or "target customers"
    problem=plan.get("problem") or "a recurring customer problem"
    return {
        "name":product.get("name",title+" Product"),
        "venture_title":title,
        "customer":customer,
        "problem":problem,
        "product_type":product.get("type","software_service"),
        "value_proposition":f"Help {customer} solve {problem} faster with less manual work.",
        "mvp_features":product.get("mvp",["intake","automation","reporting"]),
        "success_metrics":["10 qualified leads","3 paying customers","positive contribution margin","onboarding under 30 minutes"],
        "constraints":{"external_actions":"connector_controlled","financial_commitments":"approval_aware","legal_documents":"draft_only"},
    }

def architecture_spec(spec):
    return {
        "frontend":"responsive web application / PWA",
        "backend":"Python service layer",
        "database":"SQLite MVP with PostgreSQL-ready interface",
        "api":"REST JSON",
        "auth":"provider-ready email account model",
        "security":["environment secrets","input validation","least privilege","redacted logs"],
        "modules":["accounts","onboarding","core_workflow","billing_interface","analytics","admin"],
    }

def website(spec,pricing,out):
    name=html.escape(spec["name"]);customer=html.escape(spec["customer"])
    features="".join("<li>"+html.escape(str(x))+"</li>" for x in spec["mvp_features"])
    tiers="".join("<div class='tier'><h3>"+k.title()+"</h3><strong>$"+str(v)+"</strong></div>" for k,v in pricing.items() if k in {"entry","core","premium"})
    page="""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{}</title><style>body{{font-family:system-ui;background:#0d1117;color:#e6edf3;margin:0}}main{{max-width:960px;margin:auto;padding:28px}}
.card,.tier{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}.pricing{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}}
a{{display:inline-block;background:#238636;color:white;padding:12px 16px;border-radius:9px;text-decoration:none}}</style></head>
<body><main><h1>{}</h1><p>Built for {}</p><p>{}</p><a href="#pilot">Request a pilot</a>
<div class="card"><h2>MVP</h2><ul>{}</ul></div><h2>Pricing hypothesis</h2><div class="pricing">{}</div>
<div class="card" id="pilot"><h2>Early access</h2><p>Join the validation pilot.</p></div></main></body></html>""".format(
        name,name,customer,html.escape(spec["value_proposition"]),features,tiers
    )
    p=Path(out)/"website"/"index.html";p.parent.mkdir(parents=True,exist_ok=True);p.write_text(page)
    return str(p)

def make_scaffolds(spec,architecture,out):
    saas=Path(out)/"saas_app";saas.mkdir(parents=True,exist_ok=True)
    (saas/"README.md").write_text("# "+spec["name"]+"\n\nGenerated CompanyOS SaaS MVP.\n")
    (saas/"requirements.txt").write_text("flask>=3.0\n")
    app_code = (
        "from flask import Flask, jsonify, request\n"
        "app=Flask(__name__)\n"
        "@app.get('/health')\n"
        "def health(): return jsonify({'ok':True})\n"
        "@app.post('/api/intake')\n"
        "def intake(): return jsonify({'received':True,'payload':request.get_json(silent=True) or {}})\n"
        "if __name__=='__main__': app.run(host='127.0.0.1',port=5050)\n"
    )
    (saas/"app.py").write_text(app_code)
    write_json(saas/"architecture.json",architecture)
    pwa=Path(out)/"mobile_pwa";pwa.mkdir(parents=True,exist_ok=True)
    (pwa/"index.html").write_text("<!doctype html><meta name='viewport' content='width=device-width,initial-scale=1'><h1>"+html.escape(spec["name"])+"</h1><p>Mobile PWA scaffold</p>")
    (pwa/"app.js").write_text("console.log('CompanyOS PWA');\n")
    write_json(pwa/"manifest.json",{"name":spec["name"],"short_name":spec["name"][:12],"start_url":".","display":"standalone"})
    return {"saas":str(saas),"mobile_pwa":str(pwa)}

def content_calendar(name):
    topics=["problem education","cost of status quo","workflow demo","FAQ","pilot invitation","industry insight","case-study template"]
    start=date.today()
    return [{"date":str(start+timedelta(days=i*4)),"topic":topics[i%len(topics)],"venture":name,"status":"planned"} for i in range(7)]

class VentureBuilderEngine:
    def __init__(self,home=None):
        self.home=Path(home or os.environ.get("COMPANYOS_HOME",str(Path.home()/"companyos")))
        self.runtime=self.home/"companyos_runtime"/"venture_builder"
        self.output=self.home/"generated_ventures"
        self.runtime.mkdir(parents=True,exist_ok=True);self.output.mkdir(parents=True,exist_ok=True)

    def ranking(self):
        return read_json(self.home/"companyos_runtime"/"opportunity_engine"/"ranking.json",[])

    def build_top(self):
        rows=self.ranking()
        if not rows:raise RuntimeError("No ranked opportunities found. Run Opportunity Engine first.")
        return self.build(rows[0])

    def build_by_id(self,oid):
        for row in self.ranking():
            if row.get("opportunity_id")==oid:return self.build(row)
        raise KeyError("Opportunity not found: "+oid)

    def build(self,opp):
        build_id=str(uuid.uuid4());title=opp.get("title","New Venture")
        package=self.output/(slugify(title)+"-"+build_id[:8]);package.mkdir(parents=True,exist_ok=True)
        spec=product_spec(opp);arch=architecture_spec(spec)
        pricing=opp.get("pricing") or {"entry":49,"core":99,"premium":199}
        forecast=opp.get("forecast") or {}
        landing=website(spec,pricing,package)
        scaffolds=make_scaffolds(spec,arch,package)
        onboarding={"steps":["account creation","business profile","first workflow","success checkpoint"],"target_minutes":30}
        billing={"currency":"USD","plans":[{"id":k,"price":pricing.get(k),"interval":"month"} for k in ["entry","core","premium"]],"provider":"unconfigured","activation":"connector_and_approval_required"}
        kpis={"acquisition":["qualified_leads","conversion_rate","cac"],"activation":["onboarding_completion","time_to_value"],"revenue":["mrr","arr","gross_margin"],"retention":["retention","churn"],"operations":["delivery_time","automation_rate"]}
        revenue={"baseline":forecast,"conservative":{"monthly_revenue":round(forecast.get("monthly_revenue",0)*0.6,2)},"upside":{"monthly_revenue":round(forecast.get("monthly_revenue",0)*1.6,2)}}
        campaign={"goal":"book qualified pilot calls","audience":spec["customer"],"channels":["direct outreach","content","partnerships","search"],"status":"draft"}
        outreach={"steps":[{"day":0,"purpose":"introduction"},{"day":3,"purpose":"value example"},{"day":7,"purpose":"pilot invitation"},{"day":14,"purpose":"close loop"}],"execution":"connector_policy_controlled"}
        email={"messages":[{"subject":"A faster way to handle "+spec["problem"]},{"subject":"Reduce manual work"},{"subject":"Join the pilot"}],"bulk_send":"consent_and_policy_required"}
        crm=[{"operation":"create_pipeline","name":spec["name"]+" Sales"},{"operation":"create_stage","name":"Qualified"},{"operation":"create_stage","name":"Pilot"},{"operation":"create_stage","name":"Customer"}]
        vendors={"categories":["hosting","domain","email","payments"],"criteria":["reliability","cost","security","API access"],"commitments":"approval_required"}
        proposal={"title":spec["name"]+" Pilot Proposal","customer":spec["customer"],"solution":spec["value_proposition"],"scope":spec["mvp_features"],"pilot_price":pricing.get("entry"),"status":"draft"}
        contract={"title":spec["name"]+" Service Agreement Draft","sections":["parties","scope","fees","confidentiality","data handling","limitations","termination"],"legal_status":"qualified_review_required"}
        checklist=[{"item":x,"status":"pending","required":True} for x in ["problem validated","pricing tested","MVP tests passed","privacy and terms reviewed","support ready","analytics configured","deployment connector configured","launch approval recorded"]]
        deployment={"artifact":str(package),"stages":["validate","test","security_review","package","deploy_staging","verify","deploy_production"],"production":"approval_required","rollback":"restore previous artifact"}
        optimization={"cadence":"weekly","inputs":["traffic","conversion","activation","retention","revenue","support"],"rules":["improve weakest funnel stage","stop negative channels","prioritize repeatable outcomes","preserve audit trail"]}
        manifest={"phase":"25001-27000","build_id":build_id,"generated_at":datetime.now(timezone.utc).isoformat(),"source_opportunity_id":opp.get("opportunity_id"),"title":title,"package_dir":str(package),"status":"launch_package_generated","components":{"product_spec":spec,"architecture":arch,"landing_page":landing,"scaffolds":scaffolds,"onboarding":onboarding,"billing":billing,"kpis":kpis,"revenue":revenue,"marketing_campaign":campaign,"content_calendar":content_calendar(spec["name"]),"outreach":outreach,"email_campaign":email,"crm_jobs":crm,"vendors":vendors,"proposal":proposal,"contract":contract,"launch_checklist":checklist,"deployment":deployment,"optimization":optimization}}
        write_json(package/"venture_manifest.json",manifest)
        for filename,data in {
            "product_spec.json":spec,"architecture.json":arch,"business_plan.json":opp.get("business_plan",{}),
            "commercial_plan.json":{"billing":billing,"revenue":revenue,"proposal":proposal,"contract":contract},
            "marketing_plan.json":{"campaign":campaign,"calendar":manifest["components"]["content_calendar"],"outreach":outreach,"email":email},
            "operations_plan.json":{"onboarding":onboarding,"crm":crm,"vendors":vendors,"kpis":kpis},
            "launch_checklist.json":checklist,"deployment_plan.json":deployment
        }.items():write_json(package/filename,data)
        event={"build_id":build_id,"opportunity_id":opp.get("opportunity_id"),"title":title,"package_dir":str(package),"status":manifest["status"],"generated_at":manifest["generated_at"]}
        append_json(self.runtime/"build_history.json",event);write_json(self.runtime/"latest_build.json",manifest)
        return manifest

    def list_builds(self):return read_json(self.runtime/"build_history.json",[])
    def health(self):
        rows=self.list_builds()
        return {"phase":"25001-27000","generated_at":datetime.now(timezone.utc).isoformat(),"build_count":len(rows),"latest_build":rows[-1] if rows else None,"output_root":str(self.output)}
