from .engine import ProfitabilityOptimizer
from companyos.stability_tools.worker import run_worker

def main():
    run_worker("profitability_optimizer_40001_50000",lambda home:ProfitabilityOptimizer(home),interval=300,startup_delay=6)

if __name__=="__main__":
    main()
