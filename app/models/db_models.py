"""
SQLAlchemy database models for caching and history tracking
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, Index
from sqlalchemy.sql import func
from app.core.database import Base


class CachedIndexData(Base):
    """Cache for historical index data to reduce API calls"""
    __tablename__ = "cached_index_data"

    id = Column(Integer, primary_key=True, index=True)
    index_id = Column(String(50), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    date = Column(DateTime, nullable=False)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    change_percent = Column(Float)
    
    # Cache metadata
    period = Column(String(10))  # 1d, 1mo, 1y, etc.
    interval = Column(String(10))  # 1d, 1h, etc.
    fetched_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_index_date', 'index_id', 'date'),
        Index('idx_index_period', 'index_id', 'period', 'interval'),
    )


class SentimentHistory(Base):
    """Track sentiment analysis history over time"""
    __tablename__ = "sentiment_history"

    id = Column(Integer, primary_key=True, index=True)
    index_id = Column(String(50), nullable=False, index=True)
    query = Column(String(255), nullable=False)
    
    # Aggregate sentiment
    overall_sentiment = Column(String(20))  # positive, negative, neutral
    sentiment_score = Column(Float)  # -1 to 1
    
    # Article counts
    total_articles = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    
    # Detailed results (JSON)
    articles = Column(JSON)  # List of article sentiment results
    
    analyzed_at = Column(DateTime, default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_sentiment_index_date', 'index_id', 'analyzed_at'),
    )


class PredictionLog(Base):
    """Log predictions to track accuracy over time"""
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    index_id = Column(String(50), nullable=False, index=True)
    
    # Prediction details
    prediction_date = Column(DateTime, default=func.now())  # When prediction was made
    target_date = Column(DateTime, nullable=False)  # Date being predicted
    prediction_days = Column(Integer)  # Number of days ahead
    
    # Prices
    current_price = Column(Float)  # Price when prediction was made
    predicted_price = Column(Float)  # Predicted price
    actual_price = Column(Float, nullable=True)  # Actual price (filled later)
    
    # Prediction metrics
    predicted_direction = Column(String(20))  # bullish, bearish, neutral
    predicted_change_percent = Column(Float)
    confidence = Column(Float)
    
    # Analysis factors (stored as JSON)
    technical_factors = Column(JSON)
    sentiment_factors = Column(JSON)
    combined_signal = Column(Float)
    
    # Accuracy tracking (filled after target date)
    actual_direction = Column(String(20), nullable=True)
    actual_change_percent = Column(Float, nullable=True)
    was_correct = Column(Boolean, nullable=True)
    accuracy_score = Column(Float, nullable=True)  # How close was the prediction
    
    evaluated_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_prediction_index_target', 'index_id', 'target_date'),
        Index('idx_prediction_pending', 'actual_price'),  # Find unevaluated predictions
    )


class IndexQuoteCache(Base):
    """Cache for real-time quotes with short TTL"""
    __tablename__ = "index_quote_cache"

    id = Column(Integer, primary_key=True, index=True)
    index_id = Column(String(50), nullable=False, unique=True)
    symbol = Column(String(20), nullable=False)
    name = Column(String(100))
    country = Column(String(50))
    
    # Quote data
    current_price = Column(Float)
    previous_close = Column(Float)
    change = Column(Float)
    change_percent = Column(Float)
    volume = Column(Integer)
    day_high = Column(Float)
    day_low = Column(Float)
    fifty_two_week_high = Column(Float)
    fifty_two_week_low = Column(Float)
    
    # Cache timestamp
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class UserWatchlist(Base):
    """User's favorite indices for quick access"""
    __tablename__ = "user_watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)  # For future auth
    index_id = Column(String(50), nullable=False)
    
    # Display preferences
    display_order = Column(Integer, default=0)
    show_in_dashboard = Column(Boolean, default=True)
    
    added_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_user_watchlist', 'user_id', 'index_id', unique=True),
    )
