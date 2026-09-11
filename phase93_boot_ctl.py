#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict

from companyos.walletintegration.termux_boot_manager import TermuxBootManager

ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="command", required=True)
sub.add_parser("install")
sub.add_parser("status")
args = ap.parse_args()

mgr = TermuxBootManager()
result = mgr.install() if args.command == "install" else mgr.status()
print(json.dumps(asdict(result), indent=2))
