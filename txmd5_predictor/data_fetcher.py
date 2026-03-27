import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Callable

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, url: str = "https://wtxmd52.tele68.com/v1/txmd5/sessions", interval_ms: int = 500):
        self.url = url
        self.interval = interval_ms / 1000.0
        self.history: List[Dict[str, Any]] = []
        self.latest_session_id = None
        self.is_running = False
        self.callbacks: List[Callable] = []

    def add_callback(self, callback: Callable):
        self.callbacks.append(callback)

    async def fetch_data(self, session: aiohttp.ClientSession):
        try:
            async with session.get(self.url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.warning(f"Failed to fetch data. Status code: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None

    async def process_data(self, raw_data: Dict[str, Any]):
        if not raw_data or "list" not in raw_data:
            return

        sessions = raw_data["list"]
        if not sessions:
            return

        # API returns latest sessions first. We want to check for new ones.
        new_sessions = []
        for s in sessions:
            if self.latest_session_id is None or s["id"] > self.latest_session_id:
                session_data = {
                    "id": s["id"],
                    "result": s.get("resultTruyenThong"),
                    "dices": s.get("dices", []),
                    "point": s.get("point")
                }
                new_sessions.append(session_data)

        if new_sessions:
            # Sort chronologically (oldest first)
            new_sessions.sort(key=lambda x: x["id"])

            for session_data in new_sessions:
                self.history.append(session_data)
                self.latest_session_id = session_data["id"]
                logger.info(f"New session fetched: ID={session_data['id']}, Result={session_data['result']}, Dices={session_data['dices']}, Point={session_data['point']}")

                # Trigger callbacks sequentially to avoid race conditions in analyzer
                for callback in self.callbacks:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(session_data)
                    else:
                        callback(session_data)

    async def run(self):
        self.is_running = True
        logger.info(f"Starting DataFetcher for {self.url} every {self.interval}s")
        async with aiohttp.ClientSession() as session:
            while self.is_running:
                data = await self.fetch_data(session)
                if data:
                    await self.process_data(data)
                await asyncio.sleep(self.interval)

    def stop(self):
        self.is_running = False
        logger.info("Stopping DataFetcher")
