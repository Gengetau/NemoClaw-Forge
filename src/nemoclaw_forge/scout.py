import asyncio
import json
import logging
from typing import List, Dict, Any
import aiohttp
from .brain import Brain

logger = logging.getLogger(__name__)

class GitHubScout:
    """Scouts GitHub for trending repositories or user-specific updates."""
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"

    async def fetch_trending(self, query: str = "language:python", sort: str = "stars") -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search/repositories?q={query}&sort={sort}&order=desc"
        headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("items", [])[:5] # Top 5
                else:
                    logger.error(f"GitHub API Error: {resp.status}")
                    return []

class EmailScout:
    """Scouts emails for specific notifications (e.g. Upwork)."""
    def __init__(self, gog_command_func):
        # We pass a function that can execute 'gog' commands
        self.exec_cmd = gog_command_func

    async def fetch_upwork_jobs(self) -> List[str]:
        # Simple proxy: search for unread Upwork notifications
        cmd = "GOG_KEYRING_PASSWORD=openclaw gog gmail search 'is:unread from:upwork newer_than:1d' --limit 5 --select 'subject'"
        try:
            result = await self.exec_cmd(cmd)
            # Basic parsing of gog output
            lines = result.splitlines()
            jobs = [line.strip() for line in lines if "New job:" in line]
            return jobs
        except Exception as e:
            logger.error(f"EmailScout Error: {e}")
            return []

class ScoutMaster:
    """Coordinates various scouts and uses the Brain to summarize."""
    def __init__(self, github_token: str, brain: Brain, exec_cmd_func):
        self.gh_scout = GitHubScout(github_token)
        self.email_scout = EmailScout(exec_cmd_func)
        self.brain = brain

    async def run_full_scout(self) -> str:
        logger.info("Starting full scout mission...")
        
        # Parallel scouting
        gh_results, upwork_jobs = await asyncio.gather(
            self.gh_scout.fetch_trending(),
            self.email_scout.fetch_upwork_jobs()
        )
        
        # Build the prompt for the Brain
        report_data = {
            "github_trending": [{"name": r["full_name"], "desc": r["description"]} for r in gh_results],
            "upwork_notifications": upwork_jobs
        }
        
        prompt = (
            f"You are the Scout Intelligence Officer. Analyze the following data and provide a concise, "
            f"high-value summary of what the user should act on today.\n\nData:\n{json.dumps(report_data, indent=2)}"
        )
        
        return await self.brain.execute(prompt)
