import json,signal,time
from pathlib import Path
from .engine import VentureBuilder
def main():
    running=True
    def stop(*_):
        nonlocal running; running=False
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    home=Path.home()/'companyos'
    while running:
        try: print(json.dumps(VentureBuilder(home).run(),default=str),flush=True)
        except Exception as e: print(json.dumps({'status':'error','error':str(e)}),flush=True)
        for _ in range(300):
            if not running: break
            time.sleep(1)
if __name__=='__main__': main()
