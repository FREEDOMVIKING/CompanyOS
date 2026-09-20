import re

INTERNAL = {
    "accounting","runtime","logs","backups","backup","tmp","temp","quotes",
    "projects","invoices","artifacts","exports","dashboard","ceo_memory",
    "companyos_runtime",
    # Deployment output container, not a venture identity.
    "production_sites",
}

def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower())
    return re.sub(r"_+", "_", s).strip("_")

def canonical_id(name):
    s = slugify(name)
    patterns = [
        r"_?v\d+(?:_\d+){0,2}$",
        r"_?version_?\d+$",
        r"_?release_?\d+$",
        r"_?build_?\d+$",
    ]
    changed = True
    while changed:
        changed = False
        for pat in patterns:
            n = re.sub(pat, "", s, flags=re.I).strip("_")
            if n != s:
                s = n
                changed = True
    return s

def is_internal(name):
    return canonical_id(name) in {canonical_id(x) for x in INTERNAL}

def display_name(cid):
    return "_".join(x.capitalize() for x in cid.split("_") if x)
