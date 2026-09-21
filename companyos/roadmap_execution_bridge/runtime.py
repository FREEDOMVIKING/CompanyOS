from companyos.runtime_common_v3 import run_forever
from .engine import RoadmapExecutionBridge
def main():run_forever("roadmap_execution_bridge",lambda home:RoadmapExecutionBridge(home),300)
if __name__=="__main__":main()
