PHASE 106 — AUTONOMOUS OPPORTUNITY DISCOVERY + GOAL GENERATION

Adds the internal discovery layer that can turn candidate opportunity signals into
scored, deduplicated CEO goals.

FLOW:
candidate signals
 -> persistent opportunity store
 -> scoring
 -> deduplication
 -> best opportunity selection
 -> Phase 105 policy gate
 -> Phase 103 durable goal intake
 -> Phase 104 continuous CEO runtime

IMPORTANT:
Phase 106 does NOT fetch external data by itself yet.
It accepts candidate signals from future connectors/agents and keeps the
policy boundary intact.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase106_autonomous_opportunity_discovery_bundle
mkdir -p phase106_autonomous_opportunity_discovery_bundle

unzip -o ~/storage/downloads/PHASE106_AUTONOMOUS_OPPORTUNITY_DISCOVERY_BUNDLE.zip \
  -d ~/companyos/phase106_autonomous_opportunity_discovery_bundle

python ~/companyos/phase106_autonomous_opportunity_discovery_bundle/phase106_install.py

VERIFY:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase106_autonomous_opportunity_discovery_bundle/phase106_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase106_opportunity_test.py

OPTIONAL INTERNAL DEMO SEED:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase106_runtime_seed_demo.py

STATUS:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase106_opportunity_status.py
