from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib, importlib, json, os, time, urllib.request
from companyos.runtime.public_research_connectors import collect_public_research

ROOT=Path.home()/".companyos_runtime"/"external_research_network"
ROOT.mkdir(parents=True,exist_ok=True)
STATE=ROOT/"state.json"
SEEN=ROOT/"seen.json"
SIGNALS=ROOT/"external_signals.jsonl"

MIN_MB=int(os.getenv("COMPANYOS_RESEARCH_MIN_AVAILABLE_MB","2400"))
MAX_RESULTS=int(os.getenv("COMPANYOS_RESEARCH_MAX_RESULTS_PER_CYCLE","8"))
TIMEOUT=int(os.getenv("COMPANYOS_RESEARCH_HTTP_TIMEOUT_SECONDS","10"))

@dataclass
class Cycle:
    mode:str
    available_mb:int
    deferred:bool
    reason:str
    sources_checked:int
    raw_results:int
    new_signals:int
    duplicates:int
    pipeline_accepted:int
    pipeline_failed:int
    last_error:str|None
    started_at:float
    finished_at:float

def mem_mb():
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1])//1024
    except Exception:
        pass
    return 0

def load_json(p, default):
    try:return json.loads(p.read_text())
    except Exception:return default

def save_json(p,data):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(data,indent=2,sort_keys=True,default=str)+"\n")
    os.replace(t,p)

def fingerprint(x):
    raw="|".join([str(x.get(k,"")).strip().lower() for k in ("title","url","summary","source")])
    return hashlib.sha256(raw.encode()).hexdigest()

def discover_sources():
    out=[]
    mods=[
      "companyos.autonomous_opportunity_intelligence_v11.sources",
      "companyos.autonomous_opportunity_intelligence_v11.research",
      "companyos.runtime.research_signal_ingestion",
      "companyos.research_signal_ingestion",
    ]
    for name in mods:
        try:m=importlib.import_module(name)
        except Exception:continue
        for fnn in ("get_enabled_sources","list_sources","research_sources"):
            fn=getattr(m,fnn,None)
            if callable(fn):
                try:
                    v=fn()
                    if isinstance(v,list):out.extend(v)
                except Exception:pass
    return out

def src_info(s):
    if isinstance(s,dict):
        if s.get("enabled",True) is False:return None,None
        return s.get("url") or s.get("endpoint") or s.get("uri"), str(s.get("name") or s.get("source") or "companyos")
    if getattr(s,"enabled",True) is False:return None,None
    return getattr(s,"url",None) or getattr(s,"endpoint",None), str(getattr(s,"name","companyos"))

def fetch(url,name):
    if not str(url).startswith(("http://","https://")):return []
    req=urllib.request.Request(str(url),headers={"User-Agent":"CompanyOS-Research/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
        data=json.loads(r.read(2_000_000).decode("utf-8","replace"))
    rows=data if isinstance(data,list) else (data.get("items") or data.get("results") or data.get("data") or [])
    out=[]
    for row in rows[:MAX_RESULTS]:
        if not isinstance(row,dict):continue
        out.append({
          "source":name,
          "title":row.get("title") or row.get("name") or row.get("headline") or "",
          "summary":row.get("summary") or row.get("description") or row.get("text") or "",
          "url":row.get("url") or row.get("link") or "",
          "metadata":row,
          "captured_at":time.time(),
        })
    return out

def ingest(signal):
    mods=[
      "companyos.runtime.research_signal_pipeline",
      "companyos.runtime.research_signal_ingestion",
      "companyos.research_signal_pipeline",
      "companyos.research_signal_ingestion",
    ]
    for name in mods:
        try:m=importlib.import_module(name)
        except Exception:continue
        for fnn in ("ingest_signal","ingest","process","store","save_signal"):
            fn=getattr(m,fnn,None)
            if callable(fn):
                try:
                    fn(signal); return True
                except TypeError:
                    try:fn(record=signal); return True
                    except Exception:pass
                except Exception:pass
    try:
        with SIGNALS.open("a") as f:f.write(json.dumps(signal,sort_keys=True,default=str)+"\n")
        return True
    except Exception:return False

def run_cycle():
    started=time.time()
    available=mem_mb()
    if available and available<MIN_MB:
        r=Cycle("read_only_external_research",available,True,"resource_pressure",0,0,0,0,0,0,None,started,time.time())
        save_json(STATE,asdict(r)); return r

    seen=load_json(SEEN,{})
    if not isinstance(seen,dict):seen={}
    cutoff=time.time()-30*86400
    seen={k:v for k,v in seen.items() if isinstance(v,(int,float)) and v>=cutoff}

    checked=raw=new=dupes=ok=bad=0
    err=None
    items=[]
    sources=discover_sources()

    # Live public research connectors - read only.
    try:
        public_topic, public_rows, public_errors = collect_public_research()
        items.extend(public_rows)
        raw += len(public_rows)
        checked += 5
        if public_errors:
            err = ";".join(public_errors)[:240]
    except Exception as exc:
        err = f"public_connectors:{type(exc).__name__}:{str(exc)[:180]}"

    extra=os.getenv("COMPANYOS_RESEARCH_PUBLIC_JSON_URL","").strip()
    if extra:sources.append({"name":"custom_public_json","url":extra,"enabled":True})

    for s in sources:
        url,name=src_info(s)
        if not url:continue
        checked+=1
        try:
            rows=fetch(url,name)
            raw+=len(rows); items.extend(rows)
        except Exception as e:
            err=f"{type(e).__name__}:{str(e)[:240]}"

    for item in items[:MAX_RESULTS]:
        fp=fingerprint(item)
        if fp in seen:
            dupes+=1; continue
        seen[fp]=time.time(); new+=1
        signal={
          "signal_id":fp,
          "signal_source":item.get("source","external"),
          "signal_type":"external_research",
          "title":item.get("title",""),
          "content":item.get("summary",""),
          "url":item.get("url",""),
          "captured_at":item.get("captured_at",time.time()),
          "metadata":item.get("metadata",{}),
          "profit_analysis_required":True,
          "opportunity_discovery_required":True,
          "external_action_allowed":False,
          "financial_action_allowed":False,
        }
        if ingest(signal):ok+=1
        else:bad+=1

    save_json(SEEN,seen)
    reason="cycle_completed" if checked else "no_enabled_external_sources"
    r=Cycle("read_only_external_research",available,False,reason,checked,raw,new,dupes,ok,bad,err,started,time.time())
    save_json(STATE,asdict(r)); return r

# COMPANYOS_V69_31_CONTINUOUS_EXTERNAL_RESEARCH
def run():
    interval=max(
        60,
        int(os.getenv("COMPANYOS_EXTERNAL_RESEARCH_INTERVAL_SECONDS","180"))
    )
    stop=Path.home()/".companyos_runtime"/"STOP_CONTINUOUS"

    while not stop.exists():
        try:
            run_cycle()
        except Exception as exc:
            save_json(
                STATE,
                {
                    "mode":"read_only_external_research",
                    "healthy":False,
                    "last_error":f"{type(exc).__name__}:{str(exc)[:1000]}",
                    "updated_at_unix":time.time(),
                },
            )
        time.sleep(interval)

if __name__=="__main__":
    run()

