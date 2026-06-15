import logging
import random
import asyncio
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseAlgorithm:
    def predict(self, history: List[Dict[str, Any]]) -> Optional[str]:
        raise NotImplementedError

class MarkovAlgorithm(BaseAlgorithm):
    def predict(self, history: List[Dict[str, Any]]) -> Optional[str]:
        if len(history) < 2:
            return random.choice(["Tài", "Xỉu"])

        transitions = {"Tài": {"Tài": 0, "Xỉu": 0}, "Xỉu": {"Tài": 0, "Xỉu": 0}}
        for i in range(len(history) - 1):
            curr = history[i].get('result') or history[i].get('resultTruyenThong')
            nxt = history[i+1].get('result') or history[i+1].get('resultTruyenThong')
            if curr and nxt and curr in transitions and nxt in transitions[curr]:
                transitions[curr][nxt] += 1

        last_result = history[-1].get('result') or history[-1].get('resultTruyenThong')
        if not last_result or last_result not in transitions:
            return random.choice(["Tài", "Xỉu"])

        t_count = transitions[last_result]["Tài"]
        x_count = transitions[last_result]["Xỉu"]

        if t_count > x_count:
            return "Tài"
        elif x_count > t_count:
            return "Xỉu"
        else:
            return random.choice(["Tài", "Xỉu"])

class TrendAlgorithm(BaseAlgorithm):
    def predict(self, history: List[Dict[str, Any]]) -> Optional[str]:
        if len(history) < 3:
            return random.choice(["Tài", "Xỉu"])

        recent = [h.get('result') or h.get('resultTruyenThong') for h in history[-3:]]
        if all(r == recent[0] for r in recent) and recent[0]:
            # Expect trend to break after 3 identical
            return "Xỉu" if recent[0] == "Tài" else "Tài"

        return recent[-1] if recent[-1] else random.choice(["Tài", "Xỉu"])

class MajorityAlgorithm(BaseAlgorithm):
    def predict(self, history: List[Dict[str, Any]]) -> Optional[str]:
        if not history:
             return random.choice(["Tài", "Xỉu"])

        recent = history[-10:]
        results = [h.get('result') or h.get('resultTruyenThong') for h in recent]
        t_count = results.count("Tài")
        x_count = results.count("Xỉu")

        if t_count > x_count:
            return "Tài"
        elif x_count > t_count:
            return "Xỉu"
        return random.choice(["Tài", "Xỉu"])

class SumAnalysisAlgorithm(BaseAlgorithm):
    def predict(self, history: List[Dict[str, Any]]) -> Optional[str]:
        if not history:
             return random.choice(["Tài", "Xỉu"])

        last_session = history[-1]
        point = last_session.get('point')

        if point is None:
             return random.choice(["Tài", "Xỉu"])

        try:
            point = int(point)
        except ValueError:
            return random.choice(["Tài", "Xỉu"])

        # Logic: High sums might lead to low sums, and vice versa
        if point >= 14:
            return "Xỉu"
        elif point <= 7:
            return "Tài"
        else:
            # Medium sums follow the trend
            last_result = last_session.get('result') or last_session.get('resultTruyenThong')
            return last_result if last_result else random.choice(["Tài", "Xỉu"])


import json
import asyncio

