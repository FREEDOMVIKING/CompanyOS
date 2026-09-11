from .stress_plan import StressPlan
from .end_to_end_harness import EndToEndHarness

class StressRunner:
    """734: bounded repeated integration cycles."""

    def __init__(self, root):
        self.root=root

    def run(self, rounds=3):
        plan=StressPlan().build(rounds)
        results=[]
        for i in range(plan["rounds"]):
            results.append(EndToEndHarness(self.root).run(seed=f"round-{i+1}"))
        return {
            "success":all(r.get("success") for r in results),
            "status":"bounded_stress_complete",
            "plan":plan,
            "results":results,
        }
