import argparse
import asyncio
import logging
import sys

from .forge import Forge
from .claw import Claw
from .scout import ScoutMaster
from .brain import Brain
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

async def run_forge():
    forge = Forge()
    try:
        await forge.start()
        print("Forge started. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await forge.stop()

async def run_claw(worker_id: str):
    claw = Claw(worker_id=worker_id)
    try:
        await claw.start()
        print(f"Claw {worker_id} started. Press Ctrl+C to stop.")
    except KeyboardInterrupt:
        await claw.stop()

async def run_scout_task():
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        return
    brain = Brain()
    
    # Mocking gog command func for now
    async def mock_gog_exec(cmd: str):
        # We use 'exec' tool within the main agent to actually run it
        # But for the CLI inside the container, we need to handle it.
        # Let's use subprocess for the local CLI.
        import subprocess
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        return stdout

    scout = ScoutMaster(github_token, brain, mock_gog_exec)
    report = await scout.run_full_scout()
    print("\n--- SCOUT INTELLIGENCE REPORT ---")
    print(report)
    print("---------------------------------\n")

async def run_api_server():
    import uvicorn
    # Use 0.0.0.0 to allow Tailscale access
    uvicorn.run("nemoclaw_forge.api:app", host="0.0.0.0", port=8000, reload=False)

def main():
    parser = argparse.ArgumentParser(description="NemoClaw-Forge CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    forge_parser = subparsers.add_parser("forge", help="Start the Forge Master")
    
    claw_parser = subparsers.add_parser("claw", help="Start a Claw Worker")
    claw_parser.add_argument("--id", required=True, help="Unique worker ID")
    
    scout_parser = subparsers.add_parser("scout", help="Run a manual scout mission")
    
    api_parser = subparsers.add_parser("api", help="Start the Moonlight Ledger API server")
    
    args = parser.parse_args()
    
    if args.command == "forge":
        asyncio.run(run_forge())
    elif args.command == "claw":
        asyncio.run(run_claw(args.id))
    elif args.command == "scout":
        asyncio.run(run_scout_task())
    elif args.command == "api":
        asyncio.run(run_api_server())

if __name__ == "__main__":
    main()
