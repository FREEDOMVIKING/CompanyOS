COMPANYOS PHASE 337-352
AUTONOMOUS RESEARCH NETWORK + CEO DECISION INPUT

337 starter source network template
338 source policy
339 fallback manager
340 freshness filter
341 evidence-quality gate
342 problem clustering
343 market-gap detection
344 competitor pressure
345 evidence-backed opportunity builder
346 confidence engine
347 validation router
348 CEO decision packet
349 research scheduling policy
350 network health
351 autonomous live research cycle
352 runtime/status

IMPORTANT:
The starter source registry is safe by default: placeholder sources are DISABLED.
This avoids pretending arbitrary public endpoints are configured or stable.
Replace placeholders with actual public RSS/Atom/JSON/text sources and enable them.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase337_352_autonomous_research_network.zip .
unzip -o companyos_phase337_352_autonomous_research_network.zip
bash companyos_phase337_352_autonomous_research_network/install.sh ~/companyos

EXPECTED:
phase337_352_verification_passed
phase352_autonomous_research_network_ready
3 passed
PHASE337_352_INSTALL_OK
AUTONOMOUS_RESEARCH_NETWORK=READY
CEO_DECISION_INPUT=READY

SHOW CURRENT SOURCES:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/configure_research_sources.py show

RUN AFTER REAL SOURCES ARE CONFIGURED:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_autonomous_research_cycle.py
