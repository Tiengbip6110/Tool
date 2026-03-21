import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Tuple

# AI APIs
try:
    import openai
except ImportError:
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import anthropic
except ImportError:
    anthropic = None

logger = logging.getLogger(__name__)

class AI_Predictor:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if self.gemini_key and genai:
            genai.configure(api_key=self.gemini_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')

        if self.anthropic_key and anthropic:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)

        self.prompt_template = """
Bạn là một chuyên gia phân tích dữ liệu lịch sử của trò chơi Tài Xỉu (Sic Bo).
Dưới đây là lịch sử các phiên gần nhất. Mỗi phiên bao gồm kết quả (TAI hoặc XIU), các viên xúc xắc và tổng điểm.
Lịch sử từ cũ nhất đến mới nhất:
{history_str}

Nhiệm vụ của bạn là dựa vào xu hướng, chuỗi (bệt, 1-1, 1-2-1), và quy luật của điểm số để dự đoán kết quả của phiên TIẾP THEO.
Bạn chỉ được trả lời 1 từ duy nhất: "TAI" hoặc "XIU".
Không được giải thích, không thêm bất kỳ ký tự nào khác.
"""
        # Caching logic
        self.last_history_str = ""
        self.last_prediction = None

    def _prepare_history_str(self, history: List[Dict[str, Any]], limit: int = 50) -> str:
        recent = history[-limit:] if len(history) > limit else history
        lines = []
        for h in recent:
            lines.append(f"Kết quả: {h['result']}, Điểm: {h['point']}, Xúc xắc: {h['dices']}")
        return "\n".join(lines)

    async def predict_openai(self, history: List[Dict[str, Any]]) -> str:
        if not openai or not self.openai_key:
            return None

        try:
            client = openai.AsyncOpenAI(api_key=self.openai_key)
            prompt = self.prompt_template.format(history_str=self._prepare_history_str(history))
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.2
            )
            ans = response.choices[0].message.content.strip().upper()
            if "TAI" in ans: return "TAI"
            if "XIU" in ans: return "XIU"
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
        return None

    async def predict_gemini(self, history: List[Dict[str, Any]]) -> str:
        if not genai or not self.gemini_key:
            return None

        try:
            prompt = self.prompt_template.format(history_str=self._prepare_history_str(history))
            # Run blocking gemini call in thread executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self.gemini_model.generate_content(prompt))
            ans = response.text.strip().upper()
            if "TAI" in ans: return "TAI"
            if "XIU" in ans: return "XIU"
        except Exception as e:
            logger.error(f"Gemini error: {e}")
        return None

    async def predict_anthropic(self, history: List[Dict[str, Any]]) -> str:
        if not anthropic or not self.anthropic_key:
            return None

        try:
            prompt = self.prompt_template.format(history_str=self._prepare_history_str(history))
            loop = asyncio.get_event_loop()

            def call_anthropic():
                msg = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=10,
                    temperature=0.2,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return msg.content[0].text

            ans = await loop.run_in_executor(None, call_anthropic)
            ans = ans.strip().upper()
            if "TAI" in ans: return "TAI"
            if "XIU" in ans: return "XIU"
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
        return None

    async def ensemble_predict(self, history: List[Dict[str, Any]], algo_prediction: str) -> str:
        """Combine AI predictions with the best algorithmic prediction."""
        if not history:
            return "TAI"

        history_str = self._prepare_history_str(history)
        # Check cache
        if self.last_history_str == history_str and self.last_prediction:
            return self.last_prediction

        tasks = [
            self.predict_openai(history),
            self.predict_gemini(history),
            self.predict_anthropic(history)
        ]
        # Introduce a small delay to avoid hitting rate limits when backtesting heavily
        await asyncio.sleep(0.5)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        votes = {"TAI": 0, "XIU": 0}

        # Add algo prediction (weighted slightly higher)
        if algo_prediction in votes:
            votes[algo_prediction] += 1.5

        for res in results:
            if isinstance(res, str) and res in votes:
                votes[res] += 1.0

        final_prediction = None
        if votes["TAI"] > votes["XIU"]:
            final_prediction = "TAI"
        elif votes["XIU"] > votes["TAI"]:
            final_prediction = "XIU"
        else:
            final_prediction = algo_prediction or "TAI"

        # Update cache
        self.last_history_str = history_str
        self.last_prediction = final_prediction

        return final_prediction
