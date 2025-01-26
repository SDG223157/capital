import time
from openai import OpenAI
import httpx
import logging
import json
from typing import Dict, List
from datetime import datetime
import re
from .get_news import NewsFetcher
class NewsAnalyzer:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            http_client=httpx.Client(timeout=30.0)
        )
        self.logger = logging.getLogger(__name__)

    def _get_completion(self, messages: List[Dict]) -> Dict:
        try:
            response = self.client.chat.completions.create(
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