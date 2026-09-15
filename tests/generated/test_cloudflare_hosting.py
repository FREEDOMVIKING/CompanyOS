from companyos.connectors.cloudflare_hosting import CloudflareHosting
from companyos.connectors.hosting_router import HostingRouter
def test_unconfigured_is_dry(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN",raising=False)
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID",raising=False)
    h=CloudflareHosting().health()
    assert h["configured"] is False and h["dry_run"] is True
def test_router_prefers_cloudflare(monkeypatch):
    monkeypatch.setattr(CloudflareHosting,"health",lambda self:{"provider":"cloudflare","configured":True,"dry_run":False,"healthy":True})
    h=HostingRouter().health()
    assert h["provider"]=="cloudflare" and h["healthy"] is True
def test_directory_validation(tmp_path):
    c=CloudflareHosting("x","y")
    try: c.deploy_directory("x",tmp_path/"missing")
    except Exception as e: assert "does not exist" in str(e)
    else: raise AssertionError("expected validation error")
