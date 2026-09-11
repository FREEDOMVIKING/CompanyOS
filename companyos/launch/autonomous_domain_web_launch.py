from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
STATE = RUNTIME / "domain_web_launch_engine_state.json"
LAUNCH_DIR = RUNTIME / "launches"
SITE_EXPORT_DIR = ROOT / "exports" / "production_sites"

DEFAULT_DOMAIN_BUDGET_USD = float(os.getenv("COMPANYOS_DOMAIN_MAX_AUTONOMOUS_USD", "30"))
PREMIUM_DOMAIN_APPROVAL_USD = float(os.getenv("COMPANYOS_DOMAIN_PREMIUM_APPROVAL_USD", "100"))

def load(path: Path, default: Any):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return default

def save(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

def slug(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:50] or "venture"

def domain_candidates(venture: dict) -> list[str]:
    base = slug(venture.get("brand_name") or venture.get("name") or "venture")
    compact = base.replace("-", "")
    candidates = [
        f"{base}.com",
        f"{compact}.com",
        f"get{compact}.com",
        f"use{compact}.com",
        f"{compact}app.com",
        f"{compact}hq.com",
    ]
    # preserve order, remove dupes
    out = []
    for d in candidates:
        if d not in out:
            out.append(d)
    return out

def run_json_command(env_name: str, payload: dict, timeout: int = 90) -> dict:
    """
    Provider adapter contract.
    The env var contains a shell command. JSON payload is passed on stdin.
    Provider script must emit one JSON object on stdout.
    """
    cmd = os.getenv(env_name, "").strip()
    if not cmd:
        return {"ok": False, "reason": f"{env_name}_not_configured"}
    try:
        cp = subprocess.run(
            shlex.split(cmd),
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=timeout,
            cwd=ROOT,
        )
        if cp.returncode != 0:
            return {
                "ok": False,
                "reason": "provider_command_failed",
                "returncode": cp.returncode,
                "stderr": cp.stderr[-4000:],
            }
        return json.loads(cp.stdout.strip() or "{}")
    except Exception as exc:
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}

def check_domain(domain: str) -> dict:
    """
    Expected provider response:
    {
      "ok": true,
      "domain": "...",
      "available": true,
      "price_usd": 14.00,
      "premium": false
    }
    """
    return run_json_command("COMPANYOS_DOMAIN_CHECK_CMD", {"action": "check", "domain": domain})

def register_domain(domain: str, max_price_usd: float) -> dict:
    """
    Registration remains behind existing spending/approval policy.
    This adapter refuses above the autonomous budget before calling provider.
    """
    return run_json_command(
        "COMPANYOS_DOMAIN_REGISTER_CMD",
        {"action": "register", "domain": domain, "max_price_usd": max_price_usd},
    )

def configure_dns(domain: str, target: dict) -> dict:
    return run_json_command(
        "COMPANYOS_DNS_CONFIG_CMD",
        {"action": "configure_dns", "domain": domain, "target": target},
    )

def deploy_site(site_dir: Path, venture: dict) -> dict:
    """
    Hosting adapter receives local site path and venture metadata.
    Expected response should include a public URL and DNS target.
    """
    payload = {
        "action": "deploy",
        "site_dir": str(site_dir),
        "venture": venture,
    }
    return run_json_command("COMPANYOS_WEB_DEPLOY_CMD", payload, timeout=180)

