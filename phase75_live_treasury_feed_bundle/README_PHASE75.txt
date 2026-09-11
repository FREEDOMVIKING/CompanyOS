PHASE 75 — LIVE TREASURY FEED

Adds:
- live SOL balance from RPC
- configurable refresh loop
- spendable balance after reserve
- cached treasury state
- stale-data detection
- forced fresh refresh before financial actions

INSTALL:
cd ~/companyos || exit 1
rm -rf phase75_live_treasury_feed_bundle
mkdir -p phase75_live_treasury_feed_bundle

unzip -o ~/storage/downloads/PHASE75_LIVE_TREASURY_FEED_BUNDLE.zip \
  -d ~/companyos/phase75_live_treasury_feed_bundle

python ~/companyos/phase75_live_treasury_feed_bundle/phase75_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase75_live_treasury_feed_bundle/phase75_verify.py

ONE-SHOT LIVE CHECK:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase75_live_treasury.py

CONTINUOUS LIVE FEED (20 sec default):
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase75_live_feed_loop.py

CUSTOM INTERVAL EXAMPLE:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase75_live_feed_loop.py --interval 15

CTRL+C stops the continuous feed.
