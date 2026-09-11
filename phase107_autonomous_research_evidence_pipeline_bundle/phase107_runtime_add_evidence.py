#!/usr/bin/env python3
import argparse, json
from dataclasses import asdict

from companyos.runtime.research_evidence_pipeline import ResearchEvidenceStore

ap = argparse.ArgumentParser()
ap.add_argument("opportunity_id")
ap.add_argument("claim")
ap.add_argument("--source", default="manual_research")
ap.add_argument("--direction", choices=["support","contradict","neutral"], default="neutral")
ap.add_argument("--confidence", type=float, default=0.5)
ap.add_argument("--quality", type=float, default=0.5)
ap.add_argument("--relevance", type=float, default=0.5)
args = ap.parse_args()

record = ResearchEvidenceStore().add(
    opportunity_id=args.opportunity_id,
    source=args.source,
    claim=args.claim,
    direction=args.direction,
    confidence=args.confidence,
    quality=args.quality,
    relevance=args.relevance,
)

print(json.dumps(asdict(record), indent=2))
print("PHASE107_RUNTIME_ADD_EVIDENCE: PASS")
