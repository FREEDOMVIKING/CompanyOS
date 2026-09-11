#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
PIDFILE="run/external_research_network.pid"
LOOP="$HOME/companyos/tools/companyos_external_research_loop.sh"
live(){ [ -f "$PIDFILE" ] || return 1; P="$(cat "$PIDFILE" 2>/dev/null || true)"; [ -n "$P" ] && kill -0 "$P" 2>/dev/null; }
case "${1:-status}" in
 start)
  if live; then echo "EXTERNAL RESEARCH NETWORK: ALREADY LIVE PID=$(cat "$PIDFILE")"; exit 0; fi
  nohup "$LOOP" >/dev/null 2>&1 & sleep 1
  live && echo "EXTERNAL RESEARCH NETWORK: LIVE PID=$(cat "$PIDFILE")" || { echo "FAILED TO START"; exit 1; }
  ;;
 stop)
  if live; then kill "$(cat "$PIDFILE")" 2>/dev/null || true; sleep 1; fi
  rm -f "$PIDFILE"; echo "EXTERNAL RESEARCH NETWORK: STOPPED"
  ;;
 restart) "$0" stop; "$0" start ;;
 status) live && echo "EXTERNAL RESEARCH NETWORK: LIVE PID=$(cat "$PIDFILE")" || echo "EXTERNAL RESEARCH NETWORK: NOT LIVE" ;;
 *) echo "Usage: $0 {start|stop|restart|status}"; exit 2 ;;
esac
