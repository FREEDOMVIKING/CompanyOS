from .engine import StrategicPlanner
from companyos.stability_tools.worker import run_worker

def main():
    run_worker("strategic_planner_35001_40000",lambda home:StrategicPlanner(home),interval=300,startup_delay=12)

if __name__=="__main__":
    main()
