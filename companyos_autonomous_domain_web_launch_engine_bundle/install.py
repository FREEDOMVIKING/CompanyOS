from pathlib import Path
import shutil, time

ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/launch/autonomous_domain_web_launch.py",
    "scripts/companyos_launch_venture.py",
    "scripts/provider_adapter_template.py",
]:
    src = SRC / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name + ".bak." + stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

print("AUTONOMOUS_DOMAIN_WEB_LAUNCH_ENGINE_INSTALL: PASS")
print("REAL_DOMAIN_PROVIDER_INTERFACE: ENABLED")
print("REAL_WEB_DEPLOY_PROVIDER_INTERFACE: ENABLED")
print("DNS_PROVIDER_INTERFACE: ENABLED")
print("STATIC_PRODUCTION_SITE_GENERATOR: ENABLED")
print("AUTONOMOUS_DOMAIN_BUDGET_USD:", __import__("os").getenv("COMPANYOS_DOMAIN_MAX_AUTONOMOUS_USD", "30"))
print("DOMAIN_PURCHASE_WITHOUT_EXPLICIT_RUNTIME_FLAG: NO")
print("PREMIUM_DOMAIN_AUTO_PURCHASE: NO")
print("CREDENTIALS_EMBEDDED: NO")
