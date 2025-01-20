# app/utils/news/news_analyzer.py

from textblob import TextBlob
import nltk
import logging

class NewsAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            nltk.download('vader_lexicon', quiet=True)
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            self.vader = SentimentIntensityAnalyzer()
        except Exception as e:
            self.logger.error(f"Error initializing VADER: {e}")
            self.vader = None

    def analyze_sentiment(self, text):
        try:
            scores = self.vader.polarity_scores(text) if self.vader else {}
            sentiment = "POSITIVE" if scores.get('compound', 0) > 0.05 else \
                       "NEGATIVE" if scores.get('compound', 0) < -0.05 else "NEUTRAL"
            return {
                'sentiment': sentiment,
                'scores': scores
            }
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return {'sentiment': 'NEUTRAL', 'scores': {}}