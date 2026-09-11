import argparse, json
from companyos.evolution.self_evolution_promotion_engine import promote, discover

ap = argparse.ArgumentParser()
ap.add_argument("--candidate")
ap.add_argument("--latest", action="store_true")
ap.add_argument("--target-rel")
ap.add_argument("--require-approval", action="store_true")
args = ap.parse_args()

candidate = args.candidate
if args.latest:
    found = discover()
    if not found:
        raise SystemExit("No generated improvements found")
    candidate = found[0]["path"]
if not candidate:
    raise SystemExit("Use --candidate PATH or --latest")

print(json.dumps(promote(candidate, args.target_rel, args.require_approval), indent=2, default=str))
