from companyos.runtime_common_v3 import run_forever
from .engine import ProgressSyncV3
def main():run_forever("progress_sync_v3",lambda home:ProgressSyncV3(home),300)
if __name__=="__main__":main()
