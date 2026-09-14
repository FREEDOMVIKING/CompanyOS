CAPABILITY_ID = "external_evidence_requirements_analyzer"

_REQUIREMENTS = (
    ("provenance", "Identify the origin and ownership of each proposed evidence item."),
    ("recency", "Define the acceptable observation period or freshness rule for evidence."),
    ("authority", "Specify the authority or qualification expected from the evidence source."),
    ("corroboration", "Plan an independent corroboration rule for material claims."),
    ("relevance", "Map each evidence item to the candidate claim or qualification criterion."),
    ("traceability", "Define an internal reference, timestamp, and review record for each item."),
)
_EVIDENCE_KEYS = (
    "external_evidence",
    "evidence",
    "sources",
    "citations",
    "provenance",
    "references",
)


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _sequence(value):
    return value if isinstance(value, (list, tuple)) else []


def _text(value):
    return value.strip() if isinstance(value, str) else ""


def _candidate_ids(context, detail):
    raw = detail.get("candidate_ids")
    if not isinstance(raw, (list, tuple)):
        raw = context.get("candidate_ids", [])
    result = []
    for item in raw:
        value = _text(item)
        if value and value not in result:
            result.append(value)
    return result


def _records(context):
    raw = context.get("candidates", context.get("candidate_records", {}))
    if isinstance(raw, dict):
        return raw
    result = {}
    for item in _sequence(raw):
        record = _mapping(item)
        identifier = _text(record.get("candidate_id", record.get("id")))
        if identifier:
            result[identifier] = record
    return result


def _has_evidence(record):
    for key in _EVIDENCE_KEYS:
        value = record.get(key)
        if isinstance(value, (list, tuple, dict)) and len(value) > 0:
            return True
        if _text(value):
            return True
    return False


def capability_manifest():
    return {
        "capability_id": CAPABILITY_ID,
        "title": "External Evidence Requirements Analyzer",
        "kind": "analytical",
        "safe": True,
        "inputs": ["context", "semantic_evidence", "candidate_records"],
        "outputs": ["evidence_requirements", "candidate_guidance", "summary"],
        "side_effects": [],
        "external_actions": False,
    }


def evaluate(context):
    context = _mapping(context)
    request = _mapping(context.get("compounding_request"))
    semantic = _mapping(context.get("semantic_evidence"))
    if not semantic:
        semantic = _mapping(request.get("semantic_evidence"))
    detail = _mapping(semantic.get("detail"))
    reason = _text(semantic.get("reason")) or _text(detail.get("reason")) or "missing_external_evidence"
    gap_id = _text(context.get("gap_id")) or _text(request.get("gap_id"))
    source = _text(context.get("source_capability")) or _text(request.get("source_capability"))
    identifiers = _candidate_ids(context, detail)
    records = _records(context)

    requirements = []
    for key, guidance in _REQUIREMENTS:
        requirements.append({
            "requirement": key,
            "guidance": guidance,
            "status": "observed" if any(_has_evidence(records.get(identifier, {})) for identifier in identifiers) else "not_observed",
            "planning_only": True,
        })

    candidate_guidance = []
    for identifier in identifiers:
        observed = _has_evidence(records.get(identifier, {}))
        candidate_guidance.append({
            "candidate_id": identifier,
            "evidence_state": "evidence_reference_observed" if observed else "external_evidence_not_observed",
            "next_internal_step": "Map existing references to the six evidence requirements before qualification." if observed else "Define and document evidence requirements before any qualification decision.",
            "external_retrieval_performed": False,
        })

    affected = detail.get("affected_candidates")
    if not isinstance(affected, int) or affected < 0:
        affected = len(identifiers)
    return {
        "capability_id": CAPABILITY_ID,
        "status": "guidance_ready",
        "gap_id": gap_id,
        "source_capability": source,
        "bottleneck": reason,
        "evidence_requirements": requirements,
        "candidate_guidance": candidate_guidance,
        "summary": {
            "affected_candidates": affected,
            "candidate_ids_provided": len(identifiers),
            "evidence_records_observed": sum(1 for identifier in identifiers if _has_evidence(records.get(identifier, {}))),
            "requirements_count": len(requirements),
            "external_retrieval_performed": False,
            "decision_or_approval_made": False,
        },
    }
