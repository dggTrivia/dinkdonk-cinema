#!/usr/bin/env bash
# Builds the hosted edition and puts it on the server (Git Bash on Windows, or any bash).
# First run also sets the server up (setup-server.sh) and prints the admin token once.
# Usage: web/deploy/deploy.sh [host] [ssh key]
#   defaults: 2.29.56.208, ~/.ssh/dinkdonk_cinema_v2_ed25519; the site is https://<ip with dashes>.sslip.io
set -euo pipefail
HOST="${1:-2.29.56.208}"
KEY="${2:-$HOME/.ssh/dinkdonk_cinema_v2_ed25519}"
DOMAIN="${DD_DOMAIN:-${HOST//./-}.sslip.io}"
STANDBY="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$STANDBY/../dist/web"
SSH=(ssh -i "$KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new "root@$HOST")

node "$STANDBY/web/build.js"

echo "uploading to $HOST (about $(du -sh "$OUT" | cut -f1))..."
tar -C "$OUT" -cf - . | "${SSH[@]}" 'set -e; rm -rf /opt/dinkdonk-cinema/next; mkdir -p /opt/dinkdonk-cinema/next; tar -xf - -C /opt/dinkdonk-cinema/next --no-same-owner'

"${SSH[@]}" "set -e
  if [ ! -f /etc/systemd/system/dinkdonk-cinema.service ] || [ \"\${FORCE_SETUP:-}\" = 1 ]; then bash /opt/dinkdonk-cinema/next/deploy/setup-server.sh '$DOMAIN'; fi
  cd /opt/dinkdonk-cinema
  rm -rf previous; [ -d current ] && mv current previous
  mv next current
  chown -R root:root current; chmod -R a+rX current
  systemctl restart dinkdonk-cinema
  sleep 2
  systemctl is-active dinkdonk-cinema
  curl -fsS http://127.0.0.1:8080/healthz; echo"
echo "live: https://$DOMAIN/  (admin: https://$DOMAIN/admin.html)"
