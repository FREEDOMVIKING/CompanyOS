import json
import os
import time
import random
import hashlib
import requests
import subprocess
from datetime import datetime
from groq import Groq

# ========================= CONFIG =========================
GROQ_API = "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"
JUPITER_API_KEY = "jup_f7822289aca7818d36cb0748c09c7e2e5c97c3f4ea1b765a454f673af83209a0"
COMPANY_NAME = "NexusAI Solutions"
HIGH_LEVEL_COMMAND = "make money and be successful"
SLEEP_INTERVAL = 180

SOLANA_ADDRESS = "42JKhfQrVipD35S9UGRGLL8ovRFY74XXBwtHT5zgqa2UNDD4xNucKFszKS5XsuoSwC1jVj4CTeg2zxDhQuUfmsGp"   # ← CHANGE THIS

client = Groq(api_key=GROQ_API)

class BlockchainOracle:
    def get_sol_price(self):
        try:
            url = "https://hermes.pyth.network/v2/updates/price/latest"
            payload = {"ids": ["0xef0d8b6fda2ceba3c0b4a5e4c9c3a6e5f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3"]}
            r = requests.post(url, json=payload, timeout=6)
            if r.status_code == 200:
                price = r.json()["parsed"][0]["price"]["price"] / 100000000
                return round(price, 2)
        except:
            pass
        return 148.5
    def jupiter_swap(self, amount=0.001):
        helper = os.path.expanduser(
            "~/ceo_swap_helper/jupiter_swap.js"
        )

        print(f"🌐 Starting real Jupiter swap: {amount} SOL")

        try:
            result = subprocess.run(
                ["node", helper, str(amount)],
                capture_output=True,
                text=True,
                timeout=120,
                env=os.environ.copy(),
            )

            if result.stdout:
                print(result.stdout.strip())

            if result.returncode != 0:
                error = result.stderr.strip() or "Unknown Jupiter helper error"
                print(f"❌ Jupiter swap failed: {error}")
                return False

            transaction_result = None

            for line in reversed(result.stdout.splitlines()):
                line = line.strip()

                if line.startswith("{") and line.endswith("}"):
                    try:
                        transaction_result = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue

            if not transaction_result:
                print("❌ Swap completed without readable JSON.")
                return False

            if not transaction_result.get("success"):
                print(f"❌ Swap was not successful: {transaction_result}")
                return False

            mode = transaction_result.get("mode")
            signature = transaction_result.get("signature")

            print(f"✅ Jupiter result mode: {mode}")

            if signature:
                print(f"✅ Confirmed transaction: {signature}")
            else:
                print("🧪 Transaction simulated but not broadcast.")

            with open("transactions.log", "a", encoding="utf-8") as log:
                log.write(
                    json.dumps(
                        {
                            "time": datetime.now().isoformat(),
                            "amount_sol": amount,
                            "mode": mode,
                            "signature": signature,
                            "success": True,
                        }
                    )
                    + "\n"
                )

            return True

        except subprocess.TimeoutExpired:
            print("❌ Jupiter helper timed out after 120 seconds.")
            return False

        except Exception as error:
            print(f"❌ Jupiter integration error: {error}")
            return False
        # Real swap logic can be expanded here

oracle = BlockchainOracle()

def save_and_run_code(filename, code):
    try:
        with open(filename, "w") as f:
            f.write(code)
        print(f"🧬 Self-created: {filename}")
        subprocess.run(["python", filename], stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def run_autonomous_company():
    print(f"\n🌟 {COMPANY_NAME} - ULTIMATE SELF-ADAPTIVE MODE 🌟\n")
    cycle = 0

    while True:
        cycle += 1
        print(f"\n=== Cycle {cycle} - Self Evolution ===")

        sol_price = oracle.get_sol_price()
        print(f"SOL Price: ${sol_price}")

        # Self-adaptive code generation
        if random.random() > 0.4:
            new_code = f'''# Auto-evolved module v{cycle}
print("New revenue feature loaded - Cycle {cycle}")
# Add your custom logic here
'''
            save_and_run_code(f"self_module_v{cycle}.py", new_code)

        # Use money to grow
        if sol_price < 160:
          #  oracle.jupiter_swap(0.001)

        print("Using company funds to build new tasks...")
        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    try:
        run_autonomous_company()
    except KeyboardInterrupt:
        print("\n👋 CEO Bot stopped.")
    except Exception as e:
        print(f"Error: {e}")
