#!/usr/bin/env bash
# One-time setup of a fresh Ubuntu server for DinkDonk Cinema (run as root; deploy.sh runs it when needed).
# Installs Node, Caddy (automatic HTTPS), a firewall (SSH, HTTP, HTTPS only), key-only SSH, automatic security
# updates, a "dinkdonk" system user and the systemd service. Safe to run again.
# Usage: setup-server.sh <domain>     e.g. 2-29-56-208.sslip.io
set -euo pipefail
DOMAIN="${1:?usage: setup-server.sh <domain>}"
APP=/opt/dinkdonk-cinema
DATA=/var/lib/dinkdonk-cinema
ENVFILE=/etc/dinkdonk-cinema.env
HERE="$(cd "$(dirname "$0")" && pwd)"

export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q nodejs caddy ufw unattended-upgrades openssl
node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 20 ? 0 : 1)' || { echo "Node $(node -v) is too old (need 20+)"; exit 1; }

# key-only SSH (the server was created with SSH keys; this makes sure passwords never work)
cat > /etc/ssh/sshd_config.d/10-dinkdonk.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
EOF
systemctl reload ssh || systemctl reload sshd || true

# firewall
ufw default deny incoming >/dev/null
ufw default allow outgoing >/dev/null
ufw allow OpenSSH >/dev/null
ufw allow 80/tcp >/dev/null
ufw allow 443/tcp >/dev/null
ufw --force enable >/dev/null

# automatic security updates
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF

# app user, folders, secrets
id dinkdonk >/dev/null 2>&1 || useradd --system --home "$DATA" --shell /usr/sbin/nologin dinkdonk
mkdir -p "$APP" "$DATA"
chown dinkdonk:dinkdonk "$DATA"
chmod 750 "$DATA"
if [ ! -f "$ENVFILE" ]; then
  echo "ADMIN_TOKEN=$(openssl rand -base64 33 | tr '+/' '-_' | tr -d '=\n')" > "$ENVFILE"
  chmod 600 "$ENVFILE"
  echo "New admin token (shown once; also in $ENVFILE on the server): $(cut -d= -f2- "$ENVFILE")"
fi

install -m 644 "$HERE/dinkdonk-cinema.service" /etc/systemd/system/dinkdonk-cinema.service
sed "s/{{DOMAIN}}/$DOMAIN/" "$HERE/Caddyfile" > /etc/caddy/Caddyfile
systemctl daemon-reload
systemctl enable dinkdonk-cinema caddy >/dev/null
systemctl reload caddy || systemctl restart caddy
echo "server ready for $DOMAIN"
