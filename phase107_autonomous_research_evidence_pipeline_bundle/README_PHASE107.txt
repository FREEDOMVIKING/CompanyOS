PHASE 107 — AUTONOMOUS RESEARCH + EVIDENCE PIPELINE

Builds on Phase 106.

FLOW:
opportunity
 -> research evidence records
 -> quality / relevance / confidence weighting
 -> support vs contradiction scoring
 -> assessment:
      advance
      hold
      reject_or_revise
      needs_more_research
 -> opportunity rescoring
 -> CEO can use the updated opportunity score downstream

This phase stores and evaluates evidence but does not fetch external data by itself yet.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase107_autonomous_research_evidence_pipeline_bundle
mkdir -p phase107_autonomous_research_evidence_pipeline_bundle

unzip -o ~/storage/downloads/PHASE107_AUTONOMOUS_RESEARCH_EVIDENCE_PIPELINE_BUNDLE.zip \
  -d ~/companyos/phase107_autonomous_research_evidence_pipeline_bundle

python ~/companyos/phase107_autonomous_research_evidence_pipeline_bundle/phase107_install.py

VERIFY:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase107_autonomous_research_evidence_pipeline_bundle/phase107_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase107_research_test.py
