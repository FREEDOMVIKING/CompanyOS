COMPANYOS SELF-EVOLUTION PROMOTION ENGINE

Purpose
-------
Close the loop:
weakness -> generated code -> sandbox -> tests -> promotion -> live health check -> keep/rollback -> ledger

Safety model
------------
- Generated improvements are staged in an isolated sandbox.
- Python compile/import tests run before promotion.
- Local pytest tests are discovered and run when present.
- Failed candidates are rejected.
- Post-promotion health is checked.
- Failed live promotions are rolled back.
- Core CompanyOS files are NOT overwritten by default.
- Default promotion target is companyos/evolution_promoted/.
- Explicit core targeting requires --target-rel.
- --require-approval records AWAITING_APPROVAL without writing live.

INSTALL
-------
cd ~/companyos || exit 1
rm -rf companyos_self_evolution_promotion_engine_bundle
mkdir -p companyos_self_evolution_promotion_engine_bundle
unzip -o ~/storage/downloads/COMPANYOS_SELF_EVOLUTION_PROMOTION_ENGINE_BUNDLE.zip -d ~/companyos/companyos_self_evolution_promotion_engine_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_self_evolution_promotion_engine_bundle/install.py
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_self_evolution_promotion_engine_bundle/verify.py

CHECK GENERATED IMPROVEMENTS
----------------------------
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_self_evolution_status.py

SAFE PROMOTION OF LATEST GENERATED MODULE
-----------------------------------------
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_self_evolution_promote.py --latest

EXPLICIT TARGET IN APPROVAL-ONLY MODE
-------------------------------------
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_self_evolution_promote.py --candidate PATH --target-rel companyos/path/to/target.py --require-approval

DASHBOARD SNAPSHOT
------------------
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_self_evolution_dashboard_snapshot.py
