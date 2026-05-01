import unittest
from analyzer import Analyzer

class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = Analyzer()

    def test_predict_markov(self):
        history = [
            {'resultTruyenThong': 'TAI'},
            {'resultTruyenThong': 'XIU'},
            {'resultTruyenThong': 'TAI'},
            {'resultTruyenThong': 'XIU'},
            {'resultTruyenThong': 'TAI'}
        ]
        # TAI -> XIU (2 times), XIU -> TAI (2 times)
        # Last is TAI. Prediction based on TAI -> XIU transition should be XIU
        prediction = self.analyzer._predict_markov(history)
        self.assertEqual(prediction, 'XIU')

    def test_predict_trend(self):
        history = [
            {'resultTruyenThong': 'TAI'},
            {'resultTruyenThong': 'TAI'}
        ]
        # Trend continues
        prediction = self.analyzer._predict_trend(history)
        self.assertEqual(prediction, 'TAI')

        history2 = [
            {'resultTruyenThong': 'TAI'},
            {'resultTruyenThong': 'XIU'}
        ]
        # Trend breaks, switch to other side (last is XIU, switch to TAI)
        prediction = self.analyzer._predict_trend(history2)
        self.assertEqual(prediction, 'TAI')

    def test_predict_recent_majority(self):
        history = [
            {'resultTruyenThong': 'XIU'},
            {'resultTruyenThong': 'XIU'},
            {'resultTruyenThong': 'TAI'}
        ]
        prediction = self.analyzer._predict_recent_majority(history)
        self.assertEqual(prediction, 'XIU')

if __name__ == '__main__':
    unittest.main()
