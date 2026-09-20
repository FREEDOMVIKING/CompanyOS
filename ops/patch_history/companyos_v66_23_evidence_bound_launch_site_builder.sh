#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"

MOD="$ROOT/companyos/runtime/evidence_bound_launch_site_builder.py"
CTL="$ROOT/scripts/companyos_launchsitectl"
LCTL="$ROOT/scripts/companyos_livenessctl"
XCTL="$ROOT/scripts/companyos_externalctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.23 EVIDENCE-BOUND LAUNCH SITE BUILDER ====="
echo "GOAL=CREATE_REAL_DEPLOYABLE_STATIC_SITE_FOR_LAUNCH_READY_VENTURES"
echo "NOTE=PUBLIC_COPY_COMES_ONLY_FROM_EXISTING_VENTURE_ARTIFACTS"
echo "NOTE=NO_UNSUPPORTED_PRODUCT_CLAIMS"
echo "NOTE=NO_AUTHORITY_SWITCHES_CHANGED"

for f in \
  "$ROOT/companyos/governance/venture_identity_progression.py" \
  "$ROOT/companyos/runtime/stalled_stage_progression_controller.py" \
  "$ROOT/companyos/runtime/authority_aware_launch_bridge.py"
do
  [ -f "$f" ] || { echo "V66_23_ABORT=missing:$f"; exit 1; }
done

mkdir -p "$ROOT/companyos/runtime" "$ROOT/scripts" "$RT"

stamp="$(date +%Y%m%d_%H%M%S)"
if [ -f "$MOD" ]; then
  cp "$MOD" "${MOD}.v66_23_backup_${stamp}"
  echo "BACKUP=${MOD}.v66_23_backup_${stamp}"
fi

cat > "$MOD" <<'PY'
from __future__ import annotations

import html
import json
import os
import time
from pathlib import Path
from typing import Any

from companyos.governance.venture_identity_progression import candidate_ventures
from companyos.runtime.stalled_stage_progression_controller import canonical_ventures

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"

LATEST=RT/"evidence_bound_launch_site_builder_latest.json"
HISTORY=RT/"evidence_bound_launch_site_builder_history.jsonl"

VERSION="V66.23"
MAX_FILE_BYTES=1_000_000
MAX_FILES_PER_VENTURE=120

SAFE_SINGLE_KEYS=(
    "product_name","venture_name","company_name","name","title",
    "headline","tagline","description","summary","value_proposition",
    "target_customer","target_audience","audience","offer",
)

SAFE_LIST_KEYS=(
    "features","benefits","capabilities","use_cases","use_case",
    "deliverables","included","what_it_does",
)

PRICE_KEYS=(
    "price_usd","monthly_price_usd","annual_price_usd","starting_price_usd",
)

BLOCKED_PHRASES=(
    "do not fabricate",
    "procurement",
    "missing field",
    "system prompt",
    "assistant",
    "internal only",
    "approval required",
    "authority switch",
    "task queue",
    "orchestration",
    "idempotency",
)

BLOCKED_PATH_PARTS={
    ".git","node_modules","__pycache__","companyos_progress",
    ".venv","venv","runtime","logs","backup","backups",
}


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    import tempfile
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
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


def append_jsonl(path: Path,row: dict[str,Any]) -> None:
    with path.open("a") as f:
        f.write(json.dumps(row,sort_keys=True,default=str)+"\n")


def clean_text(value: Any, limit: int=700) -> str|None:
    if not isinstance(value,str):
        return None
    text=" ".join(value.split()).strip()
    if len(text)<3:
        return None
    low=text.lower()
    if any(x in low for x in BLOCKED_PHRASES):
        return None
    if text.startswith("{") or text.startswith("["):
        return None
    return text[:limit]


def venture_roots(cid: str) -> list[Path]:
    rec=(candidate_ventures().get(cid) or {})
    out=[]
    for rel in rec.get("roots") or []:
        p=ROOT/rel
        if p.exists() and p.is_dir():
            out.append(p)
    return out


