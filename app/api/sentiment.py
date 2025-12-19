"""
API routes for sentiment analysis
"""
from fastapi import APIRouter, HTTPException, Query
from app.services.news_service import fetch_news
from app.services.sentiment_service import analyze_sentiment

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])


@router.get("/{symbol}")
def sentiment_from_news(
    symbol: str,
    limit: int = Query(default=10, ge=1, le=50, description="Number of articles to analyze")
):
    """
    Analyze sentiment for news articles related to a symbol/query
    
    Uses FinBERT model for financial sentiment analysis
    """
    try:
        articles = fetch_news(symbol)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching news: {str(e)}"
        )
    
    results = []
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    total_score = 0

    for article in articles[:limit]:
        if article.get("title"):
            sentiment = analyze_sentiment(article["title"])
            
            # Calculate score (-1 to 1)
            label = sentiment["sentiment"].lower()
            confidence = sentiment["confidence"]
            
            if label == "positive":
                score = confidence
                positive_count += 1
            elif label == "negative":
                score = -confidence
                negative_count += 1
            else:
                score = 0
                neutral_count += 1
            
            total_score += score
            
            results.append({
                "headline": article["title"],
                "source": article.get("source", {}).get("name", "Unknown"),
                "published_at": article.get("publishedAt"),
                "url": article.get("url"),
                "sentiment": label,
                "confidence": round(confidence, 4),
                "score": round(score, 4)
            })

    # Calculate overall sentiment
    avg_score = total_score / len(results) if results else 0
    
    if avg_score > 0.1:
        overall_sentiment = "positive"
    elif avg_score < -0.1:
        overall_sentiment = "negative"
    else:
        overall_sentiment = "neutral"

    return {
        "symbol": symbol,
        "total_articles": len(results),
        "overall_sentiment": overall_sentiment,
        "average_score": round(avg_score, 4),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "results": results
    }
