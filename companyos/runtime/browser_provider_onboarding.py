from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from companyos.runtime.autonomous_provider_accounts import (
    ACCOUNTS,
    HUMAN,
    KNOWN_SIGNUP_ROUTES,
    append_jsonl,
    dotenv,
    env,
    existing_accounts,
    human_record,
    mailbox_config,
    vault_store,
    click_verification,
)

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"
BRT=RT/"browser_accounts"
LATEST=BRT/"latest.json"
HISTORY=BRT/"history.jsonl"
STATE=BRT/"state.json"
PID=BRT/"chromium.pid"
PORTFILE=BRT/"chromium_port.txt"
PROFILE=BRT/"chromium_profile"
BRT.mkdir(parents=True,exist_ok=True)

VERSION="V66.08"
DEFAULT_PORT=9222
MAX_PER_CYCLE=2

CAPTCHA_MARKERS=(
    "captcha","recaptcha","hcaptcha","cf-turnstile","turnstile",
)
KYC_MARKERS=(
    "identity verification","verify identity","government id","photo id",
    "know your customer","kyc",
)
PHONE_MARKERS=("phone number","mobile number","sms verification","text verification")


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    import tempfile as _tf
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=_tf.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w") as f:
            f.write(json.dumps(data,indent=2,sort_keys=True,default=str)+"\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass


def browser_executable() -> str|None:
    configured=env("COMPANYOS_BROWSER_EXECUTABLE")
    if configured and Path(configured).exists():
        return configured
    for name in ("chromium","chromium-browser","google-chrome","google-chrome-stable","chrome"):
        p=shutil.which(name)
        if p:
            return p
    return None


def remote_cdp_url() -> str|None:
    u=env("COMPANYOS_BROWSER_CDP_URL")
    return u.strip() if u else None


def backend_status() -> dict[str,Any]:
    exe=browser_executable()
    remote=remote_cdp_url()
    return {
        "local_browser_executable":exe,
        "local_browser_available":bool(exe),
        "remote_cdp_configured":bool(remote),
        "browser_backend_ready":bool(exe or remote),
        "backend":"remote_cdp" if remote else ("local_chromium" if exe else None),
    }


def _json_get(url: str, headers: dict[str,str]|None=None) -> Any:
    req=urllib.request.Request(url,headers=headers or {"User-Agent":"CompanyOS/66.08"})
    with urllib.request.urlopen(req,timeout=10) as r:
        return json.loads(r.read().decode(errors="ignore"))


def _choose_port() -> int:
    return int(env("COMPANYOS_BROWSER_DEBUG_PORT",str(DEFAULT_PORT)) or DEFAULT_PORT)


def _local_base() -> str:
    port=_choose_port()
    return f"http://127.0.0.1:{port}"


def _local_alive() -> bool:
    try:
        x=_json_get(_local_base()+"/json/version")
        return bool(x.get("Browser"))
    except Exception:
        return False


def start_local_browser() -> dict[str,Any]:
    exe=browser_executable()
    if not exe:
        return {"ok":False,"status":"LOCAL_BROWSER_NOT_FOUND"}
    if _local_alive():
        return {"ok":True,"status":"LOCAL_BROWSER_ALREADY_RUNNING","base":_local_base()}

    PROFILE.mkdir(parents=True,exist_ok=True)
    port=_choose_port()
    args=[
        exe,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={PROFILE}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--ozone-platform=headless",
        f"--remote-allow-origins=http://127.0.0.1:{port}",
        "--disable-background-networking",
        "--disable-sync",
        "--metrics-recording-only",
        "about:blank",
    ]
    if str(env("COMPANYOS_BROWSER_HEADLESS","true")).lower() not in {"0","false","no"}:
        args.insert(1,"--headless=new")

    log=(BRT/"chromium.log").open("ab")
    proc=subprocess.Popen(args,stdout=log,stderr=log,start_new_session=True)
    PID.write_text(str(proc.pid))
    PORTFILE.write_text(str(port))

    for _ in range(30):
        if _local_alive():
            return {"ok":True,"status":"LOCAL_BROWSER_STARTED","pid":proc.pid,"base":_local_base()}
        if proc.poll() is not None:
            break
        time.sleep(.3)
    return {"ok":False,"status":"LOCAL_BROWSER_START_FAILED","pid":proc.pid}


def stop_local_browser() -> dict[str,Any]:
    if PID.exists():
        try:
            pid=int(PID.read_text().strip())
            os.kill(pid,15)
        except Exception:
            pass
        try:
            PID.unlink()
        except Exception:
            pass
    return {"ok":True,"status":"LOCAL_BROWSER_STOPPED"}


def _cdp_browser_base() -> tuple[str,dict[str,str]]:
    remote=remote_cdp_url()
    headers={"User-Agent":"CompanyOS/66.08"}
    token=env("COMPANYOS_BROWSER_CDP_TOKEN")
    if token:
        headers["Authorization"]="Bearer "+token
    if remote:
        return remote.rstrip("/"),headers
    st=start_local_browser()
    if not st.get("ok"):
        raise RuntimeError(st.get("status") or "browser_unavailable")
    return _local_base(),headers


def _new_target(url: str="about:blank") -> dict[str,Any]:
    base,headers=_cdp_browser_base()
    encoded=urllib.parse.quote(url,safe=":/?&=%")
    for method in ("PUT","GET"):
        req=urllib.request.Request(
            base+"/json/new?"+encoded,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req,timeout=10) as r:
                return json.loads(r.read().decode(errors="ignore"))
        except Exception:
            continue
    # Some remote CDP providers expose a pre-created page only.
    pages=_json_get(base+"/json/list",headers)
    if pages:
        return pages[0]
    raise RuntimeError("cdp_target_creation_failed")


class CDP:
    def __init__(self, ws_url: str):
        from websocket import create_connection
        # Chromium 136+ rejects websocket clients that send a mismatched
        # Origin header. Suppress Origin for this local loopback CDP client;
        # Chromium is also launched with an explicit loopback allow-origin.
        self.ws=create_connection(ws_url,timeout=20,suppress_origin=True)
        self.seq=0

    def close(self):
        try:self.ws.close()
        except Exception:pass

    def call(self,method: str,params: dict[str,Any]|None=None) -> Any:
        self.seq+=1
        ident=self.seq
        self.ws.send(json.dumps({"id":ident,"method":method,"params":params or {}}))
        while True:
            msg=json.loads(self.ws.recv())
            if msg.get("id")==ident:
                if "error" in msg:
                    raise RuntimeError(f"cdp_error:{msg['error']}")
                return msg.get("result") or {}

    def eval(self,expr: str) -> Any:
        r=self.call("Runtime.evaluate",{
            "expression":expr,
            "returnByValue":True,
            "awaitPromise":True,
        })
        return ((r.get("result") or {}).get("value"))

    def navigate(self,url: str,wait: float=2.5):
        self.call("Page.enable")
        self.call("Runtime.enable")
        self.call("Page.navigate",{"url":url})
        time.sleep(wait)


def jsq(x: Any) -> str:
    return json.dumps(x)


def page_snapshot(cdp: CDP) -> dict[str,Any]:
    script=r'''
(() => {
  const q=(s)=>Array.from(document.querySelectorAll(s));
  return {
    url: location.href,
    title: document.title,
    text: (document.body?.innerText || "").slice(0,120000),
    inputs: q("input,select,textarea").map(e => ({
      tag:e.tagName.toLowerCase(),
      type:(e.type||"").toLowerCase(),
      name:e.name||"",
      id:e.id||"",
      placeholder:e.placeholder||"",
      autocomplete:e.autocomplete||"",
      required:!!e.required,
      checked:!!e.checked
    })),
    buttons: q("button,input[type=submit]").map(e => ({
      tag:e.tagName.toLowerCase(),
      type:(e.type||"").toLowerCase(),
      text:(e.innerText||e.value||"").trim(),
      disabled:!!e.disabled
    }))
  }
})()
'''
    return cdp.eval(script) or {}


def detect_blockers(snapshot: dict[str,Any]) -> list[str]:
    text=str(snapshot.get("text") or "").lower()
    blockers=[]
    for x in CAPTCHA_MARKERS:
        if x in text:
            blockers.append("captcha")
            break
    for x in KYC_MARKERS:
        if x in text:
            blockers.append("kyc_or_identity_verification")
            break
    for x in PHONE_MARKERS:
        if x in text:
            blockers.append("phone_or_sms_verification")
            break

    for inp in snapshot.get("inputs") or []:
        typ=str(inp.get("type") or "").lower()
        name=(str(inp.get("name") or "")+" "+str(inp.get("id") or "")+" "+str(inp.get("placeholder") or "")).lower()
        if inp.get("required") and typ=="checkbox":
            blockers.append("required_terms_or_checkbox")
        if inp.get("required") and (typ=="tel" or "phone" in name or "mobile" in name):
            blockers.append("required_phone")
    return sorted(set(blockers))


def fill_signup(cdp: CDP,email_addr: str,password: str) -> dict[str,Any]:
    # Fill common signup fields. Required terms checkboxes are intentionally
    # not touched here.
    script=f'''
(() => {{
 const email={jsq(email_addr)};
 const pass={jsq(password)};
 const set=(e,v)=>{{
   const d=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value");
   if(d && d.set) d.set.call(e,v); else e.value=v;
   e.dispatchEvent(new Event("input",{{bubbles:true}}));
   e.dispatchEvent(new Event("change",{{bubbles:true}}));
 }};
 const els=Array.from(document.querySelectorAll("input,textarea"));
 let filled=[];
 for(const e of els){{
   const type=(e.type||"").toLowerCase();
   const meta=((e.name||"")+" "+(e.id||"")+" "+(e.placeholder||"")+" "+(e.autocomplete||"")).toLowerCase();
   if(type==="email" || meta.includes("email")){{ set(e,email); filled.push("email"); continue; }}
   if(type==="password" || meta.includes("password")){{ set(e,pass); filled.push("password"); continue; }}
   if(meta.includes("company") || meta.includes("organization")){{ set(e,"CompanyAIOS"); filled.push("company"); continue; }}
   if(meta.includes("first") && meta.includes("name")){{ set(e,"CompanyAIOS"); filled.push("first_name"); continue; }}
   if(meta.includes("last") && meta.includes("name")){{ set(e,"Automation"); filled.push("last_name"); continue; }}
   if((e.name||"").toLowerCase()==="name" || meta.includes("full name")){{ set(e,"CompanyAIOS"); filled.push("name"); continue; }}
 }}
 return {{filled:[...new Set(filled)]}};
}})()
'''
    return cdp.eval(script) or {}


def click_submit(cdp: CDP) -> dict[str,Any]:
    script=r'''
(() => {
  const candidates=Array.from(document.querySelectorAll("button,input[type=submit]"));
  const score=(e)=>{
    const t=((e.innerText||e.value||"")+" "+(e.name||"")+" "+(e.id||"")).toLowerCase();
    let s=0;
    for(const w of ["sign up","signup","register","create account","get started","continue"]) if(t.includes(w)) s+=3;
    if((e.type||"").toLowerCase()==="submit") s+=1;
    if(e.disabled) s-=100;
    return s;
  };
  candidates.sort((a,b)=>score(b)-score(a));
  const b=candidates[0];
  if(!b || score(b)<=0) return {clicked:false,reason:"submit_not_found"};
  b.click();
  return {clicked:true,text:(b.innerText||b.value||"").trim()};
})()
'''
    return cdp.eval(script) or {}


def official_signup_urls(domain: str) -> list[str]:
    urls=list(KNOWN_SIGNUP_ROUTES.get(domain,[]))
    urls += [f"https://{domain}/",f"https://www.{domain}/"]
    return list(dict.fromkeys(urls))


def browser_candidates() -> list[dict[str,Any]]:
    latest=existing_accounts()
    out=[]
    for domain,row in latest.items():
        if domain=="tavily.com":
            # Search capability is now available through Tavily keyless mode;
            # browser signup is no longer on the critical path.
            continue
        if str(row.get("status") or "") not in {
            "BROWSER_ADAPTER_REQUIRED",
            "SIGNUP_DISCOVERY_PENDING",
            "SIGNUP_RESULT_UNCERTAIN",
            "BROWSER_AUTOMATION_ERROR",
            "CDP_PAGE_SOCKET_UNAVAILABLE",
        }:
            continue
        out.append({
            "domain":domain,
            "provider":row.get("provider") or domain.split(".")[0],
            "company_email":row.get("company_email"),
            "credential_env":row.get("credential_env"),
            "previous_status":row.get("status"),
        })
    return out


def process_candidate(candidate: dict[str,Any]) -> dict[str,Any]:
    identity=mailbox_config()
    email_addr=identity.get("email")
    base={
        "schema":"companyos.browser_provider_onboarding.v1",
        "timestamp_unix":time.time(),
        "provider":candidate.get("provider"),
        "domain":candidate.get("domain"),
        "company_email":email_addr,
        "secret_values_printed":False,
    }
    if not email_addr:
        row={**base,"status":"COMPANYAIOS_EMAIL_NOT_CONFIGURED"}
        append_jsonl(ACCOUNTS,row)
        return row

    domain=str(candidate["domain"])
    target=_new_target()
    ws=target.get("webSocketDebuggerUrl")
    if not ws:
        row={**base,"status":"CDP_PAGE_SOCKET_UNAVAILABLE"}
        append_jsonl(ACCOUNTS,row)
        return row

    cdp=CDP(ws)
    try:
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")

        chosen=None
        snap=None
        for url in official_signup_urls(domain):
            cdp.navigate(url,2.5)
            snap=page_snapshot(cdp)
            text=str(snap.get("text") or "").lower()
            if (
                "sign up" in text or "create account" in text or "register" in text
                or any((x.get("type")=="email") for x in (snap.get("inputs") or []))
            ):
                chosen=snap.get("url") or url
                break

        if not chosen or not snap:
            row={**base,"status":"BROWSER_SIGNUP_PAGE_NOT_FOUND"}
            append_jsonl(ACCOUNTS,row)
            return row

        blockers=detect_blockers(snap)
        if blockers:
            human=human_record(
                {"provider":candidate.get("provider"),"domain":domain},
                "browser_signup_requires_human_verification_or_acceptance",
                blockers,
            )
            row={
                **base,
                "status":"HUMAN_VERIFICATION_REQUIRED",
                "signup_host":urllib.parse.urlparse(chosen).hostname,
                "blockers":blockers,
                "human_record":human,
            }
            append_jsonl(ACCOUNTS,row)
            return row

        password=secrets.token_urlsafe(28)+"Aa9!"
        vault=vault_store(candidate.get("provider") or domain,{
            "provider":candidate.get("provider"),
            "domain":domain,
            "company_email":email_addr,
            "account_password":password,
            "created_at_unix":time.time(),
            "created_by":"V66.08_browser_onboarding",
        })
        if not vault.get("ok"):
            row={**base,"status":"VAULT_NOT_READY","vault":vault}
            append_jsonl(ACCOUNTS,row)
            return row

        filled=fill_signup(cdp,email_addr,password)
        before=page_snapshot(cdp)
        blockers=detect_blockers(before)
        if blockers:
            human=human_record(
                {"provider":candidate.get("provider"),"domain":domain},
                "browser_signup_requires_human_verification_or_acceptance",
                blockers,
            )
            row={**base,"status":"HUMAN_VERIFICATION_REQUIRED","blockers":blockers,"human_record":human}
            append_jsonl(ACCOUNTS,row)
            return row

        clicked=click_submit(cdp)
        if not clicked.get("clicked"):
            row={**base,"status":"BROWSER_SUBMIT_NOT_FOUND","filled":filled}
            append_jsonl(ACCOUNTS,row)
            return row

        time.sleep(4)
        after=page_snapshot(cdp)
        text=str(after.get("text") or "").lower()
        post_blockers=detect_blockers(after)
        if post_blockers:
            human=human_record(
                {"provider":candidate.get("provider"),"domain":domain},
                "post_submit_human_verification_required",
                post_blockers,
            )
            row={**base,"status":"HUMAN_VERIFICATION_REQUIRED","blockers":post_blockers,"human_record":human}
            append_jsonl(ACCOUNTS,row)
            return row

        awaiting=any(x in text for x in (
            "check your email","verify your email","verification email",
            "confirm your email","email sent","verification link",
        ))
        dashboard=any(x in text for x in (
            "dashboard","account settings","api keys","developer console","welcome",
        ))

        status="AWAITING_EMAIL_VERIFICATION" if awaiting else (
            "ACCOUNT_CREATED_BROWSER" if dashboard else "BROWSER_SIGNUP_RESULT_UNCERTAIN"
        )
        row={
            **base,
            "status":status,
            "signup_host":urllib.parse.urlparse(chosen).hostname,
            "filled_fields":filled.get("filled") or [],
            "submitted":True,
            "final_host":urllib.parse.urlparse(str(after.get("url") or "")).hostname,
        }
        append_jsonl(ACCOUNTS,row)

        if awaiting:
            time.sleep(5)
            verify=click_verification(domain)
            if verify.get("ok"):
                verified={
                    **row,
                    "timestamp_unix":time.time(),
                    "status":"ACCOUNT_VERIFIED_KEY_ISSUANCE_PENDING",
                    "verification":verify,
                }
                append_jsonl(ACCOUNTS,verified)
                return verified

        return row
    finally:
        cdp.close()


def run_once(max_providers: int=MAX_PER_CYCLE) -> dict[str,Any]:
    backend=backend_status()
    candidates=browser_candidates()
    results=[]
    if backend.get("browser_backend_ready"):
        for c in candidates[:max(1,int(max_providers))]:
            try:
                results.append(process_candidate(c))
            except Exception as exc:
                row={
                    "timestamp_unix":time.time(),
                    "provider":c.get("provider"),
                    "domain":c.get("domain"),
                    "status":"BROWSER_AUTOMATION_ERROR",
                    "error":f"{type(exc).__name__}:{exc}",
                    "secret_values_printed":False,
                }
                append_jsonl(ACCOUNTS,row)
                results.append(row)

    report={
        "version":VERSION,
        "mode":"browser_capable_provider_onboarding",
        "backend":backend,
        "candidate_count":len(candidates),
        "selected":len(results),
        "results":results,
        "constraints":{
            "captcha_bypass":False,
            "phone_bypass":False,
            "kyc_bypass":False,
            "required_terms_auto_acceptance":False,
            "companyaios_email_only":True,
        },
    }
    save_json(LATEST,report)
    append_jsonl(HISTORY,{"timestamp_unix":time.time(),**report})
    save_json(STATE,{"version":VERSION,"updated_at_unix":time.time(),"last_report":report})
    return report


def status() -> dict[str,Any]:
    return {
        "version":VERSION,
        "backend":backend_status(),
        "candidate_count":len(browser_candidates()),
        "latest":load_json(LATEST,{}),
        "state":load_json(STATE,{}),
    }


def loop(interval: int):
    while True:
        try:
            r=run_once()
            print(json.dumps({
                "ts":time.time(),
                "backend_ready":r["backend"]["browser_backend_ready"],
                "candidate_count":r["candidate_count"],
                "selected":r["selected"],
            },sort_keys=True),flush=True)
        except Exception as exc:
            print(json.dumps({"ts":time.time(),"error":f"{type(exc).__name__}:{exc}"},sort_keys=True),flush=True)
        time.sleep(max(180,int(interval)))


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("status")
    sub.add_parser("backend")
    sub.add_parser("candidates")
    sub.add_parser("start-browser")
    sub.add_parser("stop-browser")
    p=sub.add_parser("once")
    p.add_argument("--max-providers",type=int,default=MAX_PER_CYCLE)
    lp=sub.add_parser("loop")
    lp.add_argument("--interval",type=int,default=int(env("COMPANYOS_BROWSER_ONBOARD_INTERVAL_SECONDS","900") or 900))
    args=ap.parse_args()

    if args.cmd=="status":
        print(json.dumps(status(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="backend":
        print(json.dumps(backend_status(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="candidates":
        print(json.dumps(browser_candidates(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="start-browser":
        print(json.dumps(start_local_browser(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="stop-browser":
        print(json.dumps(stop_local_browser(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="once":
        print(json.dumps(run_once(args.max_providers),indent=2,sort_keys=True,default=str))
    elif args.cmd=="loop":
        loop(args.interval)


if __name__=="__main__":
    main()
