#!/bin/sh
set -eu

REPO_URL="${REPO_URL:-https://github.com/kdm-python/fakebook-python.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"
APP_DIR="${APP_DIR:-/opt/bytelets/app}"
SERVICE_USER="${SERVICE_USER:-bytelets}"
UV_BIN="${UV_BIN:-/usr/local/bin/uv}"
ENV_SOURCE="${ENV_SOURCE:-}"
DEPLOY_REEXECUTED="${DEPLOY_REEXECUTED:-0}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this script as root on the application LXC."
  exit 1
fi

if [ "$REPO_URL" = "https://github.com/REPLACE_ME/fakebook-python.git" ]; then
  echo "Set REPO_URL to the Git repository before deploying."
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git is required. Install it before running this script."
  exit 1
fi

if [ ! -x "$UV_BIN" ]; then
  echo "uv was not found at $UV_BIN. Install uv or set UV_BIN."
  exit 1
fi

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --create-home --shell /usr/sbin/nologin "$SERVICE_USER"
fi

if [ "$DEPLOY_REEXECUTED" != "1" ]; then
  install -d -o "$SERVICE_USER" -g "$SERVICE_USER" "$(dirname "$APP_DIR")"

  if [ -d "$APP_DIR/.git" ]; then
    chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"
    runuser -u "$SERVICE_USER" -- git -C "$APP_DIR" fetch origin "$REPO_BRANCH"
    runuser -u "$SERVICE_USER" -- git -C "$APP_DIR" checkout "$REPO_BRANCH"
    runuser -u "$SERVICE_USER" -- \
      git -C "$APP_DIR" pull --ff-only origin "$REPO_BRANCH"
  else
    runuser -u "$SERVICE_USER" -- \
      git clone --branch "$REPO_BRANCH" --single-branch "$REPO_URL" "$APP_DIR"
  fi

  chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"

  # The checkout may have updated this script. Reload it once so the remainder
  # of the deployment uses the newly checked-out logic.
  export REPO_URL REPO_BRANCH APP_DIR SERVICE_USER UV_BIN ENV_SOURCE
  DEPLOY_REEXECUTED=1 exec "$APP_DIR/deploy/deploy.sh"
fi

if [ ! -f "$APP_DIR/backend/uv.lock" ]; then
  echo "backend/uv.lock is missing; commit the lock file before deploying."
  exit 1
fi

cd "$APP_DIR/backend"
runuser -u "$SERVICE_USER" -- "$UV_BIN" sync --locked --no-dev

install -d -m 0750 -o root -g "$SERVICE_USER" /etc/fakebook
if [ -n "$ENV_SOURCE" ]; then
  install -m 0640 -o root -g "$SERVICE_USER" "$ENV_SOURCE" /etc/fakebook/backend.env
elif [ ! -f /etc/fakebook/backend.env ]; then
  install -m 0640 -o root -g "$SERVICE_USER" \
    "$APP_DIR/deploy/production.env.example" /etc/fakebook/backend.env
  echo "Created /etc/fakebook/backend.env from the example; review its placeholders."
fi

sed \
  -e "s|__SERVICE_USER__|$SERVICE_USER|g" \
  -e "s|__APP_DIR__|$APP_DIR|g" \
  -e "s|__UV_BIN__|$UV_BIN|g" \
  "$APP_DIR/deploy/fakebook-backend.service.template" \
  > /etc/systemd/system/fakebook-backend.service

systemctl daemon-reload
systemctl enable --now fakebook-backend.service
systemctl restart fakebook-backend.service

echo "Deployment complete. Check: systemctl status fakebook-backend.service"
