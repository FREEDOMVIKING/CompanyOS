#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.resilienceops import CEOResilienceOpsController

result=CEOResilienceOpsController(Path.home()/"companyos").run(
    services=[
        {"name":"ceo","critical":True,"depends_on":["state","queue"],"failure_domain":"phone","rto_minutes":15,"rpo_minutes":5,"fallback":"safe_ceo_mode"},
        {"name":"state","critical":True,"depends_on":[],"failure_domain":"local_storage","rto_minutes":15,"rpo_minutes":5,"fallback":"checkpoint_restore"},
        {"name":"queue","critical":True,"depends_on":["state"],"failure_domain":"phone","rto_minutes":30,"rpo_minutes":10,"fallback":"persistent_requeue"}
    ],
    assets=[
        {"name":"company_state","criticality":"critical"},
        {"name":"audit_logs","criticality":"high"}
    ],
    failed_capabilities=["primary_provider"],
    incident={"kind":"provider_outage","impact":.55,"spread":.3},
    providers=[
        {"name":"primary","healthy":False,"health_score":.1},
        {"name":"fallback_a","healthy":True,"health_score":.9},
        {"name":"fallback_b","healthy":True,"health_score":.8}
    ],
    integrity_checks=[
        {"name":"state_checksum","passed":True},
        {"name":"audit_chain","passed":True}
    ],
    actions=[
        {"kind":"restart_failed_service"},
        {"kind":"disable_audit"},
        {"kind":"destroy_primary_data"}
    ]
)

print(json.dumps(result,indent=2,default=str))
