import argparse
import asyncio
import logging
import sys

from .forge import Forge
from .claw import Claw

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

def main():
    parser = argparse.ArgumentParser(description="NemoClaw-Forge CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    forge_parser = subparsers.add_parser("forge", help="Start the Forge Master")
    
    claw_parser = subparsers.add_parser("claw", help="Start a Claw Worker")
    claw_parser.add_argument("--id", required=True, help="Unique worker ID")
    
    args = parser.parse_args()
    
    if args.command == "forge":
        asyncio.run(run_forge())
    elif args.command == "claw":
        asyncio.run(run_claw(args.id))

if __name__ == "__main__":
    main()
