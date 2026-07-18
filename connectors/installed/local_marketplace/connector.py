#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[4]
STOREFRONT_DIR = (
    ROOT_DIR
    / "companyos"
    / "local_marketplace"
    / "listings"
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")

    temporary.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    temporary.replace(path)


def health_check() -> dict[str, Any]:
    STOREFRONT_DIR.mkdir(parents=True, exist_ok=True)

    return {
        "success": True,
        "status": "healthy",
        "storefront_directory": str(STOREFRONT_DIR),
        "external_network_used": False,
    }


def publish(
    listing: dict[str, Any],
    product: dict[str, Any],
) -> dict[str, Any]:
    STOREFRONT_DIR.mkdir(parents=True, exist_ok=True)

    listing_id = str(listing.get("id", "")).strip()

    if not listing_id:
        return {
            "success": False,
            "error": "Listing ID is required",
        }

    published = {
        "listing_id": listing_id,
        "product_id": product.get("id"),
        "marketplace": "local",
        "title": listing.get("title"),
        "description": listing.get("description"),
        "price_usd": listing.get("price_usd"),
        "currency": "USD",
        "product_files": product.get("files", []),
        "status": "published",
        "published_at": now(),
    }

    path = STOREFRONT_DIR / f"{listing_id}.json"
    save_json(path, published)

    return {
        "success": True,
        "status": "listing_published",
        "connector_id": "local_marketplace",
        "external_id": listing_id,
        "external_url": (
            "local://marketplace/listings/"
            + listing_id
        ),
        "published_record": str(path),
        "published_at": now(),
    }
