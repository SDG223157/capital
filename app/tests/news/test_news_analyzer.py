# app/tests/news/test_news_analyzer.py

import unittest
from unittest.mock import patch

class TestNewsAnalyzer(unittest.TestCase):
    def setUp(self):
        from app.utils.news.news_analyzer import NewsAnalyzer
        self.analyzer = NewsAnalyzer()

    def test_analyzer_initialization(self):
        self.assertIsNotNone(self.analyzer)

    def test_sentiment_analysis(self):
        text = "This is a positive test."
        result = self.analyzer.analyze_sentiment(text)
        self.assertIn('sentiment', result)