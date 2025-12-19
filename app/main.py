"""
Sentilytics - Market Index Analytics with News Sentiment Prediction
"""
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import os

from app.api import indices, sentiment, predictions, history
from app.core.config import settings
from app.core.database import init_db, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup"""
    # Initialize database tables
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        print("   App will continue but caching/history features may not work")
    yield
    # Cleanup on shutdown
    print("👋 Shutting down Sentilytics...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(indices.router, prefix="/api")
app.include_router(sentiment.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")
app.include_router(history.router, prefix="/api")

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard"""
    html_path = BASE_DIR / "templates" / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return """
    <html>
        <head><title>Sentilytics</title></head>
        <body>
            <h1>Sentilytics API</h1>
            <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/api")
async def api_info():
    """API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "endpoints": {
            "indices": "/api/indices",
            "index_data": "/api/indices/{index_id}",
            "quotes": "/api/indices/quotes",
            "sentiment": "/api/sentiment/{symbol}",
            "predictions": "/api/predict/{index_id}",
            "prediction_sentiment": "/api/predict/{index_id}/sentiment",
            "sentiment_history": "/api/history/sentiment/{index_id}",
            "prediction_history": "/api/history/predictions/{index_id}",
            "accuracy_stats": "/api/history/accuracy"
        },
        "database": {
            "caching": "enabled",
            "history_tracking": "enabled"
        }
    }