class LLMEnsembleAlgorithm(BaseAlgorithm):
    def __init__(self):
        # Local imports inside init to prevent circular/early import errors if config is missing keys
        try:
            from config import OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY
            self.openai_key = OPENAI_API_KEY
            self.gemini_key = GEMINI_API_KEY
            self.anthropic_key = ANTHROPIC_API_KEY

            if self.openai_key:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=self.openai_key)

            if self.anthropic_key:
                from anthropic import AsyncAnthropic
                self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_key)

            if self.gemini_key:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
        except ImportError as e:
            logger.error(f"Error initializing LLMs: {e}")
            self.openai_key = None
            self.gemini_key = None
            self.anthropic_key = None

    def _format_prompt(self, history: List[Dict[str, Any]]) -> str:
        recent_points = [str(h.get('point')) for h in history[-10:] if h.get('point')]
        return f"Dựa vào lịch sử các điểm xí ngầu gần đây: {', '.join(recent_points)}. Theo bạn, ván tiếp theo sẽ ra Tài (tổng >= 11) hay Xỉu (tổng <= 10)? Chỉ trả lời 1 từ duy nhất là 'Tài' hoặc 'Xỉu'."

    async def _call_openai(self, prompt: str) -> Optional[str]:
        if not self.openai_key: return None
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return None

    async def _call_anthropic(self, prompt: str) -> Optional[str]:
        if not self.anthropic_key: return None
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            return None

    async def _call_gemini(self, prompt: str) -> Optional[str]:
        if not self.gemini_key: return None
        try:
            # Note: Gemini python SDK currently primarily uses generate_content synchronously or generate_content_async
            response = await self.gemini_model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return None

    async def predict_async(self, history: List[Dict[str, Any]], skip_llm: bool = False) -> Optional[str]:
        if skip_llm or not history:
            return random.choice(["Tài", "Xỉu"])

        prompt = self._format_prompt(history)

        # Run API calls concurrently
        tasks = [
            self._call_openai(prompt),
            self._call_anthropic(prompt),
            self._call_gemini(prompt)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_votes = []

        for res in results:
            if isinstance(res, str):
                if "Tài" in res:
                    valid_votes.append("Tài")
                elif "Xỉu" in res:
                    valid_votes.append("Xỉu")

        if not valid_votes:
            return random.choice(["Tài", "Xỉu"])

        t_count = valid_votes.count("Tài")
        x_count = valid_votes.count("Xỉu")

        if t_count > x_count:
            return "Tài"
        elif x_count > t_count:
            return "Xỉu"
        return random.choice(["Tài", "Xỉu"])

    def predict(self, history: List[Dict[str, Any]]) -> Optional[str]:
        # Synchronous fallback for basic testing without async loop
        return random.choice(["Tài", "Xỉu"])

class Analyzer:
    def __init__(self):
        self.history = []
        self.algorithms = {
            "markov": MarkovAlgorithm(),
            "trend": TrendAlgorithm(),
            "majority": MajorityAlgorithm(),
            "sum_analysis": SumAnalysisAlgorithm(),
            "llm_ensemble": LLMEnsembleAlgorithm()
        }
        self.current_algo = "markov"
        self.last_prediction = None
        self.last_prediction_session_id = None

        # Stats
        self.total_predictions = 0
        self.correct_predictions = 0

    def update_history(self, session: Dict[str, Any]):
        """Adds a new session or updates the latest if IDs match."""
        if not self.history:
            self.history.append(session)
            return

        latest = self.history[-1]
        if latest.get('id') == session.get('id'):
            self.history[-1] = session
        else:
            self.history.append(session)

            # Keep history from growing unbounded indefinitely
            if len(self.history) > 1000:
                self.history = self.history[-1000:]

    def get_prediction(self, skip_llm: bool = False) -> str:
        """Gets a prediction using the currently selected optimal algorithm."""
        if not self.history:
             return "Tài"

        algo = self.algorithms[self.current_algo]
        if self.current_algo == "llm_ensemble":
            # For synchronous calls fallback, though usually we'd await predict_async
            prediction = algo.predict(self.history)
        else:
            prediction = algo.predict(self.history)

        return prediction or "Tài"

    async def get_prediction_async(self, skip_llm: bool = False) -> str:
        if not self.history:
             return "Tài"

        algo = self.algorithms[self.current_algo]
        if self.current_algo == "llm_ensemble":
            prediction = await algo.predict_async(self.history, skip_llm=skip_llm)
        else:
            prediction = algo.predict(self.history)

        return prediction or "Tài"

    def evaluate_last_prediction(self):
        """Evaluates if the last prediction was correct and triggers optimization if failed."""
        if not self.last_prediction or not self.last_prediction_session_id:
            return

        # Find the session we predicted for
        actual_result = None
        for session in reversed(self.history):
            if session.get('id') == self.last_prediction_session_id:
                actual_result = session.get('result') or session.get('resultTruyenThong')
                break

        if actual_result:
            self.total_predictions += 1
            if actual_result == self.last_prediction:
                self.correct_predictions += 1
                logger.info(f"Prediction Correct! Expected: {self.last_prediction}, Actual: {actual_result}")
            else:
                logger.info(f"Prediction Failed! Expected: {self.last_prediction}, Actual: {actual_result}")
                self._simulate_and_optimize()

            self.last_prediction = None
            self.last_prediction_session_id = None

    def _simulate_and_optimize(self):
        """
        Rewinds history and backtests all algorithms to find the most accurate one.
        Uses skip_llm=True to prevent massive API spam/costs during backtesting.
        """
        logger.info("Running simulation and optimization...")
        scores = {name: 0 for name in self.algorithms.keys()}

        # Test on the last 50 historical steps
        test_history = self.history[-50:] if len(self.history) > 50 else self.history
        if len(test_history) < 5:
            return

        for name, algo in self.algorithms.items():
            correct = 0
            # Test each step
            for i in range(2, len(test_history)):
                # Provide sub-history up to i-1
                sub_history = test_history[:i]

                if name == "llm_ensemble":
                    # skip_llm must be true during optimization
                    pred = algo.predict(sub_history)
                else:
                    pred = algo.predict(sub_history)

                actual = test_history[i].get('result') or test_history[i].get('resultTruyenThong')
                if pred and actual and pred == actual:
                    correct += 1
            scores[name] = correct

        # Find the best performing algorithm
        best_algo = max(scores, key=scores.get)
        logger.info(f"Optimization complete. Scores: {scores}. Selecting: {best_algo}")
        self.current_algo = best_algo

    def get_stats(self) -> str:
        pct = (self.correct_predictions / self.total_predictions * 100) if self.total_predictions > 0 else 0
        return f"Total: {self.total_predictions}, Correct: {self.correct_predictions}, Accuracy: {pct:.2f}%, Current Logic: {self.current_algo}"
