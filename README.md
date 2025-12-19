# Sentilytics

> **Market Index Analytics with News Sentiment Prediction**

A powerful FastAPI application that provides comprehensive market index analysis, news sentiment evaluation, and AI-powered price predictions.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- **Global Index Coverage**: Support for 20+ major indices including:
  - 🇮🇳 Indian: NIFTY 50, SENSEX, NIFTY Bank, NIFTY IT
  - 🇺🇸 US: S&P 500, NASDAQ, Dow Jones, Russell 2000
  - 🇪🇺 European: FTSE 100, DAX, CAC 40, Euro Stoxx 50
  - Asian: Nikkei 225, Hang Seng, Shanghai Composite, KOSPI, ASX 200
  - Others: Bovespa, TSX, Swiss Market Index

- **News Sentiment Analysis**: FinBERT-powered sentiment analysis of financial news
- **AI Predictions**: Combines technical indicators with sentiment for price forecasting
- **Interactive Dashboard**: Beautiful, responsive web interface with real-time charts
- **Technical Indicators**: RSI, SMA, momentum, volatility analysis

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   cd Sentilytics
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment** (optional)
   
   Edit `.env` file:
   ```env
   DATABASE_URL=
   NEWS_API_KEY=your_newsapi_key_here  # Get from https://newsapi.org
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Open in browser**
   - Dashboard: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Indices

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/indices/` | GET | List all supported indices |
| `/api/indices/quotes` | GET | Get real-time quotes for all indices |
| `/api/indices/{index_id}` | GET | Get historical data for an index |
| `/api/indices/{index_id}/summary` | GET | Get detailed summary for an index |

### Sentiment

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sentiment/{symbol}` | GET | Analyze sentiment for news articles |

### Predictions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/predict/{index_id}` | GET | Generate AI price prediction |
| `/api/predict/{index_id}/sentiment` | GET | Get detailed sentiment analysis |

### Query Parameters

- `period`: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
- `interval`: Data interval (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo)
- `days`: Prediction days (1-30)

## Project Structure

```
Sentilytics/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── api/
│   │   ├── indices.py       # Index data endpoints
│   │   ├── sentiment.py     # Sentiment analysis endpoints
│   │   └── predictions.py   # Prediction endpoints
│   ├── core/
│   │   ├── config.py        # Application configuration
│   │   └── database.py      # Database setup
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── services/
│   │   ├── index_service.py      # Index data fetching
│   │   ├── news_service.py       # News API integration
│   │   ├── sentiment_service.py  # FinBERT sentiment analysis
│   │   └── prediction_service.py # Price prediction logic
│   └── templates/
│       └── index.html       # Dashboard UI
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── README.md
```

## How Predictions Work

Sentilytics uses a hybrid approach combining:

1. **Technical Analysis (60% weight)**
   - Trend: SMA crossover signals
   - Momentum: Rate of change analysis
   - RSI: Overbought/oversold adjustments
   - Volatility: Risk assessment

2. **Sentiment Analysis (40% weight)**
   - FinBERT model for financial text
   - News article sentiment scoring
   - Aggregate sentiment calculation

The combined signal determines:
- **Direction**: Bullish, Bearish, or Neutral
- **Magnitude**: Based on volatility and signal strength
- **Confidence**: Decreases over prediction horizon

## Dashboard Features

- **Dark Theme**: Modern, eye-friendly design
- **Interactive Charts**: Chart.js with hover tooltips
- **Sentiment Gauge**: Visual representation of market mood
- **Real-time Updates**: Refresh data on demand
- **Responsive Design**: Works on desktop and mobile

## Configuration

### Supported Indices

Edit `app/core/config.py` to add or modify indices:

```python
INDICES = {
    "NIFTY50": {"symbol": "^NSEI", "name": "NIFTY 50", "country": "India"},
    # Add more indices...
}
```

### News API

Get a free API key from [NewsAPI](https://newsapi.org) for real news data. Without it, the app uses mock data.

## Development

```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Format code
black app/
```


---

**Built using FastAPI, Chart.js, and FinBERT**
