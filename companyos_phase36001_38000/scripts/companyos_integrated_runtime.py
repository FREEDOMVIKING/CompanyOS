#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from companyos.runtimeintegration import IntegratedAutonomousRuntime

def payloads():
    return {
        "discover":{"task":"Discover one bounded opportunity using available evidence."},
        "research":{"task":"Research and summarize the opportunity."},
        "select":{"task":"Select the highest-value bounded candidate."},
        "plan":{"task":"Create a milestone-based execution plan."},
        "budget":{"task":"Prepare a budget proposal only; do not move funds."},
        "build":{"task":"Build the smallest reversible internal validation artifact."},
        "test":{"task":"Test the artifact and return evidence."},
        "launch_review":{"task":"Prepare launch review only; do not externally deploy."},
        "operate":{"task":"Prepare or execute bounded internal operations work."},
        "customers":{"task":"Prepare bounded customer-success workflow without unsolicited outreach."},
        "revenue":{"task":"Prepare or update revenue tracking."},
        "accounting":{"task":"Prepare or update reconciliation/accounting records."},
        "evaluate":{"task":"Evaluate outcomes and evidence."},
        "portfolio_decision":{"task":"Recommend scale, continue, pivot, or kill."},
        "learn":{"task":"Capture reusable lessons and update internal knowledge."}
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--max-cycles", type=int, default=None)
    args = ap.parse_args()

    root = Path.home() / "companyos"
    runtime = IntegratedAutonomousRuntime(root, interval_seconds=args.interval)

    if args.once:
        result = runtime.run_once(payloads(), treasury_policy_satisfied=True)
    else:
        result = runtime.run_forever(
            payloads(),
            treasury_policy_satisfied=True,
            max_cycles=args.max_cycles
        )

    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
