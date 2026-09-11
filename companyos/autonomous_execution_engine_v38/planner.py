import hashlib

def slugify(name):
    out = []
    for ch in str(name).lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "_", "-"):
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "venture"

def plan_for(venture):
    name = venture.get("venture_name") or "Unnamed Venture"
    vid = venture.get("venture_id") or hashlib.sha256(name.encode()).hexdigest()[:16]
    slug = slugify(name)
    return {
        "execution_id": f"exec-{vid}",
        "venture_id": vid,
        "venture_name": name,
        "slug": slug,
        "source_review_id": venture.get("review_id"),
        "launch_score": float(venture.get("launch_score", 0) or 0),
        "steps": [
            {"step":"workspace","required":True},
            {"step":"product_package","required":True},
            {"step":"website_bundle","required":True},
            {"step":"checkout_manifest","required":True},
            {"step":"customer_delivery_manifest","required":True},
            {"step":"rollback_snapshot","required":True},
            {"step":"external_execution_review_packet","required":True},
        ],
    }
