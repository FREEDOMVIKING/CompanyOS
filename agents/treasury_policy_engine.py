#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase29_crypto_treasury_config.json"
LEDGER=MEM/"crypto_treasury_ledger.json"

def now():return datetime.now(timezone.utc).isoformat()
def today():return datetime.now(timezone.utc).date().isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def evaluate(amount_usd,asset,chain,destination):
    cfg=load(CFG,{})["outgoing"]
    ledger=load(LEDGER,{"transactions":[]})
    spent=sum(float(x.get("amount_usd",0) or 0) for x in ledger.get("transactions",[])
              if x.get("date")==today() and x.get("direction")=="outgoing" and x.get("status")=="broadcast")
    reasons=[]
    if amount_usd>float(cfg["single_transaction_auto_limit_usd"]):
        reasons.append("single_transaction_limit")
    if spent+amount_usd>float(cfg["daily_total_limit_usd"]):
        reasons.append("daily_total_limit")
    chain_rules={
      "solana":{"SOL","USDT-SPL","USDC-SPL"},
      "evm":{"ETH","USDT-ERC20","USDC-ERC20"},
      "bitcoin":{"BTC"}
    }
    if asset not in chain_rules.get(chain,set()):
        reasons.append("asset_network_mismatch")
    return {
      "allowed_for_auto_sign":len(reasons)==0,
      "requires_owner_approval":any(x in reasons for x in ("single_transaction_limit","daily_total_limit")),
      "blocked": "asset_network_mismatch" in reasons,
      "reasons":reasons,
      "daily_spent_usd":spent,
      "daily_remaining_usd":max(0,float(cfg["daily_total_limit_usd"])-spent),
      "single_auto_limit_usd":cfg["single_transaction_auto_limit_usd"]
    }

if len(sys.argv)>=5:
    r=evaluate(float(sys.argv[1]),sys.argv[2],sys.argv[3],sys.argv[4])
else:
    r={"success":True,"status":"treasury_policy_ready"}
print(json.dumps(r,indent=2))
