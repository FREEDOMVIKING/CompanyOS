from pathlib import Path

target = Path.home() / "companyos" / "companyos" / "controlplane" / "dashboard.py"

replacement = '''from companyos.console.server import main

if __name__ == "__main__":
    main()
'''

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(replacement)
print(f"Patched dashboard entrypoint: {target}")
