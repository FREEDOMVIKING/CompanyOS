from companyos.canonicalorchestration import CanonicalOrchestrationBridge, GoalRequest

bridge = CanonicalOrchestrationBridge()

goal = GoalRequest(
    objective="Build and evaluate an internal test business concept",
    context={"mode": "smoke_test"},
    goal_id="bundle2-smoke-goal",
)

result = bridge.run_goal(goal)

assert result.tasks_total == 4
assert result.tasks_completed == 4
assert result.tasks_blocked == 0
assert result.tasks_failed == 0

for task in result.task_results:
    r = task.get("result", {})
    assert r.get("transaction_broadcast_performed") is False
    assert r.get("external_action_performed") is False

print("goal_persistence => PASS")
print("goal_decomposition => PASS")
print("task_dispatch => PASS")
print("canonical_gateway_routing => PASS")
print("no_external_action => PASS")
print("no_transaction_broadcast => PASS")
print("BUNDLE2_SMOKE_TEST: PASS")
