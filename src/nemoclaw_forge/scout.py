import asyncio
import json
import logging
from typing import List, Dict, Any
import aiohttp
from .brain import Brain

from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GitHubScout:
    """Scouts GitHub for trending repositories or user-specific updates."""
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"

    async def fetch_trending(self, days: int = 7, language: str = "python") -> List[Dict[str, Any]]:
        # Calculate date for 'recently created' to simulate trending
        date_threshold = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query = f"language:{language} created:>{date_threshold}"
        url = f"{self.base_url}/search/repositories?q={query}&sort=stars&order=desc"
        
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

    async def fetch_upwork_jobs(self) -> List[Dict[str, str]]:
        # Search for recent Upwork notifications (regardless of read status)
        cmd_search = "GOG_KEYRING_PASSWORD=openclaw gog gmail search 'from:upwork newer_than:1d' --limit 5 --select 'id,subject'"
        try:
            result = await self.exec_cmd(cmd_search)
            lines = result.splitlines()
            jobs_meta = []
            for line in lines:
                if "New job:" in line:
                    parts = line.split(None, 1)
                    if len(parts) >= 1:
                        msg_id = parts[0]
                        subject = line.split("New job:")[1].strip() if "New job:" in line else line
                        jobs_meta.append({"id": msg_id, "subject": subject})
            
            detailed_jobs = []
            for job in jobs_meta:
                # Get the snippet/body for each job to provide context for the summary
                cmd_get = f"GOG_KEYRING_PASSWORD=openclaw gog gmail get {job['id']} --select 'snippet'"
                body = await self.exec_cmd(cmd_get)
                # Extract the overview part if possible, otherwise just use the body
                detailed_jobs.append({
                    "title": job['subject'],
                    "context": body[:2000] # Limit context size
                })
            return detailed_jobs
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
            "github_trending": [{"name": r["full_name"], "url": r["html_url"], "desc": r["description"]} for r in gh_results],
            "upwork_opportunities": upwork_jobs
        }
        
        prompt = (
            "You are a senior technical intelligence analyst. Review the data below "
            "and produce a concise, high-signal Markdown brief in English.\n\n"
            "Use this structure:\n"
            "### GitHub Trending Repositories (Last 7 Days)\n"
            "List up to 5 repositories:\n"
            "- **Project name** with a link\n"
            "- **Likely technology stack** inferred from the description\n"
            "- **One-sentence summary** of the core use case\n\n"
            "### Upwork Opportunities\n"
            "List up to 5 relevant jobs:\n"
            "- **Job title**\n"
            "- **One-sentence summary** of technical requirements and delivery goal\n\n"
            f"Raw data:\n{json.dumps(report_data, indent=2, ensure_ascii=False)}"
        )
        
        return await self.brain.execute(prompt)
