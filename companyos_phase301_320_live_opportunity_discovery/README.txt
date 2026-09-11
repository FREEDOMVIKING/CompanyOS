COMPANYOS PHASE 301-320
LIVE OPPORTUNITY DISCOVERY ENGINE

301 canonical source contract
302 pluggable research configuration
303 persistent evidence store
304 signal normalization
305 evidence deduplication
306 problem/pain mining
307 market/theme mapping
308 competitor/pricing signal analysis
309 repeated trend detection
310 opportunity synthesis
311 economic opportunity ranking (reuses Phase 293-300)
312 autonomous research planner
313 durable validation queue
314 discovery memory
315 research ingestion pipeline
316 source health
317 optional OpenRouter-assisted synthesis over supplied evidence
318 CEO discovery loop
319 persistent discovery orchestrator
320 discovery runtime/status

IMPORTANT:
This bundle provides the discovery engine and pluggable live-source architecture.
It does NOT pretend the local Termux process has a search provider automatically.
Live web/source connectors are configured in later phases or through configured
provider/source adapters. The included demo uses sample evidence only.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase301_320_live_opportunity_discovery.zip .
unzip -o companyos_phase301_320_live_opportunity_discovery.zip
bash companyos_phase301_320_live_opportunity_discovery/install.sh ~/companyos

EXPECTED:
phase301_320_verification_passed
phase320_live_opportunity_discovery_ready
3 passed
PHASE301_320_INSTALL_OK
LIVE_OPPORTUNITY_DISCOVERY_ENGINE=READY
CEO_DISCOVERY_LOOP=READY

DEMO:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/opportunity_discovery_demo.py
