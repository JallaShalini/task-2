#!/usr/bin/env bash
set -e

# Ensure mount points exist
mkdir -p /data /cron /var/log
chmod 755 /data /cron

# Set timezone to UTC (Debian based)
if [ -f /usr/share/zoneinfo/UTC ]; then
  ln -sf /usr/share/zoneinfo/UTC /etc/localtime
  echo "UTC" > /etc/timezone 2>/dev/null || true
  export TZ=UTC
fi

# Install the cron file into /etc/cron.d
if [ -f /cron/mycron ]; then
  cp /cron/mycron /etc/cron.d/mycron
elif [ -f /app/cron/mycron ]; then
  cp /app/cron/mycron /etc/cron.d/mycron
fi
chmod 0644 /etc/cron.d/mycron || true

# Make cron job script available
cp /app/scripts/cron-job.sh /usr/local/bin/cron-job.sh
chmod +x /usr/local/bin/cron-job.sh

# Start cron (try variants for portability)
service cron start || cron || crond || true

# Start UVICORN server on 0.0.0.0:8080
exec uvicorn app:app --host 0.0.0.0 --port 8080
