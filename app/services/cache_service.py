"""
Cache service for database operations
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.db_models import (
    CachedIndexData,
    SentimentHistory,
    PredictionLog,
    IndexQuoteCache
)


# Cache TTL configurations (in minutes)
CACHE_TTL = {
    "quote": 5,           # Real-time quotes: 5 minutes
    "daily_data": 60,     # Daily historical data: 1 hour
    "intraday_data": 15,  # Intraday data: 15 minutes
    "sentiment": 30,      # Sentiment analysis: 30 minutes
}


def is_cache_valid(fetched_at: datetime, cache_type: str) -> bool:
    """Check if cached data is still valid"""
    if not fetched_at:
        return False
    ttl_minutes = CACHE_TTL.get(cache_type, 60)
    expiry = fetched_at + timedelta(minutes=ttl_minutes)
    return datetime.now() < expiry


# ============== Index Data Cache ==============

def get_cached_index_data(
    db: Session,
    index_id: str,
    period: str,
    interval: str
) -> Optional[List[Dict[str, Any]]]:
    """Get cached index data if available and valid"""
    
    # Get the most recent cache entry for this configuration
    latest = db.query(CachedIndexData).filter(
        and_(
            CachedIndexData.index_id == index_id.upper(),
            CachedIndexData.period == period,
            CachedIndexData.interval == interval
        )
    ).order_by(desc(CachedIndexData.fetched_at)).first()
    
    if not latest:
        return None
    
    # Check if cache is valid
    cache_type = "intraday_data" if interval in ["1m", "5m", "15m", "30m", "1h"] else "daily_data"
    if not is_cache_valid(latest.fetched_at, cache_type):
        return None
    
    # Get all data points
    data_points = db.query(CachedIndexData).filter(
        and_(
            CachedIndexData.index_id == index_id.upper(),
            CachedIndexData.period == period,
            CachedIndexData.interval == interval,
            CachedIndexData.fetched_at == latest.fetched_at
        )
    ).order_by(CachedIndexData.date).all()
    
    return [
        {
            "date": point.date.strftime("%Y-%m-%d %H:%M:%S") if interval in ["1m", "5m", "15m", "30m", "1h"] else point.date.strftime("%Y-%m-%d"),
            "open": point.open_price,
            "high": point.high_price,
            "low": point.low_price,
            "close": point.close_price,
            "volume": point.volume,
            "change_percent": point.change_percent
        }
        for point in data_points
    ]


def cache_index_data(
    db: Session,
    index_id: str,
    symbol: str,
    period: str,
    interval: str,
    data: List[Dict[str, Any]]
):
    """Cache index data to database"""
    fetched_at = datetime.now()
    
    # Delete old cache entries for this configuration (keep last 3)
    old_entries = db.query(CachedIndexData).filter(
        and_(
            CachedIndexData.index_id == index_id.upper(),
            CachedIndexData.period == period,
            CachedIndexData.interval == interval
        )
    ).order_by(desc(CachedIndexData.fetched_at)).all()
    
    # Group by fetched_at and delete old batches
    seen_batches = set()
    for entry in old_entries:
        batch_key = entry.fetched_at.isoformat()
        if batch_key not in seen_batches:
            seen_batches.add(batch_key)
        if len(seen_batches) > 3:
            db.delete(entry)
    
    # Add new cache entries
    for point in data:
        cache_entry = CachedIndexData(
            index_id=index_id.upper(),
            symbol=symbol,
            date=datetime.strptime(point["date"].split()[0], "%Y-%m-%d") if isinstance(point["date"], str) else point["date"],
            open_price=point["open"],
            high_price=point["high"],
            low_price=point["low"],
            close_price=point["close"],
            volume=point["volume"],
            change_percent=point.get("change_percent"),
            period=period,
            interval=interval,
            fetched_at=fetched_at
        )
        db.add(cache_entry)
    
    db.commit()


# ============== Sentiment History ==============

def get_cached_sentiment(
    db: Session,
    index_id: str
) -> Optional[Dict[str, Any]]:
    """Get cached sentiment if available and valid"""
    
    latest = db.query(SentimentHistory).filter(
        SentimentHistory.index_id == index_id.upper()
    ).order_by(desc(SentimentHistory.analyzed_at)).first()
    
    if not latest:
        return None
    
    if not is_cache_valid(latest.analyzed_at, "sentiment"):
        return None
    
    return {
        "score": latest.sentiment_score,
        "label": latest.overall_sentiment,
        "positive_count": latest.positive_count,
        "negative_count": latest.negative_count,
        "neutral_count": latest.neutral_count,
        "articles": latest.articles or [],
        "cached_at": latest.analyzed_at.isoformat()
    }


def save_sentiment_history(
    db: Session,
    index_id: str,
    query: str,
    sentiment_data: Dict[str, Any]
):
    """Save sentiment analysis to history"""
    
    history = SentimentHistory(
        index_id=index_id.upper(),
        query=query,
        overall_sentiment=sentiment_data.get("label"),
        sentiment_score=sentiment_data.get("score"),
        total_articles=len(sentiment_data.get("articles", [])),
        positive_count=sentiment_data.get("positive_count", 0),
        negative_count=sentiment_data.get("negative_count", 0),
        neutral_count=sentiment_data.get("neutral_count", 0),
        articles=sentiment_data.get("articles", [])
    )
    
    db.add(history)
    db.commit()
    
    return history


def get_sentiment_trend(
    db: Session,
    index_id: str,
    days: int = 7
) -> List[Dict[str, Any]]:
    """Get sentiment trend over time"""
    
    since = datetime.now() - timedelta(days=days)
    
    history = db.query(SentimentHistory).filter(
        and_(
            SentimentHistory.index_id == index_id.upper(),
            SentimentHistory.analyzed_at >= since
        )
    ).order_by(SentimentHistory.analyzed_at).all()
    
    return [
        {
            "date": h.analyzed_at.isoformat(),
            "sentiment": h.overall_sentiment,
            "score": h.sentiment_score,
            "article_count": h.total_articles
        }
        for h in history
    ]


# ============== Prediction Logs ==============

def log_prediction(
    db: Session,
    index_id: str,
    prediction_data: Dict[str, Any]
):
    """Log a prediction for future accuracy tracking"""
    
    # Log each predicted day
    for pred in prediction_data.get("predictions", []):
        log = PredictionLog(
            index_id=index_id.upper(),
            target_date=datetime.strptime(pred["date"], "%Y-%m-%d"),
            prediction_days=prediction_data.get("prediction_days"),
            current_price=prediction_data.get("current_price"),
            predicted_price=pred.get("predicted_close"),
            predicted_direction=prediction_data.get("predicted_direction"),
            predicted_change_percent=prediction_data.get("predicted_change_percent"),
            confidence=pred.get("confidence"),
            technical_factors=prediction_data.get("factors", {}).get("technical"),
            sentiment_factors=prediction_data.get("factors", {}).get("sentiment"),
            combined_signal=prediction_data.get("factors", {}).get("combined_signal")
        )
        db.add(log)
    
    db.commit()


def get_prediction_history(
    db: Session,
    index_id: str,
    days: int = 30
) -> List[Dict[str, Any]]:
    """Get prediction history for an index"""
    
    since = datetime.now() - timedelta(days=days)
    
    predictions = db.query(PredictionLog).filter(
        and_(
            PredictionLog.index_id == index_id.upper(),
            PredictionLog.prediction_date >= since
        )
    ).order_by(desc(PredictionLog.prediction_date)).limit(100).all()
    
    return [
        {
            "prediction_date": p.prediction_date.isoformat(),
            "target_date": p.target_date.isoformat(),
            "predicted_price": p.predicted_price,
            "actual_price": p.actual_price,
            "predicted_direction": p.predicted_direction,
            "actual_direction": p.actual_direction,
            "confidence": p.confidence,
            "was_correct": p.was_correct,
            "accuracy_score": p.accuracy_score
        }
        for p in predictions
    ]


def evaluate_past_predictions(db: Session, index_id: str, actual_prices: Dict[str, float]):
    """Evaluate past predictions with actual prices"""
    
    # Get unevaluated predictions for this index
    pending = db.query(PredictionLog).filter(
        and_(
            PredictionLog.index_id == index_id.upper(),
            PredictionLog.actual_price.is_(None),
            PredictionLog.target_date <= datetime.now()
        )
    ).all()
    
    for pred in pending:
        date_str = pred.target_date.strftime("%Y-%m-%d")
        if date_str in actual_prices:
            actual = actual_prices[date_str]
            pred.actual_price = actual
            
            # Calculate actual change
            if pred.current_price:
                actual_change = ((actual - pred.current_price) / pred.current_price) * 100
                pred.actual_change_percent = actual_change
                
                # Determine actual direction
                if actual_change > 0.5:
                    pred.actual_direction = "bullish"
                elif actual_change < -0.5:
                    pred.actual_direction = "bearish"
                else:
                    pred.actual_direction = "neutral"
                
                # Check if prediction was correct
                pred.was_correct = pred.predicted_direction == pred.actual_direction
                
                # Calculate accuracy score (0-1, how close was the prediction)
                if pred.predicted_price:
                    error_percent = abs(pred.predicted_price - actual) / actual * 100
                    pred.accuracy_score = max(0, 1 - (error_percent / 10))  # 10% error = 0 score
            
            pred.evaluated_at = datetime.now()
    
    db.commit()


def get_prediction_accuracy(db: Session, index_id: str) -> Dict[str, Any]:
    """Get overall prediction accuracy for an index"""
    
    evaluated = db.query(PredictionLog).filter(
        and_(
            PredictionLog.index_id == index_id.upper(),
            PredictionLog.was_correct.isnot(None)
        )
    ).all()
    
    if not evaluated:
        return {"total_predictions": 0, "accuracy": None}
    
    correct = sum(1 for p in evaluated if p.was_correct)
    avg_accuracy = sum(p.accuracy_score or 0 for p in evaluated) / len(evaluated)
    
    return {
        "total_predictions": len(evaluated),
        "correct_predictions": correct,
        "direction_accuracy": round(correct / len(evaluated) * 100, 2),
        "price_accuracy": round(avg_accuracy * 100, 2),
        "last_evaluated": max(p.evaluated_at for p in evaluated if p.evaluated_at).isoformat()
    }
