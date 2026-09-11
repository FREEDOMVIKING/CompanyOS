import json,os,signal,time
from .engine import OpportunityEngine
RUNNING=True
def stop(*_):
    global RUNNING
    RUNNING=False
def main():
    signal.signal(signal.SIGTERM,stop)
    signal.signal(signal.SIGINT,stop)
    engine=OpportunityEngine()
    while RUNNING:
        try:
            result=engine.run_cycle()
            print(json.dumps({"timestamp":result["generated_at"],"opportunities":result["opportunity_count"]}),flush=True)
        except Exception as exc:
            print(json.dumps({"opportunity_engine_error":str(exc)}),flush=True)
        for _ in range(int(os.environ.get("COMPANYOS_OPPORTUNITY_INTERVAL","300"))):
            if not RUNNING:
                break
            time.sleep(1)
if __name__=="__main__":
    main()
