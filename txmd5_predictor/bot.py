import aiohttp
import asyncio
import os

# Using the specified Bot ID and Token setup. We should ideally get token from ENV.
# Since it was not fully specified, I'll provide a structure where token can be injected or default used.
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "") # Ensure to set TELEGRAM_BOT_TOKEN environment variable
CHAT_ID = "8308036418"

async def send_report(message: str, chat_id: str = CHAT_ID, token: str = None):
    token_to_use = token or BOT_TOKEN
    if not token_to_use:
        print("Error: TELEGRAM_BOT_TOKEN is not set.")
        return

    url = f"https://api.telegram.org/bot{token_to_use}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    print(f"Failed to send Telegram message. Status: {response.status}, Error: {text}")
                else:
                    print("Telegram report sent successfully.")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

async def send_hourly_report(logic_name: str, logic_percentage: float, sessions_predicted: int, correct_predictions: int):
    message = (
        f"<b>🚀 BÁO CÁO HỆ THỐNG DỰ ĐOÁN TXMD5 🚀</b>\n\n"
        f"⏱ <b>Thời gian cập nhật:</b> Mỗi 1 giờ\n"
        f"🧠 <b>Thuật toán hiện tại:</b> {logic_name}\n"
        f"📊 <b>Tổng số phiên dự đoán:</b> {sessions_predicted}\n"
        f"✅ <b>Số phiên chính xác:</b> {correct_predictions}\n"
        f"🎯 <b>Tỷ lệ chính xác:</b> {logic_percentage:.2f}%\n\n"
        f"<i>Hệ thống đang liên tục học hỏi và tối ưu hóa qua các phiên.</i>"
    )
    await send_report(message)

# Simple test block
if __name__ == "__main__":
    asyncio.run(send_hourly_report("Markov Order 3", 85.5, 100, 85))
