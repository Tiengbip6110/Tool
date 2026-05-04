import os
import aiohttp
import asyncio

CHAT_ID = "8308036418"  # The ID you requested

async def send_telegram_message(message: str):
    """Sends a message to the Telegram bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print(f"Would send to Telegram: {message}")
        return

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    print(f"Failed to send Telegram message: {response.status} - {text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

async def report_hourly_stats(analyzer, predicted_session_count: int):
    """Formats and sends the hourly report based on the analyzer's state."""
    logic_name = analyzer.best_logic.upper()
    accuracy = analyzer.accuracy

    msg = (
        f"📊 <b>BÁO CÁO HÀNG GIỜ TXMD5 PREDICTOR</b> 📊\n\n"
        f"🧠 Logic tốt nhất hiện tại: <b>{logic_name}</b>\n"
        f"🎯 Tỉ lệ chính xác: <b>{accuracy:.2f}%</b>\n"
        f"🔄 Số phiên đã dự đoán: <b>{predicted_session_count}</b>\n\n"
        f"<i>Hệ thống đang tiếp tục theo dõi và tự động tối ưu...</i>"
    )

    await send_telegram_message(msg)

async def start_hourly_reporting_loop(analyzer, get_prediction_count_func):
    """Runs continuously and sends a report every 1 hour (3600 seconds)."""
    while True:
        await asyncio.sleep(3600)  # 1 hour
        count = get_prediction_count_func()
        await report_hourly_stats(analyzer, count)
