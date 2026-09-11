#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/companyos"
PIDFILE="$ROOT/run/autonomous_operations.pid"
LOG="$ROOT/logs/phone_watchdog.log"
PRESSURE="$ROOT/run/memory_pressure.state"

CRITICAL_MB=1500
RECOVER_MB=2500
CHECK_SECONDS=60

mkdir -p "$ROOT/run" "$ROOT/logs"

mem_available_mb() {
    awk '/MemAvailable:/ {printf "%d\n",$2/1024}' /proc/meminfo
}

scheduler_alive() {
    if [ ! -f "$PIDFILE" ]; then
        return 1
    fi

    PID="$(cat "$PIDFILE" 2>/dev/null)"

    [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null
}

start_scheduler() {
    cd "$ROOT" || return 1

    python agents/autonomous_operations_scheduler.py start \
        >>"$LOG" 2>&1
}

stop_scheduler() {
    cd "$ROOT" || return 1

    python agents/autonomous_operations_scheduler.py stop \
        >>"$LOG" 2>&1
}

echo "$(date -Iseconds) phone watchdog started" >> "$LOG"

while true; do

    AVAILABLE="$(mem_available_mb)"

    #
    # CRITICAL MEMORY PROTECTION
    #
    if [ "$AVAILABLE" -lt "$CRITICAL_MB" ]; then

        if [ ! -f "$PRESSURE" ]; then
            echo "$(date -Iseconds) CRITICAL MEMORY available=${AVAILABLE}MB - pausing scheduler" >> "$LOG"
            echo "paused" > "$PRESSURE"

            if scheduler_alive; then
                stop_scheduler
            fi
        fi

        sleep "$CHECK_SECONDS"
        continue
    fi

    #
    # MEMORY RECOVERY
    #
    if [ -f "$PRESSURE" ]; then

        if [ "$AVAILABLE" -ge "$RECOVER_MB" ]; then
            echo "$(date -Iseconds) MEMORY RECOVERED available=${AVAILABLE}MB - resuming scheduler" >> "$LOG"

            rm -f "$PRESSURE"

            if ! scheduler_alive; then
                start_scheduler
            fi
        else
            echo "$(date -Iseconds) memory pressure waiting available=${AVAILABLE}MB" >> "$LOG"
        fi

        sleep "$CHECK_SECONDS"
        continue
    fi

    #
    # NORMAL CRASH / SIGNAL-9 RECOVERY
    #
    if ! scheduler_alive; then
        echo "$(date -Iseconds) scheduler missing - restarting" >> "$LOG"

        start_scheduler
        sleep 15
    fi

    sleep "$CHECK_SECONDS"
done
