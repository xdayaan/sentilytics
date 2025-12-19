"""
Service for fetching news articles
"""
import requests
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# Cache for news to avoid hitting API limits
_news_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl = 300  # 5 minutes


def fetch_news(query: str, page_size: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch news articles from NewsAPI
    
    Args:
        query: Search query
        page_size: Number of articles to fetch
    
    Returns:
        List of article dictionaries
    """
    # Check cache
    cache_key = f"{query}_{page_size}"
    if cache_key in _news_cache:
        cached = _news_cache[cache_key]
        if datetime.now().timestamp() - cached["timestamp"] < _cache_ttl:
            return cached["articles"]
    
    if not NEWS_API_KEY or NEWS_API_KEY == "your_newsapi_key_here":
        # Return mock data if no API key
        return _get_mock_news(query)
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "pageSize": page_size,
            "sortBy": "publishedAt",
            "apiKey": NEWS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            
            # Cache the results
            _news_cache[cache_key] = {
                "articles": articles,
                "timestamp": datetime.now().timestamp()
            }
            
            return articles
        else:
            print(f"NewsAPI error: {response.status_code}")
            return _get_mock_news(query)
            
    except Exception as e:
        print(f"Error fetching news: {e}")
        return _get_mock_news(query)


def _get_mock_news(query: str) -> List[Dict[str, Any]]:
    """
    Return mock news data for testing without API key
    """
    # Generate varied mock news based on query
    sentiments = [
        ("rally", "positive"),
        ("surge", "positive"),
        ("gains", "positive"),
        ("optimism", "positive"),
        ("growth", "positive"),
        ("decline", "negative"),
        ("fall", "negative"),
        ("concerns", "negative"),
        ("volatility", "negative"),
        ("uncertainty", "neutral"),
        ("stable", "neutral"),
        ("mixed signals", "neutral"),
    ]
    
    mock_articles = []
    base_time = datetime.now()
    
    for i, (word, _) in enumerate(sentiments[:8]):
        mock_articles.append({
            "title": f"{query} markets show {word} amid global economic shifts",
            "source": {"name": ["Reuters", "Bloomberg", "CNBC", "Financial Times", "WSJ", "MarketWatch", "Yahoo Finance", "Economic Times"][i % 8]},
            "publishedAt": (base_time - timedelta(hours=i*2)).isoformat(),
            "url": f"https://example.com/news/{i}",
            "description": f"Analysis of {query} performance showing {word} patterns..."
        })
    
    return mock_articles
