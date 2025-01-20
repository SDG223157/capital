# app/utils/news/news_analyzer.py
from textblob import TextBlob
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import logging

class NewsAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        nltk.download('vader_lexicon')
        self.vader = SentimentIntensityAnalyzer()

    def analyze_sentiment(self, text: str) -> dict:
        try:
            # TextBlob analysis
            blob = TextBlob(text)
            textblob_score = blob.sentiment.polarity
            
            # VADER analysis
            vader_scores = self.vader.polarity_scores(text)
            
            # Combine scores
            compound_score = vader_scores['compound']
            sentiment = "POSITIVE" if compound_score > 0.05 else \
                       "NEGATIVE" if compound_score < -0.05 else "NEUTRAL"
            
            return {
                "sentiment": sentiment,
                "score": compound_score,
                "confidence": abs(compound_score),
                "details": {
                    "textblob_score": textblob_score,
                    "vader_scores": vader_scores
                }
            }
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis: {e}")
            return {
                "sentiment": "NEUTRAL",
                "score": 0,
                "confidence": 0,
                "details": {}
            }