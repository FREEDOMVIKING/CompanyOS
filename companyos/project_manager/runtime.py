import json, signal, time
from pathlib import Path
from .engine import ProjectManager
RUNNING=True
def stop(*_):
    global RUNNING
    RUNNING=False
def main():
    signal.signal(signal.SIGTERM,stop)
    signal.signal(signal.SIGINT,stop)
    engine=ProjectManager(Path.home()/"companyos")
    while RUNNING:
        try:
            print(json.dumps(engine.run()),flush=True)
        except Exception as exc:
            print(json.dumps({"error":str(exc),"service":"project_manager"}),flush=True)
        for _ in range(120):
            if not RUNNING:
                break
            time.sleep(1)
if __name__=="__main__":
    main()
