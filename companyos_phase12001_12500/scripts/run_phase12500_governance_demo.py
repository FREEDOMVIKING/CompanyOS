#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.governanceops import CEOGovernanceOpsController

result=CEOGovernanceOpsController(Path.home()/"companyos").run(
    policies=[
        {"policy_id":"audit","name":"Audit Integrity","controls":["audit_logging","immutable_decisions"]},
        {"policy_id":"access","name":"Least Privilege","controls":["access_control","mfa"]}
    ],
    requirements=[
        {"requirement":"critical_actions_traceable","required_controls":["audit_logging","immutable_decisions"]},
        {"requirement":"admin_access_protected","required_controls":["access_control","mfa"]}
    ],
    controls=["audit_logging","immutable_decisions","access_control","mfa"],
    evidence={
        "audit_logging":["governance_audit.jsonl"],
        "immutable_decisions":["decision_ledger.jsonl"],
        "access_control":["approval_queue"],
        "mfa":["identity_policy"]
    },
    assets=[
        {"name":"company_state","sensitivity":"restricted"},
        {"name":"public_catalog","sensitivity":"public"}
    ],
    records=[
        {"name":"audit_logs","category":"audit"},
        {"name":"operational_logs","category":"operational"}
    ],
    identities=[
        {"identity":"ceo_runtime","admin":False,"mfa":True,"permissions":["internal"]},
        {"identity":"human_owner","admin":True,"mfa":True,"permissions":["approval"]}
    ],
    vendors=[
        {"name":"primary_provider","critical":True,"risk":.3},
        {"name":"secondary_tool","critical":False,"risk":.2}
    ],
    decisions=[
        {"decision":"retain approval gates","reason":"protected external actions"}
    ],
    exceptions=[
        {"policy":"example","reason":"demo_only"}
    ],
    actions=[
        {"kind":"internal_compliance_scan"},
        {"kind":"disable_audit"},
        {"kind":"approve_policy_exception"}
    ]
)

print(json.dumps(result,indent=2,default=str))