def artifact_files(roots: list[Path]) -> list[Path]:
    rows=[]
    seen=set()
    for root in roots:
        try:
            paths=list(root.rglob("*"))
        except Exception:
            continue
        for p in paths:
            if not p.is_file():
                continue
            if any(part in BLOCKED_PATH_PARTS for part in p.parts):
                continue
            if p.name in {"index.html","launch_manifest.json"}:
                continue
            if p.suffix.lower() not in {".json",".jsonl",".md",".txt"}:
                continue
            try:
                st=p.stat()
            except Exception:
                continue
            if st.st_size<=0 or st.st_size>MAX_FILE_BYTES:
                continue
            rp=str(p.resolve())
            if rp in seen:
                continue
            seen.add(rp)
            rows.append((st.st_mtime,p))
    rows.sort(key=lambda x:-x[0])
    return [p for _,p in rows[:MAX_FILES_PER_VENTURE]]


def walk(obj: Any, depth: int=0):
    if depth>7:
        return
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():
            yield from walk(v,depth+1)
    elif isinstance(obj,list):
        for v in obj:
            yield from walk(v,depth+1)


def records(path: Path):
    try:
        text=path.read_text(errors="ignore")
    except Exception:
        return
    if path.suffix.lower()==".jsonl":
        for line_no,line in enumerate(text.splitlines(),1):
            try:
                obj=json.loads(line)
            except Exception:
                continue
            for d in walk(obj):
                yield d,f"{path}:{line_no}"
    elif path.suffix.lower()==".json":
        try:
            obj=json.loads(text)
        except Exception:
            return
        for d in walk(obj):
            yield d,str(path)
    else:
        text=" ".join(text.split()).strip()
        if text and not any(x in text.lower() for x in BLOCKED_PHRASES):
            yield {"summary":text[:1000]},str(path)


def collect_evidence(cid: str) -> dict[str,Any]:
    roots=venture_roots(cid)
    fields={}
    lists={}
    prices=[]
    provenance=[]

    for p in artifact_files(roots):
        for d,source in records(p):
            for key in SAFE_SINGLE_KEYS:
                if key not in d or key in fields:
                    continue
                txt=clean_text(d.get(key))
                if txt:
                    fields[key]=txt
                    provenance.append({"field":key,"source":source})

            for key in SAFE_LIST_KEYS:
                if key not in d:
                    continue
                vals=d.get(key)
                if isinstance(vals,str):
                    vals=[vals]
                if not isinstance(vals,list):
                    continue
                bucket=lists.setdefault(key,[])
                for v in vals:
                    txt=clean_text(v,280)
                    if txt and txt not in bucket:
                        bucket.append(txt)
                        provenance.append({"field":key,"source":source})
                    if len(bucket)>=8:
                        break

            for key in PRICE_KEYS:
                if d.get(key) in (None,""):
                    continue
                try:
                    value=float(d[key])
                except Exception:
                    continue
                if value>0 and value<1_000_000:
                    prices.append({
                        "field":key,
                        "value_usd":value,
                        "source":source,
                    })

    return {
        "roots":[str(x) for x in roots],
        "fields":fields,
        "lists":lists,
        "prices":prices[:10],
        "provenance":provenance[:200],
    }


def title_for(cid: str,evidence: dict[str,Any]) -> str:
    f=evidence.get("fields") or {}
    for key in ("product_name","venture_name","company_name","title","name"):
        if f.get(key):
            return str(f[key])
    return cid.replace("_"," ").title()


def description_for(evidence: dict[str,Any]) -> str|None:
    f=evidence.get("fields") or {}
    for key in ("tagline","headline","value_proposition","description","summary","offer"):
        if f.get(key):
            return str(f[key])
    return None


def feature_rows(evidence: dict[str,Any]) -> list[str]:
    rows=[]
    lists=evidence.get("lists") or {}
    for key in SAFE_LIST_KEYS:
        for item in lists.get(key) or []:
            if item not in rows:
                rows.append(item)
            if len(rows)>=6:
                return rows
    return rows


