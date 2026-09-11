import argparse, json, os, signal, time
from .engine import ExpansionEngine

RUNNING = True
def stop(_s,_f):
    global RUNNING
    RUNNING = False

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--interval", type=int, default=int(os.environ.get("COMPANYOS_EXPANSION_INTERVAL","60")))
    a = p.parse_args()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    engine = ExpansionEngine()

    if a.demo:
        print(json.dumps(engine.execute_internal_demo(), indent=2))
        return
    if a.once:
        print(json.dumps(engine.run_cycle(), indent=2))
        return

    while RUNNING:
        try:
            r = engine.run_cycle()
            print(json.dumps({
                "timestamp": r["generated_at"],
                "capabilities": r["capability_count"],
                "queued_actions": r["queued_actions"],
            }), flush=True)
        except Exception as e:
            print(json.dumps({"expansion_error": str(e)}), flush=True)
        for _ in range(max(1, a.interval)):
            if not RUNNING:
                break
            time.sleep(1)

if __name__ == "__main__":
    main()
