#!/usr/bin/env python3
import argparse, json
from dataclasses import asdict

from companyos.runtime.research_evidence_pipeline import ResearchEvidenceEvaluator
from companyos.runtime.opportunity_research_bridge import OpportunityResearchBridge

ap = argparse.ArgumentParser()
ap.add_argument("opportunity_id")
ap.add_argument("--apply", action="store_true")
args = ap.parse_args()

if args.apply:
    result = OpportunityResearchBridge().apply(args.opportunity_id)
else:
    result = ResearchEvidenceEvaluator().assess(args.opportunity_id)

print(json.dumps(asdict(result), indent=2))
print("PHASE107_RUNTIME_ASSESS_OPPORTUNITY: PASS")
