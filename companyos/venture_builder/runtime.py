import json,os,signal,time
from .engine import VentureBuilderEngine
RUNNING=True
def stop(*_):
    global RUNNING;RUNNING=False
def main():
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);e=VentureBuilderEngine()
    while RUNNING:
        try:print(json.dumps(e.health()),flush=True)
        except Exception as x:print(json.dumps({"venture_builder_error":str(x)}),flush=True)
        for _ in range(int(os.environ.get("COMPANYOS_VENTURE_BUILDER_INTERVAL","300"))):
            if not RUNNING:break
            time.sleep(1)
if __name__=="__main__":main()
