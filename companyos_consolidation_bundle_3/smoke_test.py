from companyos.canonicalruntime import UnifiedCEOCanonicalBridge

bridge = UnifiedCEOCanonicalBridge()

status = bridge.status()
assert status["ready"] is True
assert status["orchestration"]["gateway"]["ready"] is True

g = bridge.submit_ceo_goal(
    "Evaluate an internal autonomous business concept",
    {"mode": "bundle3_smoke"},
    goal_id="bundle3-smoke-goal",
)
assert g["tasks_total"] == 4
assert g["tasks_failed"] == 0

o = bridge.submit_opportunity(
    "AI-assisted local service operations",
    hypothesis="Automation may reduce manual overhead.",
    evidence={"smoke": True},
    opportunity_id="bundle3-smoke-opportunity",
)
assert o["tasks_total"] == 4
assert o["tasks_failed"] == 0

r = bridge.submit_research_result(
    "Can internal automation support a repeatable service workflow?",
    findings={"smoke": True},
)
assert r["tasks_total"] == 4
assert r["tasks_failed"] == 0

for result in [g, o, r]:
    for task in result["task_results"]:
        tr = task["result"]
        assert tr["transaction_broadcast_performed"] is False
        assert tr["external_action_performed"] is False

print("phase102_observer => PASS")
print("ceo_goal_bridge => PASS")
print("opportunity_bridge => PASS")
print("research_bridge => PASS")
print("canonical_orchestration => PASS")
print("no_external_action => PASS")
print("no_transaction_broadcast => PASS")
print("BUNDLE3_SMOKE_TEST: PASS")
