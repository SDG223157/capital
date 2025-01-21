# app/utils/analysis/news_analyzer.py

from datetime import datetime
from textblob import TextBlob
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import re
from typing import Dict, List
import logging
from apify_client import ApifyClient
import os

class NewsAnalyzer:
    def __init__(self, api_token: str):
        self.client = ApifyClient("apify_api_ewwcE7264pu0eRgeUBL2RaFk6rmCdy4AaAU9")
        self.logger = logging.getLogger(__name__)
        
        try:
            nltk.download('vader_lexicon')
            self.vader = SentimentIntensityAnalyzer()
            self.logger.info("Successfully initialized VADER analyzer")
        except Exception as e:
            self.logger.error(f"Error initializing VADER: {str(e)}")
            self.vader = None

    # In news_analyzer.py

    def get_news(self, symbols: List[str], limit: int = 10) -> List[Dict]:
        """Fetch news from TradingView via Apify"""
        self.logger.debug(f"Fetching news for symbols: {symbols}, limit: {limit}")
        
        run_input = {
            "symbols": symbols,
            "proxy": {"useApifyProxy": True, "apifyProxyCountry": "US"},
            "resultsLimit": limit,
        }
        
        try:
            if not self.client:
                self.logger.error("Apify client not initialized. Check API token.")
                return []
                
            self.logger.debug("Calling Apify actor")
            run = self.client.actor("mscraper/tradingview-news-scraper").call(run_input=run_input)
            
            if not run:
                self.logger.error("No response from Apify actor")
                return []
                
            dataset_id = run["defaultDatasetId"]
            self.logger.debug(f"Dataset ID received: {dataset_id}")
            
            items = list(self.client.dataset(dataset_id).iterate_items())
            self.logger.debug(f"Retrieved {len(items)} items from dataset")
            
            return items
        except Exception as e:
            self.logger.error(f"Error fetching news: {str(e)}", exc_info=True)
            return []

    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment using TextBlob and VADER"""
        try:
            blob = TextBlob(text)
            textblob_polarity = blob.sentiment.polarity
            textblob_subjectivity = blob.sentiment.subjectivity
            
            vader_scores = self.vader.polarity_scores(text)
            compound_score = vader_scores['compound']
            
            if compound_score >= 0.05:
                sentiment = "POSITIVE"
                explanation = "Strong positive" if compound_score > 0.5 else "Moderately positive"
            elif compound_score <= -0.05:
                sentiment = "NEGATIVE"
                explanation = "Strong negative" if compound_score < -0.5 else "Moderately negative"
            else:
                sentiment = "NEUTRAL"
                explanation = "Neutral or mixed sentiment"
            
            return {
                "overall_sentiment": sentiment,
                "explanation": explanation,
                "confidence": (abs(compound_score) + abs(textblob_polarity)) / 2,
                "scores": {
                    "textblob_polarity": textblob_polarity,
                    "textblob_subjectivity": textblob_subjectivity,
                    "vader_compound": compound_score,
                    "vader_pos": vader_scores['pos'],
                    "vader_neg": vader_scores['neg'],
                    "vader_neu": vader_scores['neu']
                }
            }
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis: {str(e)}")
            return {
                "overall_sentiment": "NEUTRAL",
                "explanation": "Error in analysis",
                "confidence": 0,
                "scores": {}
            }

    def generate_summary(self, text: str) -> Dict:
        """Generate different types of summaries"""
        try:
            blob = TextBlob(text)
            sentences = blob.sentences
            
            if not sentences:
                return {
                    "brief": text,
                    "key_points": text,
                    "market_impact": text
                }
            
            # Brief summary (first and last sentences)
            brief = str(sentences[0])
            if len(sentences) > 1:
                brief += ' ' + str(sentences[-1])
            
            # Select key sentences based on length and content
            key_sentences = []
            market_sentences = []
            
            market_terms = {'revenue', 'profit', 'earnings', 'growth', 'decline', 
                          'market', 'stock', 'shares', 'price', 'trading'}
            
            for sentence in sentences:
                words = set(word.lower() for word in sentence.words)
                market_relevance = len(words.intersection(market_terms))
                
                if market_relevance > 0:
                    market_sentences.append(str(sentence))
                if len(sentence.words) >= 5:  # Minimum length for key points
                    key_sentences.append(str(sentence))
            
            return {
                "brief": brief,
                "key_points": ' '.join(key_sentences[:3]),
                "market_impact": ' '.join(market_sentences[:2])
            }
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            return {
                "brief": "Summary unavailable",
                "key_points": "Summary unavailable",
                "market_impact": "Summary unavailable"
            }

    def extract_metrics(self, text: str) -> Dict:
        """Extract financial metrics with context"""
        metrics = {
            "percentages": [],
            "percentage_contexts": [],
            "currencies": [],
            "currency_contexts": []
        }
        
        try:
            # Find percentages with context
            percentage_matches = re.finditer(r'([^.!?\n]*?\b(\d+\.?\d*)%[^.!?\n]*)', text)
            for match in percentage_matches:
                context = match.group(1).strip()
                percentage = float(match.group(2))
                metrics["percentages"].append(percentage)
                metrics["percentage_contexts"].append(context)
            
            # Find currency amounts with context
            currency_matches = re.finditer(r'([^.!?\n]*?\$(\d+(?:\.\d{1,2})?(?:\s*(?:million|billion|trillion))?)[^.!?\n]*)', text)
            for match in currency_matches:
                context = match.group(1).strip()
                amount = match.group(2)
                metrics["currencies"].append(amount)
                metrics["currency_contexts"].append(context)
            
        except Exception as e:
            self.logger.error(f"Error extracting metrics: {str(e)}")
            
        return metrics

    def analyze_article(self, article: Dict) -> Dict:
        """Analyze a single article"""
        try:
            content = article.get("descriptionText", "")
            
            return {
                "title": article.get("title", ""),
                "content": content,
                "url": article.get("storyPath", ""),
                "published_at": datetime.fromtimestamp(
                    article.get("published", 0) / 1000
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "source": article.get("source", "Unknown"),
                "symbols": [symbol["symbol"] for symbol in article.get("relatedSymbols", [])],
                "sentiment": self.analyze_sentiment(content),
                "summary": self.generate_summary(content),
                "metrics": self.extract_metrics(content)
            }
        except Exception as e:
            self.logger.error(f"Error analyzing article: {str(e)}")
            return None