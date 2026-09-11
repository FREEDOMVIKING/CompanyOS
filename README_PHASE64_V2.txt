PHASE 64 V2 — AUTHORIZATION BOUNDARY HARDENING

This bundle hardens the one-shot authorization lifecycle in:
~/companyos/companyos/liveintegration/live_orchestrator.py

It moves authorization consumption to BEFORE the live execution-gate call.

Files:
- phase64_v2_install_authorization_boundary.py
- phase64_v2_verify.py

Install:
cd ~/companyos || exit 1
python phase64_v2_install_authorization_boundary.py

Verify:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase64_v2_verify.py

The installer creates a timestamped backup, preserves the Phase 63D V2 guard,
compile-checks the patch, and writes PHASE64_V2_INSTALLED.json.
It does not itself create, sign, or broadcast any transaction.
