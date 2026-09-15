import json
from pathlib import Path
from companyos.website_deployer.engine import WebsiteDeployer
from companyos.connectors.hosting_router import HostingRouter

def test_deployer_records_success(monkeypatch,tmp_path):
    vb=tmp_path/"companyos_runtime"/"venture_builder"; vb.mkdir(parents=True)
    (vb/"latest_build.json").write_text(json.dumps({"title":"Test Venture"}))
    monkeypatch.setattr(HostingRouter,"health",lambda self:{"configured":True,"dry_run":False,"healthy":True,"provider":"cloudflare"})
    monkeypatch.setattr(HostingRouter,"deploy_directory",lambda self,p,d,b:{"provider":"cloudflare","project":p,"deployment_id":"d1","url":"https://example.pages.dev","status":"submitted"})
    r=WebsiteDeployer(tmp_path).run()
    assert r["status"]=="published"
    assert r["public_url"]=="https://example.pages.dev"
    assert (tmp_path/".companyos_runtime"/"latest_deployment.json").exists()
    assert (tmp_path/".companyos_runtime"/"deployment_ledger.jsonl").exists()

def test_deployer_waits_when_hosting_not_ready(monkeypatch,tmp_path):
    monkeypatch.setattr(HostingRouter,"health",lambda self:{"configured":False,"dry_run":True,"healthy":False})
    r=WebsiteDeployer(tmp_path).run()
    assert r["publish_status"]=="waiting_for_configured_hosting_connector"
