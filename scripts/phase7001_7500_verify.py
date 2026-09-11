#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.connectors import *

root=Path(tempfile.mkdtemp())
reg=ConnectorRegistry(root)
reg.register("research_primary","provider",["research"],.9)
reg.register("deploy_primary","tool",["deploy"],.8)
assert len(reg.list_enabled())==2

caps=CapabilityDiscovery().discover(reg.list_enabled())
assert "research" in caps and "deploy" in caps

ranked=ConnectorHealthRouter().rank(
    reg.list_enabled(),
    [{"name":"research_primary","availability":1,"error_rate":0,"latency_score":.9,"quality":.9}]
)
assert ranked

assert FallbackEngine().choose(ranked)["selected"] is not None
assert ConnectorApprovalRouter().route([{"kind":"bank_transfer","amount":1000}])["approval_queue"]
assert ConnectorLayerStatus().status()["status"]=="phase7500_real_world_connector_capability_layer_ready"

print(json.dumps({
    "success":True,
    "status":"phase7001_7500_verification_passed",
    "cycle_status":"phase7500_real_world_connector_capability_layer_ready"
},indent=2))
