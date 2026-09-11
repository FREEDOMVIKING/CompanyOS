import json,os,signal,time
from .engine import APIBackboneEngine
RUNNING=True
def stop(*_):
 global RUNNING;RUNNING=False
def main():
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);e=APIBackboneEngine()
 while RUNNING:
  try:
   r=e.health();print(json.dumps({'timestamp':r['generated_at'],'profiles':r['profile_count']}),flush=True)
  except Exception as x:print(json.dumps({'api_backbone_error':str(x)}),flush=True)
  for _ in range(int(os.environ.get('COMPANYOS_API_BACKBONE_INTERVAL','30'))):
   if not RUNNING:break
   time.sleep(1)
if __name__=='__main__':main()
