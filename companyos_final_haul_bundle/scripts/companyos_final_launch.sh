#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/companyos"

case "${1:-}" in
  preflight)
    python "$ROOT/scripts/companyos_final_launch.py" preflight
    ;;
  status)
    bash "$ROOT/scripts/companyos_service.sh" status
    python "$ROOT/scripts/companyos_final_launch.py" status
    ;;
  safe)
    python "$ROOT/scripts/companyos_final_launch.py" safe
    ;;
  trial-check)
    echo "TRIAL_LIVE requires explicit limits and operator confirmation."
    echo "Example:"
    echo "python scripts/companyos_final_launch.py trial --max-single 5 --max-daily 20 --confirm I_UNDERSTAND_TRIAL_LIVE"
    ;;
  full-check)
    echo "FULL_LIVE requires explicit limits and operator confirmation."
    echo "Example:"
    echo "python scripts/companyos_final_launch.py full --max-single 25 --max-daily 100 --max-failures 3 --confirm I_UNDERSTAND_FULL_LIVE"
    ;;
  install-boot)
    mkdir -p "$HOME/.termux/boot"
    cat > "$HOME/.termux/boot/companyos_start.sh" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
sleep 20
cd "$ROOT" || exit 1
bash "$ROOT/scripts/companyos_service.sh" start
EOF
    chmod +x "$HOME/.termux/boot/companyos_start.sh"
    echo "TERMUX_BOOT_SCRIPT_INSTALLED"
    echo "NOTE: Termux:Boot app must be installed and opened once for Android boot execution."
    ;;
  remove-boot)
    rm -f "$HOME/.termux/boot/companyos_start.sh"
    echo "TERMUX_BOOT_SCRIPT_REMOVED"
    ;;
  start)
    bash "$ROOT/scripts/companyos_service.sh" start
    ;;
  stop)
    bash "$ROOT/scripts/companyos_service.sh" stop
    ;;
  restart)
    bash "$ROOT/scripts/companyos_service.sh" restart
    ;;
  logs)
    bash "$ROOT/scripts/companyos_service.sh" logs
    ;;
  *)
    echo "Usage: $0 {preflight|status|safe|trial-check|full-check|install-boot|remove-boot|start|stop|restart|logs}"
    exit 2
    ;;
esac
