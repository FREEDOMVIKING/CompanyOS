#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
mkdir -p "$HOME/.termux/boot"
printf '%s\n' '#!/data/data/com.termux/files/usr/bin/bash' 'sleep 15' 'cd "$HOME/companyos"' 'bash companyosctl start >> "$HOME/companyos/.companyos_enterprise_v10/boot.log" 2>&1' > "$HOME/.termux/boot/companyos_v10_start.sh"
chmod +x "$HOME/.termux/boot/companyos_v10_start.sh"
echo "Boot launcher installed."
echo "Requires the separate Termux:Boot Android app to run after a phone reboot."
