"""Pure marketplace funnel conversion analysis."""

CAPABILITY_ID='marketplace_conversion_analytics'


def capability_manifest():
    return {
        "id": CAPABILITY_ID,
        "title": "Marketplace Conversion Analytics",
        "version": "1.0.0",
        "kind": "safe_analytical",
        "inputs": {
            "listings": "list of records with a non-empty id",
            "inquiries": "list of records with id and listing_id; transaction_id is optional",
            "transactions": "list of records with id and inquiry_id",
        },
        "outputs": [
            "listing_to_inquiry conversion rate",
            "inquiry_to_transaction conversion rate",
            "funnel counts",
            "data quality exclusions",
            "evidence limitations",
        ],
        "safety": {
            "pure": True,
            "network": False,
            "filesystem": False,
            "external_sends": False,
            "financial_decisions": False,
            "fabricated_evidence": False,
        },
    }


def _record_list(context, key):
    value = context.get(key, [])
    return value if isinstance(value, list) else []


def _identifier(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (str, int, float)):
        text = str(value).strip()
        return text or None
    return None


def _unique_records(records, id_key, quality):
    result = {}
    for record in records:
        if not isinstance(record, dict):
            quality["invalid_records"] += 1
            continue
        record_id = _identifier(record.get(id_key))
        if record_id is None:
            quality["missing_ids"] += 1
            continue
        if record_id in result:
            quality["duplicate_ids"] += 1
            continue
        result[record_id] = record
    return result


def _metric(numerator, denominator, unit):
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": (numerator / denominator) if denominator else None,
        "unit": unit,
        "evidence_status": "observed" if denominator else "insufficient_evidence",
    }


def evaluate(context):
    """Evaluate linked marketplace funnel records without making attribution assumptions."""
    quality = {
        "invalid_records": 0,
        "missing_ids": 0,
        "duplicate_ids": 0,
        "orphan_inquiries": 0,
        "unattributed_transactions": 0,
        "duplicate_links": 0,
    }
    if not isinstance(context, dict):
        return {
            "capability_id": CAPABILITY_ID,
            "status": "insufficient_evidence",
            "metrics": {
                "listing_to_inquiry": _metric(0, 0, "listings with at least one linked inquiry / eligible listings"),
                "inquiry_to_transaction": _metric(0, 0, "inquiries with at least one linked transaction / eligible inquiries"),
            },
            "funnel": {"listings": 0, "inquiries": 0, "transactions": 0},
            "data_quality": {**quality, "context_is_not_an_object": 1},
            "limitations": ["A mapping with listings, inquiries, and transactions is required."],
        }

    listings = _unique_records(_record_list(context, "listings"), "id", quality)
    raw_inquiries = _unique_records(_record_list(context, "inquiries"), "id", quality)
    raw_transactions = _unique_records(_record_list(context, "transactions"), "id", quality)

    inquiries = {}
    for inquiry_id, inquiry in raw_inquiries.items():
        listing_id = _identifier(inquiry.get("listing_id"))
        if listing_id not in listings:
            quality["orphan_inquiries"] += 1
            continue
        inquiries[inquiry_id] = inquiry

    transactions = {}
    inquiry_transaction_ids = {}
    for transaction_id, transaction in raw_transactions.items():
        inquiry_id = _identifier(transaction.get("inquiry_id"))
        if inquiry_id not in inquiries:
            quality["unattributed_transactions"] += 1
            continue
        transactions[transaction_id] = transaction
        inquiry_transaction_ids.setdefault(inquiry_id, set()).add(transaction_id)

    for inquiry_id, inquiry in inquiries.items():
        transaction_id = _identifier(inquiry.get("transaction_id"))
        if transaction_id is None:
            continue
        if transaction_id in transactions:
            inquiry_transaction_ids.setdefault(inquiry_id, set()).add(transaction_id)
        else:
            quality["unattributed_transactions"] += 1

    listings_with_inquiries = {
        _identifier(inquiry.get("listing_id"))
        for inquiry in inquiries.values()
        if _identifier(inquiry.get("listing_id")) is not None
    }
    converted_inquiries = {
        inquiry_id for inquiry_id, linked in inquiry_transaction_ids.items() if linked
    }

    listing_metric = _metric(
        len(listings_with_inquiries),
        len(listings),
        "listings with at least one linked inquiry / eligible listings",
    )
    inquiry_metric = _metric(
        len(converted_inquiries),
        len(inquiries),
        "inquiries with at least one linked transaction / eligible inquiries",
    )
    status = "ok" if listings or inquiries or transactions else "insufficient_evidence"
    limitations = [
        "Only explicit listing_id and inquiry_id links are used; timestamps, names, and free-text fields are not used for attribution.",
        "A zero denominator is reported as null rate rather than zero conversion.",
    ]
    if quality["orphan_inquiries"] or quality["unattributed_transactions"]:
        limitations.append("Records without a valid link to the measured funnel are excluded from denominators.")

    return {
        "capability_id": CAPABILITY_ID,
        "status": status,
        "metrics": {
            "listing_to_inquiry": listing_metric,
            "inquiry_to_transaction": inquiry_metric,
        },
        "funnel": {
            "listings": len(listings),
            "inquiries": len(inquiries),
            "transactions": len(transactions),
        },
        "data_quality": quality,
        "limitations": limitations,
    }
