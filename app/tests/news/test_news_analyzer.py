# app/tests/news/test_news_analyzer.py
import unittest
from app.utils.news.news_analyzer import NewsAnalyzer

class TestNewsAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = NewsAnalyzer()

    def test_analyze_sentiment_positive(self):
        text = "Great earnings report with strong growth!"
        result = self.analyzer.analyze_sentiment(text)
        self.assertEqual(result["sentiment"], "POSITIVE")
        self.assertGreater(result["score"], 0)

    def test_analyze_sentiment_negative(self):
        text = "Disappointing results with significant losses."
        result = self.analyzer.analyze_sentiment(text)
        self.assertEqual(result["sentiment"], "NEGATIVE")
        self.assertLess(result["score"], 0)

    def test_analyze_sentiment_neutral(self):
        text = "Company released their quarterly report."
        result = self.analyzer.analyze_sentiment(text)
        self.assertEqual(result["sentiment"], "NEUTRAL")

if __name__ == '__main__':
    unittest.main()