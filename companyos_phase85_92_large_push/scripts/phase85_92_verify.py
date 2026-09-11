#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase85_92 import *
kg=KnowledgeGraph();kg.add("customer");kg.add("product");kg.link("customer","buys","product")
assert len(kg.neighbors("customer"))==1
assert DecisionQuality().score({"evidence":1,"reversibility":1,"clarity":1,"downside_risk":0})["recommendation"]=="proceed_to_gate"
assert ProcessOptimizer().analyze([{"name":"x","duration":10,"failures":1,"volume":1}])["top_bottleneck"]["name"]=="x"
assert RiskRegister().assess([{"name":"x","likelihood":5,"impact":5}])[0]["level"]=="critical"
assert ScenarioPlanner().build(100)["base"]==100
assert PortfolioGovernor().review([{"name":"x","traction":.9,"strategic_fit":.9,"risk":.1,"burn_pressure":.1}])[0]["recommendation"]=="continue"
m=ExecutiveMemory(Path(__file__).resolve().parents[1]/"state"/"executive_memory_85_92.json");m.add({"verified":True})
c=CEOOrchestrator().run({"decisions":[{"name":"test","evidence":.8,"reversibility":.8,"clarity":.9,"downside_risk":.2}],
"process_steps":[{"name":"research","duration":1}],"risks":[{"name":"market","likelihood":2,"impact":3}],
"base_value":100,"ventures":[{"name":"v","traction":.8,"strategic_fit":.8,"risk":.2,"burn_pressure":.2}]})
assert c["success"] and not c["external_action_taken"] and not c["irreversible_action_taken"]
print(json.dumps({"success":True,"status":"phase85_92_verification_passed","cycle_status":c["status"],
"external_action_taken":c["external_action_taken"],"irreversible_action_taken":c["irreversible_action_taken"]},indent=2))
