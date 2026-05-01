import asyncio
import aiohttp
import logging

class Txmd5ApiClient:
    def __init__(self, url="https://wtxmd52.tele68.com/v1/txmd5/sessions"):
        self.url = url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.session = None
        self.connector = None

    async def init_session(self):
        if self.session is None:
            self.connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(connector=self.connector, headers=self.headers)

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
        if self.connector:
            await self.connector.close()
            self.connector = None

    async def fetch_sessions(self):
        try:
            if self.session is None:
                await self.init_session()

            async with self.session.get(self.url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('list', [])
                else:
                    logging.error(f"API returned status {response.status}")
                    return []
        except Exception as e:
            logging.error(f"Error fetching API: {e}")
            return []
