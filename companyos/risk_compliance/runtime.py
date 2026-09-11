from .engine import RiskCompliance
from companyos.stability_tools.worker import run_worker

def main():
    run_worker("risk_compliance_35001_40000",lambda home:RiskCompliance(home),interval=300,startup_delay=10)

if __name__=="__main__":
    main()
