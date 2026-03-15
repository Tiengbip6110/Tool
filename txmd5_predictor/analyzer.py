import logging
from typing import List, Dict, Any, Tuple
from predictor import AI_Predictor

logger = logging.getLogger(__name__)

class Analyzer:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.ai_predictor = AI_Predictor()

        # Basic patterns tracked: 1-1, 2-2, 1-2-1, streak (bệt)
        self.algorithms = {
            "streak": self._predict_streak,
            "alternating": self._predict_alternating,
            "markov_1": self._predict_markov_order_1,
            "markov_2": self._predict_markov_order_2,
            "dice_sum": self._predict_dice_sum,
            "ai_ensemble": self._predict_ai_ensemble
        }
        self.accuracy: Dict[str, float] = {k: 0.0 for k in self.algorithms.keys()}
        self.predictions: Dict[str, str] = {k: None for k in self.algorithms.keys()}
        self.correct_counts: Dict[str, int] = {k: 0 for k in self.algorithms.keys()}
        self.total_evaluated: Dict[str, int] = {k: 0 for k in self.algorithms.keys()}
        self.best_algorithm = None

    async def add_session(self, session: Dict[str, Any]):
        self.history.append(session)
        # Evaluate previous predictions
        self._evaluate_predictions(session["result"])
        # Update predictions for next session
        await self._update_predictions()
        # Find the current best algorithm
        self._update_best_algorithm()

    def _evaluate_predictions(self, actual_result: str):
        if not self.history or actual_result not in ["TAI", "XIU"]:
            return

        for algo_name, predicted_result in self.predictions.items():
            if predicted_result is not None:
                self.total_evaluated[algo_name] += 1
                if predicted_result == actual_result:
                    self.correct_counts[algo_name] += 1

                # Update accuracy
                if self.total_evaluated[algo_name] > 0:
                    self.accuracy[algo_name] = self.correct_counts[algo_name] / self.total_evaluated[algo_name]

    async def _update_predictions(self):
        for algo_name, algo_func in self.algorithms.items():
            if algo_name == "ai_ensemble":
                self.predictions[algo_name] = await algo_func()
            else:
                self.predictions[algo_name] = algo_func()

    def _update_best_algorithm(self):
        if not self.total_evaluated:
            return

        # Require at least 5 evaluations to trust an algorithm
        valid_algos = {k: v for k, v in self.accuracy.items() if self.total_evaluated[k] >= 5}
        if not valid_algos:
            # Fallback to absolute best if none meet threshold
            valid_algos = self.accuracy
            if sum(self.total_evaluated.values()) == 0:
                self.best_algorithm = None
                return

        best_algo = max(valid_algos, key=valid_algos.get)
        self.best_algorithm = best_algo
        logger.debug(f"Current best algorithm: {self.best_algorithm} with {self.accuracy[best_algo]:.2%} accuracy")

    def get_best_prediction(self) -> Tuple[str, str, float]:
        """Returns: (best_algorithm_name, predicted_result, accuracy)"""
        if not self.best_algorithm:
            return None, None, 0.0
        return self.best_algorithm, self.predictions[self.best_algorithm], self.accuracy[self.best_algorithm]

    def get_all_predictions(self) -> Dict[str, Any]:
        return {
            "predictions": self.predictions,
            "accuracy": self.accuracy,
            "best": self.best_algorithm
        }

    # --- Prediction Algorithms ---
    def _predict_streak(self) -> str:
        """Predicts that the current streak will continue (bệt)."""
        if not self.history:
            return "TAI" # Default
        return self.history[-1]["result"]

    def _predict_alternating(self) -> str:
        """Predicts the opposite of the last result (1-1)."""
        if not self.history:
            return "XIU"
        return "TAI" if self.history[-1]["result"] == "XIU" else "XIU"

    def _predict_markov_order_1(self) -> str:
        """Looks at what usually follows the last result."""
        if len(self.history) < 2:
            return self._predict_streak()

        last_result = self.history[-1]["result"]
        counts = {"TAI": 0, "XIU": 0}
        for i in range(len(self.history) - 1):
            if self.history[i]["result"] == last_result:
                next_res = self.history[i+1]["result"]
                if next_res in counts:
                    counts[next_res] += 1

        if counts["TAI"] > counts["XIU"]:
            return "TAI"
        elif counts["XIU"] > counts["TAI"]:
            return "XIU"
        return self._predict_streak()

    def _predict_markov_order_2(self) -> str:
        """Looks at what usually follows the last TWO results."""
        if len(self.history) < 3:
            return self._predict_markov_order_1()

        last_2 = (self.history[-2]["result"], self.history[-1]["result"])
        counts = {"TAI": 0, "XIU": 0}

        for i in range(len(self.history) - 2):
            if (self.history[i]["result"], self.history[i+1]["result"]) == last_2:
                next_res = self.history[i+2]["result"]
                if next_res in counts:
                    counts[next_res] += 1

        if counts["TAI"] > counts["XIU"]:
            return "TAI"
        elif counts["XIU"] > counts["TAI"]:
            return "XIU"
        return self._predict_markov_order_1()

    def _predict_dice_sum(self) -> str:
        """Basic logic based on the sum of the last dice."""
        if not self.history:
            return "TAI"

        last_point = self.history[-1].get("point", 11)
        # If point was very low (3-5), expect rebound to TAI? Just a heuristic
        if last_point <= 6:
            return "TAI"
        elif last_point >= 15:
            return "XIU"
        # Mid-range: just alternate
        return "TAI" if self.history[-1]["result"] == "XIU" else "XIU"

    async def _predict_ai_ensemble(self) -> str:
        """Call AI Predictor combining ML models to predict."""
        # Find the best algorithmic prediction to feed to ensemble
        algo_predictions = {k: v for k, v in self.predictions.items() if k != "ai_ensemble"}

        valid_algos = {k: self.accuracy[k] for k, v in algo_predictions.items() if self.total_evaluated[k] >= 5}
        best_algo_pred = None
        if valid_algos:
            best_algo_name = max(valid_algos, key=valid_algos.get)
            best_algo_pred = algo_predictions[best_algo_name]
        else:
            best_algo_pred = algo_predictions.get("streak", "TAI")

        return await self.ai_predictor.ensemble_predict(self.history, best_algo_pred)
