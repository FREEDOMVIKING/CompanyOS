from companyos.runtime import provider_acquisition_broker as p

def test_retired_github_models_never_onboards():
    policy=p.account_creation_policy(p.PROVIDERS["github_models"])
    assert policy["action"]=="skip"
    assert policy["autonomous_account_creation_allowed"] is False

def test_public_github_requires_no_account():
    policy=p.account_creation_policy(p.PROVIDERS["github_public_rest"])
    assert policy["action"]=="use_without_account"
    assert policy["autonomous_account_creation_allowed"] is True

def test_interactive_signup_not_auto_created():
    for name in ("groq","gemini","cloudflare_workers_ai","huggingface","openai"):
        policy=p.account_creation_policy(p.PROVIDERS[name])
        assert policy["action"]=="queue_official_signup"
        assert policy["autonomous_account_creation_allowed"] is False

def test_secret_fingerprint_is_one_way_and_short():
    fp=p._fingerprint("super-secret-value")
    assert fp!="super-secret-value"
    assert len(fp)==12

def test_queue_never_enables_key_harvesting():
    inventory={name:{"credential_material_present":False,"credential_refs":[]} for name in p.PROVIDERS}
    probes={"github_public_rest":{"reachable":True}}
    q=p.build_onboarding_queue(inventory,probes)
    assert q["rules"]["search_public_repositories_for_keys"] is False
    assert q["rules"]["use_leaked_or_third_party_keys"] is False
    assert q["rules"]["automatic_purchase"] is False

def test_free_provider_catalog_contains_expected_targets():
    for name in ("github_public_rest","groq","gemini","cloudflare_workers_ai","huggingface"):
        assert p.PROVIDERS[name]["free"] is True
