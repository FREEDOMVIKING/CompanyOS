#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
AGENTS_DIR="$ROOT_DIR/agents"
MEMORY_DIR="$ROOT_DIR/ceo_memory"
PRODUCT_DIR="$ROOT_DIR/company_products"
MANIFEST_FILE="$ROOT_DIR/companyos/manifest.json"

mkdir -p \
    "$AGENTS_DIR" \
    "$MEMORY_DIR/publishing_reports" \
    "$PRODUCT_DIR"

touch "$AGENTS_DIR/__init__.py"

echo
echo "[1/6] Creating Publisher Agent..."

cat > "$AGENTS_DIR/publisher_agent.py" <<'PYTHON'
#!/usr/bin/env python3

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = BASE_DIR / "ceo_memory"
PRODUCT_DIR = BASE_DIR / "company_products"

PRODUCTS_FILE = MEMORY_DIR / "products.json"
LISTINGS_FILE = MEMORY_DIR / "marketplace_listings.json"
QUEUE_FILE = MEMORY_DIR / "publication_queue.json"
SUMMARY_FILE = MEMORY_DIR / "publishing_summary.json"
REPORT_DIR = MEMORY_DIR / "publishing_reports"

SUPPORTED_MARKETPLACES = {
    "local",
    "website",
    "etsy",
    "gumroad",
    "shopify",
}

SAFE_SLUG = re.compile(r"[^a-zA-Z0-9_-]+")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def normalize_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [
            item
            for item in value
            if isinstance(item, dict)
        ]

    return []


def slugify(value: str) -> str:
    cleaned = SAFE_SLUG.sub(
        "_",
        value.strip().lower(),
    )

    return cleaned.strip("_") or "unnamed_product"


def find_record(
    records: list[dict[str, Any]],
    record_id: str,
) -> dict[str, Any] | None:
    return next(
        (
            item
            for item in records
            if str(item.get("id", "")) == record_id
        ),
        None,
    )


