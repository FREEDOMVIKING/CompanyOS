from companyos.runtime_common_v3 import run_forever
from .engine import MilestoneGeneratorV3
def main():run_forever("milestone_generator_v3",lambda home:MilestoneGeneratorV3(home),300)
if __name__=="__main__":main()
