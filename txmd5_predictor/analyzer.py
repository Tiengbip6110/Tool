import logging
import asyncio
import os
import random

logger = logging.getLogger(__name__)

class LLMEnsembleAlgorithm:
    def __init__(self):
        # Local imports in __init__ to prevent early import/circular errors if keys are missing
        self.clients = {}
        try:
            from openai import AsyncOpenAI
            self.clients['openai'] = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        except Exception as e:
            logger.warning(f"Failed to init OpenAI: {e}")

        try:
            from anthropic import AsyncAnthropic
            self.clients['anthropic'] = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        except Exception as e:
            logger.warning(f"Failed to init Anthropic: {e}")

        # In a real scenario, other models (Gemini, Grok, DeepSeek) would be initialized here too.

    async def predict(self, sub_history, skip_llm):
        if skip_llm or not self.clients:
            # Fallback when skipped (backtesting) or no clients configured
            return "TAI" if random.random() > 0.5 else "XIU"

        try:
            # For simplicity in this demo, just return a random prediction when LLM is actually called
            # Real LLM logic would construct prompts and parse responses from multiple AI APIs.
            await asyncio.sleep(0.1) # Simulate API call latency
            return "TAI" if random.random() > 0.5 else "XIU"
        except Exception as e:
            logger.error(f"LLM Prediction error: {e}")
            return "TAI" if random.random() > 0.5 else "XIU"


