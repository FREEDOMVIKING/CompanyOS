#!/usr/bin/env python3

import json
import os
import sys
from http.server import (
    SimpleHTTPRequestHandler,
    ThreadingHTTPServer,
)
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PUBLIC_DIR = ROOT_DIR / "companyos" / "storefront" / "public"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.sales_agent import run_task  # noqa: E402

HOST = os.environ.get(
    "COMPANYOS_STOREFRONT_HOST",
    "127.0.0.1",
)

PORT = int(
    os.environ.get(
        "COMPANYOS_STOREFRONT_PORT",
        "8780",
    )
)


def product_id_from_path(path: str) -> str | None:
    if not path.startswith("/products/"):
        return None

    products_file = ROOT_DIR / "ceo_memory" / "products.json"

    try:
        products = json.loads(
            products_file.read_text(encoding="utf-8")
        )
    except Exception:
        return None

    filename = Path(path).name

    for product in products:
        if not isinstance(product, dict):
            continue

        slug = str(product.get("slug", ""))

        if filename == f"{slug}.html":
            return str(product.get("id", "")) or None

    return None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            directory=str(PUBLIC_DIR),
            **kwargs,
        )

    def send_json(
        self,
        data: Any,
        status: int = 200,
    ) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path in {"/", "/index.html"}:
            run_task({
                "action": "record_sales_event",
                "payload": {
                    "event_type": "storefront_view",
                    "path": path,
                    "source": "storefront_server",
                },
            })

        elif path.startswith("/products/"):
            run_task({
                "action": "record_sales_event",
                "payload": {
                    "event_type": "product_view",
                    "path": path,
                    "product_id": product_id_from_path(path),
                    "source": "storefront_server",
                },
            })

        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        if path != "/api/event":
            self.send_json(
                {
                    "success": False,
                    "error": "Not found",
                },
                status=404,
            )
            return

        try:
            length = int(
                self.headers.get("Content-Length", "0")
            )

            if length > 10000:
                raise ValueError("Request is too large")

            raw = self.rfile.read(length)
            data = json.loads(
                raw.decode("utf-8")
                if raw
                else "{}"
            )

            if not isinstance(data, dict):
                raise ValueError(
                    "Event body must be an object"
                )

            result = run_task({
                "action": "record_sales_event",
                "payload": data,
            })

            self.send_json(
                result,
                status=(
                    200
                    if result.get("success")
                    else 400
                ),
            )

        except Exception as error:
            self.send_json(
                {
                    "success": False,
                    "error": str(error),
                },
                status=400,
            )


def main() -> None:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    server = ThreadingHTTPServer(
        (HOST, PORT),
        Handler,
    )

    print("=" * 60)
    print("CompanyOS Storefront with Sales Tracking")
    print(f"Address: http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStorefront stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
