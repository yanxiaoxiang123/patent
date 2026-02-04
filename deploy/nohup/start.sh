#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$ROOT_DIR/logs"

mkdir -p "$RUN_DIR" "$LOG_DIR"

get_listen_pid() {
  local port="$1"
  lsof -t -iTCP:"$port" -sTCP:LISTEN -nP 2>/dev/null | head -n 1 || true
}

wait_listen_pid() {
  local port="$1"
  local seconds="${2:-10}"
  local pid=""
  for _ in $(seq 1 $((seconds * 2))); do
    pid="$(get_listen_pid "$port")"
    if [ -n "${pid:-}" ]; then
      echo "$pid"
      return 0
    fi
    sleep 0.5
  done
  return 1
}

if [ -f "$RUN_DIR/backend.pid" ]; then
  if kill -0 "$(cat "$RUN_DIR/backend.pid")" 2>/dev/null; then
    echo "backend already running pid=$(cat "$RUN_DIR/backend.pid")"
  else
    rm -f "$RUN_DIR/backend.pid"
  fi
fi

if [ -f "$RUN_DIR/frontend.pid" ]; then
  if kill -0 "$(cat "$RUN_DIR/frontend.pid")" 2>/dev/null; then
    echo "frontend already running pid=$(cat "$RUN_DIR/frontend.pid")"
  else
    rm -f "$RUN_DIR/frontend.pid"
  fi
fi

if [ ! -f "$RUN_DIR/backend.pid" ]; then
  existing_backend_pid="$(get_listen_pid 8000)"
  if [ -n "${existing_backend_pid:-}" ]; then
    echo "$existing_backend_pid" > "$RUN_DIR/backend.pid"
    echo "backend already listening on 8000 pid=$(cat "$RUN_DIR/backend.pid")"
  else
  cd "$BACKEND_DIR"
  nohup bash -lc 'exec /opt/miniconda3/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000' > "$LOG_DIR/backend.log" 2>&1 &
  backend_bg_pid="$!"
  backend_listen_pid="$(wait_listen_pid 8000 10 || true)"
  if [ -n "${backend_listen_pid:-}" ]; then
    echo "$backend_listen_pid" > "$RUN_DIR/backend.pid"
    echo "backend started pid=$(cat "$RUN_DIR/backend.pid")"
  else
    echo "$backend_bg_pid" > "$RUN_DIR/backend.pid"
    echo "backend start attempted pid=$(cat "$RUN_DIR/backend.pid")"
  fi
  fi
fi

if [ ! -f "$RUN_DIR/frontend.pid" ]; then
  existing_frontend_pid="$(get_listen_pid 5173)"
  if [ -n "${existing_frontend_pid:-}" ]; then
    echo "$existing_frontend_pid" > "$RUN_DIR/frontend.pid"
    echo "frontend already listening on 5173 pid=$(cat "$RUN_DIR/frontend.pid")"
  else
  cd "$FRONTEND_DIR"
  nohup bash -lc 'exec /usr/bin/npm run dev -- --host 0.0.0.0 --port 5173 --strictPort' > "$LOG_DIR/frontend.log" 2>&1 &
  frontend_bg_pid="$!"
  frontend_listen_pid="$(wait_listen_pid 5173 15 || true)"
  if [ -n "${frontend_listen_pid:-}" ]; then
    echo "$frontend_listen_pid" > "$RUN_DIR/frontend.pid"
    echo "frontend started pid=$(cat "$RUN_DIR/frontend.pid")"
  else
    echo "$frontend_bg_pid" > "$RUN_DIR/frontend.pid"
    echo "frontend start attempted pid=$(cat "$RUN_DIR/frontend.pid")"
  fi
  fi
fi
