#!/usr/bin/env python3
from pathlib import Path
import os, sys, argparse, uuid
for line in Path('.env').read_text(errors='ignore').splitlines():
    line=line.strip()
    if line and not line.startswith('#') and '=' in line:
        k,v=line.split('=',1); os.environ[k.strip()]=v.strip().strip('"').strip("'")
from companyos.walletintegration.solana_signer_key_adapter import load_signer_material
from companyos.walletintegration.live_solana_execution_engine import LiveSolanaExecutionEngine
from companyos.walletintegration.production_execution_coordinator import ProductionExecutionCoordinator, ProductionExecutionRequest
ap=argparse.ArgumentParser(description='Controlled CompanyOS SOL transfer CLI')
ap.add_argument('--destination',required=True)
ap.add_argument('--sol',required=True,type=float)
ap.add_argument('--reserve-sol',type=float,default=float(os.getenv('COMPANYOS_SOL_RESERVE_SOL','0.01')))
ap.add_argument('--broadcast',action='store_true')
ap.add_argument('--confirm-token',default='')
ap.add_argument('--idempotency-key',default='')
a=ap.parse_args()
if a.sol<=0: raise SystemExit('ERROR: --sol must be > 0')
lamports=int(round(a.sol*1_000_000_000))
m=load_signer_material(os.environ['SOLANA_PRIVATE_KEY'],os.getenv('SOLANA_PRIVATE_KEY_ENCODING','auto'))
engine=LiveSolanaExecutionEngine(rpc_url=os.environ['SOLANA_RPC_URL'],secret=os.environ['SOLANA_PRIVATE_KEY'],encoding=os.getenv('SOLANA_PRIVATE_KEY_ENCODING','auto'),wallet_address=m.public_address,reserve_sol=a.reserve_sol,broadcast_enabled=bool(a.broadcast))
coordinator=ProductionExecutionCoordinator(engine=engine)
req=ProductionExecutionRequest(action_type='sol_transfer',amount_lamports=lamports,destination=a.destination,allow_broadcast=bool(a.broadcast),confirm_token=a.confirm_token)
r=coordinator.execute(request=req,idempotency_key=a.idempotency_key or f'sol-transfer-{uuid.uuid4()}')
print('=== COMPANYOS SOL TRANSFER ===')
print('MODE:', 'LIVE' if a.broadcast else 'DRY RUN')
print('DESTINATION:', a.destination)
print('AMOUNT SOL:', a.sol)
print('ACCEPTED:', r.accepted)
print('REASON:', r.reason)
print('STATE:', r.state)
print('SUCCESS:', r.success)
print('SIGNATURE:', r.signature or 'NONE')
print('CONFIRMATION:', r.confirmation_status or 'NONE')
print('STATUS ERROR:', r.status_err or 'NONE')
sys.exit(0 if r.accepted else 2)
