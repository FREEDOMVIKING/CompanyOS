from .engine import ResourceAllocator
from companyos.stability_tools.worker import run_worker

def main():
    run_worker("resource_allocator_35001_40000",lambda home:ResourceAllocator(home),interval=300,startup_delay=8)

if __name__=="__main__":
    main()
