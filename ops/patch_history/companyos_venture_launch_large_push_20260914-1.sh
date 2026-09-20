#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
set -a; . "$HOME/.companyos_launch_env"; set +a
echo "===== COMPANYOS VENTURE LAUNCH LARGE PUSH ====="
echo "No supervisor restart. No finance action. No DNS mutation."
mkdir -p companyos/runtime scripts tests/generated

cat > companyos/runtime/venture_launch_orchestrator.py <<'PY'
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
PY

cat > scripts/companyos_launchventure <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import argparse,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
env=Path.home()/".companyos_launch_env"
if env.exists():
    for raw in env.read_text().splitlines():
        raw=raw.strip()
        if raw.startswith("export ") and "=" in raw:
            k,v=raw[7:].split("=",1);os.environ.setdefault(k.strip(),v.strip().strip("'").strip('"'))
from companyos.runtime.venture_launch_orchestrator import VentureLaunchOrchestrator
p=argparse.ArgumentParser();p.add_argument("--file");a=p.parse_args();v=VentureLaunchOrchestrator(ROOT)
r=v.launch(json.loads(Path(a.file).read_text())) if a.file else v.launch_latest()
print(json.dumps(r,indent=2,sort_keys=True))
PY
chmod +x scripts/companyos_launchventure

cat > scripts/companyos_venturestatus <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import json
from pathlib import Path
r=Path.cwd()/".companyos_runtime"
def load(p):
    try:return json.loads(p.read_text())
    except:return None
print(json.dumps({"launch":load(r/"venture_launch_latest.json"),"feedback":load(r/"venture_launch_feedback.json"),"deployment":load(r/"latest_deployment.json")},indent=2,sort_keys=True))
PY
chmod +x scripts/companyos_venturestatus

cat > tests/generated/test_venture_launch_orchestrator.py <<'PY'
from companyos.runtime.venture_launch_orchestrator import VentureLaunchOrchestrator
from companyos.connectors.hosting_router import HostingRouter
def test_refuses_unqualified(tmp_path):
    r=VentureLaunchOrchestrator(tmp_path).launch({"id":"x","title":"No"});assert r["reason"]=="not_execution_qualified"
def test_preserves_manual_gate(tmp_path):
    r=VentureLaunchOrchestrator(tmp_path).launch({"execution_qualified":True,"requires_manual_approval":True});assert r["reason"]=="manual_approval_required"
def test_launch_feedback(monkeypatch,tmp_path):
    monkeypatch.setattr(HostingRouter,"health",lambda s:{"healthy":True})
    monkeypatch.setattr(HostingRouter,"deploy_directory",lambda s,p,d,b:{"provider":"cloudflare","deployment_id":"D","url":"https://v.pages.dev"})
    r=VentureLaunchOrchestrator(tmp_path).launch({"id":"o1","title":"Useful Service","execution_qualified":True,"offer":"Save time"})
    assert r["status"]=="launched" and (tmp_path/".companyos_runtime"/"outcome_evidence_queue.jsonl").exists()
def test_escapes_html(monkeypatch,tmp_path):
    monkeypatch.setattr(HostingRouter,"health",lambda s:{"healthy":True})
    monkeypatch.setattr(HostingRouter,"deploy_directory",lambda s,p,d,b:{"url":"https://x","deployment_id":"1"})
    VentureLaunchOrchestrator(tmp_path).launch({"execution_qualified":True,"title":"<script>x</script>"})
    assert "<script>x</script>" not in next((tmp_path/"generated_sites").rglob("index.html")).read_text()
PY

echo "===== COMPILE + TEST ====="
python -m py_compile companyos/runtime/venture_launch_orchestrator.py scripts/companyos_launchventure scripts/companyos_venturestatus
python -m pytest -q tests/generated/test_cloudflare_hosting.py tests/generated/test_website_deployer_cloudflare.py tests/generated/test_venture_launch_orchestrator.py
echo "===== HOSTING ====="; python scripts/companyos_hostingctl

echo "===== REAL CONTROLLED PIPELINE ====="
TMP=".companyos_runtime/controlled_launch_opportunity.json"
cat > "$TMP" <<'JSON'
{"id":"controlled-large-push-verification","title":"CompanyOS Venture Launch Pipeline","execution_qualified":true,"offer":"End-to-end verification of CompanyOS opportunity-to-production launch capability.","target_customer":"CompanyOS commissioning","cta":"Launch Verified"}
JSON
python scripts/companyos_launchventure --file "$TMP" | tee .companyos_runtime/controlled_launch_result.json
python - <<'PY'
import json
from pathlib import Path
r=json.loads(Path(".companyos_runtime/controlled_launch_result.json").read_text())
assert r.get("status")=="launched" and r.get("public_url"),r
f=json.loads(Path(".companyos_runtime/venture_launch_feedback.json").read_text())
assert f.get("outcome_state")=="awaiting_market_evidence",f
print("PIPELINE_ASSERTIONS=PASS");print("PUBLIC_URL="+r["public_url"])
PY

echo "===== COMMIT THIS PUSH ONLY ====="
git add companyos/runtime/venture_launch_orchestrator.py scripts/companyos_launchventure scripts/companyos_venturestatus tests/generated/test_venture_launch_orchestrator.py
git commit -m "add qualified opportunity to production venture launch pipeline" || true
echo "===== NO-RESTART SUPERVISOR CHECK ====="
python - <<'PY'
import json
from pathlib import Path
p=Path(".companyos_runtime/service_supervisor_state.json")
if p.exists():
 r=json.loads(p.read_text());print("supervisor_alive:",r.get("supervisor_alive"));print("running:",r.get("running"));print("stop_requested:",r.get("stop_requested"))
else:print("supervisor state not found; no restart attempted")
PY
echo "===== FINAL =====";git rev-parse --short HEAD;git status --short;python scripts/companyos_venturestatus
echo "COMPANYOS_VENTURE_LAUNCH_LARGE_PUSH=PASS"
