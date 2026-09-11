from companyos.runtime_common_v2 import run_forever
from .engine import ProductFactoryV2
def main():run_forever("product_factory_v2",lambda home:ProductFactoryV2(home),300)
if __name__=="__main__":main()
