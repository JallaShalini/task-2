#!/usr/bin/env bash
set -e

# Ensure /data and /cron exist
mkdir -p /data /cron /var/log
chmod 755 /data /cron

# Install ALL cron files into /etc/cron.d
if [ -d /cron ] && [ "$(ls -A /cron 2>/dev/null)" != "" ]; then
  for f in /cron/*; do
    [ -f "$f" ] || continue
    cp "$f" "/etc/cron.d/$(basename "$f")"
    chmod 0644 "/etc/cron.d/$(basename "$f")"
  done
fi

# Fallback: if /cron is empty, copy from /app/cron
if [ -d /app/cron ] && [ "$(ls -A /etc/cron.d 2>/dev/null | wc -l)" -eq 0 ]; then
  for f in /app/cron/*; do
    [ -f "$f" ] || continue
    cp "$f" "/etc/cron.d/$(basename "$f")"
    chmod 0644 "/etc/cron.d/$(basename "$f")"
  done
fi

# Ensure cron-related scripts are in /usr/local/bin
# copy cron-job.sh (used by mycron) if present
if [ -f /app/scripts/cron-job.sh ]; then
  cp /app/scripts/cron-job.sh /usr/local/bin/cron-job.sh
  chmod +x /usr/local/bin/cron-job.sh
fi

# copy the 2fa cron script (log_2fa_cron.py)
if [ -f /app/scripts/log_2fa_cron.py ]; then
  cp /app/scripts/log_2fa_cron.py /usr/local/bin/log_2fa_cron.py
  chmod +x /usr/local/bin/log_2fa_cron.py
fi

# Start cron (most systems provide 'cron' or 'crond')
service cron start || cron || crond || true

# Start the API server
exec uvicorn app:app --host 0.0.0.0 --port 8080
