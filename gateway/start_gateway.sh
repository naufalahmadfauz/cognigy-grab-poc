#!/usr/bin/env bash
# (Re)start the Gateway: Adapter (127.0.0.1:4002) + Quick Tunnel (trycloudflare).
# Idempotent. Run ALONE in any Codespace terminal:
#   bash gateway/start_gateway.sh
set -u
cd "$(dirname "$0")/.."
TUNNEL_LOG=/tmp/opencode/cloudflared.log

# --- adapter ---
if pgrep -f "gateway/adapter[.]py" >/dev/null; then
  echo "adapter already running:"
  pgrep -af "adapter.py"
else
  nohup python3 gateway/adapter.py >> /tmp/opencode/adapter.log 2>&1 &
  ok=""
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    sleep 1
    if curl -s -m 3 http://127.0.0.1:4002/healthz > /dev/null 2>&1; then ok=1; break; fi
  done
  [ -n "$ok" ] && echo "adapter up: $(curl -s -m 3 http://127.0.0.1:4002/healthz)" \
    || { echo "adapter did not come up — see /tmp/opencode/adapter.log"; exit 1; }
fi

# --- quick tunnel (machine-traffic-safe replacement for the GitHub port forward) ---
if pgrep -f "cloudflared tunnel --url" >/dev/null; then
  :
else
  : > "$TUNNEL_LOG"
  nohup cloudflared tunnel --url http://127.0.0.1:4002 >> "$TUNNEL_LOG" 2>&1 &
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
    sleep 2
    URL=$(grep -o "https://[a-z0-9][a-z0-9-]*\.trycloudflare\.com" "$TUNNEL_LOG" | tail -1)
    [ -n "${URL:-}" ] && break
  done
  if [ -n "${URL:-}" ]; then
    echo "$URL" > /tmp/opencode/tunnel_url
    echo "TUNNEL URL: $URL"
  else
    echo "tunnel did not report a URL — see $TUNNEL_LOG"
  fi
fi
if [ -f /tmp/opencode/tunnel_url ]; then
  echo "tunnel already up: $(cat /tmp/opencode/tunnel_url)"
fi
exit 0
