#!/bin/bash
# Scout & Report Script

# Load environment variables
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$DIR/.env" ]; then
    export $(grep -v '^#' "$DIR/.env" | xargs)
fi

# Set PYTHONPATH
export PYTHONPATH="$DIR/src:$PYTHONPATH"

# Run scout and capture output
REPORT=$("$DIR/venv/bin/python3" -m nemoclaw_forge.cli scout 2>&1)

# Check for success
if [ $? -eq 0 ]; then
    # Extract only the report part (after the divider)
    CLEAN_REPORT=$(echo "$REPORT" | sed -n '/--- SCOUT INTELLIGENCE REPORT ---/,/---------------------------------/p' | sed '1d;$d')
    
    # Send report via openclaw message send
    # Using the channel and target from .env, connecting to local gateway
    export OPENCLAW_GATEWAY_URL="ws://127.0.0.1:18789"
    export OPENCLAW_GATEWAY_TOKEN="60a2863244a851589f7a6099024289a57446458ee4585a54"
    
    /home/ubuntu/.npm-global/bin/openclaw message send --channel discord --target "$REPORT_TARGET" --message "$CLEAN_REPORT"
else
    # Report error to user
    export OPENCLAW_GATEWAY_URL="ws://127.0.0.1:18789"
    export OPENCLAW_GATEWAY_TOKEN="60a2863244a851589f7a6099024289a57446458ee4585a54"
    
    /home/ubuntu/.npm-global/bin/openclaw message send --channel discord --target "$REPORT_TARGET" --message "⚠️ Forge-Scout reported an error during the scheduled mission:\n$REPORT"
fi