def create_product(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    name = str(payload.get("name", "")).strip()
    description = str(
        payload.get("description", "")
    ).strip()
    product_type = str(
        payload.get("product_type", "digital")
    ).strip().lower()
    price = float(payload.get("price_usd", 0) or 0)

    if not name:
        return {
            "success": False,
            "error": "Product name is required",
        }

    if not description:
        return {
            "success": False,
            "error": "Product description is required",
        }

    if price < 0:
        return {
            "success": False,
            "error": "price_usd cannot be negative",
        }

    products = normalize_list(
        load_json(PRODUCTS_FILE, [])
    )

    product_id = f"product-{uuid.uuid4().hex[:10]}"
    slug = slugify(name)
    product_path = PRODUCT_DIR / f"{slug}_{product_id[-4:]}"

    product_path.mkdir(parents=True, exist_ok=False)

    product = {
        "id": product_id,
        "name": name,
        "slug": product_path.name,
        "description": description,
        "short_description": str(
            payload.get(
                "short_description",
                description[:160],
            )
        ),
        "product_type": product_type,
        "price_usd": price,
        "currency": "USD",
        "project_id": payload.get("project_id"),
        "venture_id": payload.get("venture_id"),
        "status": "draft",
        "files": [],
        "marketplaces": [],
        "created_at": now(),
        "updated_at": now(),
    }

    readme = f"""# {name}

## Description
{description}

## Type
{product_type}

## Price
${price:.2f}

## Status
Draft

This product package was prepared by CompanyOS.
Public publication still requires an approved marketplace connector.
"""

    (product_path / "README.md").write_text(
        readme,
        encoding="utf-8",
    )

    save_json(
        product_path / "product.json",
        product,
    )

    products.append(product)
    save_json(PRODUCTS_FILE, products)

    refresh_summary()

    return {
        "success": True,
        "status": "product_created",
        "product": product,
        "workspace": str(product_path),
    }


def attach_file(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    product_id = str(
        payload.get("product_id", "")
    ).strip()
    source_path = str(
        payload.get("source_path", "")
    ).strip()

    if not product_id or not source_path:
        return {
            "success": False,
            "error": "product_id and source_path are required",
        }

    products = normalize_list(
        load_json(PRODUCTS_FILE, [])
    )
    product = find_record(products, product_id)

    if product is None:
        return {
            "success": False,
            "error": f"Product not found: {product_id}",
        }

    source = Path(source_path).expanduser().resolve()
    root = BASE_DIR.resolve()

    try:
        source.relative_to(root)
    except ValueError:
        return {
            "success": False,
            "error": "Files must come from inside the project folder",
        }

    if not source.exists() or not source.is_file():
        return {
            "success": False,
            "error": "Source file does not exist",
        }

    product_path = PRODUCT_DIR / product["slug"]
    files_path = product_path / "files"
    files_path.mkdir(parents=True, exist_ok=True)

    destination = files_path / source.name
    destination.write_bytes(source.read_bytes())

    file_entry = {
        "filename": source.name,
        "path": str(destination),
        "size_bytes": destination.stat().st_size,
        "added_at": now(),
    }

    product.setdefault("files", []).append(file_entry)
    product["updated_at"] = now()

    save_json(PRODUCTS_FILE, products)
    save_json(
        product_path / "product.json",
        product,
    )

    return {
        "success": True,
        "status": "product_file_attached",
        "product_id": product_id,
        "file": file_entry,
    }


def create_listing(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    product_id = str(
        payload.get("product_id", "")
    ).strip()
    marketplace = str(
        payload.get("marketplace", "local")
    ).strip().lower()

    if marketplace not in SUPPORTED_MARKETPLACES:
        return {
            "success": False,
            "error": (
                "Unsupported marketplace. Allowed: "
                + ", ".join(sorted(SUPPORTED_MARKETPLACES))
            ),
        }

    products = normalize_list(
        load_json(PRODUCTS_FILE, [])
    )
    listings = normalize_list(
        load_json(LISTINGS_FILE, [])
    )

    product = find_record(products, product_id)

    if product is None:
        return {
            "success": False,
            "error": f"Product not found: {product_id}",
        }

    duplicate = next(
        (
            listing
            for listing in listings
            if listing.get("product_id") == product_id
            and listing.get("marketplace") == marketplace
            and listing.get("status") not in {
                "cancelled",
                "archived",
            }
        ),
        None,
    )

    if duplicate:
        return {
            "success": False,
            "error": "An active listing already exists",
            "listing_id": duplicate.get("id"),
        }

    listing = {
        "id": f"listing-{uuid.uuid4().hex[:10]}",
        "product_id": product_id,
        "marketplace": marketplace,
        "title": str(
            payload.get("title", product["name"])
        ),
        "description": str(
            payload.get(
                "description",
                product["description"],
            )
        ),
        "price_usd": float(
            payload.get(
                "price_usd",
                product["price_usd"],
            )
        ),
        "tags": payload.get("tags", []),
        "status": "prepared",
        "approval_required": marketplace != "local",
        "approved": marketplace == "local",
        "external_id": None,
        "external_url": None,
        "created_at": now(),
        "updated_at": now(),
    }

    listings.append(listing)
    save_json(LISTINGS_FILE, listings)

    if marketplace not in product["marketplaces"]:
        product["marketplaces"].append(marketplace)
        product["updated_at"] = now()
        save_json(PRODUCTS_FILE, products)

    refresh_summary()

    return {
        "success": True,
        "status": "listing_prepared",
        "listing": listing,
    }


def queue_listing(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    listing_id = str(
        payload.get("listing_id", "")
    ).strip()

    listings = normalize_list(
        load_json(LISTINGS_FILE, [])
    )
    queue = normalize_list(
        load_json(QUEUE_FILE, [])
    )

    listing = find_record(listings, listing_id)

    if listing is None:
        return {
            "success": False,
            "error": f"Listing not found: {listing_id}",
        }

    if listing.get("approval_required") and not listing.get(
        "approved"
    ):
        return {
            "success": False,
            "status": "owner_approval_required",
            "error": (
                "External marketplace publication requires approval"
            ),
        }

    existing = next(
        (
            item
            for item in queue
            if item.get("listing_id") == listing_id
            and item.get("status") in {
                "queued",
                "processing",
            }
        ),
        None,
    )

    if existing:
        return {
            "success": False,
            "error": "Listing is already queued",
        }

    queue_item = {
        "id": f"publish-{uuid.uuid4().hex[:10]}",
        "listing_id": listing_id,
        "marketplace": listing.get("marketplace"),
        "status": "queued",
        "created_at": now(),
        "processed_at": None,
    }

    queue.append(queue_item)
    listing["status"] = "queued"
    listing["updated_at"] = now()

    save_json(QUEUE_FILE, queue)
    save_json(LISTINGS_FILE, listings)

    refresh_summary()

    return {
        "success": True,
        "status": "listing_queued",
        "queue_item": queue_item,
    }


def approve_listing(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    listing_id = str(
        payload.get("listing_id", "")
    ).strip()

    listings = normalize_list(
        load_json(LISTINGS_FILE, [])
    )
    listing = find_record(listings, listing_id)

    if listing is None:
        return {
            "success": False,
            "error": f"Listing not found: {listing_id}",
        }

    listing["approved"] = True
    listing["approved_at"] = now()
    listing["updated_at"] = now()

    save_json(LISTINGS_FILE, listings)

    return {
        "success": True,
        "status": "listing_approved",
        "listing": listing,
    }


def list_products() -> dict[str, Any]:
    products = normalize_list(
        load_json(PRODUCTS_FILE, [])
    )

    return {
        "success": True,
        "status": "products_listed",
        "count": len(products),
        "products": products,
    }


def list_listings() -> dict[str, Any]:
    listings = normalize_list(
        load_json(LISTINGS_FILE, [])
    )

    return {
        "success": True,
        "status": "listings_listed",
        "count": len(listings),
        "listings": listings,
    }


def refresh_summary() -> dict[str, Any]:
    products = normalize_list(
        load_json(PRODUCTS_FILE, [])
    )
    listings = normalize_list(
        load_json(LISTINGS_FILE, [])
    )
    queue = normalize_list(
        load_json(QUEUE_FILE, [])
    )

    summary = {
        "success": True,
        "status": "publishing_summary_created",
        "updated_at": now(),
        "total_products": len(products),
        "draft_products": len([
            product
            for product in products
            if product.get("status") == "draft"
        ]),
        "total_listings": len(listings),
        "prepared_listings": len([
            listing
            for listing in listings
            if listing.get("status") == "prepared"
        ]),
        "queued_listings": len([
            item
            for item in queue
            if item.get("status") == "queued"
        ]),
        "approval_required": len([
            listing
            for listing in listings
            if listing.get("approval_required")
            and not listing.get("approved")
        ]),
    }

    save_json(SUMMARY_FILE, summary)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    save_json(
        REPORT_DIR / (
            "publishing_report_"
            + datetime.now(timezone.utc).strftime(
                "%Y%m%d_%H%M%S"
            )
            + ".json"
        ),
        summary,
    )

    return summary


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action == "create_product":
        return create_product(task)

    if action == "attach_product_file":
        return attach_file(task)

    if action == "create_listing":
        return create_listing(task)

    if action == "approve_listing":
        return approve_listing(task)

    if action == "queue_listing":
        return queue_listing(task)

    if action == "list_products":
        return list_products()

    if action == "list_listings":
        return list_listings()

    if action == "publishing_summary":
        return refresh_summary()

    return {
        "success": False,
        "error": f"Unsupported publisher action: {action}",
    }


if __name__ == "__main__":
    print(json.dumps(refresh_summary(), indent=2))
PYTHON

chmod +x "$AGENTS_DIR/publisher_agent.py"

echo
echo "[2/6] Initializing publisher memory..."

for FILE in \
    products.json \
    marketplace_listings.json \
    publication_queue.json
do
    [ -f "$MEMORY_DIR/$FILE" ] || \
        printf '[]\n' > "$MEMORY_DIR/$FILE"
done

[ -f "$MEMORY_DIR/publishing_summary.json" ] || \
    printf '{}\n' > "$MEMORY_DIR/publishing_summary.json"

echo
echo "[3/6] Creating publisher command utility..."

cat > "$ROOT_DIR/companyos/publishctl" <<'PYTHON'
#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.publisher_agent import run_task


def output(data) -> None:
    print(json.dumps(data, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CompanyOS Marketplace Publisher"
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    commands.add_parser("products")
    commands.add_parser("listings")
    commands.add_parser("summary")

    product_parser = commands.add_parser("create-product")
    product_parser.add_argument("--name", required=True)
    product_parser.add_argument(
        "--description",
        required=True,
    )
    product_parser.add_argument(
        "--type",
        default="digital",
    )
    product_parser.add_argument(
        "--price",
        type=float,
        default=0,
    )
    product_parser.add_argument(
        "--project-id",
        default="",
    )
    product_parser.add_argument(
        "--venture-id",
        default="",
    )

    listing_parser = commands.add_parser("create-listing")
    listing_parser.add_argument("product_id")
    listing_parser.add_argument(
        "--marketplace",
        default="local",
    )
    listing_parser.add_argument(
        "--price",
        type=float,
        default=None,
    )

    approve_parser = commands.add_parser("approve")
    approve_parser.add_argument("listing_id")

    queue_parser = commands.add_parser("queue")
    queue_parser.add_argument("listing_id")

    args = parser.parse_args()

    if args.command == "products":
        result = run_task({
            "action": "list_products",
        })

    elif args.command == "listings":
        result = run_task({
            "action": "list_listings",
        })

    elif args.command == "summary":
        result = run_task({
            "action": "publishing_summary",
        })

    elif args.command == "create-product":
        result = run_task({
            "action": "create_product",
            "payload": {
                "name": args.name,
                "description": args.description,
                "product_type": args.type,
                "price_usd": args.price,
                "project_id": args.project_id,
                "venture_id": args.venture_id,
            },
        })

    elif args.command == "create-listing":
        payload = {
            "product_id": args.product_id,
            "marketplace": args.marketplace,
        }

        if args.price is not None:
            payload["price_usd"] = args.price

        result = run_task({
            "action": "create_listing",
            "payload": payload,
        })

    elif args.command == "approve":
        result = run_task({
            "action": "approve_listing",
            "payload": {
                "listing_id": args.listing_id,
            },
        })

    else:
        result = run_task({
            "action": "queue_listing",
            "payload": {
                "listing_id": args.listing_id,
            },
        })

    output(result)

    if result.get("success") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
PYTHON

chmod +x "$ROOT_DIR/companyos/publishctl"

echo
echo "[4/6] Updating CompanyOS manifest..."

python - "$MANIFEST_FILE" <<'PYTHON'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))

modules = data.setdefault("modules", {})
publisher = modules.setdefault("publisher", {})

publisher.update({
    "installed": True,
    "enabled": True,
    "version": "1.0.0",
    "agent": "agents/publisher_agent.py",
    "workspace": "company_products",
    "external_publication_requires_approval": True
})

path.write_text(
    json.dumps(data, indent=2),
    encoding="utf-8",
)

print("Publisher manifest entry updated.")
PYTHON

echo
echo "[5/6] Compiling and testing..."

python -m py_compile \
    "$AGENTS_DIR/publisher_agent.py" \
    "$ROOT_DIR/companyos/publishctl"

python "$ROOT_DIR/companyos/publishctl" summary

echo
echo "[6/6] Running CompanyOS verification..."

bash "$ROOT_DIR/companyos/verify.sh"

echo
echo "============================================================"
echo " MARKETPLACE PUBLISHER INSTALLED SUCCESSFULLY"
echo "============================================================"
echo
echo "Create a test product:"
echo
echo "  python companyos/publishctl create-product \\"
echo '    --name "Small Business Starter Templates" \'
echo '    --description "Editable templates and checklists for small businesses." \'
echo '    --type digital \'
echo '    --price 9.99'
echo
echo "View products:"
echo
echo "  python companyos/publishctl products"
