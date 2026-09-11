import argparse, json, os, signal, time
from pathlib import Path
from .core import *
RUNNING=True
def stop(*_):
    global RUNNING
    RUNNING=False

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--role",required=True)
    parser.add_argument("--once",action="store_true")
    args=parser.parse_args()
    signal.signal(signal.SIGTERM,stop)
    signal.signal(signal.SIGINT,stop)
    home=Path(os.environ.get("COMPANYOS_HOME",str(Path.home()/"companyos")))
    mapping={
        "research":research_snapshot,
        "revenue":revenue_snapshot,
        "marketing":marketing_snapshot,
        "acquisition":acquisition_snapshot,
        "portfolio":portfolio_snapshot,
        "improvement":improvement_snapshot,
    }
    fn=mapping[args.role]
    out=home/"companyos_runtime"/"growth_suite"
    out.mkdir(parents=True,exist_ok=True)
    def run():
        result=fn(home)
        write_json(out/(args.role+".json"),result)
        print(json.dumps(result),flush=True)
    if args.once:
        run()
        return
    while RUNNING:
        try:run()
        except Exception as exc:print(json.dumps({"growth_suite_error":str(exc),"role":args.role}),flush=True)
        for _ in range(int(os.environ.get("COMPANYOS_GROWTH_INTERVAL","120"))):
            if not RUNNING:break
            time.sleep(1)
if __name__=="__main__":
    main()
