"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class IndexInfo(BaseModel):
    """Basic index information"""
    id: str
    symbol: str
    name: str
    country: str


class IndexData(BaseModel):
    """Historical price data point"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    change_percent: Optional[float] = None


class IndexResponse(BaseModel):
    """Response for index data request"""
    index_id: str
    name: str
    symbol: str
    country: str
    period: str
    interval: str
    current_price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    data: List[IndexData]


class SentimentResult(BaseModel):
    """Individual sentiment analysis result"""
    headline: str
    source: Optional[str] = None
    published_at: Optional[str] = None
    url: Optional[str] = None
    sentiment: str
    confidence: float
    score: float  # -1 to 1 scale


class SentimentAnalysis(BaseModel):
    """Complete sentiment analysis for an index"""
    index_id: str
    name: str
    total_articles: int
    positive_count: int
    negative_count: int
    neutral_count: int
    average_sentiment_score: float
    sentiment_label: str
    results: List[SentimentResult]


class PredictionData(BaseModel):
    """Prediction data point"""
    date: str
    predicted_close: float
    confidence: float
    sentiment_influence: float


class PredictionResponse(BaseModel):
    """Response for prediction request"""
    index_id: str
    name: str
    current_price: float
    prediction_days: int
    overall_sentiment: str
    sentiment_score: float
    predicted_direction: str
    predicted_change_percent: float
    confidence: float
    historical_data: List[IndexData]
    predictions: List[PredictionData]
    factors: dict
