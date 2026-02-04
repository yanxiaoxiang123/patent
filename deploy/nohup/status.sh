#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"

get_listen_pid() {
  local port="$1"
  lsof -t -iTCP:"$port" -sTCP:LISTEN -nP 2>/dev/null | head -n 1 || true
}

status_pid_file() {
  local name="$1"
  local port="$2"
  local pid_file="$RUN_DIR/$name.pid"
  if [ ! -f "$pid_file" ]; then
    local pid_by_port
    pid_by_port="$(get_listen_pid "$port")"
    if [ -n "${pid_by_port:-}" ]; then
      echo "$pid_by_port" > "$pid_file"
      echo "$name: running pid=$(cat "$pid_file")"
    else
      echo "$name: stopped"
    fi
    return
  fi
  local pid
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    echo "$name: running pid=$pid"
  else
    local pid_by_port
    pid_by_port="$(get_listen_pid "$port")"
    if [ -n "${pid_by_port:-}" ]; then
      echo "$pid_by_port" > "$pid_file"
      echo "$name: running pid=$(cat "$pid_file")"
    else
      echo "$name: stale pid file pid=$pid"
    fi
  fi
}

status_pid_file "backend" 8000
status_pid_file "frontend" 5173
