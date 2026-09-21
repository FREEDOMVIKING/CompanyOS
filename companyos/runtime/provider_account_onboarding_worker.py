from __future__ import annotations
import argparse,json,subprocess,time
from pathlib import Path
from companyos.runtime import provider_acquisition_broker as pab
from companyos.runtime import provider_connector_router as pcr

RT=Path.home()/".companyos_runtime"
STATE=RT/"provider_account_onboarding_worker_state.json"
QUEUE=RT/"provider_onboarding_queue.json"
PRIORITY=("tavily","brave_search","groq","gemini","huggingface","cloudflare_workers_ai","github_actions")

def atomic(p,d):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2,sort_keys=True,default=str)+"\n"); t.replace(p)

def work(open_signup=False):
    pab.run(open_signup=False)
    q=json.loads(QUEUE.read_text())
    by={t.get("provider"):t for t in q.get("tasks",[]) if isinstance(t,dict)}
    pending=[by[n] for n in PRIORITY if n in by and by[n].get("status") in ("account_or_key_needed","credential_present_but_not_validated")]
    nxt=pending[0] if pending else None
    action={"performed":False,"reason":"no_pending_onboarding" if not nxt else "interactive_signup_or_verification_required"}
    if open_signup and nxt and nxt.get("signup_url"):
        try:
            subprocess.run(["termux-open-url",str(nxt["signup_url"])],check=True)
            action={"performed":True,"action":"opened_official_signup","provider":nxt.get("provider"),"submitted_form":False,"created_account":False,"verification_bypassed":False}
        except Exception as e: action={"performed":False,"reason":f"{type(e).__name__}:{str(e)[:300]}"}
    out={"schema":"companyos.provider_account_onboarding_worker.v69_27","generated_at_unix":time.time(),"available_capabilities":pcr.provider_status().get("capabilities") or {},"pending_providers":[x.get("provider") for x in pending],"next_provider":nxt.get("provider") if nxt else None,"next_signup_url":nxt.get("signup_url") if nxt else None,"company_account_email":(q.get("company_account_email") or {}).get("masked"),"action":action,"rules":{"official_programmatic_registration_only":True,"search_public_repositories_for_keys":False,"use_leaked_or_third_party_keys":False,"bypass_captcha":False,"bypass_phone_verification":False,"bypass_kyc":False,"fabricate_identity":False,"automatic_purchase":False,"paid_upgrade":False},"secret_values_emitted":False,"financial_action_performed":False}
    atomic(STATE,out); return out

if __name__=="__main__":
    a=argparse.ArgumentParser(); a.add_argument("--open-next-signup",action="store_true"); args=a.parse_args(); print(json.dumps(work(args.open_next_signup),indent=2,sort_keys=True))
