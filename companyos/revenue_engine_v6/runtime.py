import json
import signal
import time
from pathlib import Path
from .engine import RevenueEngineV6

def main():
    running = True
    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    home = Path.home() / "companyos"

    while running:
        try:
            result = RevenueEngineV6(home).run()
            print(json.dumps({
                "service": "revenue_engine_v6_140001_165000",
                "status": result.get("status"),
            }), flush=True)
        except Exception as exc:
            print(json.dumps({
                "service": "revenue_engine_v6_140001_165000",
                "status": "error",
                "error": str(exc),
            }), flush=True)

        for _ in range(1800):
            if not running:
                break
            time.sleep(1)

if __name__ == "__main__":
    main()
