from companyos.runtime import persistent_host_scout as scout


def test_profiles_are_official_https():
    assert scout.HOST_PROFILES
    for profile in scout.HOST_PROFILES.values():
        assert profile["official_url"].startswith("https://")
        assert profile["signup_url"].startswith("https://")


def test_ephemeral_compute_scores_below_real_vps_when_equally_reachable():
    probe={"reachable":True}
    gh=dict(scout.HOST_PROFILES["github_actions"])
    do=dict(scout.HOST_PROFILES["digitalocean_basic_512"])
    empty={"credential_present":False}
    assert scout.candidate_score(do,empty,probe) > scout.candidate_score(gh,empty,probe)


def test_sleeping_free_hosts_not_claimed_always_on():
    assert scout.HOST_PROFILES["render_free"]["always_on_expected"] is False
    assert scout.HOST_PROFILES["koyeb_free"]["always_on_expected"] is False


def test_paid_provisioning_disabled_by_default():
    assert scout.ALLOW_PAID_PROVISIONING is False


def test_acquisition_queue_never_allows_account_creation(monkeypatch,tmp_path):
    monkeypatch.setattr(scout,"QUEUE",tmp_path/"q.json")
    rows=[{
        "host_id":"x",
        "provider":"example",
        "kind":"vps",
        "score":80,
        "signup_url":"https://example.com/signup",
        "official_url":"https://example.com",
        "monthly_cost_usd":4.0,
        "always_on_expected":True,
        "ssh":True,
        "credential_present":False,
        "automatic_paid_provisioning_allowed":False,
    }]
    q=scout.acquisition_queue(rows)
    assert q["tasks"][0]["automatic_account_creation_allowed"] is False
    assert q["financial_action_performed"] is False


def test_handoff_requires_authorized_healthy_primary(monkeypatch):
    monkeypatch.setattr(scout,"AUTO_HANDOFF",True)
    out=scout.maybe_handoff([])
    assert out["attempted"] is False
    assert out["reason"]=="no_authorized_healthy_primary"
