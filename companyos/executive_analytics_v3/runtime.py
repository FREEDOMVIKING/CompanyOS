from companyos.runtime_common_v2 import run_forever
from .engine import ExecutiveAnalyticsV3
def main():run_forever("executive_analytics_v3",lambda home:ExecutiveAnalyticsV3(home),300)
if __name__=="__main__":main()
