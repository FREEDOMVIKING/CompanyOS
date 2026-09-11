COMPANYOS VENTURE PROGRESS TRACKER V2

This replaces the first tracker on port 8767 with a tracker connected to the same Executive Dashboard source-of-truth.

What V2 does:
- Reads the live Executive Dashboard API on port 8765
- Uses the actual roadmap record from portfolio priorities
- Matches related decisions / approvals
- Matches linked tasks and runtime records
- Distinguishes ROADMAP_REVIEW, AWAITING_APPROVAL, ACTIVE, QUEUED, BLOCKED, and NO_LINKED_WORK
- Explains why a roadmap item has no active execution
- Shows active/completed/queued/blocked work
- Shows approvals, evidence, milestones, and source records
- Uses conservative progress derived only from linked task states
- Auto refreshes every 10 seconds

Install:
cd ~/companyos
rm -rf companyos_venture_progress_v2_bundle
mkdir -p companyos_venture_progress_v2_bundle
unzip -o ~/storage/downloads/COMPANYOS_VENTURE_PROGRESS_V2_BUNDLE.zip -d ~/companyos/companyos_venture_progress_v2_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_venture_progress_v2_bundle/install.py
python companyos_venture_progress_v2_bundle/verify.py
bash dashboard/venture_progress_v2_start.sh

Open:
http://127.0.0.1:8767

The installer does NOT stop CompanyOS, modify wallet settings, or replace the Executive Dashboard.
