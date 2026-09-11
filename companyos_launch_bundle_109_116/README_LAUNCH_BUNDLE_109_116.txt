COMPANYOS LAUNCH BUNDLE — PHASES 109–116

This is the first larger bundled push for launch-day acceleration.

Includes:
109 Launch Runtime Control
110 Approval Queue
111 Action Proposal Router
112 Unified Health Snapshot
113 Unified Start/Stop Surface
114 External Action Safety Boundary
115 Financial Broadcast Boundary Preservation
116 Launch Gate + Verification

INSTALL:
cd ~/companyos || exit 1
rm -rf companyos_launch_bundle_109_116
mkdir -p companyos_launch_bundle_109_116
unzip -o ~/storage/downloads/COMPANYOS_LAUNCH_BUNDLE_PHASES_109_116.zip \
  -d ~/companyos/companyos_launch_bundle_109_116
python ~/companyos/companyos_launch_bundle_109_116/phase109_116_install.py

VERIFY:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python companyos_launch_bundle_109_116/phase109_116_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase109_116_launch_test.py

START:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase109_116_launch_ctl.py start

STATUS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase109_116_launch_ctl.py status

HEALTH:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase109_116_launch_ctl.py health

APPROVALS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase109_116_launch_ctl.py approvals