def generate_site(venture: dict, domain: str | None = None) -> Path:
    name = venture.get("brand_name") or venture.get("name") or "New Venture"
    tagline = venture.get("tagline") or venture.get("description") or "A smarter way to get results."
    description = venture.get("description") or tagline
    offer = venture.get("offer") or "Get started today."
    cta = venture.get("cta") or "Get Started"
    contact = venture.get("contact_email") or "hello@example.com"
    launch_slug = slug(name)
    out = SITE_EXPORT_DIR / launch_slug
    out.mkdir(parents=True, exist_ok=True)

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title>
<meta name="description" content="{description}">
<style>
body{{font-family:Arial,sans-serif;margin:0;background:#0b1020;color:#f5f7fb}}
main{{max-width:1000px;margin:auto;padding:64px 24px}}
.hero{{padding:80px 0}}
h1{{font-size:clamp(42px,8vw,84px);line-height:1;margin:0 0 24px}}
p{{font-size:20px;line-height:1.6;color:#cbd5e1}}
.btn{{display:inline-block;padding:16px 24px;border-radius:12px;background:#fff;color:#0b1020;text-decoration:none;font-weight:700}}
.card{{margin-top:36px;padding:28px;border:1px solid #2b3658;border-radius:18px;background:#11182c}}
footer{{margin-top:80px;color:#94a3b8;font-size:14px}}
</style>
</head>
<body>
<main>
<section class="hero">
<div>{domain or "Launching soon"}</div>
<h1>{name}</h1>
<p>{tagline}</p>
<a class="btn" href="mailto:{contact}?subject={name}%20Inquiry">{cta}</a>
<div class="card">
<h2>What we offer</h2>
<p>{offer}</p>
<p>{description}</p>
</div>
</section>
<footer>© {time.gmtime().tm_year} {name}. All rights reserved.</footer>
</main>
</body>
</html>
"""
    (out / "index.html").write_text(html, encoding="utf-8")

    manifest = {
        "venture": venture,
        "domain": domain,
        "generated_at_unix": time.time(),
        "entrypoint": "index.html",
    }
    save(out / "launch_manifest.json", manifest)
    return out

def preflight(venture: dict) -> dict:
    required = ["name", "description"]
    missing = [k for k in required if not venture.get(k)]
    return {
        "ok": not missing,
        "missing": missing,
        "launch_ready": bool(venture.get("launch_ready", True)),
    }

def select_domain(venture: dict) -> dict:
    results = []
    for domain in domain_candidates(venture):
        check = check_domain(domain)
        results.append(check)
        if not check.get("ok") or not check.get("available"):
            continue
        price = float(check.get("price_usd", 999999) or 999999)
        premium = bool(check.get("premium", False))
        if premium or price > PREMIUM_DOMAIN_APPROVAL_USD:
            continue
        if price <= DEFAULT_DOMAIN_BUDGET_USD:
            return {
                "selected": domain,
                "price_usd": price,
                "check": check,
                "all_checks": results,
                "approval_required": False,
            }
    return {
        "selected": None,
        "all_checks": results,
        "approval_required": True,
        "reason": "no_domain_within_autonomous_budget_or_provider_unavailable",
    }

def launch_venture(venture: dict, allow_domain_purchase: bool = False) -> dict:
    """
    Real launch flow:
    preflight -> domain selection -> optional purchase -> site generation -> deploy -> DNS -> live checks

    Domain purchase is only attempted when allow_domain_purchase=True AND provider reports
    a price within COMPANYOS_DOMAIN_MAX_AUTONOMOUS_USD.
    """
    launch_id = f"{slug(venture.get('name','venture'))}-{int(time.time())}"
    report_path = LAUNCH_DIR / launch_id / "launch_report.json"

    pf = preflight(venture)
    if not pf["ok"] or not pf["launch_ready"]:
        report = {"ok": False, "stage": "preflight", "preflight": pf}
        save(report_path, report)
        return report

    domain_info = select_domain(venture)
    domain = domain_info.get("selected")

    registration = {"ok": False, "reason": "not_attempted"}
    if domain and allow_domain_purchase:
        max_price = min(DEFAULT_DOMAIN_BUDGET_USD, float(domain_info.get("price_usd", DEFAULT_DOMAIN_BUDGET_USD)))
        registration = register_domain(domain, max_price)
        if not registration.get("ok"):
            report = {
                "ok": False,
                "stage": "domain_registration",
                "domain": domain_info,
                "registration": registration,
            }
            save(report_path, report)
            return report

    site_dir = generate_site(venture, domain=domain)
    deploy = deploy_site(site_dir, venture)

    dns = {"ok": False, "reason": "not_attempted"}
    public_url = deploy.get("public_url") if isinstance(deploy, dict) else None
    if domain and deploy.get("ok") and deploy.get("dns_target"):
        dns = configure_dns(domain, deploy["dns_target"])

    status = "PREVIEW_READY"
    if deploy.get("ok") and public_url:
        status = "DEPLOYED"
    if domain and registration.get("ok") and dns.get("ok"):
        status = "LIVE"

    report = {
        "ok": status in {"PREVIEW_READY", "DEPLOYED", "LIVE"},
        "launch_id": launch_id,
        "status": status,
        "venture": venture,
        "domain": domain_info,
        "registration": registration,
        "site_dir": str(site_dir),
        "deploy": deploy,
        "dns": dns,
        "public_url": public_url,
        "generated_at_unix": time.time(),
    }
    save(report_path, report)

    state = load(STATE, {"launches": []})
    state.setdefault("launches", []).append(report)
    state["launches"] = state["launches"][-100:]
    state["last_launch"] = report
    save(STATE, state)
    return report
