from companyos.runtime_common_v2 import run_forever
from .engine import ProposalContractsV2
def main():run_forever("proposal_contracts_v2",lambda home:ProposalContractsV2(home),300)
if __name__=="__main__":main()
