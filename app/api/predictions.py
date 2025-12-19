"""
API routes for predictions
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session

from app.services.prediction_service import generate_prediction, get_sentiment_analysis
from app.core.database import get_db
from app.services.cache_service import log_prediction, save_sentiment_history

router = APIRouter(prefix="/predict", tags=["Predictions"])


@router.get("/{index_id}")
def get_prediction(
    index_id: str,
    days: int = Query(default=7, ge=1, le=30, description="Number of days to predict (1-30)"),
    save_to_history: bool = Query(default=True, description="Save prediction to history"),
    db: Session = Depends(get_db)
):
    """
    Generate price prediction for an index based on technical and sentiment analysis
    
    Combines:
    - Technical indicators (SMA, RSI, momentum, trend)
    - News sentiment analysis using FinBERT
    - Volatility-adjusted forecasting
    
    Predictions are automatically logged for future accuracy tracking.
    """
    prediction = generate_prediction(index_id, days=days)
    
    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to generate prediction for '{index_id}'. Index not found or insufficient data."
        )
    
    # Log prediction to database for accuracy tracking
    if save_to_history:
        try:
            log_prediction(db, index_id, prediction)
            
            # Also save sentiment history
            if prediction.get("factors", {}).get("sentiment"):
                sentiment_data = prediction["factors"]["sentiment"]
                sentiment_data["articles"] = []  # Don't store full articles in log
                save_sentiment_history(db, index_id, prediction.get("name", index_id), sentiment_data)
        except Exception as e:
            # Don't fail the request if logging fails
            print(f"Warning: Failed to log prediction: {e}")
    
    return prediction


@router.get("/{index_id}/sentiment")
def get_index_sentiment(
    index_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed sentiment analysis for an index
    
    Analyzes recent news articles using FinBERT financial sentiment model
    """
    sentiment = get_sentiment_analysis(index_id)
    
    if not sentiment or not sentiment.get("articles"):
        return {
            "index_id": index_id,
            "message": "No recent news articles found for sentiment analysis",
            "sentiment": sentiment
        }
    
    # Save sentiment to history
    try:
        save_sentiment_history(db, index_id, index_id, sentiment)
    except Exception as e:
        print(f"Warning: Failed to save sentiment history: {e}")
    
    return {
        "index_id": index_id,
        "overall_sentiment": sentiment["label"],
        "sentiment_score": sentiment["score"],
        "total_articles": len(sentiment["articles"]),
        "positive_count": sentiment["positive_count"],
        "negative_count": sentiment["negative_count"],
        "neutral_count": sentiment["neutral_count"],
        "articles": sentiment["articles"]
    }
