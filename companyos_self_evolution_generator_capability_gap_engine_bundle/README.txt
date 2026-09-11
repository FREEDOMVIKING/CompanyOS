COMPANYOS SELF-EVOLUTION GENERATOR + CAPABILITY GAP ENGINE

Flow:
runtime evidence -> detect capability gaps -> generate targeted extension module + test -> watched generated_improvements directory -> sandbox/promotion engine -> safe promote or rollback.

INSTALL
cd ~/companyos || exit 1
rm -rf companyos_self_evolution_generator_capability_gap_engine_bundle
mkdir -p companyos_self_evolution_generator_capability_gap_engine_bundle
unzip -o ~/storage/downloads/COMPANYOS_SELF_EVOLUTION_GENERATOR_CAPABILITY_GAP_ENGINE_BUNDLE.zip -d ~/companyos/companyos_self_evolution_generator_capability_gap_engine_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_self_evolution_generator_capability_gap_engine_bundle/install.py
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_self_evolution_generator_capability_gap_engine_bundle/verify.py

RUN ONE FULL CYCLE
bash scripts/companyos_self_evolution_generator.sh once

START CONTINUOUSLY
bash scripts/companyos_self_evolution_generator.sh start

STATUS
bash scripts/companyos_self_evolution_generator.sh status
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_self_evolution_generator_status.py
