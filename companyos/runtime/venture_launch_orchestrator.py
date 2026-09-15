from __future__ import annotations
import html,json,os,re,tempfile
from datetime import datetime,timezone
from pathlib import Path
from companyos.connectors.hosting_router import HostingRouter
def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p,d=None):
    try:return json.loads(Path(p).read_text())
    except:return {} if d is None else d
def write_json(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(p.parent),prefix=p.name+".")
    try:
        with os.fdopen(fd,"w") as f:
            json.dump(data,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def slugify(s): return (re.sub(r"[^a-z0-9]+","-",str(s).lower()).strip("-")[:54] or "venture")
def esc(v): return html.escape(str(v or ""))
class VentureLaunchOrchestrator:
    ALLOWED={"execution_qualified","launch_ready","approved","ready_to_launch"}
    def __init__(self,root):
        self.root=Path(root);self.rt=self.root/".companyos_runtime";self.sites=self.root/"generated_sites";self.sites.mkdir(parents=True,exist_ok=True)
    def _qualified(self,o):
        if o.get("blocked") is True:return False,"blocked"
        if o.get("requires_manual_approval") and not o.get("manual_approval_granted"):return False,"manual_approval_required"
        state=str(o.get("qualification_state") or o.get("status") or "").lower()
        good=bool(o.get("execution_qualified") or o.get("launch_ready") or state in self.ALLOWED)
        return (True,"qualified") if good else (False,"not_execution_qualified")
    def _site(self,o):
        title=o.get("business_name") or o.get("title") or o.get("name") or "CompanyOS Venture"
        offer=o.get("offer") or o.get("value_proposition") or o.get("summary") or "A focused solution built around a validated market need."
        audience=o.get("target_customer") or o.get("audience") or "customers who need this solution"
        cta=o.get("cta") or "Get Started"; contact=o.get("public_contact") or o.get("contact") or ""
        slug=slugify(title);d=self.sites/slug;d.mkdir(parents=True,exist_ok=True)
        contact_html='<p class="contact">'+esc(contact)+'</p>' if contact else ""
        page="<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>"+esc(title)+"</title><meta name='description' content='"+esc(offer)[:155]+"'><style>body{font-family:system-ui,sans-serif;margin:0;background:#0b1020;color:#f7f8fb}main{max-width:900px;margin:auto;padding:72px 24px}.tag{opacity:.72}h1{font-size:clamp(42px,8vw,78px);line-height:1;margin:.2em 0}p{font-size:20px;line-height:1.6;max-width:720px}.card{margin-top:36px;padding:28px;border:1px solid #39415b;border-radius:18px;background:#121a30}a.cta{display:inline-block;margin-top:20px;padding:14px 22px;border-radius:12px;background:white;color:#111;text-decoration:none;font-weight:700}footer{margin-top:70px;opacity:.6}</style></head><body><main><div class='tag'>For "+esc(audience)+"</div><h1>"+esc(title)+"</h1><p>"+esc(offer)+"</p><div class='card'><h2>"+esc(cta)+"</h2><p>Connect with us to discuss the next step.</p>"+contact_html+"<a class='cta' href='#contact'>"+esc(cta)+"</a></div><footer id='contact'>Powered by CompanyOS</footer></main></body></html>"
        (d/"index.html").write_text(page);return title,slug,d
    def launch(self,o):
        ok,reason=self._qualified(o)
        if not ok:
            r={"timestamp":now(),"status":"not_launched","reason":reason,"opportunity_id":o.get("id") or o.get("opportunity_id")};write_json(self.rt/"venture_launch_latest.json",r);return r
        hosting=HostingRouter().health()
        if not hosting.get("healthy"):
            r={"timestamp":now(),"status":"not_launched","reason":"hosting_not_ready","hosting":hosting};write_json(self.rt/"venture_launch_latest.json",r);return r
        title,slug,d=self._site(o)
        project=os.getenv("COMPANYOS_CLOUDFLARE_PROJECT","companyos-commissioning").strip() or "companyos-commissioning"
        receipt=HostingRouter().deploy_directory(project,str(d),"main")
        r={"timestamp":now(),"status":"launched","opportunity_id":o.get("id") or o.get("opportunity_id"),"title":title,"slug":slug,"site_dir":str(d),"public_url":receipt.get("url"),"deployment":receipt,"next_action":"measure_market_response"}
        write_json(self.rt/"venture_launch_latest.json",r)
        with (self.rt/"venture_launch_ledger.jsonl").open("a") as f:f.write(json.dumps(r,sort_keys=True)+"\n")
        feedback={"timestamp":now(),"kind":"venture_launch","opportunity_id":r["opportunity_id"],"public_url":r["public_url"],"deployment_id":receipt.get("deployment_id"),"outcome_state":"awaiting_market_evidence","next_action":"measure_market_response"}
        write_json(self.rt/"venture_launch_feedback.json",feedback)
        with (self.rt/"outcome_evidence_queue.jsonl").open("a") as f:f.write(json.dumps(feedback,sort_keys=True)+"\n")
        return r
    def launch_latest(self):
        candidates=[self.rt/"profit_opportunity_engine"/"selected.json",self.root/"companyos_runtime"/"profit_opportunity_engine"/"selected.json",self.rt/"selected_profit_opportunity.json",self.root/"companyos_runtime"/"venture_builder"/"latest_build.json"]
        for p in candidates:
            if p.exists():
                o=read_json(p,{})
                if isinstance(o,dict) and o:return self.launch(o)
        r={"timestamp":now(),"status":"not_launched","reason":"no_opportunity_artifact"};write_json(self.rt/"venture_launch_latest.json",r);return r
