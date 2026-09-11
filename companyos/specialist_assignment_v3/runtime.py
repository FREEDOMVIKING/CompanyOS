from companyos.runtime_common_v3 import run_forever
from .engine import SpecialistAssignmentV3
def main():run_forever("specialist_assignment_v3",lambda home:SpecialistAssignmentV3(home),300)
if __name__=="__main__":main()
