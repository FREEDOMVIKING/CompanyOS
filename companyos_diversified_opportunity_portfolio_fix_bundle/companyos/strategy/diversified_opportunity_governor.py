from __future__ import annotations
from collections import Counter
from pathlib import Path

ROOT = Path.home() / "companyos"

SECTORS = {
    "construction": ["contractor","construction","concrete","bid organizer"],
    "ai_software": ["ai","agent","assistant","copilot"],
    "b2b_automation": ["workflow","crm","automation","operations"],
    "consumer_apps": ["consumer","mobile app","personal"],
    "ecommerce": ["store","shop","commerce","retail"],
    "digital_products": ["template","course","ebook","download"],
    "local_services": ["local service","cleaning","repair","lawn"],
    "marketplaces": ["marketplace","matching platform"],
    "data_information_products": ["data","research","intelligence","report"],
    "finance_ops_tools": ["accounting","billing","finance","bookkeeping"],
    "education_tools": ["education","learning","training","study"],
    "creator_tools": ["creator","content","video","podcast"],
}

def classify_sector(text):
    t=(text or "").lower()
    scored={s:sum(1 for h in hints if h in t) for s,hints in SECTORS.items()}
    best=max(scored,key=scored.get) if scored else "unknown"
    return best if scored.get(best,0)>0 else "unknown"

def portfolio_sector_counts():
    counts=Counter()
    for root in [ROOT/"workspace",ROOT/"exports",ROOT/"products"]:
        if not root.exists():
            continue
        for p in root.iterdir():
            if p.is_dir():
                counts[classify_sector(p.name.replace("_"," "))]+=1
    return counts

def should_force_diversified_discovery():
    counts=portfolio_sector_counts()
    total=sum(counts.values())
    return bool(total>=2 and max(counts.values())/total>=0.50)

def discovery_directive():
    counts=portfolio_sector_counts()
    return f"""Run a diversified CompanyOS opportunity discovery cycle.

Current portfolio sector counts: {dict(counts)}

Requirements:
1. Discover at least 12 genuinely different opportunities across at least 6 unrelated sectors.
2. Do not clone, rename, version, or lightly modify an existing venture and count it as new.
3. Score every opportunity by demand, margin, automation potential, scalability, time-to-revenue, feasibility, competition, and startup cost.
4. Penalize sectors already overrepresented in the portfolio, but never ban a sector.
5. Construction remains allowed and must compete economically against unrelated sectors.
6. Prefer opportunities that are cheap to validate, highly automatable, scalable, and fast to revenue.
7. Reject weak ventures instead of keeping everything alive indefinitely.
8. Recommend no more than 3 ventures for active validation.
9. Internal research, analysis, planning, prototyping, and delegation may proceed autonomously.
10. Keep consequential external actions, spending, irreversible commitments, credentials, and financial transactions behind existing approval and safety gates.
"""

def state_snapshot():
    counts=portfolio_sector_counts()
    total=sum(counts.values())
    largest=(max(counts.values())/total) if total else 0.0
    return {
        "sector_counts":dict(counts),
        "portfolio_total":total,
        "largest_sector_share":round(largest,3),
        "diversified_discovery_recommended":should_force_diversified_discovery(),
    }
