import json
from collections import defaultdict

class Analyzer:
    def __init__(self):
        self.history = []  # List of results (TAI/XIU)
        self.dice_history = [] # List of tuple (dice1, dice2, dice3)
        self.sum_history = [] # List of sums

        # Algorithmic models
        self.markov_model = defaultdict(lambda: {"TAI": 0, "XIU": 0})
        self.sum_frequency = defaultdict(lambda: {"TAI": 0, "XIU": 0})

        self.algorithms = {
            "markov_order_1": self._predict_markov_1,
            "markov_order_2": self._predict_markov_2,
            "markov_order_3": self._predict_markov_3,
            "frequent_sum": self._predict_frequent_sum,
            "trend_momentum": self._predict_trend_momentum,
            "ensemble_voting": self._predict_ensemble
        }

        self.current_best_algorithm = "ensemble_voting"
        self.algorithm_stats = {name: {"correct": 0, "total": 0} for name in self.algorithms.keys()}

        self.sessions_predicted = 0
        self.correct_predictions = 0

    def add_record(self, result: str, dices: list, point: int):
        self.history.append(result)
        self.dice_history.append(dices)
        self.sum_history.append(point)

        # Update Markov model
        if len(self.history) > 1:
            prev = self.history[-2]
            self.markov_model[prev][result] += 1

            if len(self.history) > 2:
                prev_2 = f"{self.history[-3]}_{self.history[-2]}"
                self.markov_model[prev_2][result] += 1

            if len(self.history) > 3:
                prev_3 = f"{self.history[-4]}_{self.history[-3]}_{self.history[-2]}"
                self.markov_model[prev_3][result] += 1

        # Update sum frequency
        if len(self.sum_history) > 1:
            prev_sum = self.sum_history[-2]
            self.sum_frequency[prev_sum][result] += 1

    def _predict_markov_1(self):
        if len(self.history) < 1: return "TAI"
        state = self.history[-1]
        counts = self.markov_model[state]
        if counts["TAI"] > counts["XIU"]: return "TAI"
        if counts["XIU"] > counts["TAI"]: return "XIU"
        return "TAI"

    def _predict_markov_2(self):
        if len(self.history) < 2: return self._predict_markov_1()
        state = f"{self.history[-2]}_{self.history[-1]}"
        counts = self.markov_model[state]
        if counts["TAI"] > counts["XIU"]: return "TAI"
        if counts["XIU"] > counts["TAI"]: return "XIU"
        return self._predict_markov_1()

    def _predict_markov_3(self):
        if len(self.history) < 3: return self._predict_markov_2()
        state = f"{self.history[-3]}_{self.history[-2]}_{self.history[-1]}"
        counts = self.markov_model[state]
        if counts["TAI"] > counts["XIU"]: return "TAI"
        if counts["XIU"] > counts["TAI"]: return "XIU"
        return self._predict_markov_2()

    def _predict_frequent_sum(self):
        if len(self.sum_history) < 1: return "TAI"
        current_sum = self.sum_history[-1]
        counts = self.sum_frequency[current_sum]
        if counts["TAI"] > counts["XIU"]: return "TAI"
        if counts["XIU"] > counts["TAI"]: return "XIU"
        return "TAI"

    def _predict_trend_momentum(self):
        # Predicts continuation of recent trend if streak >= 3
        if len(self.history) < 3: return "TAI"
        last_3 = self.history[-3:]
        if last_3 == ["TAI", "TAI", "TAI"]: return "TAI"
        if last_3 == ["XIU", "XIU", "XIU"]: return "XIU"
        # Otherwise, assume it breaks
        return "TAI" if self.history[-1] == "XIU" else "XIU"

    def _predict_ensemble(self):
        predictions = {
            "markov_1": self._predict_markov_1(),
            "markov_2": self._predict_markov_2(),
            "markov_3": self._predict_markov_3(),
            "freq_sum": self._predict_frequent_sum(),
            "trend": self._predict_trend_momentum()
        }

        tai_votes = sum(1 for p in predictions.values() if p == "TAI")
        xiu_votes = sum(1 for p in predictions.values() if p == "XIU")

        return "TAI" if tai_votes >= xiu_votes else "XIU"

    def evaluate_prediction(self, actual_result: str, predicted_result: str):
        self.sessions_predicted += 1

        # Update individual algorithm stats
        for name, alg in self.algorithms.items():
            alg_pred = alg()
            self.algorithm_stats[name]["total"] += 1
            if alg_pred == actual_result:
                self.algorithm_stats[name]["correct"] += 1

        if predicted_result == actual_result:
            self.correct_predictions += 1
        else:
            # Prediction failed, trigger optimization
            print(f"Prediction failed (Predicted {predicted_result}, Actual {actual_result}). Triggering optimization...")
            self._simulate_and_optimize()

    def _simulate_and_optimize(self):
        if self.sessions_predicted < 10:
            return # Need some data to optimize

        best_accuracy = -1
        best_alg = "ensemble_voting"

        for name, stats in self.algorithm_stats.items():
            if stats["total"] > 0:
                accuracy = stats["correct"] / stats["total"]
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_alg = name

        if best_alg != self.current_best_algorithm:
            print(f"Algorithm optimized! Switching from {self.current_best_algorithm} to {best_alg} (Accuracy: {best_accuracy*100:.2f}%)")
            self.current_best_algorithm = best_alg

    def get_current_logic_accuracy(self):
        stats = self.algorithm_stats[self.current_best_algorithm]
        if stats["total"] == 0: return 0.0
        return (stats["correct"] / stats["total"]) * 100.0

    def predict(self):
        # Use the current best algorithm
        alg = self.algorithms.get(self.current_best_algorithm, self._predict_ensemble)
        return alg()
