from companyos.runtime_common_v2 import run_forever
from .engine import TaskDelegationV2
def main():run_forever("task_delegation_v2",lambda home:TaskDelegationV2(home),300)
if __name__=="__main__":main()
