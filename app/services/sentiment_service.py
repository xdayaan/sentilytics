from transformers import pipeline

sentiment_model = pipeline(
    "sentiment-analysis",
    model="ProsusAI/finbert"
)

def analyze_sentiment(text: str):
    result = sentiment_model(text)[0]
    return {
        "sentiment": result["label"].lower(),
        "confidence": round(result["score"], 4)
    }
