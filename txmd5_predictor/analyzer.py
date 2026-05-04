import math
from typing import List, Dict, Any, Optional
import os
import aiohttp
import asyncio

class MarkovChainPredictor:
    def __init__(self, order=2):
        self.order = order
        self.transitions = {}
        self.history = []

    def update(self, result: str):
        self.history.append(result)
        if len(self.history) > self.order:
            state = tuple(self.history[-self.order-1:-1])
            if state not in self.transitions:
                self.transitions[state] = {'TAI': 0, 'XIU': 0}
            self.transitions[state][result] += 1

    def predict(self) -> str:
        if len(self.history) < self.order:
            return "TAI"  # default

        current_state = tuple(self.history[-self.order:])
        if current_state in self.transitions:
            tai_count = self.transitions[current_state]['TAI']
            xiu_count = self.transitions[current_state]['XIU']
            if tai_count > xiu_count:
                return "TAI"
            elif xiu_count > tai_count:
                return "XIU"
        return "TAI" if len(self.history) % 2 == 0 else "XIU" # Fallback heuristic


class TrendAnalysisPredictor:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.history = []

    def update(self, result: str):
        self.history.append(result)
        if len(self.history) > 100: # keep memory somewhat bounded
            self.history = self.history[-100:]

    def predict(self) -> str:
        if len(self.history) < self.window_size:
            return "TAI"

        recent = self.history[-self.window_size:]
        tai_count = recent.count("TAI")

        if tai_count >= self.window_size - 1:
            return "TAI"
        elif tai_count <= 1:
            return "XIU"

        last_result = self.history[-1]
        if last_result == "TAI":
            return "XIU"
        else:
            return "TAI"


class RecentMajorityPredictor:
    def __init__(self, window_size=7):
        self.window_size = window_size
        self.history = []

    def update(self, result: str):
        self.history.append(result)
        if len(self.history) > self.window_size * 2:
            self.history = self.history[-self.window_size * 2:]

    def predict(self) -> str:
        if not self.history:
            return "TAI"
        recent = self.history[-self.window_size:]
        if recent.count("TAI") > recent.count("XIU"):
            return "TAI"
        return "XIU"


class SumAnalysisPredictor:
    def __init__(self):
        self.sum_history = []
        self.result_history = []

    def update(self, point: int, result: str):
        self.sum_history.append(point)
        self.result_history.append(result)
        if len(self.sum_history) > 50:
            self.sum_history = self.sum_history[-50:]
            self.result_history = self.result_history[-50:]

    def predict(self) -> str:
        if not self.sum_history:
            return "TAI"

        last_sum = self.sum_history[-1]

        tai_after_sum = 0
        xiu_after_sum = 0
        for i in range(len(self.sum_history) - 1):
            if self.sum_history[i] == last_sum:
                if self.result_history[i+1] == "TAI":
                    tai_after_sum += 1
                else:
                    xiu_after_sum += 1

        if tai_after_sum > xiu_after_sum:
            return "TAI"
        elif xiu_after_sum > tai_after_sum:
            return "XIU"

        if last_sum > 10:
            return "XIU"
        else:
            return "TAI"


class EnsembleAnalyzer:
    def __init__(self):
        self.markov = MarkovChainPredictor(order=2)
        self.trend = TrendAnalysisPredictor(window_size=5)
        self.majority = RecentMajorityPredictor(window_size=7)
        self.sum_analysis = SumAnalysisPredictor()

        self.predictors = {
            'markov': self.markov,
            'trend': self.trend,
            'majority': self.majority,
            'sum_analysis': self.sum_analysis
        }

        self.best_logic = 'majority'
        self.accuracy = 0.0

        self.full_history_cache = []

    def feed_data(self, session_data: dict):
        result = session_data.get('resultTruyenThong')
        point = session_data.get('point', 0)

        if result:
            self.markov.update(result)
            self.trend.update(result)
            self.majority.update(result)
            self.sum_analysis.update(point, result)

            self.full_history_cache.append(session_data)
            if len(self.full_history_cache) > 200:
                self.full_history_cache = self.full_history_cache[-200:]

    def get_prediction(self) -> str:
        if not self.best_logic or self.best_logic not in self.predictors:
            return self.majority.predict()
        return self.predictors[self.best_logic].predict()

    def simulate_and_optimize(self):
        """Backtests historical data to evaluate all algorithms and select the best one."""
        if len(self.full_history_cache) < 20:
            return # Need more data

        scores = {k: 0 for k in self.predictors.keys()}
        total_evals = 0

        # Test on the last 50 entries to see what *would* have worked best
        test_window = self.full_history_cache[-50:]

        # Create temporary predictors for simulation
        sim_predictors = {
            'markov': MarkovChainPredictor(order=2),
            'trend': TrendAnalysisPredictor(window_size=5),
            'majority': RecentMajorityPredictor(window_size=7),
            'sum_analysis': SumAnalysisPredictor()
        }

        # Train on older data
        training_data = self.full_history_cache[:-50]
        for data in training_data:
            r = data.get('resultTruyenThong')
            p = data.get('point', 0)
            if r:
                sim_predictors['markov'].update(r)
                sim_predictors['trend'].update(r)
                sim_predictors['majority'].update(r)
                sim_predictors['sum_analysis'].update(p, r)

        # Evaluate on the test window
        for data in test_window:
            r = data.get('resultTruyenThong')
            p = data.get('point', 0)
            if not r: continue

            for name, pred_obj in sim_predictors.items():
                prediction = pred_obj.predict()
                if prediction == r:
                    scores[name] += 1

                # Update with the actual result for the next iteration
                if name == 'sum_analysis':
                    pred_obj.update(p, r)
                else:
                    pred_obj.update(r)

            total_evals += 1

        if total_evals > 0:
            best_score = -1
            best_name = 'majority'
            for name, score in scores.items():
                if score > best_score:
                    best_score = score
                    best_name = name

            self.best_logic = best_name
            self.accuracy = (best_score / total_evals) * 100
            print(f"Optimized logic to {self.best_logic} with accuracy {self.accuracy:.2f}%")


    async def call_llm_api_stub(self, session_id: str, prompt: str) -> str:
        """Stub for external LLM API calls (OpenAI, Gemini, etc.)"""
        # In a real implementation, you would use aiohttp to make a POST request to an LLM provider.
        # This is just a stub returning a dummy prediction.
        print(f"Stub: Calling LLM API for session {session_id}...")
        await asyncio.sleep(0.1) # Simulate network delay
        return "TAI"
