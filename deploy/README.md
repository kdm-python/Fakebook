# Application LXC deployment

The application LXC needs Git, uv, systemd, and network access to the Git
repository. uv installs the requested Python version when the LXC does not
already provide it. Nginx remains on the separate main proxy LXC.

On a fresh Debian or Ubuntu LXC, first run:

```sh
sh deploy/bootstrap.sh
```

This installs Git, curl, certificates, and uv. FastAPI and Uvicorn are installed
from the committed lock file during deployment.

## 1. Prepare deployment values

Copy and edit the production environment example on your own machine or LXC:

```sh
cp deploy/production.env.example /tmp/fakebook-production.env
```

Replace the example public URL and LXC addresses. Set
`FAKEBOOK_SCHOOL_DOMAINS` to the parent domain accepted by the application.
The Python application uses the
`FAKEBOOK_` settings; the other values are deployment notes/placeholders.

## 2. Deploy on the application LXC

After obtaining this repository or the deployment script, run as root:

```sh
REPO_URL="git@github.com:YOUR_ACCOUNT/YOUR_REPOSITORY.git" \
ENV_SOURCE="/tmp/fakebook-production.env" \
sh deploy/deploy.sh
```

Optional variables are `REPO_BRANCH`, `APP_DIR`, `SERVICE_USER`, and `UV_BIN`.
Running the same command again updates the checkout and restarts the service.
For a private repository, configure an SSH deploy key on the LXC separately;
do not put a token or private key in this repository or its environment example.

The default application address is port 8000 on the application LXC. Verify it
from another machine on the LAN:

```sh
curl http://APPLICATION_LXC_IP:8000/api/health
```

## 3. Configure the main Nginx LXC

Use `reverse-proxy.example.conf` as a reference. Replace `192.0.2.20` with the
application LXC address. Keep the original Host header, and use WebSocket upgrade
headers for interactive input. The same virtual host can serve each configured
school subdomain; TLS and DNS are managed on the main Nginx LXC.

## 4. Inspect service logs

```sh
systemctl status fakebook-backend.service
journalctl -u fakebook-backend.service -f
```

Restrict port 8000 to the main Nginx LXC when you configure the host or LXC
firewall.
