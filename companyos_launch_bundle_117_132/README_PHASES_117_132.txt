COMPANYOS LARGE LAUNCH BUNDLE — PHASES 117–132

Purpose:
Accelerate launch-day readiness with a larger integrated internal business/project stack.

Includes:
117 Project Pipeline
118 Specialist Coordination
119 Project Checkpointing
120 Recovery Manager
121 Launch Readiness Evaluator
122 Internal Operations Loop
123 Business Workspace
124 Portfolio Manager
125 Revenue Observation Store
126 Internal Launch Dashboard
127 Project State Persistence
128 Blocker Tracking
129 Artifact Tracking
130 Internal Launch Gate
131 External-Action Boundary Preservation
132 Transaction-Broadcast Boundary Preservation

INSTALL:
cd ~/companyos || exit 1
rm -rf companyos_launch_bundle_117_132
mkdir -p companyos_launch_bundle_117_132
unzip -o ~/storage/downloads/COMPANYOS_LAUNCH_BUNDLE_PHASES_117_132.zip \
  -d ~/companyos/companyos_launch_bundle_117_132
python ~/companyos/companyos_launch_bundle_117_132/phase117_132_install.py

VERIFY:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python companyos_launch_bundle_117_132/phase117_132_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase117_132_test.py

DASHBOARD:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase117_132_launch_ctl.py dashboard
