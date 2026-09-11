#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase689_704 import *

assert AuthorityMatrix().classify("research")=="autonomous"
assert AuthorityMatrix().classify("spend_money")=="approval_required"
assert RiskClassifier().classify({"action_type":"sign_contract"})=="irreversible"
assert ApprovalGateway().evaluate({"action_type":"deploy_production"})["approval_required"] is True
assert DelegatedBudget().evaluate({"financial_commitment_usd":10},{"max_financial_commitment_usd":0})["within_budget"] is False
assert FinancialExposure().evaluate({"financial_commitment_usd":100})["automatic_purchase_authorized"] is False
assert ExternalActionPolicy().evaluate({"action_type":"publish_publicly"})["requires_review"] is True
assert SecretsPolicy().evaluate({"requested_secrets":["a"],"allowed_secrets":["a"]})["approved"] is True
assert AgentPermission().check("builder","write_internal_file")["allowed"] is True

pre=PreflightCheck().run({"action_type":"research","financial_commitment_usd":0})
assert pre["allowed_to_execute"] is True
assert RollbackPolicy().evaluate({"mutates_state":True,"reversible":False})["autonomous_execution_allowed"] is False

root=Path(tempfile.mkdtemp(prefix="phase704_"))
safe=SafeMode(root)
assert safe.status()["enabled"] is False
assert safe.enable("test")["enabled"] is True
assert safe.disable()["enabled"] is False

violation=PolicyViolation().detect(
    PreflightCheck().run({"action_type":"deploy_production"}),
    RollbackPolicy().evaluate({"mutates_state":True,"reversible":True}),
    {"enabled":False}
)
assert violation["violation"] is True

esc=EscalationQueue(root)
assert esc.add({"x":1})["x"]==1
prov=DecisionProvenance().build(
    {"action_type":"research"},
    PreflightCheck().run({"action_type":"research"}),
    {"violation":False,"reasons":[]}
)
assert prov["allowed"] is True
assert GovernanceLedger(root).append(prov)["action_type"]=="research"
assert GovernanceRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase689_704_verification_passed",
    "cycle_status":"phase704_governance_risk_oversight_ready",
    "authority_matrix":True,
    "risk_classification":True,
    "approval_gateway":True,
    "delegated_budgets":True,
    "financial_exposure_limits":True,
    "external_action_controls":True,
    "least_privilege_secrets":True,
    "agent_permission_boundaries":True,
    "preflight_checks":True,
    "rollback_requirements":True,
    "safe_mode":True,
    "policy_violation_detection":True,
    "human_escalation_queue":True,
    "decision_provenance":True,
    "governance_ledger":True,
    "autonomy_mode":"high_with_governance"
},indent=2))
