from companyos.runtime_common_v2 import run_forever
from .engine import UnifiedRuntimeController
def main():run_forever("unified_runtime_controller",lambda home:UnifiedRuntimeController(home),300)
if __name__=="__main__":main()
