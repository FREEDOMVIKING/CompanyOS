COMPANYOS PHASE 321-336
LIVE RESEARCH CONNECTORS

321 source registry
322 bounded HTTP client
323 RSS/Atom source
324 JSON API source
325 HTML/text page source
326 source router
327 fetch budgets
328 provenance
329 live collector
330 query expansion
331 evidence quality
332 source priority scheduler
333 connector health
334 live research cycle
335 CEO research bridge
336 runtime/status

This connects the Phase 301-320 opportunity engine to ACTUAL CONFIGURED
HTTP/RSS/JSON/text sources.

It intentionally does not hardcode private API keys or pretend arbitrary web
search exists without a provider.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase321_336_live_research_connectors.zip .
unzip -o companyos_phase321_336_live_research_connectors.zip
bash companyos_phase321_336_live_research_connectors/install.sh ~/companyos

EXPECTED:
phase321_336_verification_passed
phase336_live_research_connectors_ready
3 passed
PHASE321_336_INSTALL_OK
LIVE_RESEARCH_CONNECTORS=READY
CEO_DISCOVERY_BRIDGE=READY

SHOW CONFIG:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/configure_research_sources.py show

EXAMPLE CONFIG:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/configure_research_sources.py example

LIVE RUN AFTER SOURCES ARE CONFIGURED:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_live_research_cycle.py
