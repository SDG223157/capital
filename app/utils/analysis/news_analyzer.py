from openai import OpenAI
import httpx
import logging
from typing import Dict, List
from datetime import datetime
import re
import json
from apify_client import ApifyClient
import time

class NewsAnalyzer:
    def __init__(self, deepseek_api_key: str, apify_token: str):
        self.openai_client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com",
            http_client=httpx.Client(timeout=60.0)
        )
        self.apify_client = ApifyClient(apify_token)
        self.logger = logging.getLogger(__name__)

    def get_news(self, symbols: List[str], limit: int = 10, retries: int = 3) -> List[Dict]:
        self.logger.debug(f"Fetching news for symbols: {symbols}")

        run_input = {
            "symbols": symbols,
            "proxy": {"useApifyProxy": True},
            "resultsLimit": 3
        }

        for attempt in range(retries):
            try:
                run = self.apify_client.actor("mscraper/tradingview-news-scraper").call(run_input=run_input)
                
                if not run or not run.get("defaultDatasetId"):
                    continue

                items = list(self.apify_client.dataset(run["defaultDatasetId"]).iterate_items())
                return items

            except Exception as e:
                self.logger.error(f"Error fetching news (attempt {attempt + 1}): {str(e)}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)

        return []

    def _get_completion(self, messages: List[Dict]) -> Dict:
        try:
            response = self.openai_client.chat.completions.create(
                model="deepseek-chat",
                messages=messages
            )
            content = response.choices[0].message.content
            if '{' in content and '}' in content:
                json_str = content[content.find('{'):content.rfind('}')+1]
                return json.loads(json_str)
            return {}
        except Exception as e:
            self.logger.error(f"API call error: {str(e)}")
            return {}

    def analyze_sentiment(self, text: str) -> Dict:
        messages = [
            {"role": "system", "content": 'Return only a JSON object like {"overall_sentiment": "POSITIVE", "explanation": "...", "confidence": 0.9, "scores": {"positive": 0.8, "neutral": 0.1, "negative": 0.1}}'},
            {"role": "user", "content": f"Analyze sentiment: {text}"}
        ]
        result = self._get_completion(messages)
        return result or {"overall_sentiment": "NEUTRAL", "confidence": 0}

    def generate_summary(self, text: str) -> Dict:
        messages = [
            {"role": "system", "content": 'Return only a JSON object like {"brief": "...", "key_points": "...", "market_impact": "..."}'},
            {"role": "user", "content": f"Summarize: {text}"}
        ]
        result = self._get_completion(messages)
        return result or {"brief": "Summary unavailable", "key_points": ""}

    def analyze_article(self, article: Dict) -> Dict:
        content = article.get("descriptionText", "")
        title = article.get("title", "")
        
        return {
            "external_id": article.get("id", str(hash(title + content))),
            "title": title,
            "url": article.get("storyPath", ""),
            "published_at": datetime.fromtimestamp(
                article.get("published", 0) / 1000
            ).strftime("%Y-%m-%d %H:%M:%S"),
            "source": article.get("source", "Unknown"),
            "symbols": [{"symbol": s["symbol"]} for s in article.get("relatedSymbols", [])],
            "sentiment": self.analyze_sentiment(content),
            "summary": self.generate_summary(content),
            "metrics": self.extract_metrics(content)
        }

    def analyze_sentiment_trend(self, articles: List[Dict]) -> Dict:
        try:
            sorted_articles = sorted(articles, 
                key=lambda x: datetime.fromtimestamp(x.get("published", 0) / 1000))
            
            trends = {
                "sentiment_timeline": [],
                "symbol_sentiment": {},
                "confidence_avg": 0,
                "trend_direction": "NEUTRAL"
            }
            
            for article in sorted_articles:
                sentiment = self.analyze_sentiment(article.get("descriptionText", ""))
                date = datetime.fromtimestamp(
                    article.get("published", 0) / 1000
                ).strftime("%Y-%m-%d")
                
                trends["sentiment_timeline"].append({
                    "date": date,
                    "sentiment": sentiment["overall_sentiment"],
                    "confidence": sentiment["confidence"]
                })
                
                for symbol in article.get("relatedSymbols", []):
                    sym = symbol["symbol"]
                    if sym not in trends["symbol_sentiment"]:
                        trends["symbol_sentiment"][sym] = {
                            "positive": 0, "negative": 0, "neutral": 0
                        }
                    trends["symbol_sentiment"][sym][sentiment["overall_sentiment"].lower()] += 1
            
            if len(trends["sentiment_timeline"]) > 1:
                positive_count = sum(1 for x in trends["sentiment_timeline"] 
                    if x["sentiment"] == "POSITIVE")
                negative_count = sum(1 for x in trends["sentiment_timeline"] 
                    if x["sentiment"] == "NEGATIVE")
                
                total = len(trends["sentiment_timeline"])
                positive_ratio = positive_count / total
                negative_ratio = negative_count / total
                
                if positive_ratio > 0.6:
                    trends["trend_direction"] = "IMPROVING"
                elif negative_ratio > 0.6:
                    trends["trend_direction"] = "DECLINING"
                else:
                    trends["trend_direction"] = "STABLE"
            
            trends["confidence_avg"] = sum(x["confidence"] 
                for x in trends["sentiment_timeline"]) / len(trends["sentiment_timeline"])
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment trend: {str(e)}")
            return {}

    def extract_metrics(self, text: str) -> Dict:
        try:
            return {
                "percentage": {
                    "values": self._extract_percentages(text),
                    "contexts": self._extract_contexts(text, r'\d+%')
                }
            }
        except Exception as e:
            self.logger.error(f"Error extracting metrics: {str(e)}")
            return {}

    def _extract_percentages(self, text: str) -> List[float]:
        matches = re.findall(r'(\d+(?:\.\d+)?)%', text)
        return [float(match) for match in matches]

    def _extract_contexts(self, text: str, pattern: str) -> List[str]:
        contexts = []
        for match in re.finditer(pattern, text):
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            contexts.append(text[start:end].strip())
        return contexts