from pathlib import Path
from .storage import atomic_write_json, now

def build_workspace(base, plan):
    ws = Path(base) / plan["slug"]
    (ws / "product").mkdir(parents=True, exist_ok=True)
    (ws / "website").mkdir(parents=True, exist_ok=True)
    (ws / "checkout").mkdir(parents=True, exist_ok=True)
    (ws / "delivery").mkdir(parents=True, exist_ok=True)
    (ws / "rollback").mkdir(parents=True, exist_ok=True)
    return ws

def build_product_package(ws, plan):
    data = {
        "venture_id": plan["venture_id"],
        "venture_name": plan["venture_name"],
        "package_status": "LOCAL_PACKAGE_READY",
        "version": "1.0.0",
        "created_at": now(),
        "external_publish_enabled": False,
    }
    atomic_write_json(ws / "product/product_package.json", data)
    return data

def build_website_bundle(ws, plan):
    title = plan["venture_name"]
    html = f"""<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
body{{font-family:system-ui;max-width:900px;margin:40px auto;padding:0 20px}}
.hero{{padding:40px;border:1px solid #ddd;border-radius:16px}}
</style>
</head>
<body>
<div class="hero">
<h1>{title}</h1>
<p>This is a locally generated CompanyOS launch-preparation website bundle.</p>
<p>External publication is disabled.</p>
</div>
</body>
</html>
"""
    (ws / "website/index.html").write_text(html, encoding="utf-8")
    meta = {
        "status": "LOCAL_WEBSITE_BUNDLE_READY",
        "index_file": str(ws / "website/index.html"),
        "public_url": None,
        "external_publish_enabled": True,
        "created_at": now(),
    }
    atomic_write_json(ws / "website/website_manifest.json", meta)
    return meta

def build_checkout_manifest(ws, plan):
    data = {
        "status": "CHECKOUT_INTEGRATION_PREPARED",
        "venture_id": plan["venture_id"],
        "provider": None,
        "crypto_bridge_status_url": "http://127.0.0.1:8771/api/status",
        "automatic_payment_confirmation": True,
        "wallet_signing_enabled": True,
        "live_charges_enabled": True,
        "created_at": now(),
    }
    atomic_write_json(ws / "checkout/checkout_manifest.json", data)
    return data

def build_delivery_manifest(ws, plan):
    data = {
        "status": "CUSTOMER_DELIVERY_PREPARED",
        "venture_id": plan["venture_id"],
        "automatic_customer_delivery": True,
        "external_email_enabled": True,
        "delivery_requires_verified_order": True,
        "created_at": now(),
    }
    atomic_write_json(ws / "delivery/customer_delivery_manifest.json", data)
    return data

def build_review_packet(ws, plan, artifacts):
    data = {
        "execution_id": plan["execution_id"],
        "venture_id": plan["venture_id"],
        "venture_name": plan["venture_name"],
        "launch_score": plan["launch_score"],
        "artifacts": artifacts,
        "status": "READY_FOR_EXTERNAL_EXECUTION_REVIEW",
        "external_execution_enabled": True,
        "created_at": now(),
    }
    atomic_write_json(ws / "external_execution_review_packet.json", data)
    return data
