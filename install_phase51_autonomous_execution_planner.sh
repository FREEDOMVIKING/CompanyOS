#!/data/data/com.termux/files/usr/bin/bash
set -e

ROOT="${HOME}/companyos"

echo "============================================"
echo "INSTALLING PHASE 51"
echo "AUTONOMOUS OPPORTUNITY-TO-EXECUTION PLANNER"
echo "============================================"

cd "$ROOT"

mkdir -p agents/phase51_execution_planner
mkdir -p ceo_memory/phase51

touch agents/__init__.py
touch agents/phase51_execution_planner/__init__.py

chmod +x companyos/phase51ctl
chmod +x companyos/verify_phase51.py

python -m py_compile \
  agents/phase51_execution_planner/execution_planner.py \
  agents/phase51_execution_planner/task_dispatcher.py \
  agents/phase51_execution_planner/task_executor.py \
  agents/phase51_execution_planner/execution_loop.py \
  companyos/phase51ctl \
  companyos/verify_phase51.py

python -m json.tool \
  ceo_memory/phase51/phase51_config.json \
  >/dev/null

cat > ceo_memory/phase51/phase51_manifest.json <<'JSON'
{
  "phase": 51,
  "name": "Autonomous Opportunity-to-Execution Planner",
  "enabled": true,
  "source_phase": 50,
  "components": [
    "execution_planning",
    "milestone_generation",
    "dependency_mapping",
    "specialist_task_routing",
    "bounded_task_execution",
    "autonomous_execution_loop",
    "persistent_task_results"
  ],
  "integration": {
    "phase50_opportunity_input": true,
    "controller": "companyos/phase51ctl",
    "verification": "companyos/verify_phase51.py"
  },
  "execution_policy": {
    "autonomous_reversible_internal_actions": true,
    "owner_approval_for_financial_commitments": true,
    "owner_approval_for_irreversible_external_actions": true
  }
}
JSON

echo
python companyos/verify_phase51.py

echo
echo "============================================"
echo "PHASE 51 AUTONOMOUS EXECUTION PLANNER INSTALLED"
echo "PHASE 50 QUALIFIED OPPORTUNITY INPUT: ENABLED"
echo "EXECUTION PLAN GENERATION: ENABLED"
echo "DEPENDENCY-AWARE DISPATCH: ENABLED"
echo "SPECIALIST TASK ROUTING: ENABLED"
echo "BOUNDED AUTONOMOUS LOOP: ENABLED"
echo "PERSISTENT TASK RESULTS: ENABLED"
echo "FINANCIAL COMMITMENT APPROVAL: REQUIRED"
echo "IRREVERSIBLE EXTERNAL ACTION APPROVAL: REQUIRED"
echo "============================================"
