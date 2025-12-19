"""
API routes for index data and visualization
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.services.index_service import (
    get_all_indices,
    fetch_index_data,
    fetch_realtime_quotes,
    get_index_summary
)
from app.core.config import settings

router = APIRouter(prefix="/indices", tags=["Indices"])


@router.get("/")
def list_indices():
    """Get list of all supported indices"""
    indices = get_all_indices()
    
    # Group by country
    by_country = {}
    for idx in indices:
        country = idx["country"]
        if country not in by_country:
            by_country[country] = []
        by_country[country].append(idx)
    
    return {
        "total": len(indices),
        "indices": indices,
        "by_country": by_country,
        "available_periods": settings.TIME_PERIODS,
        "available_intervals": settings.INTERVALS
    }


@router.get("/quotes")
def get_realtime_quotes():
    """Get real-time quotes for all indices"""
    quotes = fetch_realtime_quotes()
    return {
        "total": len(quotes),
        "quotes": quotes
    }


@router.get("/{index_id}")
def get_index_data(
    index_id: str,
    period: str = Query(default="1mo", description="Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
    interval: str = Query(default="1d", description="Data interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo")
):
    """Get historical data for a specific index"""
    
    # Validate period
    if period not in settings.TIME_PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period. Choose from: {settings.TIME_PERIODS}"
        )
    
    # Validate interval
    if interval not in settings.INTERVALS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid interval. Choose from: {settings.INTERVALS}"
        )
    
    data = fetch_index_data(index_id, period=period, interval=interval)
    
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"Index '{index_id}' not found or data unavailable"
        )
    
    return data


@router.get("/{index_id}/summary")
def get_index_details(index_id: str):
    """Get detailed summary for a specific index"""
    summary = get_index_summary(index_id)
    
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"Index '{index_id}' not found"
        )
    
    return summary
