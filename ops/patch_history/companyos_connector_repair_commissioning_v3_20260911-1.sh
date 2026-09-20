#!/data/data/com.termux/files/usr/bin/bash
set -u
cd "$HOME/companyos" || exit 1
ENVFILE="$HOME/.companyos_launch_env"
[ ! -f "$ENVFILE" ] || . "$ENVFILE"

echo "===== COMPANYOS CONNECTOR REPAIR + COMMISSIONING V3 ====="

python - <<'PY'
from __future__ import annotations
import json, os, shlex, socket, smtplib, subprocess
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

home=Path.home()
root=home/"companyos"
envfile=home/".companyos_launch_env"
report={}

def rec(name,status,**kw):
    report[name]={"status":status,**kw}

# ---------- SMTP diagnose and choose a reachable standard port ----------
host=os.getenv("SMTP_HOST","").strip()
raw_port=os.getenv("SMTP_PORT","").strip()
user=os.getenv("SMTP_USERNAME","").strip()
pwd=os.getenv("SMTP_PASSWORD","")
smtp_from=os.getenv("SMTP_FROM","").strip()

if not host:
    rec("smtp","CONFIG_ERROR",reason="SMTP_HOST missing")
else:
    candidates=[]
    try:
        p=int(raw_port)
        if 1 <= p <= 65535:
            candidates.append(p)
    except Exception:
        pass
    for p in (587,465,25):
        if p not in candidates:
            candidates.append(p)

    reachable=[]
    for port in candidates:
        try:
            with socket.create_connection((host,port),timeout=6):
                reachable.append(port)
        except Exception:
            pass

    chosen = reachable[0] if reachable else None
    if chosen is None:
        rec("smtp","FAIL",reason="No tested SMTP port reachable",tested_ports=candidates)
    else:
        try:
            if chosen == 465:
                s=smtplib.SMTP_SSL(host,chosen,timeout=12)
            else:
                s=smtplib.SMTP(host,chosen,timeout=12)
            with s:
                s.ehlo()
                if chosen == 587:
                    s.starttls(); s.ehlo()
                authenticated=None
                if user and pwd:
                    s.login(user,pwd)
                    authenticated=True
            rec("smtp","PASS",port=chosen,authenticated=authenticated,
                from_present=bool(smtp_from),username_present=bool(user))
        except Exception as exc:
            rec("smtp","FAIL",port=chosen,reason=f"{type(exc).__name__}:{exc}")

    # Repair only SMTP_PORT, and only when the current value is invalid and a live port worked.
    if report["smtp"]["status"]=="PASS":
        valid_current=False
        try:
            valid_current=1 <= int(raw_port) <= 65535
        except Exception:
            valid_current=False
        if not valid_current and envfile.exists():
            lines=envfile.read_text(encoding="utf-8").splitlines()
            out=[]
            replaced=False
            for line in lines:
                stripped=line.strip()
                if stripped.startswith("export SMTP_PORT=") or stripped.startswith("SMTP_PORT="):
                    prefix="export " if stripped.startswith("export ") else ""
                    out.append(f"{prefix}SMTP_PORT={report['smtp']['port']}")
                    replaced=True
                else:
                    out.append(line)
            if not replaced:
                out.append(f"export SMTP_PORT={report['smtp']['port']}")
            envfile.write_text("\n".join(out)+"\n",encoding="utf-8")
            try: envfile.chmod(0o600)
            except Exception: pass
            report["smtp"]["env_repaired"]=True

# ---------- Vercel scope-aware read-only diagnostics ----------
token=os.getenv("VERCEL_TOKEN","").strip()
if not token:
    rec("vercel","CONFIG_ERROR",reason="VERCEL_TOKEN missing")
