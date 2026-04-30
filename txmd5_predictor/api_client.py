import aiohttp
import asyncio
from loguru import logger
from typing import List, Dict, Callable, Any

class APIClient:
    def __init__(self, analyzer=None):
        self.url = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
        self.history = []
        self.history_ids = set()
        self.is_running = False
        self.analyzer = analyzer  # We'll pass analyzer to push new data to it
        self.on_new_data_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._session = None

    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self.on_new_data_callbacks.append(callback)

    async def _get_session(self):
        if self._session is None or self._session.closed:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*"
            }
            connector = aiohttp.TCPConnector(ssl=False)
            self._session = aiohttp.ClientSession(headers=headers, connector=connector)
        return self._session

    async def fetch_data(self):
        session = await self._get_session()
        try:
            async with session.get(self.url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("list", [])
                else:
                    logger.warning(f"Failed to fetch API, status: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching API: {e}")
            return []

    async def poll(self):
        self.is_running = True
        logger.info(f"Starting API Poller on {self.url} every 500ms...")

        # Initial fetch to populate history
        initial_data = await self.fetch_data()
        if initial_data:
            # Sort by id to process oldest to newest if needed, or just insert
            # Usually API returns newest first. We want history to be sorted oldest -> newest
            sorted_data = sorted(initial_data, key=lambda x: x["id"])
            for session_data in sorted_data:
                self._process_session(session_data, initial=True)
            logger.info(f"Loaded {len(initial_data)} initial sessions.")
            if self.analyzer:
                self.analyzer.initialize_history(self.history)

        while self.is_running:
            data = await self.fetch_data()
            if data:
                # The newest might be at index 0
                sorted_data = sorted(data, key=lambda x: x["id"])
                for session_data in sorted_data:
                    self._process_session(session_data, initial=False)

            await asyncio.sleep(0.5) # 500ms

    def _process_session(self, session_data: dict, initial: bool = False):
        session_id = session_data.get("id")
        if session_id and session_id not in self.history_ids:
            self.history_ids.add(session_id)
            self.history.append(session_data)

            if not initial:
                logger.info(f"New Session Detected: {session_id} - {session_data.get('resultTruyenThong')} ({session_data.get('point')})")
                for callback in self.on_new_data_callbacks:
                    try:
                        callback(session_data)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")

    def stop(self):
        self.is_running = False
        if self._session and not self._session.closed:
            asyncio.create_task(self._session.close())
