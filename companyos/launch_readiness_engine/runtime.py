from companyos.runtime_common_v3 import run_forever
from .engine import LaunchReadinessEngine
def main():run_forever("launch_readiness_engine",lambda home:LaunchReadinessEngine(home),300)
if __name__=="__main__":main()
