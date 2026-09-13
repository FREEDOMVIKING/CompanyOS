from __future__ import annotations
import json,os,time
from pathlib import Path
from companyos.runtime.profit_opportunity_engine import dispatch
from companyos.runtime.candidate_enrichment_bridge import refresh_enrichments
RT=Path.home()/"companyos/.companyos_runtime"; STATE=RT/"profit_opportunity_runtime_state.json"
def run():
 interval=max(60,int(os.getenv("COMPANYOS_PROFIT_ENGINE_INTERVAL_SECONDS","300")))
 while not (RT/"STOP_CONTINUOUS").exists():
  try:x={"running":True,"healthy":True,"last_cycle_unix":time.time(),"enrichment":refresh_enrichments(),"result":dispatch()}
  except Exception as e:x={"running":True,"healthy":False,"last_cycle_unix":time.time(),"error":repr(e)}
  STATE.write_text(json.dumps(x,indent=2,sort_keys=True,default=str));time.sleep(interval)
if __name__=="__main__":run()
