from .engine import MemoryGraph
from companyos.stability_tools.worker import run_worker

def main():
    run_worker("memory_graph_40001_50000",lambda home:MemoryGraph(home),interval=360,startup_delay=4)

if __name__=="__main__":
    main()
