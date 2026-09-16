from companyos.runtime import profit_to_action_closure as m
def test_priority():
    assert m.priority({"candidate_score":50,"decision_closure":{"decision":"promote_to_guarded_execution"}})>m.priority({"candidate_score":99,"decision_closure":{"decision":"continue_research"}})
def test_action_choice():
    assert m.choose({"recommended_actions":[{"action":"a","confidence":20},{"action":"b","confidence":90}]})["action"]=="b"
def test_gates():
    g=m.goal({"candidate_name":"demo","action_packet_id":"1"},{"action":"validate","confidence":80})
    assert "MUST pass" in g and "finance" in g.lower() and "Never fabricate" in g
