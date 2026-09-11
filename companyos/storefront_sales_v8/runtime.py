import signal
import subprocess
import sys
import time
from pathlib import Path

def main():
    running = True
    def stop(*_):
        nonlocal running
        running = False
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    root = Path.home() / "companyos"
    log = root / ".companyos_runtime" / "storefront_sales_v8_server.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    proc = None

    while running:
        if proc is None or proc.poll() is not None:
            with log.open("ab") as out:
                proc = subprocess.Popen(
                    [sys.executable, "-u", "-m", "companyos.storefront_sales_v8.server"],
                    cwd=root,
                    stdin=subprocess.DEVNULL,
                    stdout=out,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
        for _ in range(20):
            if not running:
                break
            time.sleep(1)

    if proc and proc.poll() is None:
        proc.terminate()

if __name__ == "__main__":
    main()
