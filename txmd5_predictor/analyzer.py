import logging
import asyncio
import os
import copy
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class LLMEnsembleAlgorithm:
    def __init__(self):
        # Local imports in __init__ to avoid early import errors if keys are missing
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        try:
            from openai import AsyncOpenAI
            if self.openai_key:
                self.openai_client = AsyncOpenAI(api_key=self.openai_key)
            else:
                self.openai_client = None
        except ImportError:
            self.openai_client = None

        try:
            from anthropic import AsyncAnthropic
            if self.anthropic_key:
                self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_key)
            else:
                self.anthropic_client = None
        except ImportError:
            self.anthropic_client = None

        # Add more clients as needed

    async def predict(self, history: List[Dict], skip_llm: bool = False) -> str:
        if skip_llm:
            return None # Skip actual LLM call during backtesting

        # For a real implementation, we would call the APIs here.
        # Currently just a stub since real LLM API usage inside the tight loop can be expensive.
        return "Tài" if len(history) % 2 == 0 else "Xỉu"


class Analyzer:
    def __init__(self):
        self.history = []
        self.best_algo = "trend"
        self.best_algo_accuracy = 0.0
        self.llm_ensemble = LLMEnsembleAlgorithm()
        self.algorithms = {
            "markov": self._algo_markov,
            "trend": self._algo_trend,
            "recent_majority": self._algo_recent_majority,
            "sum_analysis": self._algo_sum_analysis,
            "llm_ensemble": self._algo_llm_ensemble
        }

    def add_session(self, session: Dict):
        # Ensure we don't duplicate
        if self.history and self.history[0].get('id') == session.get('id'):
            self.history[0] = session
        else:
            self.history.insert(0, session)
            # Keep history manageable
            if len(self.history) > 1000:
                self.history = self.history[:1000]

    def _algo_markov(self, sub_history: List[Dict]) -> str:
        if len(sub_history) < 2: return "Tài"

        # Simple markov: count transitions from last state
        last_result = "Tài" if sub_history[0].get('point', 0) >= 11 else "Xỉu"

        tai_to_tai = 0
        tai_to_xiu = 0
        xiu_to_tai = 0
        xiu_to_xiu = 0

        for i in range(1, min(len(sub_history) - 1, 100)):
            curr = "Tài" if sub_history[i].get('point', 0) >= 11 else "Xỉu"
            prev = "Tài" if sub_history[i+1].get('point', 0) >= 11 else "Xỉu"

            if prev == "Tài" and curr == "Tài": tai_to_tai += 1
            elif prev == "Tài" and curr == "Xỉu": tai_to_xiu += 1
            elif prev == "Xỉu" and curr == "Tài": xiu_to_tai += 1
            elif prev == "Xỉu" and curr == "Xỉu": xiu_to_xiu += 1

        if last_result == "Tài":
            return "Tài" if tai_to_tai >= tai_to_xiu else "Xỉu"
        else:
            return "Tài" if xiu_to_tai >= xiu_to_xiu else "Xỉu"

    def _algo_trend(self, sub_history: List[Dict]) -> str:
        if len(sub_history) < 3: return "Tài"

        # Detect simple bệt (streak) or cầu chuyền (alternating)
        r1 = "Tài" if sub_history[0].get('point', 0) >= 11 else "Xỉu"
        r2 = "Tài" if sub_history[1].get('point', 0) >= 11 else "Xỉu"
        r3 = "Tài" if sub_history[2].get('point', 0) >= 11 else "Xỉu"

        if r1 == r2 == r3:
            return r1 # Bet
        elif r1 != r2 and r2 != r3:
            return "Xỉu" if r1 == "Tài" else "Tài" # Chuyen

        # Default to following the last
        return r1

    def _algo_recent_majority(self, sub_history: List[Dict]) -> str:
        if not sub_history: return "Tài"

        recent = sub_history[:10]
        tai_count = sum(1 for s in recent if s.get('point', 0) >= 11)

        return "Tài" if tai_count >= len(recent)/2 else "Xỉu"

    def _algo_sum_analysis(self, sub_history: List[Dict]) -> str:
        if not sub_history: return "Tài"

        recent_sums = [s.get('point', 0) for s in sub_history[:5]]
        avg_sum = sum(recent_sums) / len(recent_sums)

        return "Tài" if avg_sum >= 10.5 else "Xỉu"

    async def _algo_llm_ensemble(self, sub_history: List[Dict], skip_llm: bool = False) -> str:
        return await self.llm_ensemble.predict(sub_history, skip_llm=skip_llm)

    async def predict_next(self, skip_llm: bool = False) -> str:
        if not self.history:
            return "Tài"

        algo_func = self.algorithms.get(self.best_algo, self._algo_trend)

        if self.best_algo == "llm_ensemble":
            return await algo_func(self.history, skip_llm=skip_llm)
        else:
            return algo_func(self.history)

    async def simulate_and_optimize(self):
        """
        Backtest all algorithms against history (oldest to newest) to find the best one.
        If analyzing history[i], the prediction is made on history[i+1:] (older data)
        and evaluated against history[i].
        """
        if len(self.history) < 20:
            return

        logger.info("Starting simulation and optimization...")

        results = {name: {"correct": 0, "total": 0} for name in self.algorithms.keys()}

        # Test against the last 100 sessions if available
        test_history = self.history[:100]

        for name, algo_func in self.algorithms.items():
            # Go from oldest in our test slice to newest
            for i in range(len(test_history) - 2, -1, -1):
                sub_history = test_history[i+1:]
                if not sub_history:
                    continue

                if name == "llm_ensemble":
                    pred = await algo_func(sub_history, skip_llm=True)
                else:
                    pred = algo_func(sub_history)

                # Actual result is at index i
                actual_point = test_history[i].get('point', 0)
                actual_result = test_history[i].get('result') or test_history[i].get('resultTruyenThong')

                if not actual_result:
                    actual_result = "Tài" if actual_point >= 11 else "Xỉu"

                if pred and pred == actual_result:
                    results[name]["correct"] += 1
                results[name]["total"] += 1

        best_name = self.best_algo
        best_acc = 0.0

        for name, res in results.items():
            if res["total"] > 0:
                acc = res["correct"] / res["total"]
                logger.debug(f"Algorithm {name} accuracy: {acc:.2f}")
                if acc > best_acc:
                    best_acc = acc
                    best_name = name

        self.best_algo = best_name
        self.best_algo_accuracy = best_acc
        logger.info(f"Optimization complete. Best algorithm: {self.best_algo} with {self.best_algo_accuracy*100:.2f}% accuracy")
