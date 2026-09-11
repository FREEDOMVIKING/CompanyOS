#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$HOME/companyos"
python scripts/companyos_launch_readiness.py assess >/dev/null
python scripts/companyos_product_builder.py build >/dev/null
python scripts/companyos_release_packager.py package >/dev/null
