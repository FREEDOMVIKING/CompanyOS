class CapitalAllocator:
    def allocate(self, plans, available_capital, reserve_floor):
        available = max(0.0, float(available_capital) - float(reserve_floor))
        ranked = sorted(
            plans,
            key=lambda x: (
                x.get("evaluation", {}).get("net_expected_value", 0),
                x.get("evaluation", {}).get("expected_gain", 0),
            ),
            reverse=True,
        )

        allocations = []
        remaining = available
        for item in ranked:
            plan = item["plan"]
            required = float(plan.get("required_capital", 0) or 0)
            approved = min(required, remaining) if item["evaluation"].get("positive_ev") else 0.0
            allocations.append({
                "plan": plan,
                "evaluation": item["evaluation"],
                "allocated_capital": round(approved, 8),
            })
            remaining -= approved
            if remaining <= 0:
                remaining = 0.0

        return {
            "available_for_allocation": round(available, 8),
            "remaining_unallocated": round(remaining, 8),
            "allocations": allocations,
        }
