import json
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def design_business(opportunity):
    title = opportunity.get("title", "Untitled opportunity")
    summary = opportunity.get("summary", "")

    architecture = {
        "problem": summary or f"Validated problem behind {title}",
        "customer": "Define primary paying customer segment",
        "value_proposition": f"Deliver a focused solution for {title}",
        "offer": "Start with a narrow, testable paid offer",
        "distribution": [
            "direct outreach",
            "content/organic acquisition",
            "partner/referral channels",
        ],
        "revenue_model": [
            "subscription",
            "usage-based",
            "project/service fee",
        ],
        "automation_plan": [
            "automate intake",
            "automate delivery workflow",
            "automate monitoring and follow-up",
        ],
        "first_validation": "Acquire evidence of demand before financial commitment.",
    }

    return {
        "success": True,
        "status": "phase73_business_architecture_complete",
        "opportunity_id": opportunity.get("opportunity_id"),
        "title": title,
        "architecture": architecture,
        "created_at": now(),
    }

def status():
    return {
        "success": True,
        "status": "phase73_business_architect_status",
        "ready": True,
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
