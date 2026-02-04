#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"

get_listen_pids() {
  local port="$1"
  lsof -t -iTCP:"$port" -sTCP:LISTEN -nP 2>/dev/null | sort -u || true
}

stop_pid_file() {
  local name="$1"
  local pid_file="$RUN_DIR/$name.pid"
  if [ ! -f "$pid_file" ]; then
    echo "$name not running"
    return
  fi
  local pid
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" || true
    for _ in 1 2 3 4 5; do
      if kill -0 "$pid" 2>/dev/null; then
        sleep 0.5
      else
        break
      fi
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" || true
    fi
    echo "$name stopped pid=$pid"
  else
    echo "$name pid file exists but process not running pid=$pid"
  fi
  rm -f "$pid_file"
}

stop_pid_file "frontend"
stop_pid_file "backend"

while read -r pid; do
  [ -z "${pid:-}" ] && continue
  kill "$pid" || true
  echo "frontend stopped by port pid=$pid"
done < <(get_listen_pids 5173)

while read -r pid; do
  [ -z "${pid:-}" ] && continue
  kill "$pid" || true
  echo "backend stopped by port pid=$pid"
done < <(get_listen_pids 8000)
