"""
Service for fetching index/stock data using yfinance
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.core.config import settings


def get_all_indices() -> List[Dict[str, str]]:
    """Get list of all supported indices"""
    indices = []
    for idx_id, info in settings.INDICES.items():
        indices.append({
            "id": idx_id,
            "symbol": info["symbol"],
            "name": info["name"],
            "country": info["country"]
        })
    return indices


def get_index_info(index_id: str) -> Optional[Dict[str, str]]:
    """Get info for a specific index"""
    if index_id.upper() not in settings.INDICES:
        return None
    info = settings.INDICES[index_id.upper()]
    return {
        "id": index_id.upper(),
        "symbol": info["symbol"],
        "name": info["name"],
        "country": info["country"]
    }


def fetch_index_data(
    index_id: str,
    period: str = "1mo",
    interval: str = "1d"
) -> Optional[Dict[str, Any]]:
    """
    Fetch historical data for an index
    
    Args:
        index_id: The index identifier (e.g., 'NIFTY50', 'SP500')
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
        interval: Data interval (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo)
    
    Returns:
        Dictionary with index info and historical data
    """
    index_info = get_index_info(index_id)
    if not index_info:
        return None
    
    try:
        ticker = yf.Ticker(index_info["symbol"])
        
        # Fetch historical data
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return None
        
        # Get current info
        info = ticker.info
        current_price = info.get("regularMarketPrice") or info.get("previousClose") or hist["Close"].iloc[-1]
        previous_close = info.get("previousClose") or hist["Close"].iloc[-2] if len(hist) > 1 else current_price
        
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close else 0
        
        # Format data for response
        data = []
        for idx, row in hist.iterrows():
            date_str = idx.strftime("%Y-%m-%d %H:%M:%S") if interval in ["1m", "5m", "15m", "30m", "1h"] else idx.strftime("%Y-%m-%d")
            
            prev_close = data[-1]["close"] if data else row["Open"]
            day_change = ((row["Close"] - prev_close) / prev_close * 100) if prev_close else 0
            
            data.append({
                "date": date_str,
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
                "change_percent": round(day_change, 2)
            })
        
        return {
            "index_id": index_info["id"],
            "name": index_info["name"],
            "symbol": index_info["symbol"],
            "country": index_info["country"],
            "period": period,
            "interval": interval,
            "current_price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "data": data
        }
        
    except Exception as e:
        print(f"Error fetching data for {index_id}: {e}")
        return None


def fetch_realtime_quotes() -> List[Dict[str, Any]]:
    """Fetch real-time quotes for all indices"""
    quotes = []
    
    for idx_id, info in settings.INDICES.items():
        try:
            ticker = yf.Ticker(info["symbol"])
            ticker_info = ticker.info
            
            current_price = ticker_info.get("regularMarketPrice") or ticker_info.get("previousClose", 0)
            previous_close = ticker_info.get("previousClose", current_price)
            
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            quotes.append({
                "id": idx_id,
                "name": info["name"],
                "symbol": info["symbol"],
                "country": info["country"],
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": ticker_info.get("regularMarketVolume", 0),
                "market_cap": ticker_info.get("marketCap"),
                "day_high": ticker_info.get("dayHigh"),
                "day_low": ticker_info.get("dayLow"),
                "fifty_two_week_high": ticker_info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": ticker_info.get("fiftyTwoWeekLow"),
            })
        except Exception as e:
            print(f"Error fetching quote for {idx_id}: {e}")
            continue
    
    return quotes


def get_index_summary(index_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed summary for an index"""
    index_info = get_index_info(index_id)
    if not index_info:
        return None
    
    try:
        ticker = yf.Ticker(index_info["symbol"])
        info = ticker.info
        
        return {
            "id": index_info["id"],
            "name": index_info["name"],
            "symbol": index_info["symbol"],
            "country": index_info["country"],
            "current_price": info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose"),
            "open": info.get("regularMarketOpen"),
            "day_high": info.get("dayHigh"),
            "day_low": info.get("dayLow"),
            "volume": info.get("regularMarketVolume"),
            "avg_volume": info.get("averageVolume"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "fifty_day_avg": info.get("fiftyDayAverage"),
            "two_hundred_day_avg": info.get("twoHundredDayAverage"),
        }
    except Exception as e:
        print(f"Error fetching summary for {index_id}: {e}")
        return None
