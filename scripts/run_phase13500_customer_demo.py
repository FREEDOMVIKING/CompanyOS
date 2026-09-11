#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.customerops import CEOCustomerOpsController
r=CEOCustomerOpsController(Path.home()/"companyos").run(
 customers=[
  {"customer_id":"c1","usage":.9,"satisfaction":.9,"payment_health":1,"support_friction":.1,"value_realization":.9},
  {"customer_id":"c2","usage":.3,"satisfaction":.4,"payment_health":.8,"support_friction":.7,"value_realization":.35}],
 tickets=[
  {"ticket_id":"t1","severity":.9,"impact":.9,"blocked":True,"sla_minutes":30,"elapsed_minutes":45,"issue":"integration unavailable"},
  {"ticket_id":"t2","severity":.3,"impact":.4,"blocked":False,"sla_minutes":120,"elapsed_minutes":30,"issue":"billing question"}],
 feedback=[{"theme":"onboarding"},{"theme":"onboarding"},{"theme":"reporting"}],
 resolved_tickets=[{"ticket_id":"old1","issue":"reset integration token"}],
 service_signals={"resolution_rate":.92,"satisfaction":.88,"sla_rate":.85,"first_contact_resolution":.82},
 actions=[{"kind":"draft_help_article"},{"kind":"issue_refund"},{"kind":"change_contract"}])
print(json.dumps(r,indent=2,default=str))
