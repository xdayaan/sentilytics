"""
Application configuration settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = "Sentilytics"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Market Index Analytics with News Sentiment Prediction"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sentilytics.db")
    
    # News API
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    
    # Supported Indices with their Yahoo Finance symbols and display names
    INDICES: dict = {
        # Indian Indices
        "NIFTY50": {"symbol": "^NSEI", "name": "NIFTY 50", "country": "India"},
        "SENSEX": {"symbol": "^BSESN", "name": "BSE SENSEX", "country": "India"},
        "NIFTYBANK": {"symbol": "^NSEBANK", "name": "NIFTY Bank", "country": "India"},
        "NIFTYIT": {"symbol": "^CNXIT", "name": "NIFTY IT", "country": "India"},
        
        # US Indices
        "SP500": {"symbol": "^GSPC", "name": "S&P 500", "country": "USA"},
        "NASDAQ": {"symbol": "^IXIC", "name": "NASDAQ Composite", "country": "USA"},
        "DOWJONES": {"symbol": "^DJI", "name": "Dow Jones Industrial", "country": "USA"},
        "RUSSELL2000": {"symbol": "^RUT", "name": "Russell 2000", "country": "USA"},
        
        # European Indices
        "FTSE100": {"symbol": "^FTSE", "name": "FTSE 100", "country": "UK"},
        "DAX": {"symbol": "^GDAXI", "name": "DAX", "country": "Germany"},
        "CAC40": {"symbol": "^FCHI", "name": "CAC 40", "country": "France"},
        "EUROSTOXX50": {"symbol": "^STOXX50E", "name": "Euro Stoxx 50", "country": "Europe"},
        
        # Asian Indices
        "NIKKEI225": {"symbol": "^N225", "name": "Nikkei 225", "country": "Japan"},
        "HANGSENG": {"symbol": "^HSI", "name": "Hang Seng", "country": "Hong Kong"},
        "SHANGHAI": {"symbol": "000001.SS", "name": "Shanghai Composite", "country": "China"},
        "KOSPI": {"symbol": "^KS11", "name": "KOSPI", "country": "South Korea"},
        "ASX200": {"symbol": "^AXJO", "name": "ASX 200", "country": "Australia"},
        
        # Other Global Indices
        "BOVESPA": {"symbol": "^BVSP", "name": "Bovespa", "country": "Brazil"},
        "TSX": {"symbol": "^GSPTSE", "name": "S&P/TSX Composite", "country": "Canada"},
        "SWISSMARKET": {"symbol": "^SSMI", "name": "Swiss Market Index", "country": "Switzerland"},
    }
    
    # Time periods for data fetching
    TIME_PERIODS: list = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
    
    # Intervals for data
    INTERVALS: list = ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]

settings = Settings()
