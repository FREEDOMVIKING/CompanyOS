from companyos.runtime_common_v2 import run_forever
from .engine import QARecoveryV2
def main():run_forever("qa_recovery_v2",lambda home:QARecoveryV2(home),300)
if __name__=="__main__":main()
