from pathlib import Path
import py_compile

ROOT = Path.home() / "companyos"
files = [
    ROOT / "companyos/governance/venture_identity_resolver.py",
    ROOT / "companyos/runtime/stalled_stage_progression_controller.py",
    ROOT / "companyos/runtime/productive_autonomy_watchdog.py",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
    py_compile.compile(str(p), doraise=True)

from companyos.governance.venture_identity_resolver import canonical_id
tests = {
    "local_contractor_bid_organizer": "local_contractor_bid_organizer",
    "local_contractor_bid_organizer_v1": "local_contractor_bid_organizer",
    "local-contractor-bid-organizer-v2": "local_contractor_bid_organizer",
}
for raw, expected in tests.items():
    got = canonical_id(raw)
    print(raw, "=>", got)
    if got != expected:
        raise SystemExit("CANONICALIZATION_TEST_FAIL")

print("STALLED_STAGE_PROGRESSION_VERIFY: PASS")
