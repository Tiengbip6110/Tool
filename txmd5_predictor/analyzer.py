import logging
import asyncio
from typing import List, Dict, Any, Tuple
import os
import openai
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class SicBoAnalyzer:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.algorithms = ["markov", "trend", "recent_majority", "sum_analysis", "llm_ensemble"]
        self.current_algorithm = "recent_majority"
        self.predictions_made = 0
        self.correct_predictions = 0
        self.last_prediction: Tuple[str, str] = None # (session_id, prediction)
        self.openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", "dummy")) if os.environ.get("OPENAI_API_KEY") else None

    def add_history(self, sessions: List[Dict[str, Any]]):
        """Add new sessions to history, ensuring no duplicates."""
        existing_ids = {s['id'] for s in self.history}
        new_sessions = [s for s in sessions if s['id'] not in existing_ids]

        # Keep history sorted by ID (assuming sequential)
        self.history.extend(new_sessions)
        self.history.sort(key=lambda x: int(x['id']) if str(x['id']).isdigit() else x['id'])

        # Limit history size to prevent memory issues (e.g. keep last 1000)
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

    def get_stats(self) -> Dict[str, Any]:
        """Return current statistics for the reporting bot."""
        win_rate = (self.correct_predictions / self.predictions_made * 100) if self.predictions_made > 0 else 0.0
        return {
            "total_sessions": len(self.history),
            "predicted_sessions": self.predictions_made,
            "current_algorithm": self.current_algorithm,
            "win_rate": win_rate
        }

    async def predict_next(self) -> str:
        """Main method to predict the next session outcome."""
        if not self.history:
            return "unknown"

        # Delegate to the currently selected algorithm
        prediction = await self._run_algorithm(self.current_algorithm, self.history)

        # Estimate next session ID (usually current_last_id + 1, but depends on API)
        # We just store the prediction. Verification happens when the next result arrives.
        next_session_id = str(int(self.history[-1]['id']) + 1) if str(self.history[-1]['id']).isdigit() else "next"
        self.last_prediction = (next_session_id, prediction)

        return prediction

    def verify_prediction(self, new_session: Dict[str, Any]):
        """Check if the last prediction was correct."""
        if not self.last_prediction:
            return

        pred_id, pred_val = self.last_prediction
        # We check if the newly arrived session matches our predicted ID
        if str(new_session['id']) == pred_id:
            actual_point = new_session.get('point')
            if actual_point is None:
                return

            actual_val = "tai" if actual_point >= 11 else "xiu"
            self.predictions_made += 1

            if actual_val == pred_val:
                self.correct_predictions += 1
                logger.info(f"✅ Prediction CORRECT! Session: {pred_id}, Predicted: {pred_val}, Actual: {actual_point}({actual_val})")
            else:
                logger.info(f"❌ Prediction WRONG! Session: {pred_id}, Predicted: {pred_val}, Actual: {actual_point}({actual_val})")
                # Trigger optimization if prediction is wrong
                asyncio.create_task(self._simulate_and_optimize())

            self.last_prediction = None # Reset after verifying

    async def _run_algorithm(self, algo_name: str, data: List[Dict[str, Any]]) -> str:
        """Run a specific algorithm."""
        if not data:
            return "tai" # Default fallback

        if algo_name == "recent_majority":
            return self._algo_recent_majority(data)
        elif algo_name == "trend":
            return self._algo_trend(data)
        elif algo_name == "markov":
            return self._algo_markov(data)
        elif algo_name == "sum_analysis":
            return self._algo_sum_analysis(data)
        elif algo_name == "llm_ensemble":
            return await self._algo_llm_ensemble(data)

        return "tai" # Fallback

    def _get_result(self, point: int) -> str:
        return "tai" if point >= 11 else "xiu"

    def _algo_recent_majority(self, data: List[Dict[str, Any]], window: int = 10) -> str:
        """Predict based on the most frequent outcome in the recent window."""
        recent = data[-window:] if len(data) >= window else data
        outcomes = [self._get_result(s['point']) for s in recent if 'point' in s]
        if not outcomes: return "tai"

        tai_count = outcomes.count("tai")
        xiu_count = outcomes.count("xiu")
        return "tai" if tai_count >= xiu_count else "xiu"

    def _algo_trend(self, data: List[Dict[str, Any]]) -> str:
        """Analyze if there's a running streak (e.g. 3 Tai in a row)."""
        if len(data) < 3:
            return self._algo_recent_majority(data)

        recent_3 = [self._get_result(s['point']) for s in data[-3:] if 'point' in s]
        if len(recent_3) == 3 and recent_3[0] == recent_3[1] == recent_3[2]:
            # Expecting trend to break after 3 (simple mean reversion logic)
            return "xiu" if recent_3[0] == "tai" else "tai"

        # If no streak, follow the last result
        return self._get_result(data[-1]['point']) if 'point' in data[-1] else "tai"

    def _algo_markov(self, data: List[Dict[str, Any]]) -> str:
        """Simple 1st-order Markov chain to predict next state based on transition probability."""
        if len(data) < 2:
            return "tai"

        transitions = {"tai": {"tai": 0, "xiu": 0}, "xiu": {"tai": 0, "xiu": 0}}

        for i in range(len(data) - 1):
            if 'point' not in data[i] or 'point' not in data[i+1]: continue
            current_state = self._get_result(data[i]['point'])
            next_state = self._get_result(data[i+1]['point'])
            transitions[current_state][next_state] += 1

        last_state = self._get_result(data[-1]['point'])
        if transitions[last_state]["tai"] >= transitions[last_state]["xiu"]:
            return "tai"
        return "xiu"

    def _algo_sum_analysis(self, data: List[Dict[str, Any]]) -> str:
        """Analyze the specific dice sum of the last roll.
           (e.g., sum=11 often followed by xiu, sum=10 often followed by tai)"""
        if not data or 'point' not in data[-1]:
            return "tai"

        last_point = data[-1]['point']
        # Arbitrary sum-based logic derived from standard Sic Bo observations
        if last_point in [11, 12, 13]:
            return "xiu" # Expect downward mean reversion
        elif last_point in [8, 9, 10]:
            return "tai" # Expect upward mean reversion

        return self._algo_recent_majority(data)

    async def _algo_llm_ensemble(self, data: List[Dict[str, Any]], skip_llm: bool = False) -> str:
        """Simulate an ensemble of different AI algorithms voting, including LLM if available."""
        votes = []
        votes.append(self._algo_recent_majority(data))
        votes.append(self._algo_trend(data))
        votes.append(self._algo_markov(data))
        votes.append(self._algo_sum_analysis(data))

        # If OpenAI client is initialized and we are not skipping (e.g. during heavy backtests)
        if self.openai_client and not skip_llm:
            try:
                # Prepare a short history sequence for context
                recent_history = [self._get_result(s['point']) for s in data[-10:] if 'point' in s]
                prompt = f"Analyze this recent sequence of Sic Bo outcomes (tai >= 11, xiu <= 10): {recent_history}. Predict the next outcome based on patterns. Reply ONLY with the word 'tai' or 'xiu'."

                # We use a quick, cheap model call for rapid predictions
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an algorithmic Sic Bo prediction AI."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=5,
                    timeout=2
                )

                llm_vote = response.choices[0].message.content.strip().lower()
                if llm_vote in ["tai", "xiu"]:
                    # Give LLM double weight in the ensemble
                    votes.extend([llm_vote, llm_vote])
            except Exception as e:
                logger.warning(f"LLM API request failed or timed out: {e}. Falling back to standard ensemble.")

        tai_count = votes.count("tai")
        xiu_count = votes.count("xiu")
        return "tai" if tai_count >= xiu_count else "xiu"

    async def _simulate_and_optimize(self):
        """Backtesting loop to evaluate all algorithms and select the best one."""
        if len(self.history) < 20:
            return # Not enough data to optimize

        logger.info("🔄 Running backtest simulation to optimize algorithm...")

        best_algo = self.current_algorithm
        best_win_rate = 0.0

        # Test each algorithm against the historical data
        for algo in self.algorithms:
            correct = 0
            total = 0

            # Start evaluating from the 10th item onwards
            for i in range(10, len(self.history) - 1):
                # Provide history UP TO index i (exclusive of the current result we want to predict)
                sub_history = self.history[:i]
                # Pass skip_llm=True directly if the algorithm is llm_ensemble to avoid spam
                if algo == "llm_ensemble":
                    prediction = await self._algo_llm_ensemble(sub_history, skip_llm=True)
                else:
                    prediction = await self._run_algorithm(algo, sub_history)

                # The actual result is at index i (remember, memory note says `self.history[i]['point']` not `i+1` because we simulated up to `i` exclusive)
                actual_point = self.history[i].get('point')
                if actual_point is not None:
                    actual_val = self._get_result(actual_point)
                    if prediction == actual_val:
                        correct += 1
                    total += 1

            if total > 0:
                win_rate = correct / total
                if win_rate > best_win_rate:
                    best_win_rate = win_rate
                    best_algo = algo

        if best_algo != self.current_algorithm:
            logger.info(f"✨ Optimized! Switching algorithm from {self.current_algorithm} to {best_algo} (Simulated Win Rate: {best_win_rate*100:.2f}%)")
            self.current_algorithm = best_algo
        else:
            logger.info(f"✅ Current algorithm {self.current_algorithm} remains the best. (Simulated Win Rate: {best_win_rate*100:.2f}%)")

    async def _call_llm_api(self, prompt: str) -> str:
        """Stub for integrating multiple LLM APIs (OpenAI, Gemini, etc.) if needed."""
        # For a full implementation, you would check env vars and route to the respective SDK.
        return "tai"
