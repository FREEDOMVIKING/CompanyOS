from companyos.runtime_common_v3 import run_forever
from .engine import DashboardClusterManager
def main():run_forever("dashboard_cluster_manager",lambda home:DashboardClusterManager(home),300)
if __name__=="__main__":main()
