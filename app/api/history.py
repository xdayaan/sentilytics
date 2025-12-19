"""
API routes for history and analytics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.cache_service import (
    get_sentiment_trend,
    get_prediction_history,
    get_prediction_accuracy,
    evaluate_past_predictions
)
from app.services.index_service import fetch_index_data

router = APIRouter(prefix="/history", tags=["History & Analytics"])


@router.get("/sentiment/{index_id}")
def get_sentiment_history(
    index_id: str,
    days: int = Query(default=7, ge=1, le=90, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """
    Get sentiment analysis history for an index over time.
    Shows how sentiment has changed over the specified period.
    """
    trend = get_sentiment_trend(db, index_id, days=days)
    
    if not trend:
        return {
            "index_id": index_id,
            "days": days,
            "message": "No sentiment history available yet. Analyze the index to start tracking.",
            "data": []
        }
    
    # Calculate trend statistics
    scores = [t["score"] for t in trend if t["score"] is not None]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return {
        "index_id": index_id,
        "days": days,
        "total_analyses": len(trend),
        "average_score": round(avg_score, 4),
        "current_sentiment": trend[-1]["sentiment"] if trend else None,
        "data": trend
    }


@router.get("/predictions/{index_id}")
def get_predictions_history(
    index_id: str,
    days: int = Query(default=30, ge=1, le=180, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """
    Get prediction history for an index.
    Shows past predictions along with their actual outcomes (where available).
    """
    history = get_prediction_history(db, index_id, days=days)
    accuracy = get_prediction_accuracy(db, index_id)
    
    return {
        "index_id": index_id,
        "days": days,
        "accuracy_stats": accuracy,
        "predictions": history
    }


@router.post("/predictions/{index_id}/evaluate")
def evaluate_predictions(
    index_id: str,
    db: Session = Depends(get_db)
):
    """
    Evaluate past predictions against actual prices.
    Fetches current data and compares with predicted values.
    """
    # Fetch recent actual data
    data = fetch_index_data(index_id, period="1mo", interval="1d")
    
    if not data or not data.get("data"):
        raise HTTPException(
            status_code=404,
            detail=f"Unable to fetch data for {index_id}"
        )
    
    # Create price map
    actual_prices = {
        point["date"]: point["close"]
        for point in data["data"]
    }
    
    # Evaluate predictions
    evaluate_past_predictions(db, index_id, actual_prices)
    
    # Get updated accuracy
    accuracy = get_prediction_accuracy(db, index_id)
    
    return {
        "index_id": index_id,
        "message": "Predictions evaluated successfully",
        "accuracy_stats": accuracy
    }


@router.get("/accuracy")
def get_all_accuracy_stats(
    db: Session = Depends(get_db)
):
    """
    Get prediction accuracy statistics for all indices.
    """
    from app.core.config import settings
    
    stats = {}
    for index_id in settings.INDICES.keys():
        accuracy = get_prediction_accuracy(db, index_id)
        if accuracy["total_predictions"] > 0:
            stats[index_id] = accuracy
    
    if not stats:
        return {
            "message": "No evaluated predictions yet",
            "indices": {}
        }
    
    # Calculate overall stats
    total = sum(s["total_predictions"] for s in stats.values())
    correct = sum(s["correct_predictions"] for s in stats.values())
    
    return {
        "overall": {
            "total_predictions": total,
            "correct_predictions": correct,
            "direction_accuracy": round(correct / total * 100, 2) if total > 0 else None
        },
        "by_index": stats
    }
