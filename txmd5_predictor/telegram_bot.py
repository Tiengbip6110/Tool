import logging
import asyncio
import aiohttp
import os

logger = logging.getLogger(__name__)

class TelegramReporter:
    def __init__(self, bot_token: str = None, chat_id: str = "8308036418"):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    async def send_message(self, text: str) -> bool:
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not set, skipping message.")
            return False

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }
                async with session.post(self.api_url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"Telegram message sent to {self.chat_id}")
                        return True
                    else:
                        resp_text = await response.text()
                        logger.error(f"Failed to send Telegram message: {response.status} - {resp_text}")
                        return False
        except Exception as e:
            logger.error(f"Exception while sending telegram message: {e}")
            return False

    def format_report(self, session_id: int, result: str, point: int, dices: list,
                      predicted_next: str, best_algo: str, accuracy: float) -> str:

        icon = "🟢" if result == "TAI" else "🔴"
        pred_icon = "🟢" if predicted_next == "TAI" else "🔴"

        msg = (
            f"📊 *BÁO CÁO PHÂN TÍCH TÀI XỈU MD5*\n"
            f"🕒 Cập nhật sau mỗi 1 giờ\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🎲 Phiên gần nhất: `{session_id}`\n"
            f"Kết quả: *{result}* {icon} - Tổng: {point}\n"
            f"Xúc xắc: {dices}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *DỰ ĐOÁN PHIÊN TIẾP THEO*\n"
            f"Dự đoán: *{predicted_next}* {pred_icon}\n"
            f"Thuật toán tối ưu nhất hiện tại: `{best_algo}`\n"
            f"Tỷ lệ chuẩn xác (Backtest): `{accuracy*100:.2f}%`\n\n"
            f"💡 *Hệ thống tự động điều chỉnh thuật toán sau mỗi ván sai dựa trên backtest lịch sử.*"
        )
        return msg
