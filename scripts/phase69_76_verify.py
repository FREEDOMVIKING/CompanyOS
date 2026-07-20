#!/usr/bin/env python3
import json
from companyos_phase69_76 import *
r=OpportunityPipeline().rank([
{"name":"strong","demand":90,"margin":80,"speed":80,"confidence":.9,"risk":.2},
{"name":"weak","demand":20,"margin":20,"speed":20,"confidence":.3,"risk":.8}])
assert r[0]["name"]=="strong"
assert ValidationEngine().validate([{"support":.8,"reliability":.9}])["verdict"]=="validated"
spec=ProductFactory().create_spec({"name":"x"}); assert spec["external_deployment"] is False
assert LaunchPlanner().plan(spec)["external_action_taken"] is False
assert RevenueEngine().scenarios(10,[10])[0]["revenue"]==100
assert OperationsController().assess({"core":True})["status"]=="healthy"
assert LearningSystem().learn(1,2)["auto_policy_change"] is False
cycle=VentureOrchestrator().run({
"opportunities":[{"name":"AI service","demand":85,"margin":90,"speed":75,"confidence":.8,"risk":.2}],
"evidence":[{"support":.8,"reliability":.9}],"price":25,"customer_scenarios":[1,10,100],
"systems":{"core":True,"queue":True}})
assert cycle["success"] and not cycle["external_action_taken"]
print(json.dumps({"success":True,"status":"phase69_76_verification_passed",
"cycle_status":cycle["status"],"external_action_taken":cycle["external_action_taken"]},indent=2))
