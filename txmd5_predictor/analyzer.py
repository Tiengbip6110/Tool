from typing import List, Dict, Any, Tuple
from loguru import logger
from collections import defaultdict

class Analyzer:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.best_algorithm = "markov_1"
        self.algorithms = {
            "markov_1": self._predict_markov_1,
            "markov_2": self._predict_markov_2,
            "markov_3": self._predict_markov_3,
            "rolling_avg_5": self._predict_rolling_avg_5,
            "rolling_avg_10": self._predict_rolling_avg_10,
            "streak_breaker": self._predict_streak_breaker,
            "exact_match_4": self._predict_exact_match_4,
            "dice_pattern": self._predict_dice_pattern,
            "shadow_logic": self._predict_shadow_logic,
            "frequent_sum": self._predict_frequent_sum,
            "trend_momentum": self._predict_trend_momentum,
            "ensemble_vote": self._predict_ensemble_vote
        }
        self.stats = {
            "total_predicted": 0,
            "correct_predictions": 0,
            "algorithm_scores": {k: {"correct": 0, "total": 0} for k in self.algorithms.keys()}
        }
        self.current_prediction = None
        self.current_prediction_session_id = None

    def initialize_history(self, history: List[Dict[str, Any]]):
        self.history = history.copy()
        logger.info(f"Analyzer initialized with {len(self.history)} historical records.")
        self._simulate_and_optimize()

    def process_new_session(self, session_data: Dict[str, Any]):
        """Called when a new session result arrives."""
        actual_result = session_data.get("resultTruyenThong")
        session_id = session_data.get("id")

        # Evaluate previous prediction if exists
        if self.current_prediction and self.current_prediction_session_id == session_id:
            self.stats["total_predicted"] += 1
            is_correct = (self.current_prediction == actual_result)
            if is_correct:
                self.stats["correct_predictions"] += 1
                logger.success(f"Prediction for {session_id} was CORRECT ({actual_result}). Accuracy: {self.get_accuracy():.2f}%")
            else:
                logger.warning(f"Prediction for {session_id} was WRONG (Predicted: {self.current_prediction}, Actual: {actual_result}). Re-optimizing...")
                # Add to history before simulating to include this result
                self.history.append(session_data)
                self._simulate_and_optimize()
                # Skip adding again since it's already added

        if session_data not in self.history:
            self.history.append(session_data)

        # Make next prediction
        next_session_id = session_id + 1
        self.current_prediction = self.predict_next()
        self.current_prediction_session_id = next_session_id
        logger.info(f"Predicted NEXT ({next_session_id}): {self.current_prediction} using {self.best_algorithm}")

    def predict_next(self) -> str:
        """Predicts the next result using the currently selected best algorithm."""
        if not self.history:
            return "TAI" # Default fallback

        prediction_func = self.algorithms.get(self.best_algorithm, self._predict_markov_1)
        return prediction_func(self.history)

    def _simulate_and_optimize(self):
        """Runs all algorithms on the entire history to find the most accurate one."""
        if len(self.history) < 10:
            return

        logger.info("Running backtesting to optimize algorithms...")

        # Reset scores
        for k in self.stats["algorithm_scores"]:
            self.stats["algorithm_scores"][k] = {"correct": 0, "total": 0}

        # Simulate from index 10 to end
        for i in range(10, len(self.history)):
            sub_history = self.history[:i]
            actual_next = self.history[i].get("resultTruyenThong")

            for alg_name, alg_func in self.algorithms.items():
                predicted = alg_func(sub_history)
                self.stats["algorithm_scores"][alg_name]["total"] += 1
                if predicted == actual_next:
                    self.stats["algorithm_scores"][alg_name]["correct"] += 1

        # Find best
        best_acc = -1
        best_alg = self.best_algorithm
        for alg_name, scores in self.stats["algorithm_scores"].items():
            if scores["total"] > 0:
                acc = scores["correct"] / scores["total"]
                if acc > best_acc:
                    best_acc = acc
                    best_alg = alg_name

        self.best_algorithm = best_alg
        logger.info(f"Optimization complete. Best algorithm selected: {self.best_algorithm} with {best_acc*100:.2f}% accuracy.")

    def get_accuracy(self) -> float:
        if self.stats["total_predicted"] == 0:
            return 0.0
        return (self.stats["correct_predictions"] / self.stats["total_predicted"]) * 100

    # --- Predictive Algorithms ---

    def _predict_markov_1(self, history: List[Dict[str, Any]]) -> str:
        """Predicts based on the probability of transition from the last state."""
        if not history: return "TAI"
        last_state = history[-1].get("resultTruyenThong")
        transitions = {"TAI": {"TAI": 0, "XIU": 0}, "XIU": {"TAI": 0, "XIU": 0}}

        for i in range(len(history) - 1):
            current = history[i].get("resultTruyenThong")
            nxt = history[i+1].get("resultTruyenThong")
            if current in transitions and nxt in transitions[current]:
                transitions[current][nxt] += 1

        if transitions[last_state]["TAI"] >= transitions[last_state]["XIU"]:
            return "TAI"
        return "XIU"

    def _predict_markov_2(self, history: List[Dict[str, Any]]) -> str:
        if len(history) < 2: return "TAI"
        last_2 = (history[-2].get("resultTruyenThong"), history[-1].get("resultTruyenThong"))
        transitions = defaultdict(lambda: {"TAI": 0, "XIU": 0})

        for i in range(len(history) - 2):
            state = (history[i].get("resultTruyenThong"), history[i+1].get("resultTruyenThong"))
            nxt = history[i+2].get("resultTruyenThong")
            transitions[state][nxt] += 1

        if transitions[last_2]["TAI"] >= transitions[last_2]["XIU"]:
            return "TAI"
        return "XIU"

    def _predict_markov_3(self, history: List[Dict[str, Any]]) -> str:
        if len(history) < 3: return "TAI"
        last_3 = (history[-3].get("resultTruyenThong"), history[-2].get("resultTruyenThong"), history[-1].get("resultTruyenThong"))
        transitions = defaultdict(lambda: {"TAI": 0, "XIU": 0})

        for i in range(len(history) - 3):
            state = (history[i].get("resultTruyenThong"), history[i+1].get("resultTruyenThong"), history[i+2].get("resultTruyenThong"))
            nxt = history[i+3].get("resultTruyenThong")
            transitions[state][nxt] += 1

        if transitions[last_3]["TAI"] >= transitions[last_3]["XIU"]:
            return "TAI"
        return "XIU"

    def _predict_rolling_avg_5(self, history: List[Dict[str, Any]]) -> str:
        """Predicts based on the average points of the last 5 sessions."""
        if len(history) < 5: return "TAI"
        pts = [h.get("point", 10.5) for h in history[-5:]]
        avg = sum(pts) / 5
        # If trend is high, predict TAI (11-18), else XIU (3-10)
        return "TAI" if avg >= 10.5 else "XIU"

    def _predict_rolling_avg_10(self, history: List[Dict[str, Any]]) -> str:
        if len(history) < 10: return "TAI"
        pts = [h.get("point", 10.5) for h in history[-10:]]
        avg = sum(pts) / 10
        return "TAI" if avg >= 10.5 else "XIU"

    def _predict_streak_breaker(self, history: List[Dict[str, Any]]) -> str:
        """Predicts the opposite if the same result has appeared 3 or more times."""
        if len(history) < 3: return "TAI"
        last_results = [h.get("resultTruyenThong") for h in history[-3:]]
        if all(r == "TAI" for r in last_results):
            return "XIU"
        if all(r == "XIU" for r in last_results):
            return "TAI"
        return self._predict_markov_1(history) # Fallback

    def _predict_exact_match_4(self, history: List[Dict[str, Any]]) -> str:
        """Finds the most recent exact match of the last 4 results and predicts what came next."""
        if len(history) < 5: return "TAI"
        pattern = [h.get("resultTruyenThong") for h in history[-4:]]

        for i in range(len(history) - 5, -1, -1):
            match_pattern = [h.get("resultTruyenThong") for h in history[i:i+4]]
            if match_pattern == pattern:
                return history[i+4].get("resultTruyenThong")

        return self._predict_markov_1(history)

    def _predict_dice_pattern(self, history: List[Dict[str, Any]]) -> str:
        """Finds if a specific combination of dice tends to lead to a certain result."""
        if not history: return "TAI"
        last_dices = history[-1].get("dices", [])
        if not last_dices or len(last_dices) != 3:
            return "TAI"

        # Create a simple hash/sum of dice
        dice_sum = sum(last_dices)

        counts = {"TAI": 0, "XIU": 0}
        for i in range(len(history) - 1):
            if sum(history[i].get("dices", [])) == dice_sum:
                nxt_res = history[i+1].get("resultTruyenThong")
                if nxt_res in counts:
                    counts[nxt_res] += 1

        if counts["TAI"] > counts["XIU"]:
            return "TAI"
        elif counts["XIU"] > counts["TAI"]:
            return "XIU"
        return "TAI"

    def _predict_shadow_logic(self, history: List[Dict[str, Any]]) -> str:
        """Predicts based on dice 'shadow' mappings (e.g. 1->6, 2->5, 3->4)."""
        if not history: return "TAI"
        last_dices = history[-1].get("dices", [])
        if not last_dices or len(last_dices) != 3:
            return "TAI"

        shadow_map = {1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}
        shadow_sum = sum(shadow_map.get(d, d) for d in last_dices)
        return "TAI" if shadow_sum >= 11 else "XIU"

    def _predict_frequent_sum(self, history: List[Dict[str, Any]]) -> str:
        """Tracks what result most frequently follows the current point sum."""
        if not history: return "TAI"
        last_point = history[-1].get("point")
        if last_point is None:
            return "TAI"

        counts = {"TAI": 0, "XIU": 0}
        for i in range(len(history) - 1):
            if history[i].get("point") == last_point:
                nxt_res = history[i+1].get("resultTruyenThong")
                if nxt_res in counts:
                    counts[nxt_res] += 1

        if counts["TAI"] > counts["XIU"]:
            return "TAI"
        elif counts["XIU"] > counts["TAI"]:
            return "XIU"
        return "TAI"

    def _predict_trend_momentum(self, history: List[Dict[str, Any]]) -> str:
        """Detects trend momentum based on alternating patterns or strong streaks."""
        if len(history) < 4: return "TAI"
        recent = [h.get("resultTruyenThong") for h in history[-4:]]

        # If strong alternating pattern, continue it
        if recent == ["TAI", "XIU", "TAI", "XIU"]:
            return "TAI"
        if recent == ["XIU", "TAI", "XIU", "TAI"]:
            return "XIU"

        # If strong streak, bet against it (momentum exhaustion)
        if all(r == "TAI" for r in recent):
            return "XIU"
        if all(r == "XIU" for r in recent):
            return "TAI"

        return self._predict_markov_1(history)

    def _predict_ensemble_vote(self, history: List[Dict[str, Any]]) -> str:
        """A meta-algorithm that takes the majority vote of other primary algorithms."""
        if not history: return "TAI"

        votes = {"TAI": 0, "XIU": 0}

        # Don't recurse into ensemble_vote to avoid infinite loop
        primary_algs = [
            self._predict_markov_1, self._predict_markov_2, self._predict_markov_3,
            self._predict_rolling_avg_5, self._predict_streak_breaker,
            self._predict_exact_match_4, self._predict_dice_pattern,
            self._predict_shadow_logic, self._predict_frequent_sum
        ]

        for alg in primary_algs:
            pred = alg(history)
            if pred in votes:
                votes[pred] += 1

        return "TAI" if votes["TAI"] >= votes["XIU"] else "XIU"
