#!/usr/bin/env bash
# start_services.sh - Start / stop / status for EOS Lab Python services
#
# Live stack
#   gateway   TCP ingest on 127.0.0.1:5555 (MT5 Observatory EA -> EventBus
#             -> EventStore + MarketStateEngine)
#
# Not started here
#   collector.py        Prototype listener on the same port as gateway
#   replay.py           One-shot reader of storage/*/tick.bin
#   event_reader.py     One-shot reader of MT5 Common Files EventStore
#   Observatory.mq5     Runs inside Windows MetaTrader 5, not from this script
#
# Usage
#   ./scripts/start_services.sh              # start all live services
#   ./scripts/start_services.sh start
#   ./scripts/start_services.sh stop
#   ./scripts/start_services.sh restart
#   ./scripts/start_services.sh status
#   ./scripts/start_services.sh logs [name]
#   ./scripts/start_services.sh start gateway
#   ./scripts/start_services.sh start jupyter

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_DIR="$PROJECT_ROOT/src/python"
VENV_PYTHON="$PYTHON_DIR/venv/bin/python"
VENV_JUPYTER="$PYTHON_DIR/venv/bin/jupyter"
LOG_DIR="$PROJECT_ROOT/logs"
RUN_DIR="$PROJECT_ROOT/run"

GATEWAY_HOST="${EOS_GATEWAY_HOST:-127.0.0.1}"
GATEWAY_PORT="${EOS_GATEWAY_PORT:-5555}"
JUPYTER_PORT="${EOS_JUPYTER_PORT:-8888}"

# name|description
ALL_SERVICES=(
    "gateway|EOS Gateway (TCP ${GATEWAY_HOST}:${GATEWAY_PORT})"
)

usage() {
    sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'
    exit "${1:-0}"
}

ensure_dirs() {
    mkdir -p "$LOG_DIR" "$RUN_DIR"
}

pid_file() {
    echo "$RUN_DIR/$1.pid"
}

log_file() {
    echo "$LOG_DIR/$1.log"
}

is_pid_running() {
    local pid="$1"
    [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

read_pid() {
    local file
    file="$(pid_file "$1")"
    if [[ -f "$file" ]]; then
        tr -d '[:space:]' < "$file"
    fi
}

service_running() {
    local pid
    pid="$(read_pid "$1")"
    is_pid_running "$pid"
}

port_in_use() {
    local port="$1"
    if command -v ss >/dev/null 2>&1; then
        ss -ltn "sport = :$port" 2>/dev/null | tail -n +2 | grep -q .
    elif command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    else
        return 1
    fi
}

require_venv() {
    if [[ ! -x "$VENV_PYTHON" ]]; then
        echo "Python venv not found at:"
        echo "  $VENV_PYTHON"
        echo
        echo "Create it first:"
        echo "  $PROJECT_ROOT/scripts/setup_env.sh"
        exit 1
    fi
}

start_gateway() {
    require_venv

    if service_running gateway; then
        echo "gateway already running (pid $(read_pid gateway))"
        return 0
    fi

    if port_in_use "$GATEWAY_PORT"; then
        echo "Port ${GATEWAY_PORT} is already in use."
        echo "Stop the other listener (often collector.py) before starting gateway."
        exit 1
    fi

    # EventStore writes to ./storage relative to CWD. Keep CWD at the
    # project root so ticks land in $PROJECT_ROOT/storage.
    nohup env \
        PYTHONUNBUFFERED=1 \
        PYTHONPATH="$PYTHON_DIR${PYTHONPATH:+:$PYTHONPATH}" \
        "$VENV_PYTHON" "$PYTHON_DIR/gateway.py" \
        >>"$(log_file gateway)" 2>&1 &

    echo $! >"$(pid_file gateway)"

    local i
    for i in $(seq 1 30); do
        if ! service_running gateway; then
            break
        fi
        if port_in_use "$GATEWAY_PORT"; then
            echo "Started gateway  pid=$(read_pid gateway)  ${GATEWAY_HOST}:${GATEWAY_PORT}"
            echo "  log  $(log_file gateway)"
            echo "  data $PROJECT_ROOT/storage"
            return 0
        fi
        sleep 0.1
    done

    echo "gateway failed to start. Last log lines:"
    tail -n 20 "$(log_file gateway)" || true
    rm -f "$(pid_file gateway)"
    exit 1
}

start_jupyter() {
    require_venv

    if [[ ! -x "$VENV_JUPYTER" ]]; then
        echo "jupyter is not installed in the venv."
        echo "  $VENV_PYTHON -m pip install jupyter"
        exit 1
    fi

    if service_running jupyter; then
        echo "jupyter already running (pid $(read_pid jupyter))"
        return 0
    fi

    if port_in_use "$JUPYTER_PORT"; then
        echo "Port ${JUPYTER_PORT} is already in use."
        exit 1
    fi

    nohup env \
        PYTHONUNBUFFERED=1 \
        PYTHONPATH="$PYTHON_DIR${PYTHONPATH:+:$PYTHONPATH}" \
        "$VENV_JUPYTER" lab \
        --no-browser \
        --ip=127.0.0.1 \
        --port="$JUPYTER_PORT" \
        --notebook-dir="$PROJECT_ROOT" \
        >>"$(log_file jupyter)" 2>&1 &

    echo $! >"$(pid_file jupyter)"
    sleep 0.5

    if service_running jupyter; then
        echo "Started jupyter  pid=$(read_pid jupyter)  http://127.0.0.1:${JUPYTER_PORT}"
        echo "  log $(log_file jupyter)"
    else
        echo "jupyter failed to start. Last log lines:"
        tail -n 20 "$(log_file jupyter)" || true
        rm -f "$(pid_file jupyter)"
        exit 1
    fi
}

stop_service() {
    local name="$1"
    local pid
    pid="$(read_pid "$name")"

    if ! is_pid_running "$pid"; then
        rm -f "$(pid_file "$name")"
        echo "$name is not running"
        return 0
    fi

    kill "$pid" 2>/dev/null || true

    local i
    for i in $(seq 1 20); do
        if ! is_pid_running "$pid"; then
            break
        fi
        sleep 0.1
    done

    if is_pid_running "$pid"; then
        kill -9 "$pid" 2>/dev/null || true
    fi

    rm -f "$(pid_file "$name")"
    echo "Stopped $name"
}

status_service() {
    local name="$1"
    local desc="$2"
    if service_running "$name"; then
        printf "  %-10s running  pid=%-7s  %s\n" "$name" "$(read_pid "$name")" "$desc"
    else
        printf "  %-10s stopped             %s\n" "$name" "$desc"
    fi
}

start_named() {
    case "$1" in
        gateway) start_gateway ;;
        jupyter) start_jupyter ;;
        *)
            echo "Unknown service: $1"
            echo "Known services: gateway, jupyter"
            exit 1
            ;;
    esac
}

