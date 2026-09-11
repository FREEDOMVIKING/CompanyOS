import time
from datetime import datetime, timezone
from .tick_runner import TickRunner
from .idle_policy import IdlePolicy
from .backoff_policy import BackoffPolicy
from .crash_recovery import CrashRecovery

class ServiceLoop:
    """558: bounded continuous autonomous CEO loop."""

    def __init__(self, root, config, state_store, journal):
        self.root = root
        self.config = config
        self.state_store = state_store
        self.journal = journal
        self.runner = TickRunner(root, config["quality_cycle_every_ticks"])

    def run(self, max_ticks=None):
        state = self.state_store.load()
        state["running"] = True
        self.state_store.save(state)

        results = []
        count = 0

        while True:
            if max_ticks is not None and count >= int(max_ticks):
                break

            count += 1
            tick_number = int(state.get("ticks",0)) + 1
            try:
                result = self.runner.run(tick_number)
                results.append(result)

                state["ticks"] = tick_number
                state["last_status"] = result.get("status")
                state["last_tick_at"] = datetime.now(timezone.utc).isoformat()

                if result.get("success"):
                    state["consecutive_failures"] = 0
                else:
                    state["consecutive_failures"] = int(state.get("consecutive_failures",0)) + 1

                self.state_store.save(state)
                self.journal.append("tick_complete", {
                    "tick":tick_number,
                    "success":bool(result.get("success")),
                })

                recovery = CrashRecovery().decide(
                    state["consecutive_failures"],
                    self.config["max_consecutive_failures"],
                )
                if recovery["action"] == "halt_for_review":
                    break

                idle = IdlePolicy().evaluate(result)
                if max_ticks is None:
                    if idle["idle"]:
                        time.sleep(self.config["idle_sleep_seconds"])
                    else:
                        time.sleep(self.config["tick_interval_seconds"])

            except KeyboardInterrupt:
                self.journal.append("service_interrupted", {"tick":tick_number})
                break
            except Exception as exc:
                state["consecutive_failures"] = int(state.get("consecutive_failures",0)) + 1
                state["last_status"] = f"error:{type(exc).__name__}"
                state["last_tick_at"] = datetime.now(timezone.utc).isoformat()
                self.state_store.save(state)
                self.journal.append("tick_exception", {
                    "tick":tick_number,
                    "error":f"{type(exc).__name__}:{exc}",
                })
                recovery = CrashRecovery().decide(
                    state["consecutive_failures"],
                    self.config["max_consecutive_failures"],
                )
                if recovery["action"] == "halt_for_review":
                    break
                if max_ticks is None:
                    time.sleep(BackoffPolicy().delay(state["consecutive_failures"]))

        state["running"] = False
        self.state_store.save(state)
        return {
            "success":True,
            "status":"ceo_service_loop_stopped",
            "ticks_run":len(results),
            "results":results,
            "state":state,
        }
