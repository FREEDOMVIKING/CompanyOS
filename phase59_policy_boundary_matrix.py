from pathlib import Path
import json

from companyos.liveintegration.live_orchestrator import FinalLiveExecutionOrchestrator
from companyos.walletsource.identity_loader import VerifiedWalletIdentity

root = Path.home() / "companyos"

print("===== PHASE 59: POLICY BOUNDARY MATRIX =====")

identity = VerifiedWalletIdentity(root).load()
assert identity.get("success") is True, identity
destination = identity.get("public_address")
assert destination, "VERIFIED_PUBLIC_ADDRESS_MISSING"

orch = FinalLiveExecutionOrchestrator(root)
controller = getattr(orch.execgate, "controller", None)
assert controller is not None, "SPEND_CONTROLLER_MISSING"
policy = getattr(controller, "policy", None)
assert policy is not None, "TREASURY_POLICY_MISSING"

reserve = float(getattr(policy, "reserve_floor", 0.0))
single = float(getattr(policy, "autonomous_single_tx_limit", 0.0))
daily = float(getattr(policy, "autonomous_daily_limit", 0.0))

# Synthetic balances only. No execution/signing/broadcast path is called.
safe_balance = reserve + max(single, 1.0) + 10.0
tiny = min(max(single / 1000.0, 0.000001), 0.001)

scenarios = [
    {
        "name": "ALLOWLISTED_SMALL_AMOUNT",
        "amount": tiny,
        "balance": safe_balance,
        "destination": destination,
        "daily_loss": 0.0,
        "expect_destination_allowed": True,
    },
    {
        "name": "UNKNOWN_DESTINATION",
        "amount": tiny,
        "balance": safe_balance,
        "destination": "TEST_DESTINATION_NOT_ALLOWLISTED",
        "daily_loss": 0.0,
        "expect_destination_allowed": False,
    },
    {
        "name": "NON_POSITIVE_AMOUNT",
        "amount": 0.0,
        "balance": safe_balance,
        "destination": destination,
        "daily_loss": 0.0,
        "expect_allowed": False,
    },
    {
        "name": "OVER_SINGLE_LIMIT",
        "amount": single + max(1.0, single * 0.01),
        "balance": reserve + single + max(100.0, single),
        "destination": destination,
        "daily_loss": 0.0,
        "expect_allowed": False,
    },
    {
        "name": "RESERVE_FLOOR_VIOLATION",
        "amount": max(tiny, 0.001),
        "balance": reserve,
        "destination": destination,
        "daily_loss": 0.0,
        "expect_allowed": False,
    },
]

results = []
failed = []

for s in scenarios:
    result = controller.authorize(
        amount=s["amount"],
        balance=s["balance"],
        destination=s["destination"],
        allowlist=orch.allowlist,
        daily_loss=s["daily_loss"],
        purpose="phase59_policy_boundary_test",
    )

    item = {
        "scenario": s["name"],
        "input": {
            "amount": s["amount"],
            "balance": s["balance"],
            "destination": s["destination"],
            "daily_loss": s["daily_loss"],
        },
        "result": result,
    }

    checks = result.get("risk", {}).get("checks", {})
    passed = True

    if "expect_allowed" in s:
        passed = bool(result.get("allowed")) is s["expect_allowed"]

    if "expect_destination_allowed" in s:
        passed = (
            checks.get("destination_allowed")
            is s["expect_destination_allowed"]
        )

    item["passed"] = passed
    results.append(item)

    print(f"{s['name']}: {'PASS' if passed else 'FAIL'}")
    print(json.dumps(result, indent=2, default=str))

    if not passed:
        failed.append(s["name"])

postlock = orch.postlock.status()

summary = {
    "success": not failed,
    "failed_scenarios": failed,
    "policy": {
        "reserve_floor": reserve,
        "autonomous_single_tx_limit": single,
        "autonomous_daily_limit": daily,
        "require_allowlist": getattr(policy, "require_allowlist", None),
        "allow_autonomous_transfers": getattr(
            policy, "allow_autonomous_transfers", None
        ),
    },
    "results": results,
    "postlock": postlock,
}

print("\n===== SUMMARY =====")
print(json.dumps(summary, indent=2, default=str))

print("\n======================================")
print(
    "PHASE59_POLICY_BOUNDARY_MATRIX:",
    "PASS" if not failed else "REVIEW_REQUIRED",
)
print("======================================")
print("SCENARIOS_TESTED:", len(results))
print("ALL_BOUNDARIES_BEHAVED_AS_EXPECTED:", not failed)
print("ALLOWLIST_PRESERVED:", destination in orch.allowlist)
print("POSTLOCK_CLEAR:", not bool(postlock.get("locked", False)))
print("REAL_AUTH_CREATED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("BROADCAST_ATTEMPTED: False")

raise SystemExit(0 if not failed else 2)
