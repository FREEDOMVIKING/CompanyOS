import json,signal,time
from pathlib import Path
from .engine import SalesEngine
RUNNING=True
def stop(*_):
 global RUNNING;RUNNING=False
def main():
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);e=SalesEngine(Path.home()/"companyos")
 while RUNNING:
  try:print(json.dumps(e.run()),flush=True)
  except Exception as x:print(json.dumps({"sales_engine_error":str(x)}),flush=True)
  for _ in range(300):
   if not RUNNING:break
   time.sleep(1)
if __name__=="__main__":main()