stop_named() {
    case "$1" in
        gateway|jupyter)
            stop_service "$1"
            ;;
        *)
            echo "Unknown service: $1"
            echo "Known services: gateway, jupyter"
            exit 1
            ;;
    esac
}

cmd_start() {
    ensure_dirs
    echo "=========================================="
    echo "EOS Lab — starting services"
    echo "Project: $PROJECT_ROOT"
    echo "=========================================="

    if [[ $# -eq 0 ]]; then
        start_gateway
    else
        local name
        for name in "$@"; do
            start_named "$name"
        done
    fi

    echo
    echo "Attach the Observatory EA in MT5 to 127.0.0.1:${GATEWAY_PORT}"
    echo "Stop with:  $0 stop"
}

cmd_stop() {
    echo "=========================================="
    echo "EOS Lab — stopping services"
    echo "=========================================="

    if [[ $# -eq 0 ]]; then
        stop_service gateway
        if [[ -f "$(pid_file jupyter)" ]]; then
            stop_service jupyter
        fi
    else
        local name
        for name in "$@"; do
            stop_named "$name"
        done
    fi
}

cmd_status() {
    echo "EOS Lab services"
    echo "  root $PROJECT_ROOT"
    echo
    local entry name desc
    for entry in "${ALL_SERVICES[@]}"; do
        name="${entry%%|*}"
        desc="${entry#*|}"
        status_service "$name" "$desc"
    done
    if [[ -f "$(pid_file jupyter)" ]] || service_running jupyter; then
        status_service jupyter "JupyterLab (http://127.0.0.1:${JUPYTER_PORT})"
    fi
}

cmd_logs() {
    local name="${1:-gateway}"
    local file
    file="$(log_file "$name")"
    if [[ ! -f "$file" ]]; then
        echo "No log file: $file"
        exit 1
    fi
    tail -n 80 -f "$file"
}

cmd_restart() {
    cmd_stop "$@"
    cmd_start "$@"
}

main() {
    local cmd="${1:-start}"
    if [[ $# -gt 0 ]]; then
        shift
    fi

    case "$cmd" in
        start)   cmd_start "$@" ;;
        stop)    cmd_stop "$@" ;;
        restart) cmd_restart "$@" ;;
        status)  cmd_status ;;
        logs)    cmd_logs "$@" ;;
        -h|--help|help) usage 0 ;;
        *)
            echo "Unknown command: $cmd"
            usage 1
            ;;
    esac
}

main "$@"
