#!/bin/bash
# Start the Moonlight Ledger API
DIR="/home/ubuntu/.openclaw/workspace/nemoclaw_forge"
cd "$DIR"
export PYTHONPATH="$DIR/src:$PYTHONPATH"
nohup ./venv/bin/python3 -m nemoclaw_forge.cli api > /tmp/ledger_api.log 2>&1 &
echo "Moonlight Ledger API started on port 8000."
