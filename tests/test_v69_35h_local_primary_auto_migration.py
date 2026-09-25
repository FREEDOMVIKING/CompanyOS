from companyos.runtime import local_primary_registry as reg
from companyos.runtime import authorized_local_migration_controller as ctl

def test_capacity_score_prefers_more_resources():
    assert reg.capacity_score(8,16,250)>reg.capacity_score(2,4,40)

def test_authorization_is_required(monkeypatch):
    monkeypatch.setattr(ctl.fabric,"inventory",lambda:{
        "nodes":[
            {"name":"yes","enabled":True,"authorized_by_user":True,"ssh_target":"host-a"},
            {"name":"no","enabled":True,"authorized_by_user":False,"ssh_target":"host-b"},
        ]
    })
    assert [x["name"] for x in ctl.eligible_nodes()]==["yes"]

def test_gain_floor_is_nontrivial():
    assert ctl.MIN_GAIN>=1.05
