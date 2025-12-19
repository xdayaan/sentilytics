"""
Prediction service combining technical analysis with sentiment
"""
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.services.index_service import fetch_index_data, get_index_info
from app.services.news_service import fetch_news
from app.services.sentiment_service import analyze_sentiment


def calculate_technical_indicators(data: List[Dict]) -> Dict[str, float]:
    """Calculate technical indicators from price data"""
    if len(data) < 20:
        return {"trend": 0, "momentum": 0, "volatility": 0}
    
    closes = np.array([d["close"] for d in data])
    
    # Simple Moving Averages
    sma_5 = np.mean(closes[-5:])
    sma_20 = np.mean(closes[-20:])
    
    # Trend: SMA crossover signal (-1 to 1)
    trend = (sma_5 - sma_20) / sma_20 if sma_20 else 0
    trend = max(min(trend * 10, 1), -1)  # Normalize to -1 to 1
    
    # Momentum: Rate of change
    roc = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] else 0
    momentum = max(min(roc * 5, 1), -1)
    
    # Volatility: Standard deviation of returns
    returns = np.diff(closes) / closes[:-1]
    volatility = np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0
    
    # RSI (14-period)
    rsi = calculate_rsi(closes, 14)
    
    return {
        "trend": round(trend, 4),
        "momentum": round(momentum, 4),
        "volatility": round(volatility, 4),
        "rsi": round(rsi, 2),
        "sma_5": round(sma_5, 2),
        "sma_20": round(sma_20, 2),
        "current_price": round(closes[-1], 2)
    }


def calculate_rsi(closes: np.ndarray, period: int = 14) -> float:
    """Calculate Relative Strength Index"""
    if len(closes) < period + 1:
        return 50.0
    
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def get_sentiment_analysis(index_id: str) -> Dict[str, Any]:
    """Analyze news sentiment for an index"""
    index_info = get_index_info(index_id)
    if not index_info:
        return {"score": 0, "label": "neutral", "articles": []}
    
    # Create search queries based on index
    queries = [index_info["name"]]
    
    # Add related terms based on index
    market_terms = {
        "NIFTY50": ["NSE India", "Indian stock market", "Nifty"],
        "SENSEX": ["BSE India", "Bombay Stock Exchange", "Sensex"],
        "SP500": ["S&P 500", "US stock market", "Wall Street"],
        "NASDAQ": ["NASDAQ", "tech stocks", "US technology"],
        "DOWJONES": ["Dow Jones", "US blue chips"],
        "NIKKEI225": ["Nikkei", "Japan stocks", "Tokyo Stock Exchange"],
        "FTSE100": ["FTSE", "London Stock Exchange", "UK stocks"],
    }
    
    if index_id.upper() in market_terms:
        queries.extend(market_terms[index_id.upper()][:2])
    
    all_results = []
    
    for query in queries[:2]:  # Limit queries
        articles = fetch_news(query)
        
        for article in articles:
            if article.get("title"):
                sentiment = analyze_sentiment(article["title"])
                
                # Convert sentiment to score (-1 to 1)
                label = sentiment["sentiment"].lower()
                confidence = sentiment["confidence"]
                
                if label == "positive":
                    score = confidence
                elif label == "negative":
                    score = -confidence
                else:
                    score = 0
                
                all_results.append({
                    "headline": article["title"],
                    "source": article.get("source", {}).get("name"),
                    "published_at": article.get("publishedAt"),
                    "url": article.get("url"),
                    "sentiment": label,
                    "confidence": confidence,
                    "score": round(score, 4)
                })
    
    if not all_results:
        return {
            "score": 0,
            "label": "neutral",
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "articles": []
        }
    
    # Calculate aggregate sentiment
    avg_score = np.mean([r["score"] for r in all_results])
    
    positive_count = sum(1 for r in all_results if r["sentiment"] == "positive")
    negative_count = sum(1 for r in all_results if r["sentiment"] == "negative")
    neutral_count = sum(1 for r in all_results if r["sentiment"] == "neutral")
    
    if avg_score > 0.1:
        label = "positive"
    elif avg_score < -0.1:
        label = "negative"
    else:
        label = "neutral"
    
    return {
        "score": round(avg_score, 4),
        "label": label,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "articles": all_results
    }


