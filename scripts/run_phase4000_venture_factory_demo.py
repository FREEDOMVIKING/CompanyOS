#!/usr/bin/env python3
import json
from companyos.venture_factory import AutonomousVentureFactory
r=AutonomousVentureFactory().cycle(
 candidates=[
  {"name":"contractor_estimation_ai","demand":.91,"pain":.88,"willingness_to_pay":.82,"competition":.42,"evidence":.86,"growth":.31,"reliability":.81},
  {"name":"generic_content_tool","demand":.55,"pain":.35,"willingness_to_pay":.4,"competition":.9,"evidence":.5}
 ],
 existing_ventures=[
  {"venture_id":"venture_a","score":.82,"growth":.3,"reliability":.88},
  {"venture_id":"venture_b","score":.28,"growth":.05,"reliability":.46}
 ],
 actions=[
  {"kind":"internal_research"},
  {"kind":"build_prototype"},
  {"kind":"production_deploy"},
  {"kind":"bank_transfer","amount":1500}
 ],
 budget=10000,worker_slots=10
)
print(json.dumps(r,indent=2))
