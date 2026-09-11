COMPANYOS PHASE 369-384
OPPORTUNITY INTELLIGENCE + MARKET THESIS

369 noise rejection
370 semantic clustering
371 cross-source agreement
372 customer identification
373 pain severity
374 problem frequency
375 willingness-to-pay reasoning
376 replacement analysis
377 business-model generation
378 startup effort estimate
379 time-to-revenue estimate
380 descriptive opportunity naming
381 market-thesis generation
382 CEO investment decision
383 opportunity-intelligence cycle
384 runtime/status

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase369_384_opportunity_intelligence_market_thesis.zip .
unzip -o companyos_phase369_384_opportunity_intelligence_market_thesis.zip
bash companyos_phase369_384_opportunity_intelligence_market_thesis/install.sh ~/companyos

EXPECTED:
phase369_384_verification_passed
phase384_opportunity_intelligence_market_thesis_ready
3 passed
PHASE369_384_INSTALL_OK
OPPORTUNITY_INTELLIGENCE=READY
MARKET_THESIS_ENGINE=READY
CEO_INVESTMENT_DECISIONS=READY

RUN AGAINST COLLECTED PUBLIC EVIDENCE:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_opportunity_intelligence.py

This layer is intentionally evidence-driven. It does not automatically spend money,
launch products, or perform irreversible external actions.
