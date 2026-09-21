#!/usr/bin/env bash
set -euo pipefail

ROLE="${1:-research_worker}"
REPO="${2:-https://github.com/FREEDOMVIKING/CompanyOS.git}"
BRANCH="${3:-companyos-continuous-fix-2026-09-11}"

case "$ROLE" in primary|research_worker|standby) ;; *) echo "INVALID_ROLE"; exit 2 ;; esac
command -v git >/dev/null || { echo "GIT_REQUIRED"; exit 3; }
command -v python3 >/dev/null || { echo "PYTHON3_REQUIRED"; exit 4; }

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
mkdir -p "$RT"

if [ ! -d "$ROOT/.git" ]; then
  git clone --branch "$BRANCH" --single-branch "$REPO" "$ROOT"
else
  cd "$ROOT"
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git reset --hard "origin/$BRANCH"
fi

cd "$ROOT"
if [ ! -x .venv/bin/python ]; then python3 -m venv --system-site-packages .venv; fi
PY="$ROOT/.venv/bin/python"
"$PY" -m pip install --upgrade pip >/dev/null 2>&1 || true
if [ -f requirements.txt ]; then "$PY" -m pip install -r requirements.txt >/dev/null 2>&1 || true; fi

cat > "$HOME/.companyos_remote_node" <<EOF
COMPANYOS_NODE_ROLE=$ROLE
COMPANYOS_GIT_BRANCH=$BRANCH
EOF
chmod 600 "$HOME/.companyos_remote_node"

if [ "$ROLE" = "primary" ]; then
  mkdir -p "$HOME/.config/systemd/user"
  cat > "$HOME/.config/systemd/user/companyos.service" <<EOF
[Unit]
Description=CompanyOS Remote Primary
After=network-online.target

[Service]
Type=simple
WorkingDirectory=$ROOT
Environment=PYTHONPATH=$ROOT
Environment=COMPANYOS_NODE_ROLE=primary
ExecStart=$PY -m companyos.runtime.service_supervisor
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF
  if command -v systemctl >/dev/null; then
    systemctl --user daemon-reload >/dev/null 2>&1 || true
    systemctl --user enable companyos.service >/dev/null 2>&1 || true
  fi
fi

echo "REMOTE_BOOTSTRAP_ROLE=$ROLE"
echo "REMOTE_BOOTSTRAP=PASS"
