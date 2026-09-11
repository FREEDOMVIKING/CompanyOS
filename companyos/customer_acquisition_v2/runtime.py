from .engine import CustomerAcquisitionV2
from companyos.stability_tools.worker import run_worker

def main():
    run_worker("customer_acquisition_v2_40001_50000",lambda home:CustomerAcquisitionV2(home),interval=300,startup_delay=2)

if __name__=="__main__":
    main()
