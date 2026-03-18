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
    
    # Save to Markdown file with date
    REPORT_FILE="$DIR/reports/$(date +%Y-%m-%d)-scout.md"
    echo "$CLEAN_REPORT" > "$REPORT_FILE"

    # Send report via openclaw message send
    export OPENCLAW_GATEWAY_URL="ws://127.0.0.1:18789"
    export OPENCLAW_GATEWAY_TOKEN="60a2863244a851589f7a6099024289a57446458ee4585a54"
    
    /home/ubuntu/.npm-global/bin/openclaw message send --channel discord --target "$REPORT_TARGET" --message "📜 今日份赛博情报简报（$(date +%Y-%m-%d)）已铸造完成，请查收下方附件。" --media "$REPORT_FILE"
else
    # Report error to user
    export OPENCLAW_GATEWAY_URL="ws://127.0.0.1:18789"
    export OPENCLAW_GATEWAY_TOKEN="60a2863244a851589f7a6099024289a57446458ee4585a54"
    
    /home/ubuntu/.npm-global/bin/openclaw message send --channel discord --target "$REPORT_TARGET" --message "⚠️ Forge-Scout 在执行调度任务时遭遇了未知的虚空干扰：\n$REPORT"
fi
