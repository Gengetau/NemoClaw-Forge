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
PYTHON_BIN="${PYTHON_BIN:-python3}"
REPORT=$("$PYTHON_BIN" -m nemoclaw_forge.cli scout 2>&1)

# Check for success
if [ $? -eq 0 ]; then
    # Extract only the report part (after the divider)
    CLEAN_REPORT=$(echo "$REPORT" | sed -n '/--- SCOUT INTELLIGENCE REPORT ---/,/---------------------------------/p' | sed '1d;$d')
    
    # Save to Markdown file with date
    REPORT_FILE="$DIR/reports/$(date +%Y-%m-%d)-scout.md"
    echo "$CLEAN_REPORT" > "$REPORT_FILE"

    # Send report via openclaw message send
    export OPENCLAW_GATEWAY_URL="${OPENCLAW_GATEWAY_URL:-ws://127.0.0.1:18789}"
    : "${OPENCLAW_GATEWAY_TOKEN:?Set OPENCLAW_GATEWAY_TOKEN before sending reports}"
    
    /home/ubuntu/.npm-global/bin/openclaw message send --channel discord --target "$REPORT_TARGET" --message "Scout intelligence brief for $(date +%Y-%m-%d) is ready. See the attached report." --media "$REPORT_FILE"
else
    # Report error to user
    export OPENCLAW_GATEWAY_URL="${OPENCLAW_GATEWAY_URL:-ws://127.0.0.1:18789}"
    : "${OPENCLAW_GATEWAY_TOKEN:?Set OPENCLAW_GATEWAY_TOKEN before sending reports}"
    
    /home/ubuntu/.npm-global/bin/openclaw message send --channel discord --target "$REPORT_TARGET" --message "Forge-Scout failed during the scheduled run:\n$REPORT"
fi
