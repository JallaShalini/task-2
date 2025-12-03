# Install ALL cron files into /etc/cron.d
if [ -d /cron ] && [ "$(ls -A /cron 2>/dev/null)" != "" ]; then
  for f in /cron/*; do
    [ -f "$f" ] || continue
    cp "$f" /etc/cron.d/$(basename "$f")
    chmod 0644 /etc/cron.d/$(basename "$f")
  done
fi

