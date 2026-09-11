import json, signal, time
from pathlib import Path
from .engine import FinancialForecasting
RUNNING=True
def stop(*_):
    global RUNNING
    RUNNING=False
def main():
    signal.signal(signal.SIGTERM,stop)
    signal.signal(signal.SIGINT,stop)
    engine=FinancialForecasting(Path.home()/"companyos")
    while RUNNING:
        try:
            print(json.dumps(engine.run()),flush=True)
        except Exception as exc:
            print(json.dumps({"error":str(exc),"service":"financial_forecasting"}),flush=True)
        for _ in range(180):
            if not RUNNING:
                break
            time.sleep(1)
if __name__=="__main__":
    main()
