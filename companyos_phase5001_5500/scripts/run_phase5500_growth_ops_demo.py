#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.growthops import CEOGrowthOpsController
r=CEOGrowthOpsController(Path.home()/"companyos").run(
 market_signals=[
  {"name":"ai_ops_smb","demand":.9,"growth":.85,"urgency":.8,"competition":.55},
  {"name":"contractor_estimating","demand":.8,"growth":.7,"urgency":.9,"competition":.35}],
 competitors=[
  {"name":"competitor_a","strength":.8,"momentum":.7,"differentiation_gap":.4}],
 customer_signals=[
  {"kind":"pain","text":"manual workflow takes too long"},
  {"kind":"request","text":"automated reporting"},
  {"kind":"objection","text":"setup complexity"}],
 opportunities=[
  {"name":"automated_onboarding","value":.8,"confidence":.85,"speed":.9,"effort":.4,"risk":.15},
  {"name":"new_vertical","value":.95,"confidence":.55,"speed":.5,"effort":.8,"risk":.3}],
 experiments=[
  {"name":"pricing_page","confidence":.85,"impact":.7,"result":.2},
  {"name":"new_outbound","confidence":.6,"impact":.6,"result":.05}],
 offers=[
  {"name":"basic","conversion":.08,"price":99,"margin":.8},
  {"name":"pro","conversion":.05,"price":299,"margin":.85}],
 cohorts=[
  {"name":"cohort_a","retention":.85,"expansion":.7,"satisfaction":.9},
  {"name":"cohort_b","retention":.5,"expansion":.3,"satisfaction":.6}],
 channels=[
  {"channel":"outbound","roi":2.2,"confidence":.8,"capacity":.9},
  {"channel":"content","roi":1.8,"confidence":.75,"capacity":1}],
 budget=5000,current_revenue=20000,monthly_growth=.08,
 actions=[
  {"kind":"internal_analysis"},
  {"kind":"large_marketing_spend","amount":2500},
  {"kind":"public_campaign_launch"},
  {"kind":"contract_signature"}])
print(json.dumps(r,indent=2,default=str))
