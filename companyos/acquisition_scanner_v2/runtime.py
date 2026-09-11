from companyos.runtime_common_v2 import run_forever
from .engine import AcquisitionScannerV2
def main():run_forever("acquisition_scanner_v2",lambda home:AcquisitionScannerV2(home),300)
if __name__=="__main__":main()
