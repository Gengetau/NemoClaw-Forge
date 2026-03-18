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
        # Search for unread Upwork notifications
        cmd_search = "GOG_KEYRING_PASSWORD=openclaw gog gmail search 'is:unread from:upwork newer_than:1d' --limit 5 --select 'id,subject'"
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
            "你是一名资深的侦察情报官。请分析以下数据，并为用户提供一份高价值的中文情报简报。\n"
            "请务必使用 Markdown 格式，且确保内容专业、干练。\n\n"
            "报告结构如下：\n"
            "### 🚀 GitHub 热门趋势 (近7天)\n"
            "列出前 5 个项目：\n"
            "- **项目名称** (带链接: [name](url))\n"
            "- **技术栈** (根据项目描述预测)\n"
            "- **中文概要** (一句话说明该项目的核心用途)\n\n"
            "### 💼 Upwork 赚钱机会\n"
            "列出前 5 个最相关的职位：\n"
            "- **职位名称**\n"
            "- **中文概要** (核心技术要求与交付目标)\n\n"
            f"原始数据：\n{json.dumps(report_data, indent=2, ensure_ascii=False)}"
        )
        
        return await self.brain.execute(prompt)
