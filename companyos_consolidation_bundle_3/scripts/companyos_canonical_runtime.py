#!/usr/bin/env python3
from __future__ import annotations
import argparse, json

from companyos.canonicalruntime import UnifiedCEOCanonicalBridge

def main():
    ap = argparse.ArgumentParser(description="CompanyOS Canonical Runtime Bridge")
    sub = ap.add_subparsers(dest="command", required=True)

    sub.add_parser("status")

    p_goal = sub.add_parser("submit-goal")
    p_goal.add_argument("--objective", required=True)
    p_goal.add_argument("--context-json", default="{}")

    p_opp = sub.add_parser("submit-opportunity")
    p_opp.add_argument("--title", required=True)
    p_opp.add_argument("--hypothesis", default="")
    p_opp.add_argument("--evidence-json", default="{}")

    p_res = sub.add_parser("submit-research")
    p_res.add_argument("--question", required=True)
    p_res.add_argument("--findings-json", default="{}")

    args = ap.parse_args()
    bridge = UnifiedCEOCanonicalBridge()

    if args.command == "status":
        out = bridge.status()

    elif args.command == "submit-goal":
        out = bridge.submit_ceo_goal(
            args.objective,
            json.loads(args.context_json),
        )

    elif args.command == "submit-opportunity":
        out = bridge.submit_opportunity(
            args.title,
            hypothesis=args.hypothesis,
            evidence=json.loads(args.evidence_json),
        )

    else:
        out = bridge.submit_research_result(
            args.question,
            findings=json.loads(args.findings_json),
        )

    print(json.dumps(out, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
