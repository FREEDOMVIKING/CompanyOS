PHASE 90 — RUNTIME CONTROL PLANE

Adds simple production commands for the Phase 89 supervisor:

START
STATUS
STOP

It launches the supervisor as a detached Termux process and stores:

PID:
~/.companyos_runtime/production_runtime_supervisor.pid

LOG:
~/.companyos_runtime/production_runtime_supervisor.log

STATE:
~/.companyos_runtime/production_runtime_supervisor.json

The control plane itself never builds, signs, or broadcasts transactions.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase90_runtime_control_plane_bundle
mkdir -p phase90_runtime_control_plane_bundle

unzip -o ~/storage/downloads/PHASE90_RUNTIME_CONTROL_PLANE_BUNDLE.zip \
  -d ~/companyos/phase90_runtime_control_plane_bundle

python ~/companyos/phase90_runtime_control_plane_bundle/phase90_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase90_runtime_control_plane_bundle/phase90_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase90_control_plane_test.py

START DETACHED:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase90_runtime_ctl.py start --interval 15 --max-failures 5

STATUS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase90_runtime_ctl.py status

STOP:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase90_runtime_ctl.py stop

VIEW LOG:
tail -f ~/.companyos_runtime/production_runtime_supervisor.log
