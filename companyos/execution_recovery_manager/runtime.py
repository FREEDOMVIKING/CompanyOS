from companyos.runtime_common_v3 import run_forever
from .engine import ExecutionRecoveryManager
def main():run_forever("execution_recovery_manager",lambda home:ExecutionRecoveryManager(home),300)
if __name__=="__main__":main()
