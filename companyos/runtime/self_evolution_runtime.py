import fcntl
import json
import os
import time

from .self_evolution_engine import EV,cycle


STATE=EV/"runtime_state.json"
LOCK=EV/"runtime.lock"


def save(d):
    t=STATE.with_suffix(".tmp")
    t.write_text(
        json.dumps(
            d,
            indent=2,
            sort_keys=True,
        )+"\n"
    )
    t.replace(STATE)


def main():
    interval=max(
        300,
        int(
            os.getenv(
                "COMPANYOS_SELF_EVOLUTION_INTERVAL_SECONDS",
                "1800",
            )
        ),
    )

    retry_interval=max(
        300,
        min(
            interval,
            int(
                os.getenv(
                    "COMPANYOS_SELF_EVOLUTION_RETRY_SECONDS",
                    "420",
                )
            ),
        ),
    )

    delay=max(
        20,
        int(
            os.getenv(
                "COMPANYOS_SELF_EVOLUTION_INITIAL_DELAY_SECONDS",
                "60",
            )
        ),
    )

    f=LOCK.open("a+")

    try:
        fcntl.flock(
            f.fileno(),
            fcntl.LOCK_EX
            | fcntl.LOCK_NB,
        )
    except BlockingIOError:
        return 2

    save({
        "running":True,
        "pid":os.getpid(),
        "interval_seconds":interval,
        "retry_seconds":retry_interval,
        "started_at":time.time(),
        "next_cycle_at":(
            time.time()+delay
        ),
    })

    time.sleep(delay)

    retry_statuses={
        "generation_failed",
        "candidate_tests_failed",
        "candidate_rejected_by_guard",
        "candidate_commit_failed",
        "exception",
    }

    while True:
        started=time.time()

        try:
            result=cycle()

            status=str(
                result.get("status") or ""
            )

            if status in retry_statuses:
                sleep_for=retry_interval
            else:
                sleep_for=interval

            row={
                "running":True,
                "pid":os.getpid(),
                "interval_seconds":interval,
                "retry_seconds":retry_interval,
                "last_cycle_started":started,
                "last_cycle_finished":time.time(),
                "last_ok":result.get("ok"),
                "last_status":status,
                "last_result_summary":{
                    "run_id":result.get("run_id"),
                    "status":status,
                    "changed_files":result.get(
                        "changed_files"
                    ),
                },
                "next_cycle_at":(
                    time.time()+sleep_for
                ),
            }

        except Exception as exc:
            sleep_for=retry_interval

            row={
                "running":True,
                "pid":os.getpid(),
                "interval_seconds":interval,
                "retry_seconds":retry_interval,
                "last_cycle_started":started,
                "last_cycle_finished":time.time(),
                "last_ok":False,
                "last_status":"exception",
                "error":(
                    f"{type(exc).__name__}: {exc}"
                ),
                "next_cycle_at":(
                    time.time()+sleep_for
                ),
            }

        save(row)
        time.sleep(sleep_for)


if __name__=="__main__":
    raise SystemExit(main())
