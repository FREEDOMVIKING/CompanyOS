COMPANYOS AUTONOMOUS DOMAIN + WEB LAUNCH ENGINE

Purpose
-------
Give launch-ready ventures the ability to:
1. generate brand/domain candidates
2. check real domain availability through a provider adapter
3. register a domain within an autonomous spending limit
4. generate a production website
5. deploy through a hosting provider adapter
6. configure DNS through a provider adapter
7. track PREVIEW_READY / DEPLOYED / LIVE state

Important
---------
This bundle contains the complete CompanyOS launch orchestration and provider interfaces,
but it does not embed registrar, hosting, DNS, payment, or API credentials.

Real external deployment requires provider adapters configured with:
  COMPANYOS_DOMAIN_CHECK_CMD
  COMPANYOS_DOMAIN_REGISTER_CMD
  COMPANYOS_WEB_DEPLOY_CMD
  COMPANYOS_DNS_CONFIG_CMD

Default autonomous domain budget:
  COMPANYOS_DOMAIN_MAX_AUTONOMOUS_USD=30

Premium/expensive domains are not automatically purchased.

INSTALL
-------

cd ~/companyos || exit 1

rm -rf companyos_autonomous_domain_web_launch_engine_bundle
mkdir -p companyos_autonomous_domain_web_launch_engine_bundle

unzip -o ~/storage/downloads/COMPANYOS_AUTONOMOUS_DOMAIN_WEB_LAUNCH_ENGINE_BUNDLE.zip   -d ~/companyos/companyos_autonomous_domain_web_launch_engine_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_autonomous_domain_web_launch_engine_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_autonomous_domain_web_launch_engine_bundle/verify.py

TEST PREVIEW SITE
-----------------

cp companyos_autonomous_domain_web_launch_engine_bundle/sample_venture.json   .companyos_runtime/test_launch_venture.json

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_launch_venture.py .companyos_runtime/test_launch_venture.json

Generated sites appear under:
  exports/production_sites/

REAL DOMAIN + LIVE WEB LAUNCH
-----------------------------
After configuring provider adapters:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_launch_venture.py path/to/venture.json --allow-domain-purchase

The engine will only attempt autonomous registration when:
- provider says domain is available
- price is within COMPANYOS_DOMAIN_MAX_AUTONOMOUS_USD
- runtime launch command explicitly allows domain purchase

Recommended next integration:
wire launch_venture() into the venture lifecycle transition:
VALIDATED -> BUILD -> LAUNCH_READY -> DEPLOYING -> LIVE
