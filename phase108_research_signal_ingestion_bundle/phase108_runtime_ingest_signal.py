#!/usr/bin/env python3
import argparse, json
from dataclasses import asdict

from companyos.runtime.research_signal_pipeline import ResearchSignalPipeline

ap = argparse.ArgumentParser()
ap.add_argument("opportunity_id")
ap.add_argument("title")
ap.add_argument("content")
ap.add_argument("--source-type", default="research")
ap.add_argument("--source-name", default="manual_signal")
ap.add_argument("--url-or-ref", default="")
ap.add_argument("--source-quality", type=float, default=0.5)
ap.add_argument("--relevance", type=float, default=0.5)
args = ap.parse_args()

result = ResearchSignalPipeline().process(
    opportunity_id=args.opportunity_id,
    source_type=args.source_type,
    source_name=args.source_name,
    title=args.title,
    content=args.content,
    url_or_ref=args.url_or_ref,
    source_quality=args.source_quality,
    relevance_hint=args.relevance,
)

print(json.dumps(asdict(result), indent=2))
print("PHASE108_RUNTIME_INGEST_SIGNAL: PASS")
