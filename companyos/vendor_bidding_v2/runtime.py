from companyos.runtime_common_v2 import run_forever
from .engine import VendorBiddingV2
def main():run_forever("vendor_bidding_v2",lambda home:VendorBiddingV2(home),300)
if __name__=="__main__":main()