else:
    tests={}
    for label,url in [
        ("user","https://api.vercel.com/v2/user"),
        ("projects","https://api.vercel.com/v9/projects?limit=1"),
        ("teams","https://api.vercel.com/v2/teams?limit=1"),
    ]:
        req=Request(url,headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"})
        try:
            with urlopen(req,timeout=15) as r:
                body=r.read().decode("utf-8","replace")
                tests[label]={"status":r.status,"ok":200 <= r.status < 300}
        except HTTPError as exc:
            body=exc.read().decode("utf-8","replace")
            detail={}
            try:
                x=json.loads(body)
                err=x.get("error",x)
                if isinstance(err,dict):
                    for k in ("code","message","scope","teamId","enforced"):
                        if k in err:
                            detail[k]=err[k]
            except Exception:
                pass
            tests[label]={"status":exc.code,"ok":False,"detail":detail}
        except Exception as exc:
            tests[label]={"ok":False,"reason":f"{type(exc).__name__}:{exc}"}

    # CLI whoami is an additional read-only check when installed.
    cli=None
    try:
        p=subprocess.run(
            ["vercel","whoami","--token",token],
            cwd=root,text=True,capture_output=True,timeout=20
        )
        cli={"ok":p.returncode==0,"returncode":p.returncode,
             "output":(p.stdout or p.stderr).strip()[-300:]}
    except FileNotFoundError:
        cli={"ok":False,"reason":"vercel_cli_not_installed"}
    except Exception as exc:
        cli={"ok":False,"reason":f"{type(exc).__name__}:{exc}"}

    any_api=any(v.get("ok") for v in tests.values())
    if any_api or cli.get("ok"):
        rec("vercel","PASS",api_tests=tests,cli_whoami=cli)
    else:
        codes=[v.get("status") for v in tests.values() if v.get("status")]
        scoped=any(
            isinstance(v.get("detail"),dict) and
            (v["detail"].get("scope") or "scope" in str(v["detail"].get("message","")).lower())
            for v in tests.values()
        )
        rec("vercel","SCOPE_OR_AUTH_ERROR" if scoped or 403 in codes else "FAIL",
            api_tests=tests,cli_whoami=cli)

# ---------- Recheck already-passing paths ----------
def test_openai():
    k=os.getenv("OPENAI_API_KEY","").strip()
    if not k: return rec("openai","CONFIG_ERROR",reason="missing key")
    req=Request("https://api.openai.com/v1/models",headers={"Authorization":f"Bearer {k}"})
    with urlopen(req,timeout=15) as r: rec("openai","PASS" if r.status==200 else "FAIL",http_status=r.status)
try: test_openai()
except Exception as exc: rec("openai","FAIL",reason=f"{type(exc).__name__}:{exc}")

try:
    p=subprocess.run(["git","ls-remote","--exit-code","origin","HEAD"],cwd=root,
                     text=True,capture_output=True,timeout=20)
    rec("github","PASS" if p.returncode==0 else "FAIL")
except Exception as exc:
    rec("github","FAIL",reason=f"{type(exc).__name__}:{exc}")

rpc=os.getenv("SOLANA_RPC_URL","").strip()
try:
    if not rpc:
        rec("solana_rpc","CONFIG_ERROR",reason="missing RPC URL")
    else:
        data=json.dumps({"jsonrpc":"2.0","id":1,"method":"getHealth"}).encode()
        req=Request(rpc,data=data,headers={"Content-Type":"application/json"})
        with urlopen(req,timeout=15) as r:
            x=json.loads(r.read().decode())
        rec("solana_rpc","PASS" if x.get("result")=="ok" else "FAIL",response=x)
except Exception as exc:
    rec("solana_rpc","FAIL",reason=f"{type(exc).__name__}:{exc}")

print(json.dumps(report,indent=2,sort_keys=True))
print("\n===== SUMMARY =====")
for name in ("openai","github","smtp","vercel","solana_rpc"):
    print(f"{name:12} {report.get(name,{}).get('status','NOT_RUN')}")
print("\nSMTP_ENV_REPAIRED=" + str(bool(report.get("smtp",{}).get("env_repaired"))).lower())
print("COMMISSIONING_V3_COMPLETE=true")
PY

echo
echo "===== VERCEL CODE PATHS ====="
grep -RIn --exclude-dir=.git --exclude-dir=backups \
  -E 'VERCEL_TOKEN|api\\.vercel\\.com|teamId|VERCEL_(TEAM|ORG|PROJECT)' \
  companyos scripts 2>/dev/null | head -80 || true

echo
echo "===== RESTART IF SMTP PORT WAS REPAIRED ====="
./scripts/companyosctl restart >/dev/null 2>&1 || true
sleep 3
./scripts/companyosctl health || true

echo
echo "COMPANYOS_CONNECTOR_REPAIR_COMMISSIONING_V3=COMPLETE"
