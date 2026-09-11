from .ceo_state import CEOState
from .ceo_cycle import CEOCycle
from .decision_journal import DecisionJournal
from .cycle_budget import CycleBudget

class PersistentCEO:
    """479: persistent bounded CEO loop across multiple cycles."""

    def __init__(self, root):
        self.state_store = CEOState(root)
        self.cycle = CEOCycle(root)
        self.journal = DecisionJournal(root)
        self.budget = CycleBudget()

    def run(self, cycles=None, context=None):
        state = self.state_store.load()
        max_cycles = cycles or self.budget.limits()["max_cycles_per_run"]
        results = []

        for idx in range(1, int(max_cycles)+1):
            start = state.get("current_stage") or "opportunity"
            print(f"[CompanyOS CEO] cycle {idx}/{max_cycles} start={start}", flush=True)

            result = self.cycle.run(start_stage=start, context=context)
            results.append(result)

            for item in result.get("history",[]):
                self.journal.append(item.get("stage"), item)

            state["cycles_completed"] = int(state.get("cycles_completed",0)) + 1
            state["current_stage"] = result.get("end_stage") or "opportunity"
            state["last_status"] = result.get("status")
            state["last_success"] = bool(result.get("success"))
            if result.get("context",{}).get("venture_id"):
                state["active_venture_id"] = result["context"]["venture_id"]
            self.state_store.save(state)

            print(
                f"[CompanyOS CEO] cycle {idx}/{max_cycles} "
                f"{'SUCCESS' if result.get('success') else 'FAILED'} "
                f"end={state['current_stage']}",
                flush=True,
            )

            if result.get("end_stage") in ("validation","operations") and result.get("history",[]):
                last = result["history"][-1]
                if last.get("status") in ("validation_plan_ready","operations_waiting_for_metrics"):
                    break

        return {
            "success":all(bool(x.get("success")) for x in results) if results else False,
            "status":"persistent_ceo_run_completed",
            "cycles":results,
            "state":state,
        }
