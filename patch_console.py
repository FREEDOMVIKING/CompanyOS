from pathlib import Path

target = Path.home() / "companyos" / "companyos" / "controlplane" / "dashboard.py"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text('from companyos.opscenter.server import main\n\nif __name__ == "__main__":\n    main()\n')
print(f"Patched dashboard entrypoint: {target}")
