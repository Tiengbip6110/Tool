import collections

class PredictorAnalyzer:
    def __init__(self):
        self.best_logic = "ensemble"
        self.accuracy_stats = {}
        self.algorithms = [
            "markov_1", "markov_2", "markov_3",
            "streak_breaker", "dice_shadow",
            "exact_pattern", "frequent_sums", "trend_momentum", "ensemble"
        ]

    def predict_markov(self, history, order):
        if len(history) < order + 1:
            return "TAI"

        last_n = [h["resultTruyenThong"] for h in history[-order:]]
        counts = {"TAI": 0, "XIU": 0}

        for i in range(len(history) - order):
            if [h["resultTruyenThong"] for h in history[i:i+order]] == last_n:
                next_res = history[i+order]["resultTruyenThong"]
                counts[next_res] += 1

        if counts["TAI"] > counts["XIU"]:
            return "TAI"
        elif counts["XIU"] > counts["TAI"]:
            return "XIU"
        return "TAI"

    def predict_streak_breaker(self, history):
        if not history: return "TAI"
        last_res = history[-1]["resultTruyenThong"]
        streak = 0
        for h in reversed(history):
            if h["resultTruyenThong"] == last_res:
                streak += 1
            else:
                break

        if streak >= 4:
            return "XIU" if last_res == "TAI" else "TAI"
        return last_res

    def predict_dice_shadow(self, history):
        # Dice shadow ('bóng'): 1->6, 2->5, 3->4
        if not history: return "TAI"
        last_dices = history[-1].get("dices", [])
        if len(last_dices) == 3:
            shadow_sum = sum([7 - d for d in last_dices])
            return "TAI" if shadow_sum > 10 else "XIU"
        return "TAI"

    def predict_exact_pattern(self, history):
        if len(history) < 5: return "TAI"
        recent = [h["resultTruyenThong"] for h in history[-5:]]

        # 1-1 pattern: TAI, XIU, TAI, XIU, TAI -> XIU
        if recent == ["TAI", "XIU", "TAI", "XIU", "TAI"]: return "XIU"
        if recent == ["XIU", "TAI", "XIU", "TAI", "XIU"]: return "TAI"

        # 2-2 pattern: TAI, TAI, XIU, XIU -> TAI
        if recent[-4:] == ["TAI", "TAI", "XIU", "XIU"]: return "TAI"
        if recent[-4:] == ["XIU", "XIU", "TAI", "TAI"]: return "XIU"

        return "TAI"

    def predict_frequent_sums(self, history):
        if not history: return "TAI"
        sums = [h.get("point", 0) for h in history]
        if not sums: return "TAI"
        most_common = collections.Counter(sums).most_common(1)[0][0]
        return "TAI" if most_common > 10 else "XIU"

    def predict_trend_momentum(self, history):
        if len(history) < 10: return "TAI"
        recent_10 = [h["resultTruyenThong"] for h in history[-10:]]
        tai_count = recent_10.count("TAI")
        return "TAI" if tai_count >= 5 else "XIU"

    def predict_ensemble(self, history):
        preds = [
            self.predict_markov(history, 1),
            self.predict_markov(history, 2),
            self.predict_markov(history, 3),
            self.predict_streak_breaker(history),
            self.predict_dice_shadow(history),
            self.predict_exact_pattern(history),
            self.predict_frequent_sums(history),
            self.predict_trend_momentum(history)
        ]
        counts = collections.Counter(preds)
        return counts.most_common(1)[0][0]

    def get_prediction_by_logic(self, logic, history):
        if logic == "markov_1": return self.predict_markov(history, 1)
        if logic == "markov_2": return self.predict_markov(history, 2)
        if logic == "markov_3": return self.predict_markov(history, 3)
        if logic == "streak_breaker": return self.predict_streak_breaker(history)
        if logic == "dice_shadow": return self.predict_dice_shadow(history)
        if logic == "exact_pattern": return self.predict_exact_pattern(history)
        if logic == "frequent_sums": return self.predict_frequent_sums(history)
        if logic == "trend_momentum": return self.predict_trend_momentum(history)
        if logic == "ensemble": return self.predict_ensemble(history)
        return "TAI"

    def _simulate_and_optimize(self, history):
        if len(history) < 20:
            return

        scores = {alg: 0 for alg in self.algorithms}

        # Test on the last 50 results (or fewer if history is short)
        test_size = min(50, len(history) - 5)
        test_history = history[:-test_size]
        actual_results = history[-test_size:]

        for i, actual in enumerate(actual_results):
            current_hist = test_history + actual_results[:i]
            if not current_hist: continue

            for alg in self.algorithms:
                pred = self.get_prediction_by_logic(alg, current_hist)
                if pred == actual.get("resultTruyenThong"):
                    scores[alg] += 1

        if scores:
            self.best_logic = max(scores, key=scores.get)
            self.accuracy_stats = {alg: (score / test_size * 100) for alg, score in scores.items()}

    def predict(self, history, prediction_failed=False):
        if prediction_failed or not self.best_logic:
            self._simulate_and_optimize(history)

        return self.get_prediction_by_logic(self.best_logic, history)
