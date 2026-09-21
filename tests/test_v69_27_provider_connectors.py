from companyos.runtime import provider_acquisition_broker as pab
from companyos.runtime import provider_connector_router as pcr
from companyos.runtime import provider_account_onboarding_worker as paw

def test_search_providers_are_cataloged():
    assert pab.PROVIDERS["tavily"]["free"] is True
    assert pab.PROVIDERS["brave_search"]["free"] is True

def test_cloudflare_default_avoids_paid_only_models():
    m=pcr.FREE_CF_MODEL
    for bad in ("kimi-k2.6","kimi-k2.7-code","glm-5.2","glm-5.3","deepseek-v4"):
        assert bad not in m

def test_onboarding_worker_policy_blocks_key_harvesting_and_paid_upgrade():
    src=open(paw.__file__,encoding="utf-8").read()
    assert '"search_public_repositories_for_keys":False' in src
    assert '"use_leaked_or_third_party_keys":False' in src
    assert '"automatic_purchase":False' in src
    assert '"paid_upgrade":False' in src

def test_search_router_empty_without_search_keys(monkeypatch):
    monkeypatch.setattr(pcr,"provider_status",lambda:{"capabilities":{"web_search":[]}})
    out=pcr.search_web("x",3)
    assert out["status"]=="no_usable_web_search_provider"
