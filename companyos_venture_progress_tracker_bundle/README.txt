COMPANYOS LIVE VENTURE PROGRESS TRACKER

Adds a live progress page for Executive Roadmap subjects.

Features:
- Search/load any venture or roadmap subject
- Current observed stage
- Observed task-state progress percentage
- Active work
- Completed work
- Queued next actions
- Blockers
- Pending approvals
- Research/evidence records
- Milestones/stages
- Source record paths for traceability
- Auto refresh every 15 seconds

Important:
The progress percentage is conservative and derived from observed task states. It does not invent a business-completion percentage.

Install:
cd ~/companyos
rm -rf companyos_venture_progress_tracker_bundle
mkdir -p companyos_venture_progress_tracker_bundle
unzip -o ~/storage/downloads/COMPANYOS_VENTURE_PROGRESS_TRACKER_BUNDLE.zip -d ~/companyos/companyos_venture_progress_tracker_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_venture_progress_tracker_bundle/install.py
python companyos_venture_progress_tracker_bundle/verify.py
bash dashboard/venture_progress_start.sh

Open:
http://127.0.0.1:8767

Existing dashboards remain:
Executive: http://127.0.0.1:8765
Master Controls: http://127.0.0.1:8766
