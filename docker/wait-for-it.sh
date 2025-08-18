#!/usr/bin/env bash
# wait-for-it.sh (cross-platform safe)
# Usage: ./wait-for-it.sh host:port [timeout] -- command args...

# --- Normalize line endings in-memory ---
# This avoids "exec format error" if CRLF snuck in
[ -n "$BASH_VERSION" ] && sed -i 's/\r$//' "$0"

# --- Args ---
HOSTPORT="$1"
TIMEOUT="${2:-30}" # default 30s
shift 2 || true

if [ -z "$HOSTPORT" ]; then
    echo "Usage: $0 host:port [timeout] -- command args..."
    exit 1
fi

HOST="${HOSTPORT%:*}"
PORT="${HOSTPORT##*:}"

END=$((SECONDS+TIMEOUT))

# --- Wait loop ---
while [ $SECONDS -lt $END ]; do
    if (echo > /dev/tcp/$HOST/$PORT) >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

# --- Timeout check ---
if [ $SECONDS -ge $END ]; then
    echo "Timeout waiting for $HOSTPORT" >&2
    exit 1
fi

# --- Run the command ---
exec "$@"
