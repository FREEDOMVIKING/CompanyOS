import json
import signal
import time
from pathlib import Path
from .engine import ProductPortfolioEngineV7

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
            result = ProductPortfolioEngineV7(home).run()
            print(json.dumps({
                "service": "product_portfolio_v7_165001_190000",
                "status": result.get("status"),
                "portfolio_size": result.get("portfolio_size"),
            }), flush=True)
        except Exception as exc:
            print(json.dumps({
                "service": "product_portfolio_v7_165001_190000",
                "status": "error",
                "error": str(exc),
            }), flush=True)

        for _ in range(3600):
            if not running:
                break
            time.sleep(1)

if __name__ == "__main__":
    main()