class Analyzer:
    def __init__(self):
        self.history = []
        self.algorithms = ['markov', 'trend', 'majority', 'sum_analysis', 'llm_ensemble']
        self.current_optimal_algo = 'markov'
        self.algo_performance = {algo: {'correct': 0, 'total': 0} for algo in self.algorithms}

        # General stats
        self.total_predictions = 0
        self.correct_predictions = 0

        self.llm_ensemble = LLMEnsembleAlgorithm()

    def add_session(self, session_data):
        if not self.history:
            self.history.append(session_data)
            return

        incoming_id = session_data['id']

        # Check if the session is already in history to update it (e.g. adding the final result)
        # We only need to check the last few entries
        for i in range(len(self.history)-1, max(-1, len(self.history)-5), -1):
            if self.history[i]['id'] == incoming_id:
                self.history[i] = session_data
                return

        # If not found and it's newer, append it
        if incoming_id > self.history[-1]['id']:
            self.history.append(session_data)

    def _algo_markov(self, sub_history):
        if len(sub_history) < 2:
            return "TAI" if random.random() > 0.5 else "XIU"

        transitions = {'TAI': {'TAI': 0, 'XIU': 0}, 'XIU': {'TAI': 0, 'XIU': 0}}
        for i in range(len(sub_history) - 1):
            curr = sub_history[i].get('resultTruyenThong')
            nxt = sub_history[i+1].get('resultTruyenThong')
            if curr in transitions and nxt in transitions[curr]:
                transitions[curr][nxt] += 1

        last_result = sub_history[-1].get('resultTruyenThong')
        if not last_result or last_result not in transitions:
            return "TAI" if random.random() > 0.5 else "XIU"

        tai_prob = transitions[last_result]['TAI']
        xiu_prob = transitions[last_result]['XIU']

        if tai_prob > xiu_prob:
            return "TAI"
        elif xiu_prob > tai_prob:
            return "XIU"
        return last_result # stick to current state if tie

    def _algo_trend(self, sub_history):
        if len(sub_history) < 3:
            return "TAI" if random.random() > 0.5 else "XIU"

        # Look for alternating (TAI, XIU, TAI) or streaks (TAI, TAI, TAI)
        last_3 = [s.get('resultTruyenThong') for s in sub_history[-3:]]
        if last_3 == ['TAI', 'TAI', 'TAI']:
            return "TAI"
        elif last_3 == ['XIU', 'XIU', 'XIU']:
            return "XIU"
        elif last_3 == ['TAI', 'XIU', 'TAI']:
            return "XIU"
        elif last_3 == ['XIU', 'TAI', 'XIU']:
            return "TAI"
        return "TAI" if random.random() > 0.5 else "XIU"

    def _algo_majority(self, sub_history):
        limit = min(10, len(sub_history))
        if limit == 0:
            return "TAI" if random.random() > 0.5 else "XIU"

        recent = [s.get('resultTruyenThong') for s in sub_history[-limit:]]
        tai_count = recent.count('TAI')
        xiu_count = recent.count('XIU')
        if tai_count > xiu_count:
            return "TAI"
        elif xiu_count > tai_count:
            return "XIU"
        return "TAI" if random.random() > 0.5 else "XIU"

    def _algo_sum(self, sub_history):
        if len(sub_history) < 3:
            return "TAI" if random.random() > 0.5 else "XIU"

        avg_point = sum([s.get('point', 0) for s in sub_history[-3:]]) / 3

        if avg_point > 10.5:
            # Usually if sum is high, expectation might mean it drops back, or continues streak. Let's say mean reversion.
            return "XIU"
        else:
            return "TAI"

    async def _algo_llm_ensemble(self, sub_history, skip_llm):
        return await self.llm_ensemble.predict(sub_history, skip_llm)

    async def _simulate_and_optimize(self):
        """
        Backtesting mechanism that rewinds history and evaluates algorithms.
        """
        if len(self.history) < 10:
            return # Need more data for optimization

        # Reset stats
        for algo in self.algorithms:
            self.algo_performance[algo] = {'correct': 0, 'total': 0}

        # We need to simulate predicting history[i] given history[:i]
        # Skip the first 5 elements to build some initial sub_history context
        for i in range(5, len(self.history)):
            sub_history = self.history[:i]
            # According to memory: The actual result corresponds to the current index i (new_history[i].get('resultTruyenThong'))
            actual_result = self.history[i].get('resultTruyenThong') or self.history[i].get('result')

            if not actual_result:
                continue

            # Run all algos
            preds = {
                'markov': self._algo_markov(sub_history),
                'trend': self._algo_trend(sub_history),
                'majority': self._algo_majority(sub_history),
                'sum_analysis': self._algo_sum(sub_history)
            }
            # Run async LLM
            preds['llm_ensemble'] = await self._algo_llm_ensemble(sub_history, skip_llm=True)

            for algo, pred in preds.items():
                if pred:
                    self.algo_performance[algo]['total'] += 1
                    if pred == actual_result:
                        self.algo_performance[algo]['correct'] += 1

        # Calculate best algo
        best_accuracy = -1
        best_algo = self.current_optimal_algo
        for algo, stats in self.algo_performance.items():
            if stats['total'] > 0:
                acc = stats['correct'] / stats['total']
                if acc > best_accuracy:
                    best_accuracy = acc
                    best_algo = algo

        self.current_optimal_algo = best_algo
        logger.info(f"Optimization complete. New optimal algorithm: {self.current_optimal_algo} with accuracy: {best_accuracy:.2f}")

    async def predict_next(self, skip_llm=False):
        """Make prediction for the next session using the current optimal algorithm."""
        sub_history = self.history

        if self.current_optimal_algo == 'llm_ensemble':
            prediction = await self._algo_llm_ensemble(sub_history, skip_llm)
        elif self.current_optimal_algo == 'markov':
            prediction = self._algo_markov(sub_history)
        elif self.current_optimal_algo == 'trend':
            prediction = self._algo_trend(sub_history)
        elif self.current_optimal_algo == 'majority':
            prediction = self._algo_majority(sub_history)
        elif self.current_optimal_algo == 'sum_analysis':
            prediction = self._algo_sum(sub_history)
        else:
            prediction = "TAI" if random.random() > 0.5 else "XIU"

        return prediction

    def get_stats(self):
        acc = 0
        if self.total_predictions > 0:
            acc = (self.correct_predictions / self.total_predictions) * 100

        logic_perf = {}
        for algo, stats in self.algo_performance.items():
            if stats['total'] > 0:
                logic_perf[algo] = (stats['correct'] / stats['total']) * 100
            else:
                logic_perf[algo] = 0.0

        return {
            'total_predictions': self.total_predictions,
            'correct_predictions': self.correct_predictions,
            'accuracy': acc,
            'current_algorithm': self.current_optimal_algo,
            'logic_performance': logic_perf
        }
