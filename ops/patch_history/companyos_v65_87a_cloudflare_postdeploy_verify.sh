#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.87A CLOUDFLARE POST-DEPLOY VERIFY ====="
echo "ACTION=VERIFY_EXISTING_DEPLOYMENT_ONLY"
echo "REDEPLOY=NO"
echo "FINANCIAL_ACTIONS=DISABLED"

python - <<'PY'
from pathlib import Path
import json, os, re, socket, statistics, time, urllib.request

HOME = Path.home()
ROOT = HOME / "companyos"
LOCAL_RT = ROOT / ".companyos_runtime"
GLOBAL_RT = HOME / ".companyos_runtime"
REPORT_DIR = GLOBAL_RT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def load_json(path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(Path(path).read_text(errors="ignore"))
    except Exception:
        return default

# Recover the same top candidate used by V65.87.
status = load_json(LOCAL_RT / "profit_opportunity_status.json", {})
ranked = [x for x in (status.get("ranked") or []) if isinstance(x, dict)]
if not ranked:
    raise SystemExit("V65_87A_ABORT=no_ranked_candidate")

candidate = ranked[0]
name = str(candidate.get("name") or candidate.get("title") or "companyos-validation")
slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60] or "companyos-validation"
project_name = ("companyos-" + slug)[:58]

print("CANDIDATE_NAME=", name)
print("PROJECT_NAME=", project_name)

from companyos.connectors.cloudflare_hosting import CloudflareHosting
cf = CloudflareHosting()

if not cf.configured:
    raise SystemExit("V65_87A_ABORT=cloudflare_not_configured")

project = cf.project(project_name)
print("CLOUDFLARE_PROJECT_FOUND=", bool(project))
print("CLOUDFLARE_PROJECT_SUBDOMAIN=", project.get("subdomain"))
print("CLOUDFLARE_PROJECT_DOMAINS=", project.get("domains") or [])

latest = project.get("latest_deployment") or {}
canonical = project.get("canonical_deployment") or {}

print("LATEST_DEPLOYMENT_ID=", latest.get("id"))
print("LATEST_DEPLOYMENT_URL=", latest.get("url"))
print("LATEST_DEPLOYMENT_ENVIRONMENT=", latest.get("environment"))
print("LATEST_DEPLOYMENT_ALIASES=", latest.get("aliases") or [])
print("LATEST_DEPLOYMENT_STAGES=", latest.get("stages") or {})
print("CANONICAL_DEPLOYMENT_ID=", canonical.get("id"))
print("CANONICAL_DEPLOYMENT_URL=", canonical.get("url"))

urls = []

def add_url(v):
    if not v:
        return
    s = str(v).strip()
    if not s:
        return
    if not s.startswith(("http://", "https://")):
        s = "https://" + s
    if s not in urls:
        urls.append(s)

add_url(latest.get("url"))
for a in latest.get("aliases") or []:
    add_url(a)
add_url(canonical.get("url"))
add_url(project.get("subdomain"))
for d in project.get("domains") or []:
    add_url(d)

if not urls:
    raise SystemExit("V65_87A_ABORT=no_project_url_found")

print("URL_CANDIDATES=", urls)

# Cloudflare Pages can return from deployment creation before Android/Termux DNS
# sees the new hostname. Retry resolution + HTTP without creating a new deploy.
deadline = time.time() + 180
attempt = 0
resolved = {}
success_url = None
http_status = None
page_bytes = None
samples = []
errors = []

while time.time() < deadline and success_url is None:
    attempt += 1
    print("VERIFY_ATTEMPT=", attempt)

    for url in urls:
        host = re.sub(r"^https?://", "", url).split("/", 1)[0]
        try:
            infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
            ips = sorted({row[4][0] for row in infos})
            resolved[host] = ips
            print("DNS_RESOLVED=", host, ips)
        except Exception as exc:
            err = f"dns:{host}:{type(exc).__name__}:{exc}"
            errors.append(err)
            print("DNS_WAIT=", err)
            continue

        try:
            t0 = time.perf_counter()
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "CompanyOS-V65.87A-Verify/1.0"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read()
                ms = round((time.perf_counter() - t0) * 1000, 2)
                status = int(resp.status)
                print("HTTP_PROBE=", url, status, ms, len(body))
                if 200 <= status < 400:
                    success_url = url
                    http_status = status
                    page_bytes = len(body)
                    samples.append(ms)
                    break
        except Exception as exc:
            err = f"http:{url}:{type(exc).__name__}:{exc}"
            errors.append(err)
            print("HTTP_WAIT=", err)

    if success_url is None:
        time.sleep(10)

if success_url is None:
    report = {
        "version": "V65.87A",
        "verified": False,
        "project_name": project_name,
        "candidate_name": name,
        "project": project,
        "urls_tried": urls,
        "resolved": resolved,
        "errors": errors[-20:],
        "timestamp_unix": time.time(),
    }
    rp = REPORT_DIR / f"v65_87a_postdeploy_verify_{int(time.time())}.json"
    rp.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print("REPORT=", rp)
    print("V65_87A_PROVIDER_DEPLOYMENT_EXISTS=PASS")
    print("V65_87A_PUBLIC_HTTP=NOT_YET_REACHABLE_FROM_THIS_PHONE")
    raise SystemExit(2)

# Additional latency probes once DNS/public route is working.
for _ in range(4):
    try:
        t0 = time.perf_counter()
        req = urllib.request.Request(
            success_url,
            headers={"User-Agent": "CompanyOS-V65.87A-Verify/1.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read()
            samples.append(round((time.perf_counter() - t0) * 1000, 2))
    except Exception as exc:
        errors.append(f"latency:{type(exc).__name__}:{exc}")

avg_ms = round(statistics.mean(samples), 2)
min_ms = round(min(samples), 2)
max_ms = round(max(samples), 2)

report = {
    "version": "V65.87A",
    "verified": True,
    "candidate_name": name,
    "project_name": project_name,
    "deployment_id": latest.get("id"),
    "public_url": success_url,
    "http_status": http_status,
    "page_bytes": page_bytes,
    "dns": resolved,
    "latency_ms": {
        "samples": samples,
        "average": avg_ms,
        "minimum": min_ms,
        "maximum": max_ms,
    },
    "provider_environment": latest.get("environment"),
    "provider_aliases": latest.get("aliases") or [],
    "timestamp_unix": time.time(),
}

rp = REPORT_DIR / f"v65_87a_postdeploy_verify_{int(time.time())}.json"
rp.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
(LOCAL_RT / "live_validation_latest.json").write_text(
    json.dumps(report, indent=2, sort_keys=True, default=str) + "\n"
)

print("PUBLIC_URL=", success_url)
print("HTTP_STATUS=", http_status)
print("PAGE_BYTES=", page_bytes)
print("LATENCY_SAMPLES_MS=", samples)
print("LATENCY_AVG_MS=", avg_ms)
print("LATENCY_MIN_MS=", min_ms)
print("LATENCY_MAX_MS=", max_ms)
print("REPORT=", rp)
print("V65_87A_PROVIDER_DEPLOYMENT_EXISTS=PASS")
print("V65_87A_PUBLIC_HTTP=PASS")
print("V65_87A_PERFORMANCE_MEASUREMENT=PASS")
print("V65_87A_COMPLETE")
PY
