#!/usr/bin/env python3
from pathlib import Path

root = Path.home() / "companyos"
candidates = [
    root / "companyos_phase285_292" / "persistent_improver.py",
    root / "src" / "companyos_phase285_292" / "persistent_improver.py",
]
target = next((p for p in candidates if p.exists()), None)
if target is None:
    raise SystemExit("ERROR: persistent_improver.py not found")

text = target.read_text(encoding="utf-8")
start = text.find("class PersistentImprover:")
if start == -1:
    raise SystemExit("ERROR: PersistentImprover class not found")

prefix = text[:start]

replacement = """class PersistentImprover:
    \\\"\\\"\\\"Persistent improvement with exactly one autonomous cycle per requested round.\\\"\\\"\\\"

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.supervisor = ContinuousSupervisor(self.root)
        self.failures = FailureTracker(self.root)
        self.state_store = ImprovementStateStore(self.root)
        self.journal = CycleJournal(self.root)
        self.pause_policy = PausePolicy()
        self.scheduler = AdaptiveScheduler()

    def run(self, max_rounds=1, sleep_between=False):
        import os, time

        state = self.state_store.load()
        rounds = []
        total = max(1, int(max_rounds))
        old_cycles = os.environ.get("COMPANYOS_MAX_CYCLES_PER_RUN")
        os.environ["COMPANYOS_MAX_CYCLES_PER_RUN"] = "1"

        try:
            for idx in range(1, total + 1):
                print(f"[CompanyOS] round {idx}/{total}: starting", flush=True)

                pause = self.pause_policy.evaluate(
                    state,
                    self.failures.state(),
                    max_failures=3,
                )
                if pause["pause"]:
                    print(f"[CompanyOS] round {idx}/{total}: paused ({pause['reason']})", flush=True)
                    self.journal.append("paused", pause)
                    return {
                        "success": False,
                        "status": "persistent_improvement_paused",
                        "reason": pause["reason"],
                        "rounds": rounds,
                        "state": state,
                    }

                self.journal.append("round_started", {"round": idx})
                result = self.supervisor.run()
                rounds.append(result)

                state["cycles_completed"] = int(state.get("cycles_completed", 0)) + 1
                state["last_status"] = result.get("status")
                state["last_success"] = bool(result.get("success"))

                try:
                    cycles = result.get("cycles") or []
                    if cycles:
                        proposal = cycles[-1]["result"].get("proposal") or {}
                        state["last_capability"] = proposal.get("improvement")
                except Exception:
                    pass

                self.state_store.save(state)
                self.journal.append("round_completed", {
                    "round": idx,
                    "success": bool(result.get("success")),
                    "status": result.get("status"),
                })

                print(
                    f"[CompanyOS] round {idx}/{total}: "
                    f"{'SUCCESS' if result.get('success') else 'FAILED'} "
                    f"({result.get('status')})",
                    flush=True,
                )

                if sleep_between and idx < total:
                    delay = self.scheduler.next_delay(bool(result.get("success")))
                    print(f"[CompanyOS] cooldown: {delay}s", flush=True)
                    time.sleep(delay)

            return {
                "success": all(bool(x.get("success")) for x in rounds),
                "status": "persistent_improvement_run_completed",
                "rounds": rounds,
                "state": state,
                "requested_rounds": total,
                "actual_autonomous_cycles": len(rounds),
            }
        finally:
            if old_cycles is None:
                os.environ.pop("COMPANYOS_MAX_CYCLES_PER_RUN", None)
            else:
                os.environ["COMPANYOS_MAX_CYCLES_PER_RUN"] = old_cycles
"""
target.write_text(prefix + replacement + "\n", encoding="utf-8")
print("PATCHED_PERSISTENT_ROUND_FLATTENING:", target)
