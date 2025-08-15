#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Helpers and configuration
# -----------------------------
usage() {
  cat <<USAGE
Usage: $0 <command> [options]

Commands:
  run           Start the API server (default if no command given)
  install       Install Python dependencies from requirements.txt
  help          Show this help message

Environment variables:
  HOST          Bind host (default: 0.0.0.0)
  PORT          Bind port (default: 8001)
  RELOAD        Enable auto-reload (1/true to enable; default: 1)
  LOG_LEVEL     Log level for app (default: DEBUG)
USAGE
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

activate_venv() {
  # Activate venv if present (Linux/Mac or Windows Git Bash)
  if [[ -f "venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "venv/bin/activate"
  elif [[ -f "venv/Scripts/activate" ]]; then
    # shellcheck disable=SC1091
    source "venv/Scripts/activate"
  fi
}

ensure_python() {
  if ! command -v python >/dev/null 2>&1; then
    echo "python not found on PATH" >&2
    exit 1
  fi
}

install_deps() {
  cd "$PROJECT_ROOT"
  ensure_python
  echo "Installing requirements..."
  python -m pip install -r requirements.txt --disable-pip-version-check
}

run_server() {
  cd "$PROJECT_ROOT"
  activate_venv

  export LOG_LEVEL="${LOG_LEVEL:-DEBUG}"
  local host="${HOST:-0.0.0.0}"
  local port="${PORT:-8001}"
  local reload="${RELOAD:-1}"

  # Use uvicorn or fall back to python -m uvicorn
  local uvicorn_cmd
  if command -v uvicorn >/dev/null 2>&1; then
    uvicorn_cmd=(uvicorn app.main:app)
  else
    ensure_python
    uvicorn_cmd=(python -m uvicorn app.main:app)
  fi

  local args=("--host" "$host" "--port" "$port" "--no-access-log")
  if [[ "$reload" == "1" || "$reload" == "true" ]]; then
    args+=("--reload")
  fi

  echo "Starting Paper Search API on $host:$port (reload=$reload)"
  exec "${uvicorn_cmd[@]}" "${args[@]}"
}

# -----------------------------
# Entry point
# -----------------------------
cmd="${1:-run}"
case "$cmd" in
  run)
    run_server
    ;;
  install|--install)
    install_deps
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    echo "Unknown command: $cmd" >&2
    usage
    exit 1
    ;;
esac


