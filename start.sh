#!/usr/bin/env bash
set -e

# Ensure /data and /cron exist
mkdir -p /data /cron /var/log
chmod 755 /data /cron

# Copy any cron files found in /cron (host bind or image copy)
if [ -d /cron ] && [ "$(ls -A /cron 2>/dev/null)" != "" ]; then
  for f in /cron/*; do
    [ -f "$f" ] || continue
    cp "$f" "/etc/cron.d/$(basename "$f")"
    chmod 0644 "/etc/cron.d/$(basename "$f")"
  done
fi

# Fallback: copy cron files from /app/cron if /cron empty
if [ -d /app/cron ] && [ "$(ls -A /etc/cron.d 2>/dev/null | wc -l)" -eq 0 ]; then
  for f in /app/cron/*; do
    [ -f "$f" ] || continue
    cp "$f" "/etc/cron.d/$(basename "$f")"
    chmod 0644 "/etc/cron.d/$(basename "$f")"
  done
fi

# Copy cron scripts into /usr/local/bin (used by cron jobs)
if [ -f /app/scripts/cron-job.sh ]; then
  cp /app/scripts/cron-job.sh /usr/local/bin/cron-job.sh
  chmod +x /usr/local/bin/cron-job.sh
fi
if [ -f /app/scripts/log_2fa_cron.py ]; then
  cp /app/scripts/log_2fa_cron.py /usr/local/bin/log_2fa_cron.py
  chmod +x /usr/local/bin/log_2fa_cron.py
fi

# Start cron service (try common names)
service cron start || cron || crond || true

# Start application server (uvicorn)
exec uvicorn app:app --host 0.0.0.0 --port 8080
