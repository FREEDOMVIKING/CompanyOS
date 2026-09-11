from companyos.canonicalproduction import CanonicalProductionRuntime

rt = CanonicalProductionRuntime()

s = rt.status()
assert s["execution_gateway"]["ready"] is True
assert s["orchestration"]["ready"] is True
assert s["ceo_bridge"]["ready"] is True

t = rt.test()
assert t["pass"] is True
assert t["goal_result"]["tasks_failed"] == 0

for task in t["goal_result"]["task_results"]:
    r = task["result"]
    assert r["transaction_broadcast_performed"] is False
    assert r["external_action_performed"] is False

print("phase102_adapter => PASS")
print("ceo_bridge => PASS")
print("canonical_orchestration => PASS")
print("canonical_execution_gateway => PASS")
print("master_status => PASS")
print("one_shot_cycle => PASS")
print("no_external_action => PASS")
print("no_transaction_broadcast => PASS")
print("BUNDLE4_SMOKE_TEST: PASS")
