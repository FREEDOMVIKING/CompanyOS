from companyos.runtime_common_v2 import run_forever
from .engine import CRMAutomationV2
def main():run_forever("crm_automation_v2",lambda home:CRMAutomationV2(home),300)
if __name__=="__main__":main()
