from companyos.runtime import hybrid_compute_mesh_controller as mesh


def test_remote_primary_wins_when_healthy():
    out=mesh.choose_operating_mode(
        {"healthy":True},
        {"healthy":True},
        {"healthy":True,"healthy_primary_count":1},
        {"credential_ready_count":0,"auto_provision_enabled":False},
    )
    assert out["primary_control_plane"]=="persistent_remote"
    assert out["mode"]=="remote_primary_plus_burst"


def test_phone_plus_github_when_no_remote_primary():
    out=mesh.choose_operating_mode(
        {"healthy":True},
        {"healthy":True},
        {"healthy":False,"healthy_primary_count":0},
        {"credential_ready_count":0,"auto_provision_enabled":False},
    )
    assert out["primary_control_plane"]=="termux_local"
    assert out["burst_compute_plane"]=="github_actions"


def test_provider_ready_but_disabled_is_not_auto_spend():
    out=mesh.choose_operating_mode(
        {"healthy":True},
        {"healthy":True},
        {"healthy":False,"healthy_primary_count":0},
        {"credential_ready_count":1,"auto_provision_enabled":False},
    )
    assert out["next_action"]=="provider_ready_but_auto_provision_disabled"


def test_once_never_enables_sensitive_mesh_actions(monkeypatch,tmp_path):
    monkeypatch.setattr(mesh,"STATE",tmp_path/"state.json")
    monkeypatch.setattr(mesh,"HISTORY",tmp_path/"history.jsonl")
    monkeypatch.setattr(mesh,"local_plane",lambda:{"healthy":True})
    monkeypatch.setattr(mesh,"github_plane",lambda:{"healthy":True,"configured_burst_lane_ceiling":32})
    monkeypatch.setattr(mesh,"remote_plane",lambda:{"healthy":False,"healthy_primary_count":0,"healthy_capacity_score":0,"healthy_node_count":0})
    monkeypatch.setattr(mesh,"provider_plane",lambda:{"healthy":True,"credential_ready_count":0,"auto_provision_enabled":False})
    monkeypatch.setattr(mesh,"host_discovery_plane",lambda:{"healthy":True})
    monkeypatch.setattr(mesh,"offload_plane",lambda:{"healthy":True,"recommended_shards":2})
    out=mesh.once()
    assert out["restrictions"]["mesh_financial_actions"] is False
    assert out["restrictions"]["mesh_account_creation"] is False
    assert out["restrictions"]["mesh_deployment_actions"] is False
    assert out["restrictions"]["quota_bypass"] is False
