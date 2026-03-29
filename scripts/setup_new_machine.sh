#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

log() { printf "\n[%s] %s\n" "$(date +"%H:%M:%S")" "$*"; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

auto_install=${AUTO_INSTALL:-0}

log "Checking system dependencies"
if ! need_cmd python3; then
  if [[ "$auto_install" == "1" ]] && need_cmd apt-get; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-pip
  elif [[ "$auto_install" == "1" ]] && need_cmd brew; then
    brew install python
  else
    echo "Missing python3. Install it and rerun."; exit 1
  fi
fi

if ! need_cmd node; then
  if [[ "$auto_install" == "1" ]] && need_cmd apt-get; then
    sudo apt-get update
    sudo apt-get install -y nodejs npm
  elif [[ "$auto_install" == "1" ]] && need_cmd brew; then
    brew install node
  else
    echo "Missing node. Install Node.js (v18+ recommended) and rerun."; exit 1
  fi
fi

if ! need_cmd npm; then
  if [[ "$auto_install" == "1" ]] && need_cmd apt-get; then
    sudo apt-get update
    sudo apt-get install -y npm
  else
    echo "Missing npm. Install npm and rerun."; exit 1
  fi
fi

if ! need_cmd mongod && ! need_cmd mongosh && ! need_cmd mongo; then
  echo "MongoDB not found. Install MongoDB and ensure it is running."
  echo "Ubuntu hint: https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/"
  echo "macOS hint: brew tap mongodb/brew && brew install mongodb-community"
fi

log "Setting up Python virtual environment"
if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip

log "Installing backend Python dependencies"
python -m pip install -r "$ROOT_DIR/backend/requirements.txt"

log "Installing frontend dependencies"
( cd "$ROOT_DIR/frontend" && npm install )

log "Running Django migrations"
( cd "$ROOT_DIR/backend" && python manage.py migrate )

log "Setup complete"
cat <<'EOF'
Next steps:
1) Start backend:  (cd backend && source ../.venv/bin/activate && python manage.py runserver)
2) Start frontend: (cd frontend && npm start)
EOF
