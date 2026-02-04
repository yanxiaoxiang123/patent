#!/usr/bin/env bash
set -e
TS=$(date +%Y%m%d_%H%M%S)
LATEST=$(ls -1t /www/wwwroot/iprs/patent/frontend/iprs_frontend_*.tar.gz | head -n 1)
DST=/www/wwwroot/iprs_site
BACKUP_DIR=/www/wwwroot/iprs_site_backups
mkdir -p "$BACKUP_DIR"
tar -C "$DST" -czf "$BACKUP_DIR/site_$TS.tar.gz" .
tar -C "$DST" -xzf "$LATEST"
nginx -t
systemctl reload nginx
