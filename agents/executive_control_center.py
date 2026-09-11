#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"executive_control_center.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    approvals=load("governed_approval_queue.json",{})
    actions=load("external_action_registry.json",{})
    receipts=load("execution_receipts.json",{})
    connectors=load("connector_readiness_report.json",{})
    obs=load("operations_observability_report.json",{})
    incidents=load("incident_response_queue.json",{})
    portfolio=load("ceo_project_portfolio.json",{})
    payload={
      "generated_at":now(),
      "system_health":"healthy" if obs.get("healthy",False) else "attention",
      "pending_approval_count":sum(1 for x in approvals.get("items",[]) if x.get("status")=="pending"),
      "registered_external_action_count":actions.get("action_count",0),
      "execution_receipt_count":receipts.get("receipt_count",0),
      "connector_readiness":connectors.get("connectors",[]),
      "incident_count":incidents.get("incident_count",0),
      "project_count":portfolio.get("project_count",0),
      "external_authority_granted":False,
      "control_note":"External actions remain blocked until explicit approval changes authority state."
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"executive_control_center_complete","control_center":payload}

r=build()
print(json.dumps(r,indent=2))