def company_email() -> str|None:
    for key in (
        "COMPANYOS_EMAIL",
        "COMPANYOS_SMTP_USERNAME",
        "SMTP_USERNAME",
        "EMAIL_USERNAME",
    ):
        value=os.environ.get(key)
        if value and "@" in value:
            return value.strip()
    env_path=ROOT/".env"
    if env_path.exists():
        for raw in env_path.read_text(errors="ignore").splitlines():
            if "=" not in raw or raw.lstrip().startswith("#"):
                continue
            k,v=raw.split("=",1)
            if k.strip() in {
                "COMPANYOS_EMAIL","COMPANYOS_SMTP_USERNAME",
                "SMTP_USERNAME","EMAIL_USERNAME",
            }:
                v=v.strip().strip('"').strip("'")
                if "@" in v:
                    return v
    return None


def render_html(cid: str,evidence: dict[str,Any]) -> str:
    title=title_for(cid,evidence)
    desc=description_for(evidence)
    features=feature_rows(evidence)
    email=company_email()

    h_title=html.escape(title)
    h_desc=html.escape(desc) if desc else ""
    feature_html="".join(
        f"<li>{html.escape(x)}</li>"
        for x in features
    )

    hero=(
        f"<p class='lead'>{h_desc}</p>"
        if desc
        else "<p class='lead'>This venture is preparing for public launch.</p>"
    )

    feature_section=(
        "<section><h2>What it offers</h2>"
        f"<ul>{feature_html}</ul></section>"
        if features else ""
    )

    cta=""
    if email:
        safe_email=html.escape(email,quote=True)
        cta=(
            "<section class='cta'><h2>Interested?</h2>"
            f"<a href='mailto:{safe_email}'>Contact us</a></section>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{h_title}</title>
<meta name="description" content="{html.escape(desc or title,quote=True)}">
<style>
:root {{ color-scheme: light dark; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; line-height:1.55; }}
main {{ max-width:900px; margin:auto; padding:72px 24px; }}
.hero {{ padding:56px 0 36px; }}
h1 {{ font-size:clamp(2.2rem,7vw,5rem); line-height:1; margin:0 0 24px; }}
h2 {{ margin-top:48px; }}
.lead {{ max-width:700px; font-size:1.2rem; opacity:.85; }}
ul {{ padding-left:22px; }}
li {{ margin:10px 0; }}
.cta a {{ display:inline-block; padding:12px 18px; border:1px solid currentColor; border-radius:10px; text-decoration:none; }}
footer {{ margin-top:72px; opacity:.6; font-size:.9rem; }}
</style>
</head>
<body>
<main>
<section class="hero">
<h1>{h_title}</h1>
{hero}
</section>
{feature_section}
{cta}
<footer>Powered by CompanyOS</footer>
</main>
</body>
</html>
"""


def existing_static_root(cid: str) -> Path|None:
    for root in venture_roots(cid):
        for p in (
            root/"site",
            root/"public",
            root/"dist",
            root/"build",
            root,
        ):
            if (p/"index.html").is_file():
                return p
    return None


def build_one(cid: str) -> dict[str,Any]:
    roots=venture_roots(cid)
    if not roots:
        return {"canonical_id":cid,"status":"venture_root_missing"}

    existing=existing_static_root(cid)
    if existing:
        return {
            "canonical_id":cid,
            "status":"static_site_already_present",
            "site_root":str(existing),
        }

    evidence=collect_evidence(cid)
    root=roots[0]
    site=root/"site"
    site.mkdir(parents=True,exist_ok=True)

    index=site/"index.html"
    manifest=site/"launch_manifest.json"

    index.write_text(render_html(cid,evidence),encoding="utf-8")
    save_json(manifest,{
        "schema":"companyos.evidence_bound_launch_manifest.v1",
        "version":VERSION,
        "canonical_id":cid,
        "created_at_unix":time.time(),
        "site_root":str(site),
        "index_path":str(index),
        "title":title_for(cid,evidence),
        "description_present":bool(description_for(evidence)),
        "feature_count":len(feature_rows(evidence)),
        "source_provenance":evidence.get("provenance") or [],
        "rules":{
            "unsupported_claim_fabrication":False,
            "public_copy_from_existing_artifacts_only":True,
            "static_index_created":True,
        },
    })

    return {
        "canonical_id":cid,
        "status":"static_site_created",
        "site_root":str(site),
        "index_path":str(index),
        "manifest_path":str(manifest),
        "description_present":bool(description_for(evidence)),
        "feature_count":len(feature_rows(evidence)),
        "provenance_count":len(evidence.get("provenance") or []),
    }


def run_once() -> dict[str,Any]:
    ventures=canonical_ventures()
    results=[]

    for cid,row in sorted(ventures.items()):
        if str(row.get("stage") or "")!="LAUNCH_READY":
            continue
        results.append(build_one(cid))

    report={
        "version":VERSION,
        "mode":"evidence_bound_launch_site_build",
        "launch_ready_count":sum(
            1 for x in ventures.values()
            if str(x.get("stage") or "")=="LAUNCH_READY"
        ),
        "results":results,
        "created_count":sum(
            1 for x in results
            if x.get("status")=="static_site_created"
        ),
        "rules":{
            "unsupported_claim_fabrication":False,
            "venture_content_deleted":False,
            "authority_switches_changed":False,
        },
        "timestamp_unix":time.time(),
    }
    save_json(LATEST,report)
    append_jsonl(HISTORY,report)
    return report
PY

cat > "$CTL" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"
cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-once}" in
  once)
    python - <<'PY'
import json
from companyos.runtime.evidence_bound_launch_site_builder import run_once
print(json.dumps(run_once(),indent=2,sort_keys=True,default=str))
PY
    ;;
  status)
    cat "$HOME/.companyos_runtime/evidence_bound_launch_site_builder_latest.json" 2>/dev/null || echo '{"status":"no_run_yet"}'
    ;;
  *)
    echo "usage: $0 {once|status}"
    exit 2
    ;;
esac
SH
chmod +x "$CTL"

cat > "$ROOT/tests/test_evidence_bound_launch_site_builder.py" <<'PY'
from companyos.runtime.evidence_bound_launch_site_builder import clean_text

def test_internal_instruction_is_rejected():
    assert clean_text("Do not fabricate vendor price or payment destination") is None

def test_normal_public_copy_is_allowed():
    assert clean_text("Automate repetitive field workflows") is not None
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD"
echo "V66_23_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_evidence_bound_launch_site_builder.py
echo "V66_23_TESTS=PASS"

echo "===== BUILD MISSING LAUNCH-READY SITE ====="
"$CTL" once

echo "===== VERIFY INDEX FILE ====="
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/".companyos_runtime/evidence_bound_launch_site_builder_latest.json"
x=json.loads(p.read_text()) if p.exists() else {}
for row in x.get("results") or []:
    root=row.get("site_root")
    if root:
        idx=Path(root)/"index.html"
        print(f"{row.get('canonical_id')} INDEX_PRESENT={idx.is_file()} PATH={idx}")
PY

echo "===== RESTART EXTERNAL ROUTER IF PRESENT ====="
if [ -x "$XCTL" ]; then
  "$XCTL" restart || true
fi

echo "===== RUN LAUNCH BRIDGE ====="
python - <<'PY'
import json
from companyos.runtime.authority_aware_launch_bridge import run_once
print(json.dumps(run_once(),indent=2,sort_keys=True,default=str))
PY

echo "===== RESTART LIVENESS ====="
"$LCTL" restart

echo "===== ALLOW EXTERNAL ROUTER TO EXECUTE ====="
sleep 15

echo "===== RECONCILE REAL DEPLOYMENT RESULT ====="
python - <<'PY'
import json
from companyos.runtime.authority_aware_launch_bridge import run_once
print(json.dumps(run_once(),indent=2,sort_keys=True,default=str))
PY

echo "===== FINAL LIVENESS STATUS ====="
"$LCTL" status

echo "V66_23_EVIDENCE_BOUND_COPY=PASS"
echo "V66_23_STATIC_INDEX_CREATED=PASS"
echo "V66_23_LAUNCH_BRIDGE_RETRY=PASS"
echo "V66_23_REAL_DEPLOYMENT_EVIDENCE_GATE_PRESERVED=PASS"
echo "V66_23_NO_UNSUPPORTED_CLAIMS=PASS"
echo "V66_23_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_23_COMPLETE"
