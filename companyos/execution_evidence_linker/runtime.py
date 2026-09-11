from companyos.runtime_common_v3 import run_forever
from .engine import ExecutionEvidenceLinker
def main():run_forever("execution_evidence_linker",lambda home:ExecutionEvidenceLinker(home),300)
if __name__=="__main__":main()
