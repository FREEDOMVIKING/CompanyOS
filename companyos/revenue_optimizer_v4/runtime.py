from companyos.runtime_common_v2 import run_forever
from .engine import RevenueOptimizerV4
def main():run_forever("revenue_optimizer_v4",lambda home:RevenueOptimizerV4(home),300)
if __name__=="__main__":main()
