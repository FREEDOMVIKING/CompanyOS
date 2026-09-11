import json,signal,time
from pathlib import Path
from .engine import DashboardV2
RUNNING=True
def stop(*_):
 global RUNNING;RUNNING=False
def main():
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);e=DashboardV2(Path.home()/"companyos")
 while RUNNING:
  try:print(json.dumps(e.snapshot()),flush=True)
  except Exception as x:print(json.dumps({"dashboard_v2_error":str(x)}),flush=True)
  for _ in range(60):
   if not RUNNING:break
   time.sleep(1)
if __name__=="__main__":main()
