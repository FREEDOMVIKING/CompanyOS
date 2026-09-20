#!/data/data/com.termux/files/usr/bin/bash
set -u
cd "$HOME/companyos" || exit 1
[ ! -f "$HOME/.companyos_launch_env" ] || . "$HOME/.companyos_launch_env"

echo "===== COMPANYOS EXTERNAL COMMISSIONING V2 ====="

python - <<'PY'
import os, json, subprocess
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path.home()/"companyos"
R={}

def record(name,status,**kw):
    R[name]={"status":status,**kw}
def safe(name,fn):
    try: fn()
    except Exception as e: record(name,"FAIL",reason=f"{type(e).__name__}: {e}")

def openai():
    k=os.getenv("OPENAI_API_KEY","").strip()
    if not k: return record("openai","CONFIG_ERROR",reason="OPENAI_API_KEY missing")
    q=Request("https://api.openai.com/v1/models",headers={"Authorization":f"Bearer {k}"})
    with urlopen(q,timeout=15) as r: record("openai","PASS" if r.status==200 else "FAIL",http_status=r.status)

def github():
    p=subprocess.run(["git","ls-remote","--exit-code","origin","HEAD"],cwd=ROOT,text=True,capture_output=True,timeout=20)
    record("github","PASS" if p.returncode==0 else "FAIL",detail=(p.stderr or p.stdout)[-250:].strip())

def vercel():
    k=os.getenv("VERCEL_TOKEN","").strip()
    if not k: return record("vercel","CONFIG_ERROR",reason="VERCEL_TOKEN missing")
    q=Request("https://api.vercel.com/v2/user",headers={"Authorization":f"Bearer {k}"})
    with urlopen(q,timeout=15) as r: record("vercel","PASS" if r.status==200 else "FAIL",http_status=r.status)

def smtp():
    import smtplib
    host=os.getenv("SMTP_HOST","").strip()
    raw=os.getenv("SMTP_PORT","587").strip()
    user=os.getenv("SMTP_USERNAME","").strip()
    pwd=os.getenv("SMTP_PASSWORD","")
    if not host: return record("smtp","CONFIG_ERROR",reason="SMTP_HOST missing")
    try: port=int(raw)
    except ValueError:
        return record("smtp","CONFIG_ERROR",reason=f"SMTP_PORT is not numeric (value looks like configuration was shifted)")
    with smtplib.SMTP(host,port,timeout=15) as s:
        s.ehlo()
        if port==587: s.starttls(); s.ehlo()
        auth=None
        if user and pwd: s.login(user,pwd); auth=True
        record("smtp","PASS",reachable=True,authenticated=auth)

def solrpc():
    rpc=os.getenv("SOLANA_RPC_URL","").strip()
    if not rpc: return record("solana_rpc","CONFIG_ERROR",reason="SOLANA_RPC_URL missing")
    data=json.dumps({"jsonrpc":"2.0","id":1,"method":"getHealth"}).encode()
    q=Request(rpc,data=data,headers={"Content-Type":"application/json"})
    with urlopen(q,timeout=15) as r:
        body=json.loads(r.read().decode())
        record("solana_rpc","PASS" if body.get("result")=="ok" else "FAIL",response=body)

def signer():
    key=os.getenv("SOLANA_PRIVATE_KEY","").strip()
    if not key: return record("solana_signer","CONFIG_ERROR",reason="SOLANA_PRIVATE_KEY missing")
    lengths=[]
    try:
        import base58
        b=base58.b58decode(key); lengths.append(("base58",len(b)))
    except Exception: pass
    try:
        import base64
        b=base64.b64decode(key,validate=True); lengths.append(("base64",len(b)))
    except Exception: pass
    valid=[x for x in lengths if x[1] in (32,64)]
    record("solana_signer","PASS" if valid else "FAIL",decoded=valid or lengths)

for name,fn in [("openai",openai),("github",github),("vercel",vercel),("smtp",smtp),("solana_rpc",solrpc),("solana_signer",signer)]:
    safe(name,fn)

print(json.dumps(R,indent=2))
print("\n===== SUMMARY =====")
for n in ("openai","github","vercel","smtp","solana_rpc","solana_signer"):
    print(f"{n:15} {R.get(n,{}).get('status','NOT_RUN')}")
passed=sum(v["status"]=="PASS" for v in R.values())
print(f"\nPASS_COUNT={passed}/{len(R)}")
print("ALL_EXTERNAL_CONNECTORS_PASS=" + ("true" if R and all(v["status"]=="PASS" for v in R.values()) else "false"))
PY

echo
echo "===== RUNTIME HEALTH ====="
./scripts/companyosctl health 2>/dev/null || true
echo
echo "COMPANYOS_EXTERNAL_COMMISSIONING_V2=COMPLETE"
