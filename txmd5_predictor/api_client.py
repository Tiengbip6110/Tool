import aiohttp
import logging
from config import API_URL

logger = logging.getLogger(__name__)

async def fetch_sessions(session: aiohttp.ClientSession) -> list:
    """Fetches the latest Sic Bo sessions from the API."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        async with session.get(API_URL, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if 'list' in data:
                    return data['list']
                else:
                    logger.warning("Key 'list' not found in API response.")
            else:
                logger.error(f"API returned status code: {response.status}")
    except Exception as e:
        logger.error(f"Error fetching data from API: {e}")

    return []
