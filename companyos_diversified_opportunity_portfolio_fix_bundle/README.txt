COMPANYOS DIVERSIFIED OPPORTUNITY + PORTFOLIO FIX

Purpose:
Prevent CompanyOS from over-focusing on construction simply because construction-related ventures already exist.

Behavior:
- Detects portfolio sector concentration.
- If one sector represents 50% or more of detected ventures, the productive-autonomy watchdog redirects the next internal goal toward broad diversified opportunity discovery.
- Requires at least 12 opportunities across at least 6 unrelated sectors.
- Construction stays allowed; it is not banned.
- New opportunities are judged by demand, margin, automation, scalability, time-to-revenue, feasibility, competition, and startup cost.
- Renamed/versioned clones do not count as new opportunities.
- Recommends no more than 3 ventures for active validation.

Install:
cd ~/companyos || exit 1
rm -rf companyos_diversified_opportunity_portfolio_fix_bundle
mkdir -p companyos_diversified_opportunity_portfolio_fix_bundle
unzip -o ~/storage/downloads/COMPANYOS_DIVERSIFIED_OPPORTUNITY_PORTFOLIO_FIX_BUNDLE.zip -d ~/companyos/companyos_diversified_opportunity_portfolio_fix_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_diversified_opportunity_portfolio_fix_bundle/install.py
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_diversified_opportunity_portfolio_fix_bundle/verify.py
bash scripts/companyos_productive_autonomy.sh restart

Inspect diversity state:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_diversified_discovery.py
