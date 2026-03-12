import aiohttp
import logging
import asyncio

# Cấu hình logging cơ bản
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TelegramReporter:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    async def send_message(self, text: str):
        """
        Gửi tin nhắn văn bản đến Telegram Chat ID được cấu hình.
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }
                async with session.post(self.base_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logging.error(f"Lỗi gửi Telegram (Mã {response.status}): {error_text}")
                    else:
                        logging.info("Đã gửi báo cáo qua Telegram thành công.")
        except Exception as e:
            logging.error(f"Lỗi kết nối khi gửi Telegram: {e}")

# Đoạn mã dùng để kiểm thử độc lập (nếu cần)
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # Load .env variables (nếu có)
    load_dotenv()

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        reporter = TelegramReporter(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

        async def test():
            await reporter.send_message("🚀 *Kiểm tra hệ thống báo cáo Dự đoán TXMD5* 🚀\n\nHệ thống đã sẵn sàng!")

        asyncio.run(test())
    else:
        print("Vui lòng cấu hình TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID trong .env")
