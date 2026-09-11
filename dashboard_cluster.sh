#!/data/data/com.termux/files/usr/bin/bash
set -u
H="$HOME/companyos"; P="$H/.companyos_runtime/dashboard_pids"; L="$H/.companyos_runtime/dashboard_logs"
mkdir -p "$P" "$L"
start_one(){ n="$1"; f="$2"; pf="$P/$n.pid"; lf="$L/$n.log"; if [ -f "$pf" ] && kill -0 "$(cat "$pf")" 2>/dev/null; then echo "$n already running"; return; fi; cd "$H" || exit 1; nohup python -u "$f" >>"$lf" 2>&1 </dev/null & echo $! >"$pf"; sleep 1; kill -0 "$(cat "$pf")" 2>/dev/null && echo "$n started" || echo "$n failed; see $lf"; }
stop_one(){ n="$1"; pf="$P/$n.pid"; [ -f "$pf" ] && { kill "$(cat "$pf")" 2>/dev/null || true; rm -f "$pf"; echo "$n stopped"; } || echo "$n not running"; }
status_one(){ n="$1"; pf="$P/$n.pid"; [ -f "$pf" ] && kill -0 "$(cat "$pf")" 2>/dev/null && echo "$n: RUNNING" || echo "$n: STOPPED"; }
case "${1:-status}" in
 start) start_one master_control dashboard/master_control_server.py; start_one venture_progress dashboard/venture_progress_v2_server.py; start_one activity_ledger dashboard/autonomy_activity_ledger_server.py;;
 stop) stop_one master_control; stop_one venture_progress; stop_one activity_ledger;;
 restart) "$0" stop; sleep 2; "$0" start;;
 status) status_one master_control; status_one venture_progress; status_one activity_ledger;;
 *) echo "Usage: bash dashboard_cluster.sh {start|stop|restart|status}"; exit 2;;
esac
