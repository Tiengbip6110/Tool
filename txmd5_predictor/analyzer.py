import logging

logger = logging.getLogger(__name__)

class SicBoAnalyzer:
    def __init__(self):
        self.history = []
        self.best_algo = 'majority'
        self.best_accuracy = 0.0

    def add_session(self, session_data):
        try:
            session_id = session_data['id']
            point = session_data['point']
            result = 'Tai' if point >= 11 else 'Xiu'

            # check if session already in history
            if any(s['id'] == session_id for s in self.history):
                return False

            self.history.append({'id': session_id, 'point': point, 'result': result})
            return True
        except KeyError as e:
            logger.error(f"Invalid session data format: missing {e}")
            return False

    def predict_markov(self, history):
        if len(history) < 2:
            return 'Tai'

        last_state = history[-1]['result']
        transitions = {'Tai': {'Tai': 0, 'Xiu': 0}, 'Xiu': {'Tai': 0, 'Xiu': 0}}

        for i in range(len(history) - 1):
            current = history[i]['result']
            next_state = history[i+1]['result']
            transitions[current][next_state] += 1

        tai_prob = transitions[last_state]['Tai']
        xiu_prob = transitions[last_state]['Xiu']

        return 'Tai' if tai_prob >= xiu_prob else 'Xiu'

    def predict_trend(self, history):
        if not history:
            return 'Tai'
        return history[-1]['result']

    def predict_majority(self, history):
        if not history:
            return 'Tai'

        recent = history[-10:]
        tai_count = sum(1 for s in recent if s['result'] == 'Tai')
        xiu_count = len(recent) - tai_count

        return 'Tai' if tai_count >= xiu_count else 'Xiu'

    def predict_sum_analysis(self, history):
        if not history:
            return 'Tai'

        recent = history[-5:]
        even_count = sum(1 for s in recent if s['point'] % 2 == 0)
        odd_count = len(recent) - even_count

        # basic arbitrary logic based on odd/even sums
        return 'Tai' if even_count >= odd_count else 'Xiu'

    def _algo_llm_ensemble(self, sub_history, algo_name, skip_llm=False):
        if algo_name == 'markov':
            return self.predict_markov(sub_history)
        elif algo_name == 'trend':
            return self.predict_trend(sub_history)
        elif algo_name == 'majority':
            return self.predict_majority(sub_history)
        elif algo_name == 'sum_analysis':
            return self.predict_sum_analysis(sub_history)
        return 'Tai'

    def _simulate_and_optimize(self):
        if len(self.history) < 10:
            return

        algorithms = ['markov', 'trend', 'majority', 'sum_analysis']
        scores = {algo: 0 for algo in algorithms}
        total_evaluations = len(self.history) - 10

        for i in range(10, len(self.history)):
            sub_history = self.history[:i]
            actual_result = self.history[i]['result']

            for algo in algorithms:
                prediction = self._algo_llm_ensemble(sub_history, algo, skip_llm=True)
                if prediction == actual_result:
                    scores[algo] += 1

        best_algo = max(scores, key=scores.get)
        best_accuracy = scores[best_algo] / total_evaluations * 100 if total_evaluations > 0 else 0

        self.best_algo = best_algo
        self.best_accuracy = best_accuracy
        logger.info(f"Optimized. Best Algo: {self.best_algo} with Accuracy: {self.best_accuracy:.2f}%")

    def get_prediction(self):
        if not self.history:
            return "Tai"
        return self._algo_llm_ensemble(self.history, self.best_algo, skip_llm=False)
