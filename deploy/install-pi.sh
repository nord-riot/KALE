#!/bin/sh
# KALE Raspberry Pi OS / Debian / Ubuntu installer (local server, no outbound downloads).
# Usage: sudo sh deploy/install-pi.sh [--dry-run]
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1
[ "${1:-}" = "" ] || [ "${1:-}" = "--dry-run" ] || { echo 'Only --dry-run supported' >&2; exit 2; }
[ -f "$ROOT/server.py" ] && [ -f "$ROOT/data/kale.db" ] || { echo 'Run from extracted KALE directory' >&2; exit 2; }
command -v python3 >/dev/null && command -v systemctl >/dev/null || { echo 'Python 3 and systemd required' >&2;exit 2; }
python3 -c 'import sys; assert sys.version_info >= (3,9), "Python 3.9+ required"'
if [ "$DRY" -eq 1 ]; then
  echo 'DRY RUN: would copy package to /opt/kale, create kale service, enable local web and daily backup timer';
  echo 'Existing /opt/kale will NOT be overwritten. For upgrades use separate manual backup+copy.';exit 0
fi
[ "$(id -u)" -eq 0 ] || { echo 'Must run as root (sudo)' >&2;exit 2; }
[ ! -e /opt/kale ] || { echo '/opt/kale exists. Back up and upgrade manually; installer will not overwrite.' >&2;exit 2; }
# Create dedicated locked system identity.
if ! id kale >/dev/null 2>&1;then useradd --system --user-group --home-dir /var/lib/kale --shell /usr/sbin/nologin kale;fi
install -d -m 0700 -o kale -g kale /var/lib/kale/backups
install -d -m 0755 /opt/kale
cp -a "$ROOT"/. /opt/kale/
chown -R root:root /opt/kale
chmod -R go-w /opt/kale
install -m 0644 "$SCRIPT_DIR/kale.service" /etc/systemd/system/kale.service
install -m 0644 "$SCRIPT_DIR/kale-backup.service" /etc/systemd/system/kale-backup.service
install -m 0644 "$SCRIPT_DIR/kale-backup.timer" /etc/systemd/system/kale-backup.timer
if [ ! -e /etc/default/kale ];then printf 'KALE_HOST=127.0.0.1\nKALE_PORT=8090\n' > /etc/default/kale;chmod 0644 /etc/default/kale;fi
/usr/bin/python3 /opt/kale/server.py --selftest
systemctl daemon-reload
systemctl enable --now kale.service kale-backup.timer
printf 'KALE installed at http://127.0.0.1:8090/\n'
printf 'Daily backups: /var/lib/kale/backups (03:15, up to 10 min delay)\n'
printf 'For LAN access, set KALE_HOST=0.0.0.0 in /etc/default/kale and restart; apply firewall restrictions.\n'
