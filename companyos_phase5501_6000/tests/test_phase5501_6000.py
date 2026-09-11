from companyos.orchestration import PersistentGoalGraph, DynamicAgentFactory, AuthorityRouter

def test_goal(tmp_path):
    g=PersistentGoalGraph(tmp_path)
    g.upsert_goal("g","x",1)
    assert "g" in g.load()["goals"]

def test_agent_gap():
    assert DynamicAgentFactory().fill_gaps(["research"],{})[0]["role"]=="research_specialist"

def test_authority():
    assert AuthorityRouter().route([{"kind":"bank_transfer","amount":1000}])["approval_queue"]
