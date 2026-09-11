#!/data/data/com.termux/files/usr/bin/bash
set -e

ROOT="${HOME}/companyos"

echo "============================================"
echo "INSTALLING PHASE 50"
echo "AUTONOMOUS OPPORTUNITY DISCOVERY +"
echo "QUALIFICATION ENGINE"
echo "============================================"

cd "$ROOT"

mkdir -p agents/phase50_opportunity_engine
mkdir -p ceo_memory/phase50

touch agents/__init__.py
touch agents/phase50_opportunity_engine/__init__.py

chmod +x companyos/phase50ctl
chmod +x companyos/verify_phase50.py

python -m py_compile \
  agents/phase50_opportunity_engine/opportunity_engine.py \
  agents/phase50_opportunity_engine/discovery_intake.py \
  companyos/phase50ctl \
  companyos/verify_phase50.py

python -m json.tool \
  ceo_memory/phase50/phase50_config.json \
  >/dev/null

cat > ceo_memory/phase50/phase50_manifest.json <<'JSON'
{
  "phase": 50,
  "name": "Autonomous Opportunity Discovery and Qualification Engine",
  "enabled": true,
  "components": [
    "opportunity_scoring",
    "weighted_qualification",
    "confidence_filtering",
    "duplicate_protection",
    "discovery_intake",
    "persistent_opportunity_memory",
    "discovery_history"
  ],
  "integration": {
    "phase49_preserved": true,
    "controller": "companyos/phase50ctl",
    "verification": "companyos/verify_phase50.py"
  },
  "safety": {
    "reject_illegal_or_prohibited": true,
    "reject_unbounded_financial_risk": true,
    "owner_approval_for_irreversible_external_actions": true,
    "owner_approval_for_financial_commitments": true
  }
}
JSON

echo
python companyos/verify_phase50.py

echo
echo "============================================"
echo "PHASE 50 AUTONOMOUS OPPORTUNITY ENGINE INSTALLED"
echo "OPPORTUNITY DISCOVERY INTAKE: ENABLED"
echo "WEIGHTED QUALIFICATION: ENABLED"
echo "DUPLICATE PROTECTION: ENABLED"
echo "PERSISTENT OPPORTUNITY MEMORY: ENABLED"
echo "PHASE 49 COMMUNICATION PATH: PRESERVED"
echo "IRREVERSIBLE EXTERNAL ACTION APPROVAL: REQUIRED"
echo "FINANCIAL COMMITMENT APPROVAL: REQUIRED"
echo "============================================"
