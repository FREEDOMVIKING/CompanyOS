from __future__ import annotations
import json, os, time, hashlib
from pathlib import Path
from typing import Any

ROOT = Path.home() / 'companyos'
RUNTIME = ROOT / '.companyos_runtime'
STATE = RUNTIME / 'self_evolution_runtime_integration_state.json'
LEDGER = RUNTIME / 'self_evolution_runtime_integration_ledger.jsonl'
DISCOVERY_DIRS = [RUNTIME/'generated_improvements', ROOT/'companyos_runtime/generated_improvements', ROOT/'generated_improvements']

def load(path: Path, default: Any):
    try: return json.loads(path.read_text(encoding='utf-8', errors='ignore'))
    except Exception: return default

def save(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str)+'\n', encoding='utf-8')

def append(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f: f.write(json.dumps(obj, sort_keys=True, default=str)+'\n')

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def discover() -> list[dict]:
    out, seen = [], set()
    for base in DISCOVERY_DIRS:
        if not base.exists(): continue
        for p in base.rglob('*.py'):
            rp = str(p.resolve())
            if rp in seen: continue
            seen.add(rp)
            out.append({'path': rp, 'sha256': digest(p), 'mtime': p.stat().st_mtime, 'size': p.stat().st_size})
    return sorted(out, key=lambda x: x['mtime'])

def run_once() -> dict:
    from companyos.evolution.self_evolution_promotion_engine import promote
    st = load(STATE, {'seen_sha256': [], 'processed': 0, 'promoted': 0, 'rejected': 0, 'rolled_back': 0})
    seen = set(st.get('seen_sha256', []))
    results = []
    for item in discover():
        if item['sha256'] in seen: continue
        result = promote(item['path'])
        status = str(result.get('status', 'UNKNOWN'))
        row = {'candidate': item, 'result': result, 'processed_at_unix': time.time()}
        append(LEDGER, row); results.append(row); seen.add(item['sha256'])
        st['processed'] = int(st.get('processed',0))+1
        if status == 'PROMOTED': st['promoted'] = int(st.get('promoted',0))+1
        elif status == 'ROLLED_BACK': st['rolled_back'] = int(st.get('rolled_back',0))+1
        elif status.startswith('REJECTED'): st['rejected'] = int(st.get('rejected',0))+1
    st['seen_sha256'] = list(seen)[-5000:]
    st['last_run_unix'] = time.time(); st['last_results'] = results[-50:]
    save(STATE, st)
    return {'ok': True, 'discovered_total': len(discover()), 'new_processed': len(results), 'results': results, 'state': st}
