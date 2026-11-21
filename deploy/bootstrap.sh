#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this script as root on a Debian or Ubuntu application LXC."
  exit 1
fi

apt-get update
apt-get install -y ca-certificates curl git

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
fi

echo "Base packages are ready. Run deploy/deploy.sh with REPO_URL and ENV_SOURCE."
