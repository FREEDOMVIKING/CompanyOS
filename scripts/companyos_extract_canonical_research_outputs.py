from __future__ import annotations

import json
from pathlib import Path

ROOT = Path.home() / "companyos"
RAW_DIR = ROOT / ".companyos_runtime" / "canonical_research_outputs"

def main():
    from companyos.strategy.orchestration_candidate_extractor_v2 import (
        candidate_from_dict,
        dedupe,
        parse_candidate_blocks_from_text,
        slug,
        fingerprint,
    )

    out = []
    if not RAW_DIR.exists():
        print(json.dumps({"raw_capture_files": 0, "candidates_found": 0, "written": []}, indent=2))
        return

    files = sorted(RAW_DIR.glob("*.json"))
    for p in files[-100:]:
        try:
            obj = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        oid = obj.get("orchestration_id") or "unknown"

        # Inspect each captured return value as dict and text.
        for event in obj.get("returns", []):
            rv = event.get("return_value")
            if isinstance(rv, dict):
                c = candidate_from_dict(rv, oid, str(p.relative_to(ROOT)), extracted_from_text=False)
                if c:
                    out.append(c)
            text = json.dumps(rv, default=str) if not isinstance(rv, str) else rv
            for pd in parse_candidate_blocks_from_text(text):
                c = candidate_from_dict(pd, oid, str(p.relative_to(ROOT)), extracted_from_text=True)
                if c:
                    out.append(c)

        result = obj.get("result")
        if isinstance(result, dict):
            c = candidate_from_dict(result, oid, str(p.relative_to(ROOT)), extracted_from_text=False)
            if c:
                out.append(c)

    out = dedupe(out)
    candidate_dir = ROOT / ".companyos_runtime" / "profit_first_candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    written = []

    for c in out:
        fn = f"{slug(c['name'])}_{c['candidate_fingerprint']}.json"
        path = candidate_dir / fn
        existing = {}
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
        if existing and float(existing.get("evidence_confidence", 0) or 0) > float(c.get("evidence_confidence", 0) or 0):
            existing["orchestration_id"] = c.get("orchestration_id")
            existing.setdefault("source_orchestration_ids", [])
            if c.get("orchestration_id") not in existing["source_orchestration_ids"]:
                existing["source_orchestration_ids"].append(c.get("orchestration_id"))
            path.write_text(json.dumps(existing, indent=2, default=str) + "\n", encoding="utf-8")
        else:
            path.write_text(json.dumps(c, indent=2, default=str) + "\n", encoding="utf-8")
        written.append(str(path.relative_to(ROOT)))

    print(json.dumps({
        "raw_capture_files": len(files),
        "candidates_found": len(out),
        "written": written[:200],
    }, indent=2, default=str))

if __name__ == "__main__":
    main()
