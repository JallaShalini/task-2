#!/usr/bin/env bash
# write heartbeat timestamp to /cron/heartbeat.log
mkdir -p /cron
echo "$(date -u +'%Y-%m-%dT%H:%M:%SZ') heartbeat" >> /cron/heartbeat.log
chmod 644 /cron/heartbeat.log 2>/dev/null || true
