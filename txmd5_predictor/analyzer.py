import random

class Analyzer:
    def __init__(self):
        self.history = []
        self.total_predictions = 0
        self.correct_predictions = 0
        self.current_best_algorithm = None
        self.last_prediction = None
        self.last_prediction_algorithm = None
        self.algorithms = [
            'markov_chain',
            'trend',
            'recent_majority',
            'llm_ensemble',
            'sum_analysis'
        ]

    def predict_markov_chain(self, data):
        # A simple first-order Markov Chain
        if len(data) < 2:
            return 'Tài' # Default

        transitions = {'Tài': {'Tài': 0, 'Xỉu': 0}, 'Xỉu': {'Tài': 0, 'Xỉu': 0}}
        for i in range(len(data) - 1):
            prev_result = data[i]['result']
            next_result = data[i+1]['result']
            if prev_result in transitions and next_result in transitions[prev_result]:
                transitions[prev_result][next_result] += 1

        last_result = data[-1]['result']
        if last_result not in transitions:
             return 'Tài'

        t_tai = transitions[last_result]['Tài']
        t_xiu = transitions[last_result]['Xỉu']

        if t_tai > t_xiu:
            return 'Tài'
        elif t_xiu > t_tai:
            return 'Xỉu'
        else:
            return 'Tài'

    def predict_trend(self, data):
        # Looks for the recent trend
        if not data:
             return 'Tài'

        streak = 1
        last_result = data[-1]['result']
        for i in range(len(data) - 2, -1, -1):
            if data[i]['result'] == last_result:
                streak += 1
            else:
                break

        # If streak is long, follow it, else reverse
        if streak >= 3:
            return last_result
        else:
            return 'Tài' if last_result == 'Xỉu' else 'Xỉu'

    def predict_recent_majority(self, data):
        # Looks at the last N elements and finds the majority
        if not data:
            return 'Tài'

        N = min(10, len(data))
        recent_data = data[-N:]
        tai_count = sum(1 for d in recent_data if d['result'] == 'Tài')
        xiu_count = sum(1 for d in recent_data if d['result'] == 'Xỉu')

        if tai_count >= xiu_count:
            return 'Tài'
        else:
            return 'Xỉu'

    def predict_sum_analysis(self, data):
        if not data:
            return 'Tài'
        recent = data[-5:]
        total_points = sum(d.get('point', sum(d.get('dices', []))) for d in recent)
        avg = total_points / len(recent)
        if avg > 10.5:
            return 'Tài'
        return 'Xỉu'

    def _algo_llm_ensemble(self, data, skip_llm=False):
        if skip_llm:
            return 'Tài'
        return random.choice(['Tài', 'Xỉu'])

    def predict(self, algo_name, data, skip_llm=False):
        if algo_name == 'markov_chain':
            return self.predict_markov_chain(data)
        elif algo_name == 'trend':
            return self.predict_trend(data)
        elif algo_name == 'recent_majority':
            return self.predict_recent_majority(data)
        elif algo_name == 'llm_ensemble':
            return self._algo_llm_ensemble(data, skip_llm=skip_llm)
        elif algo_name == 'sum_analysis':
            return self.predict_sum_analysis(data)
        return 'Tài'

    def _simulate_and_optimize(self):
        if len(self.history) < 10:
            self.current_best_algorithm = self.algorithms[0]
            return

        best_accuracy = -1
        best_algo = None

        for algo in self.algorithms:
            correct = 0
            total = 0

            # Simulate through history, start from index 5 to have some initial data
            for i in range(5, len(self.history)):
                historical_slice = self.history[:i]
                actual_next_result = self.history[i]['result']

                prediction = self.predict(algo, historical_slice, skip_llm=True)
                if prediction == actual_next_result:
                    correct += 1
                total += 1

            if total > 0:
                accuracy = correct / total
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_algo = algo

        self.current_best_algorithm = best_algo if best_algo else self.algorithms[0]

    def process_new_session(self, session):
        # Determine the result based on dice sum (if not directly provided)
        # Assuming the session contains 'result' or we derive it
        if 'result' not in session:
             dice_sum = session.get('point', sum(session.get('dices', [])))
             # Example rule: 3-10 is Xỉu, 11-18 is Tài
             if 3 <= dice_sum <= 10:
                 session['result'] = 'Xỉu'
             else:
                 session['result'] = 'Tài'
             session['point'] = dice_sum

        # Check if previous prediction was correct
        if self.last_prediction is not None:
             self.total_predictions += 1
             if self.last_prediction == session['result']:
                 self.correct_predictions += 1
             else:
                 # Prediction was wrong, trigger optimization
                 self._simulate_and_optimize()

        self.history.append(session)

        # If no best algorithm yet, run initial optimization
        if self.current_best_algorithm is None and len(self.history) >= 10:
             self._simulate_and_optimize()

        # Make next prediction
        if self.current_best_algorithm is None:
             algo_to_use = self.algorithms[0]
        else:
             algo_to_use = self.current_best_algorithm

        self.last_prediction = self.predict(algo_to_use, self.history)
        self.last_prediction_algorithm = algo_to_use

        return {
            'prediction': self.last_prediction,
            'algorithm': self.last_prediction_algorithm,
            'total_predictions': self.total_predictions,
            'correct_predictions': self.correct_predictions
        }
