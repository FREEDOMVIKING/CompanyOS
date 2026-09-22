from companyos.runtime import official_provider_provisioner as p


def test_auto_provision_disabled_by_default():
    assert p.AUTO_PROVISION is False


def test_monthly_cap_is_nonnegative():
    assert p.MAX_MONTHLY_USD >= 0


def test_no_token_is_not_ready(monkeypatch):
    monkeypatch.setattr(p,"token_for",lambda provider:None)
    assert p.hetzner_readiness()["ready"] is False
    assert p.digitalocean_readiness()["ready"] is False


def test_choose_provider_prefers_capacity_then_price():
    snap={"providers":[
        {"provider":"a","ready":True,"candidate":{"memory_mb":512,"monthly_usd":4}},
        {"provider":"b","ready":True,"candidate":{"memory_mb":4096,"monthly_usd":7}},
    ]}
    assert p.choose_provider(snap)["provider"]=="b"


def test_choose_provider_none_when_not_ready():
    assert p.choose_provider({"providers":[{"provider":"a","ready":False}]}) is None


def test_once_does_not_spend_when_disabled(monkeypatch,tmp_path):
    monkeypatch.setattr(p,"SSH_PRIVATE",tmp_path/"k")
    monkeypatch.setattr(p,"SSH_PUBLIC",tmp_path/"k.pub")
    monkeypatch.setattr(p,"AUTO_PROVISION",False)
    monkeypatch.setattr(p,"AUTO_ADOPT",False)
    monkeypatch.setattr(p,"ensure_local_ssh_key",lambda:{"present":True,"created":False,"private_path":"x","public_path":"y"})
    monkeypatch.setattr(p,"readiness",lambda:{
        "providers":[{
            "provider":"digitalocean","credential_present":True,"ready":True,
            "candidate":{"memory_mb":512,"monthly_usd":4,"size":"s","region":"r"},
            "existing_companyos_primary":None,
        }],
        "best_ready_provider":"digitalocean","credential_ready_count":1,
        "provisioning_enabled":False,
    })
    monkeypatch.setattr(p,"STATE",tmp_path/"state.json")
    monkeypatch.setattr(p,"HISTORY",tmp_path/"hist.jsonl")
    out=p.once()
    assert out["action"]["performed"] is False
    assert out["action"]["reason"]=="provisioning_disabled"
    assert out["financial_action_performed"] is False
    assert out["account_creation_performed"] is False
    assert out["credential_harvesting_performed"] is False
