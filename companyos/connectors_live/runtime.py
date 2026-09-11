import argparse,json,os,signal,time
from .engine import ConnectorEngine
RUNNING=True
def stop(_s,_f):
    global RUNNING
    RUNNING=False
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--once',action='store_true')
    p.add_argument('--interval',type=int,default=int(os.environ.get('COMPANYOS_CONNECTOR_INTERVAL','60')))
    a=p.parse_args()
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    e=ConnectorEngine()
    if a.once:
        print(json.dumps(e.health(),indent=2));return
    while RUNNING:
        try:
            r=e.health()
            print(json.dumps({'timestamp':r['generated_at'],'configured':r['configured_count'],'enabled':r['enabled_count']}),flush=True)
        except Exception as exc:
            print(json.dumps({'connector_runtime_error':str(exc)}),flush=True)
        for _ in range(max(1,a.interval)):
            if not RUNNING:break
            time.sleep(1)
if __name__=='__main__':
    main()
