import argparse, json
from pathlib import Path
from companyos.launch.autonomous_domain_web_launch import launch_venture, load

ap = argparse.ArgumentParser()
ap.add_argument("venture_json")
ap.add_argument("--allow-domain-purchase", action="store_true")
args = ap.parse_args()

venture = load(Path(args.venture_json), {})
if not venture:
    raise SystemExit("FAIL: venture JSON unreadable")

print(json.dumps(
    launch_venture(venture, allow_domain_purchase=args.allow_domain_purchase),
    indent=2,
    default=str
))