def generate_prediction(
    index_id: str,
    days: int = 7
) -> Optional[Dict[str, Any]]:
    """
    Generate price predictions combining technical and sentiment analysis
    
    Args:
        index_id: The index identifier
        days: Number of days to predict
    
    Returns:
        Prediction data including forecasted prices
    """
    # Fetch historical data
    index_data = fetch_index_data(index_id, period="3mo", interval="1d")
    if not index_data or not index_data["data"]:
        return None
    
    historical = index_data["data"]
    current_price = index_data["current_price"]
    
    # Calculate technical indicators
    technicals = calculate_technical_indicators(historical)
    
    # Get sentiment analysis
    sentiment = get_sentiment_analysis(index_id)
    
    # Combine signals for prediction
    # Weights: Technical (60%), Sentiment (40%)
    tech_signal = (technicals["trend"] * 0.4 + technicals["momentum"] * 0.6)
    sent_signal = sentiment["score"]
    
    combined_signal = (tech_signal * 0.6) + (sent_signal * 0.4)
    
    # Adjust for RSI (overbought/oversold)
    rsi = technicals.get("rsi", 50)
    if rsi > 70:  # Overbought - reduce bullish signal
        combined_signal *= 0.7
    elif rsi < 30:  # Oversold - reduce bearish signal
        combined_signal *= 0.7
    
    # Determine direction and magnitude
    if combined_signal > 0.1:
        direction = "bullish"
    elif combined_signal < -0.1:
        direction = "bearish"
    else:
        direction = "neutral"
    
    # Calculate predicted change (conservative estimate)
    volatility = technicals.get("volatility", 0.15)
    max_daily_change = volatility / np.sqrt(252) * 2  # 2 sigma move
    
    base_change = combined_signal * max_daily_change * 100
    
    # Generate predictions for each day
    predictions = []
    cumulative_change = 0
    
    for i in range(1, days + 1):
        # Add some randomness and mean reversion
        daily_change = base_change * (0.9 ** i)  # Decay factor
        noise = np.random.normal(0, max_daily_change * 0.3)
        
        cumulative_change += (daily_change + noise * 100)
        
        predicted_price = current_price * (1 + cumulative_change / 100)
        
        # Confidence decreases with time
        day_confidence = max(0.3, 0.85 - (i * 0.07))
        
        future_date = datetime.now() + timedelta(days=i)
        
        predictions.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "predicted_close": round(predicted_price, 2),
            "confidence": round(day_confidence, 2),
            "sentiment_influence": round(sent_signal * 0.4, 4)
        })
    
    # Calculate overall prediction
    final_prediction = predictions[-1]["predicted_close"]
    total_change_percent = ((final_prediction - current_price) / current_price) * 100
    
    # Overall confidence based on signal strength and volatility
    signal_strength = abs(combined_signal)
    confidence = min(0.85, 0.5 + signal_strength * 0.5) * (1 - volatility * 0.5)
    
    return {
        "index_id": index_data["index_id"],
        "name": index_data["name"],
        "current_price": current_price,
        "prediction_days": days,
        "overall_sentiment": sentiment["label"],
        "sentiment_score": sentiment["score"],
        "predicted_direction": direction,
        "predicted_change_percent": round(total_change_percent, 2),
        "confidence": round(confidence, 2),
        "historical_data": historical[-30:],  # Last 30 days
        "predictions": predictions,
        "factors": {
            "technical": {
                "trend": technicals["trend"],
                "momentum": technicals["momentum"],
                "rsi": technicals["rsi"],
                "volatility": round(volatility * 100, 2),
                "sma_5": technicals["sma_5"],
                "sma_20": technicals["sma_20"]
            },
            "sentiment": {
                "score": sentiment["score"],
                "label": sentiment["label"],
                "positive_articles": sentiment["positive_count"],
                "negative_articles": sentiment["negative_count"],
                "neutral_articles": sentiment["neutral_count"]
            },
            "combined_signal": round(combined_signal, 4)
        }
    }
