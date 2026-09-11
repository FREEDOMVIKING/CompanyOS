#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/companyos"
RUN="$ROOT/run"
LOGS="$ROOT/logs"

SCHED_PID="$RUN/autonomous_operations.pid"
WATCH_PID="$RUN/phone_watchdog.pid"
LAUNCH_PID="$RUN/phone_runtime.pid"

WATCHDOG="$ROOT/phone_watchdog.sh"
SCHED="$ROOT/agents/autonomous_operations_scheduler.py"

mkdir -p "$RUN" "$LOGS"

alive() {
    [ -n "$1" ] && kill -0 "$1" 2>/dev/null
}

readpid() {
    [ -f "$1" ] && cat "$1" 2>/dev/null
}

start_scheduler() {
    local pid
    pid="$(readpid "$SCHED_PID")"

    if alive "$pid"; then
        echo "Scheduler already live PID=$pid"
        return 0
    fi

    rm -f "$SCHED_PID"

    cd "$ROOT" || exit 1
    python "$SCHED" start >/dev/null 2>&1
    sleep 2

    pid="$(readpid "$SCHED_PID")"

    if alive "$pid"; then
        echo "Scheduler started PID=$pid"
    else
        echo "ERROR: scheduler failed to start"
        return 1
    fi
}

start_watchdog() {
    local pid
    pid="$(readpid "$WATCH_PID")"

    if alive "$pid"; then
        echo "Watchdog already live PID=$pid"
        return 0
    fi

    rm -f "$WATCH_PID"

    nohup "$WATCHDOG" >/dev/null 2>&1 &
    pid=$!
    echo "$pid" > "$WATCH_PID"

    sleep 1

    if alive "$pid"; then
        echo "Watchdog started PID=$pid"
    else
        echo "ERROR: watchdog failed to start"
        return 1
    fi
}

start_all() {
    termux-wake-lock 2>/dev/null || true

    start_scheduler || return 1
    start_watchdog || return 1

    echo "$$" > "$LAUNCH_PID"

    echo
    echo "PHONE-SAFE COMPANYOS RUNTIME ACTIVE"
}

stop_all() {
    local wpid spid

    wpid="$(readpid "$WATCH_PID")"
    spid="$(readpid "$SCHED_PID")"

    # Stop watchdog first so it cannot restart scheduler.
    if alive "$wpid"; then
        kill "$wpid" 2>/dev/null || true
        sleep 1
    fi
    rm -f "$WATCH_PID"

    if alive "$spid"; then
        cd "$ROOT" || exit 1
        python "$SCHED" stop >/dev/null 2>&1 || kill "$spid" 2>/dev/null || true
        sleep 2
    fi
    rm -f "$SCHED_PID"

    rm -f "$LAUNCH_PID"

    termux-wake-unlock 2>/dev/null || true

    echo "PHONE-SAFE COMPANYOS RUNTIME STOPPED"
}

status_all() {
    local spid wpid

    spid="$(readpid "$SCHED_PID")"
    wpid="$(readpid "$WATCH_PID")"

    echo "=== PHONE-SAFE COMPANYOS ==="

    if alive "$spid"; then
        echo "Scheduler: LIVE PID=$spid"
    else
        echo "Scheduler: DEAD"
    fi

    if alive "$wpid"; then
        echo "Watchdog : LIVE PID=$wpid"
    else
        echo "Watchdog : DEAD"
    fi

    echo
    free -h 2>/dev/null || true

    echo
    cd "$ROOT" || exit 1
    python "$SCHED" status 2>/dev/null | tail -20
}

case "${1:-status}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 2
        start_all
        ;;
    status)
        status_all
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
