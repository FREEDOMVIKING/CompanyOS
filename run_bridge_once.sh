#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$HOME/companyos"
for m in roadmap_execution_bridge milestone_generator_v3 specialist_assignment_v3 venture_artifact_pipeline execution_evidence_linker progress_sync_v3 venture_validation_engine launch_readiness_engine dashboard_cluster_manager execution_recovery_manager; do
  echo "Running $m..."
  python -m "companyos.$m.cli"
done
