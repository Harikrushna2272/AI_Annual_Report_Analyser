from typing import List, Dict, Any
import requests
from datetime import datetime, timedelta

class NewsAPI:
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys

    def get_company_news(self, company: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get company news from multiple sources
        """
        news = []
        news.extend(self._get_newsapi_news(company, days))
        news.extend(self._get_bloomberg_news(company, days))
        news.extend(self._get_reuters_news(company, days))
        return news

    def _get_newsapi_news(self, company: str, days: int) -> List[Dict[str, Any]]:
        """
        Get news from NewsAPI.org
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': company,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'sortBy': 'relevancy',
                'language': 'en',
                'apiKey': self.api_keys['newsapi']
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') == 'ok':
                articles = data.get('articles', [])
                return [{
                    'title': article.get('title'),
                    'description': article.get('description'),
                    'url': article.get('url'),
                    'source': article.get('source', {}).get('name'),
                    'published_at': article.get('publishedAt'),
                    'provider': 'newsapi'
                } for article in articles]
        except Exception as e:
            print(f"NewsAPI error: {str(e)}")
        return []

    def _get_bloomberg_news(self, company: str, days: int) -> List[Dict[str, Any]]:
        """
        Get news from Bloomberg API
        """
        try:
            # Bloomberg API implementation
            # Note: This requires a Bloomberg Terminal subscription
            pass
        except Exception as e:
            print(f"Bloomberg API error: {str(e)}")
        return []

    def _get_reuters_news(self, company: str, days: int) -> List[Dict[str, Any]]:
        """
        Get news from Reuters API
        """
        try:
            # Reuters API implementation
            pass
        except Exception as e:
            print(f"Reuters API error: {str(e)}")
        return []

    def get_industry_news(self, industry: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get industry-specific news
        """
        try:
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': f"{industry} industry",
                'from': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                'sortBy': 'relevancy',
                'language': 'en',
                'apiKey': self.api_keys['newsapi']
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') == 'ok':
                articles = data.get('articles', [])
                return [{
                    'title': article.get('title'),
                    'description': article.get('description'),
                    'url': article.get('url'),
                    'source': article.get('source', {}).get('name'),
                    'published_at': article.get('publishedAt'),
                    'provider': 'newsapi'
                } for article in articles]
        except Exception as e:
            print(f"Industry news error: {str(e)}")
        return []

    def analyze_market_sentiment(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze market sentiment from news articles
        """
        try:
            from textblob import TextBlob
            
            total_sentiment = 0.0
            article_count = 0
            
            for item in news_items:
                text = f"{item.get('title', '')} {item.get('description', '')}"
                if text.strip():
                    blob = TextBlob(text)
                    total_sentiment += blob.sentiment.polarity
                    article_count += 1
            
            if article_count > 0:
                average_sentiment = total_sentiment / article_count
                
                # Convert to sentiment label
                if average_sentiment > 0.2:
                    sentiment = 'positive'
                elif average_sentiment < -0.2:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'
                
                return {
                    'sentiment': sentiment,
                    'confidence': abs(average_sentiment),
                    'mentions': article_count
                }
        except Exception as e:
            print(f"Sentiment analysis error: {str(e)}")
        
        return {
            'sentiment': 'neutral',
            'confidence': 0.0,
            'mentions': 0
        }
