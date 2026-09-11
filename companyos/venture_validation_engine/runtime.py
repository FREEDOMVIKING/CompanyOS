from companyos.runtime_common_v3 import run_forever
from .engine import VentureValidationEngine
def main():run_forever("venture_validation_engine",lambda home:VentureValidationEngine(home),300)
if __name__=="__main__":main()
